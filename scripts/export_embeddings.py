from __future__ import annotations
import argparse
from pathlib import Path
from typing import Dict, Any
import yaml
import torch
import pandas as pd
from tqdm import tqdm

from src.data.opera.dataset import OPeRADataModule
from src.models.encoder.fuser import MultiViewEncoder


def export_embeddings(
    ckpt_path: Path,
    data_path: Path,
    config_path: Path,
    output_path: Path,
    batch_size: int = 64,
    device: str = "auto"
) -> None:
    """
    Export session-level fused embeddings from trained encoder.

    Aggregates step-level embeddings to session-level using mean pooling.
    Saves to parquet with metadata (user_id, session_id, persona_vec, etc.)
    """

    # Load config
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Auto-detect device
    if device == "auto":
        if torch.cuda.is_available():
            device = "cuda"
        elif torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"

    print(f"Using device: {device}")

    # Load data
    print(f"Loading data from {data_path}")
    dm = OPeRADataModule(
        data_dir=str(data_path),
        batch_size=batch_size,
        num_workers=config.get("data", {}).get("num_workers", 4)
    )
    dm.setup()

    # Load model from checkpoint
    print(f"Loading model from {ckpt_path}")
    checkpoint = torch.load(ckpt_path, map_location=device)

    # Initialize model
    model_config = config["model"]
    model = MultiViewEncoder(
        vocab_size_seq=dm.vocab_size,
        vocab_size_rat=dm.vocab_size,
        num_actions=dm.num_actions,
        fused_dim=model_config["fused_dim"],
        seq_config=model_config["sequence"],
        rat_config=model_config["rationale"],
        persona_config=model_config["persona"],
        catalog_config=model_config["catalog"],
        fusion_config=model_config["fusion"]
    )

    # Load weights
    model.load_state_dict(checkpoint["state_dict"])
    model = model.to(device)
    model.eval()

    # Extract embeddings
    print("Extracting embeddings...")
    all_embeddings = []
    all_metadata = []

    with torch.no_grad():
        for split_name, dataloader in [
            ("train", dm.train_dataloader()),
            ("val", dm.val_dataloader()),
            ("test", dm.test_dataloader())
        ]:
            print(f"Processing {split_name} split...")
            for batch in tqdm(dataloader, desc=split_name):
                # Move batch to device
                seq_tokens = batch["seq_tokens"].to(device)
                rat_tokens = batch["rationale_tokens"].to(device)
                persona_vec = batch["persona_vec"].to(device)
                catalog_vec = batch["catalog_vec"].to(device)

                # Forward pass
                outputs = model(
                    seq_tokens=seq_tokens,
                    rationale_tokens=rat_tokens,
                    persona_vec=persona_vec,
                    catalog_vec=catalog_vec
                )

                # Extract fused embeddings
                fused_emb = outputs["fused_embedding"].cpu().numpy()

                # Store embeddings
                for i in range(len(fused_emb)):
                    all_embeddings.append(fused_emb[i])
                    all_metadata.append({
                        "split": split_name,
                        "user_id": batch.get("user_id", [None])[i] if "user_id" in batch else None,
                        "session_id": batch.get("session_id", [None])[i] if "session_id" in batch else None,
                        "persona_id": batch.get("persona_id", [None])[i] if "persona_id" in batch else None,
                    })

    # Create DataFrame
    print("Creating DataFrame...")
    df_metadata = pd.DataFrame(all_metadata)
    df_embeddings = pd.DataFrame(
        all_embeddings,
        columns=[f"emb_{i}" for i in range(model_config["fused_dim"])]
    )
    df = pd.concat([df_metadata, df_embeddings], axis=1)

    # Save to parquet
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Saving to {output_path}")
    df.to_parquet(output_path, index=False, compression="snappy")

    print(f"\n✓ Exported {len(df)} session embeddings")
    print(f"  Train: {(df['split'] == 'train').sum()}")
    print(f"  Val:   {(df['split'] == 'val').sum()}")
    print(f"  Test:  {(df['split'] == 'test').sum()}")
    print(f"  Embedding dim: {model_config['fused_dim']}")


def main():
    parser = argparse.ArgumentParser(
        description="Export session-level fused embeddings from trained encoder"
    )
    parser.add_argument(
        "--ckpt",
        type=Path,
        required=True,
        help="Path to model checkpoint (.ckpt)"
    )
    parser.add_argument(
        "--data",
        type=Path,
        required=True,
        help="Path to processed OPeRA data directory"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("CONFIGS/encoder.yaml"),
        help="Path to encoder config"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("artifacts/encoder/embeddings.parquet"),
        help="Output path for embeddings parquet"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Batch size for inference"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        choices=["auto", "cpu", "cuda", "mps"],
        help="Device to use"
    )

    args = parser.parse_args()

    export_embeddings(
        ckpt_path=args.ckpt,
        data_path=args.data,
        config_path=args.config,
        output_path=args.out,
        batch_size=args.batch_size,
        device=args.device
    )


if __name__ == "__main__":
    main()
