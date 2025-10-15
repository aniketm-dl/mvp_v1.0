#!/usr/bin/env python3
"""Evaluate trained encoder with ablations."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import torch
import yaml
from rich.console import Console
from rich.table import Table
from torch.utils.data import DataLoader

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.opera.dataset import OPeRADataModule

console = Console()


def load_model_from_checkpoint(ckpt_path: str):
    """Load model from checkpoint."""
    from scripts.train.encoder_train import EncoderLightningModule

    model = EncoderLightningModule.load_from_checkpoint(ckpt_path)
    model.eval()
    return model


def compute_next_action_metrics(
    model, dataloader, topk: List[int], disable_persona=False, disable_rationale=False
):
    """Compute next-action prediction metrics."""
    all_logits = []
    all_labels = []

    with torch.no_grad():
        for batch in dataloader:
            outputs = model(
                batch, disable_persona=disable_persona, disable_rationale=disable_rationale
            )
            all_logits.append(outputs["action_logits"].cpu())
            all_labels.append(batch["action_label"].cpu())

    all_logits = torch.cat(all_logits, dim=0)
    all_labels = torch.cat(all_labels, dim=0)

    # Compute top-k accuracy
    metrics = {}
    for k in topk:
        topk_preds = all_logits.topk(k, dim=-1).indices
        correct = (topk_preds == all_labels.unsqueeze(-1)).any(dim=-1).float()
        metrics[f"top{k}_acc"] = correct.mean().item()

    return metrics


def compute_persona_alignment_metrics(
    model, dataloader, recall_k: List[int]
):
    """Compute persona alignment retrieval metrics."""
    all_fused = []
    all_persona = []

    with torch.no_grad():
        for batch in dataloader:
            outputs = model(batch)
            all_fused.append(outputs["fused_embedding"].cpu())
            all_persona.append(outputs["persona_embedding"].cpu())

    all_fused = torch.cat(all_fused, dim=0)
    all_persona = torch.cat(all_persona, dim=0)

    # Normalize
    all_fused = torch.nn.functional.normalize(all_fused, dim=-1)
    all_persona = torch.nn.functional.normalize(all_persona, dim=-1)

    # Compute similarity matrix
    similarity = torch.matmul(all_fused, all_persona.t())

    # Compute recall@k
    metrics = {}
    for k in recall_k:
        topk_indices = similarity.topk(k, dim=-1).indices
        correct_indices = torch.arange(len(all_fused)).unsqueeze(-1)
        recall = (topk_indices == correct_indices).any(dim=-1).float().mean().item()
        metrics[f"recall@{k}"] = recall

    return metrics


def compute_embedding_stats(model, dataloader):
    """Compute embedding quality statistics."""
    all_fused = []

    with torch.no_grad():
        for batch in dataloader:
            outputs = model(batch)
            all_fused.append(outputs["fused_embedding"].cpu().numpy())

    all_fused = np.concatenate(all_fused, axis=0)

    stats = {
        "mean_norm": np.linalg.norm(all_fused, axis=-1).mean(),
        "std_norm": np.linalg.norm(all_fused, axis=-1).std(),
        "mean_value": all_fused.mean(),
        "std_value": all_fused.std(),
    }

    return stats


def run_ablation_study(
    model, dataloader, config: Dict, ablations: List[Dict]
):
    """Run ablation experiments."""
    results = {}

    for ablation in ablations:
        name = ablation["name"]
        disable_persona = ablation.get("disable_persona", False)
        disable_rationale = ablation.get("disable_rationale", False)

        console.print(f"\n[yellow]Running ablation: {name}[/yellow]")
        console.print(
            f"  Disable persona: {disable_persona}, Disable rationale: {disable_rationale}"
        )

        # Compute metrics
        action_metrics = compute_next_action_metrics(
            model,
            dataloader,
            config["eval"]["next_action_topk"],
            disable_persona=disable_persona,
            disable_rationale=disable_rationale,
        )

        results[name] = action_metrics

    return results


def export_embeddings(model, dataloader, output_path: str):
    """Export embeddings to parquet."""
    all_data = {
        "fused_embedding": [],
        "user_id": [],
        "session_id": [],
        "t": [],
        "action_label": [],
    }

    with torch.no_grad():
        for batch in dataloader:
            outputs = model(batch)
            all_data["fused_embedding"].extend(
                outputs["fused_embedding"].cpu().numpy().tolist()
            )
            all_data["user_id"].extend(batch["user_id"])
            all_data["session_id"].extend(batch["session_id"])
            all_data["t"].extend(batch["t"].tolist())
            all_data["action_label"].extend(batch["action_label"].tolist())

    df = pd.DataFrame(all_data)
    df.to_parquet(output_path, index=False)
    console.print(f"[green]✓ Embeddings exported to {output_path}[/green]")


def export_onnx(model, output_path: str, config: Dict):
    """Export model to ONNX."""
    model.eval()

    # Create dummy inputs
    batch_size = 1
    seq_len = config["model"]["sequence"]["max_seq_len"]
    rat_len = config["model"]["rationale"]["max_seq_len"]

    dummy_inputs = (
        torch.randint(0, 100, (batch_size, seq_len)),  # seq_tokens
        torch.randint(0, 100, (batch_size, rat_len)),  # rationale_tokens
        torch.randn(batch_size, 12),  # persona_vec
        torch.randn(batch_size, 10),  # catalog_vec
    )

    # Export
    torch.onnx.export(
        model.model,
        dummy_inputs,
        output_path,
        input_names=["seq_tokens", "rationale_tokens", "persona_vec", "catalog_vec"],
        output_names=["fused_embedding", "action_logits"],
        dynamic_axes={
            "seq_tokens": {0: "batch"},
            "rationale_tokens": {0: "batch"},
            "persona_vec": {0: "batch"},
            "catalog_vec": {0: "batch"},
        }
        if config["export"]["onnx"]["dynamic_axes"]
        else None,
        opset_version=config["export"]["onnx"]["opset_version"],
    )

    console.print(f"[green]✓ ONNX model exported to {output_path}[/green]")


def main():
    parser = argparse.ArgumentParser(description="Evaluate encoder")
    parser.add_argument("--ckpt", required=True, help="Path to checkpoint")
    parser.add_argument(
        "--data", required=True, help="Path to processed OPeRA data directory"
    )
    parser.add_argument(
        "--config", default="CONFIGS/encoder.yaml", help="Path to config file"
    )
    parser.add_argument(
        "--out", default="artifacts/encoder/eval", help="Output directory"
    )
    args = parser.parse_args()

    # Load config
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    output_dir = Path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load model
    console.print(f"[blue]Loading model from {args.ckpt}[/blue]")
    model = load_model_from_checkpoint(args.ckpt)

    # Load data
    console.print(f"[blue]Loading data from {args.data}[/blue]")
    dm = OPeRADataModule(
        args.data, batch_size=config["training"]["batch_size"], num_workers=0
    )
    dm.setup()

    test_loader = dm.test_dataloader()

    # Evaluate next-action prediction
    console.print("\n[yellow]Evaluating next-action prediction[/yellow]")
    action_metrics = compute_next_action_metrics(
        model, test_loader, config["eval"]["next_action_topk"]
    )

    action_table = Table(title="Next-Action Prediction Metrics")
    action_table.add_column("Metric", style="cyan")
    action_table.add_column("Value", style="magenta")

    for metric, value in action_metrics.items():
        action_table.add_row(metric, f"{value:.4f}")

    console.print(action_table)

    # Evaluate persona alignment
    console.print("\n[yellow]Evaluating persona alignment[/yellow]")
    persona_metrics = compute_persona_alignment_metrics(
        model, test_loader, config["eval"]["persona_recall_k"]
    )

    persona_table = Table(title="Persona Alignment Metrics")
    persona_table.add_column("Metric", style="cyan")
    persona_table.add_column("Value", style="magenta")

    for metric, value in persona_metrics.items():
        persona_table.add_row(metric, f"{value:.4f}")

    console.print(persona_table)

    # Compute embedding stats
    if config["eval"]["compute_embedding_stats"]:
        console.print("\n[yellow]Computing embedding statistics[/yellow]")
        emb_stats = compute_embedding_stats(model, test_loader)

        stats_table = Table(title="Embedding Statistics")
        stats_table.add_column("Statistic", style="cyan")
        stats_table.add_column("Value", style="magenta")

        for stat, value in emb_stats.items():
            stats_table.add_row(stat, f"{value:.4f}")

        console.print(stats_table)

    # Run ablations
    if config["ablation"]["enabled"]:
        console.print("\n[yellow]Running ablation study[/yellow]")
        ablation_results = run_ablation_study(
            model, test_loader, config, config["ablation"]["ablations"]
        )

        ablation_table = Table(title="Ablation Study Results")
        ablation_table.add_column("Ablation", style="cyan")
        ablation_table.add_column("Top-1 Acc", style="magenta")

        for abl_name, metrics in ablation_results.items():
            ablation_table.add_row(abl_name, f"{metrics['top1_acc']:.4f}")

        console.print(ablation_table)

        # Save results
        results_df = pd.DataFrame(ablation_results).T
        results_path = output_dir / "ablation_results.csv"
        results_df.to_csv(results_path)
        console.print(f"[green]✓ Ablation results saved to {results_path}[/green]")

    # Export embeddings
    if config["export"]["embeddings"]["enabled"]:
        console.print("\n[yellow]Exporting embeddings[/yellow]")
        emb_path = output_dir / "test_embeddings.parquet"
        export_embeddings(model, test_loader, str(emb_path))

    # Export ONNX
    if config["export"]["onnx"]["enabled"]:
        console.print("\n[yellow]Exporting ONNX model[/yellow]")
        onnx_path = output_dir / "encoder.onnx"
        export_onnx(model, str(onnx_path), config)

    console.print("\n[bold green]✓ Evaluation complete![/bold green]")


if __name__ == "__main__":
    main()
