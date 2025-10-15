#!/usr/bin/env python3
"""Train multi-view encoder with PyTorch Lightning."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pytorch_lightning as pl
import torch
import torch.nn.functional as F
import yaml
from pytorch_lightning.callbacks import (
    EarlyStopping,
    LearningRateMonitor,
    ModelCheckpoint,
)
from pytorch_lightning.loggers import CSVLogger
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.opera.dataset import OPeRADataModule
from src.models.encoder.fuser import MultiViewEncoder
from src.models.encoder.losses import MultiObjectiveLoss


class EncoderLightningModule(pl.LightningModule):
    """PyTorch Lightning module for encoder training."""

    def __init__(self, config: dict, vocab_size: int, num_actions: int):
        super().__init__()
        self.save_hyperparameters()
        self.config = config

        # Build model
        self.model = MultiViewEncoder(
            vocab_size=vocab_size,
            num_actions=num_actions,
            seq_config=config["model"]["sequence"],
            rationale_config=config["model"]["rationale"],
            persona_config=config["model"]["persona"],
            catalog_config=config["model"]["catalog"],
            fusion_config=config["model"]["fusion"],
            fused_dim=config["model"]["fused_dim"],
        )

        # Build loss
        loss_config = config["loss"].copy()
        loss_config["next_action"]["num_actions"] = num_actions
        loss_config["psychometric"]["input_dim"] = config["model"]["fused_dim"]
        loss_config["fused_dim"] = config["model"]["fused_dim"]
        loss_config["persona_dim"] = config["model"]["persona"]["output_dim"]
        loss_config["rationale_dim"] = config["model"]["rationale"]["hidden_dim"]
        self.criterion = MultiObjectiveLoss(loss_config)

        # Metrics tracking
        self.val_action_preds = []
        self.val_action_labels = []

    def forward(self, batch, disable_persona=False, disable_rationale=False):
        """Forward pass."""
        return self.model(
            seq_tokens=batch["seq_tokens"],
            rationale_tokens=batch["rationale_tokens"],
            persona_vec=batch["persona_vec"],
            catalog_vec=batch["catalog_vec"],
            disable_persona=disable_persona,
            disable_rationale=disable_rationale,
        )

    def training_step(self, batch, batch_idx):
        """Training step."""
        outputs = self(batch)

        # Compute rationale mask (non-zero rationales)
        rationale_mask = (batch["rationale_tokens"].sum(dim=1) > 0).float()

        # Compute losses
        losses = self.criterion(
            outputs=outputs,
            action_labels=batch["action_label"],
            rationale_mask=rationale_mask,
        )

        # Log losses
        for loss_name, loss_value in losses.items():
            self.log(
                f"train/{loss_name}_loss",
                loss_value,
                on_step=True,
                on_epoch=True,
                prog_bar=(loss_name == "total"),
            )

        # Compute accuracy
        preds = outputs["action_logits"].argmax(dim=-1)
        acc = (preds == batch["action_label"]).float().mean()
        self.log("train/action_acc", acc, on_step=True, on_epoch=True, prog_bar=True)

        return losses["total"]

    def validation_step(self, batch, batch_idx):
        """Validation step."""
        outputs = self(batch)

        # Compute rationale mask
        rationale_mask = (batch["rationale_tokens"].sum(dim=1) > 0).float()

        # Compute losses
        losses = self.criterion(
            outputs=outputs,
            action_labels=batch["action_label"],
            rationale_mask=rationale_mask,
        )

        # Log losses
        for loss_name, loss_value in losses.items():
            self.log(f"val/{loss_name}_loss", loss_value, prog_bar=(loss_name == "total"))

        # Store predictions for epoch-end metrics
        preds = outputs["action_logits"].argmax(dim=-1)
        self.val_action_preds.append(preds.cpu())
        self.val_action_labels.append(batch["action_label"].cpu())

        return losses["total"]

    def on_validation_epoch_end(self):
        """Compute epoch-level validation metrics."""
        if not self.val_action_preds:
            return

        # Compute accuracy
        all_preds = torch.cat(self.val_action_preds)
        all_labels = torch.cat(self.val_action_labels)
        acc = (all_preds == all_labels).float().mean()

        self.log("val/next_action_acc", acc, prog_bar=True)

        # Clear for next epoch
        self.val_action_preds.clear()
        self.val_action_labels.clear()

    def configure_optimizers(self):
        """Configure optimizer and scheduler."""
        train_config = self.config["training"]

        # Optimizer
        optimizer = AdamW(
            self.parameters(),
            lr=train_config["learning_rate"],
            weight_decay=train_config["weight_decay"],
            betas=train_config["betas"],
            eps=train_config["eps"],
        )

        # Scheduler
        if train_config["lr_scheduler"] == "cosine":
            scheduler = CosineAnnealingLR(
                optimizer,
                T_max=train_config["num_epochs"],
                eta_min=train_config["min_lr"],
            )
            return {
                "optimizer": optimizer,
                "lr_scheduler": {
                    "scheduler": scheduler,
                    "interval": "epoch",
                },
            }

        return optimizer


def main():
    parser = argparse.ArgumentParser(description="Train multi-view encoder")
    parser.add_argument(
        "--data", required=True, help="Path to processed OPeRA data directory"
    )
    parser.add_argument(
        "--config", default="CONFIGS/encoder.yaml", help="Path to config file"
    )
    parser.add_argument(
        "--out", default="artifacts/encoder", help="Output directory for checkpoints"
    )
    parser.add_argument("--fast-dev-run", action="store_true", help="Fast dev run")
    args = parser.parse_args()

    # Load config
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    # Set seed
    pl.seed_everything(config["seed"], workers=True)

    # Setup data
    print(f"Loading data from {args.data}")
    dm = OPeRADataModule(
        args.data,
        batch_size=config["training"]["batch_size"],
        num_workers=config["data"]["num_workers"],
    )
    dm.setup()

    vocab_size = dm.get_vocab_size()
    num_actions = len(set(dm.train_dataset.df["action_label"]))

    print(f"Vocab size: {vocab_size}")
    print(f"Num actions: {num_actions}")
    print(f"Train steps: {len(dm.train_dataset)}")
    print(f"Val steps: {len(dm.val_dataset)}")

    # Build model
    model = EncoderLightningModule(config, vocab_size, num_actions)

    # Callbacks
    output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_callback = ModelCheckpoint(
        dirpath=output_dir / "checkpoints",
        filename="encoder-{epoch:02d}-{val/next_action_acc:.3f}",
        monitor=config["training"]["monitor"],
        mode=config["training"]["mode"],
        save_top_k=config["training"]["save_top_k"],
        save_last=True,
    )

    early_stop_callback = EarlyStopping(
        monitor=config["training"]["monitor"],
        patience=config["training"]["early_stop_patience"],
        min_delta=config["training"]["early_stop_min_delta"],
        mode=config["training"]["mode"],
    )

    lr_monitor = LearningRateMonitor(logging_interval="epoch")

    # Logger
    logger = CSVLogger(output_dir, name="logs")

    # Trainer
    trainer = pl.Trainer(
        max_epochs=config["training"]["num_epochs"],
        accelerator="auto" if config["device"] == "auto" else config["device"],
        devices=1,
        precision=config["training"]["precision"],
        gradient_clip_val=config["training"]["gradient_clip_val"],
        gradient_clip_algorithm=config["training"]["gradient_clip_algorithm"],
        accumulate_grad_batches=config["training"]["accumulate_grad_batches"],
        val_check_interval=config["training"]["val_check_interval"],
        limit_val_batches=config["training"]["limit_val_batches"],
        callbacks=[checkpoint_callback, early_stop_callback, lr_monitor],
        logger=logger,
        deterministic=config["deterministic"],
        fast_dev_run=args.fast_dev_run,
    )

    # Train
    print("\nStarting training...")
    trainer.fit(model, dm)

    # Save best checkpoint path
    best_ckpt = checkpoint_callback.best_model_path
    print(f"\nBest checkpoint: {best_ckpt}")

    # Create symlink to best checkpoint
    best_link = output_dir / "best.ckpt"
    if best_link.exists():
        best_link.unlink()
    if best_ckpt:
        best_link.symlink_to(Path(best_ckpt).resolve())
        print(f"Created symlink: {best_link} -> {best_ckpt}")

    print("\nTraining complete!")


if __name__ == "__main__":
    main()
