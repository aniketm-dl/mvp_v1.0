#!/usr/bin/env python3
"""Download the public OPeRA dataset from Hugging Face."""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
from datasets import load_dataset
from huggingface_hub.utils._errors import HfHubHTTPError
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

REPO_ID = "wang-ziyi/OPeRA"
SPLIT_MAP: Dict[str, Tuple[str, str]] = {
    "opera_users.parquet": ("filtered_user", "train"),
    "opera_actions.parquet": ("filtered_action", "train"),
    "opera_sessions.parquet": ("filtered_session", "train"),
}


def download_split(config: str, split: str, target_path: Path, force: bool) -> None:
    """Download a single split and write it to parquet."""

    if target_path.exists() and not force:
        console.print(f"[yellow]⚠️  {target_path.name} already exists, skipping (use --force to overwrite).[/yellow]")
        return

    console.print(f"[cyan]📥 Downloading {config} → {target_path.name}[/cyan]")

    try:
        dataset = load_dataset(REPO_ID, config, split=split)
    except HfHubHTTPError as err:
        console.print(f"[red]❌ Failed to download {config}: {err}[/red]")
        console.print("   Ensure you have set HF_TOKEN if the dataset requires authentication.")
        raise SystemExit(1) from err

    # Convert to pandas DataFrame and save as parquet (single file)
    df = dataset.to_pandas()
    df.to_parquet(target_path, index=False)
    console.print(f"[green]✅ Saved {len(df):,} rows to {target_path}[/green]")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download OPeRA parquet splits from Hugging Face")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("DATA/OPeRA/raw"),
        help="Directory to store parquet files",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing parquet files",
    )

    args = parser.parse_args()

    if not os.environ.get("HF_TOKEN"):
        console.print("[yellow]⚠️  HF_TOKEN not set – continuing anonymously (may be rate-limited).[/yellow]")

    args.out_dir.mkdir(parents=True, exist_ok=True)

    console.print("\n[bold cyan]🔻 Downloading OPeRA dataset[/bold cyan]")
    console.print(f"   Repository: [bold]{REPO_ID}[/bold]")
    console.print(f"   Output dir: {args.out_dir}\n")

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        task = progress.add_task("Downloading splits...", total=len(SPLIT_MAP))
        for filename, (config, split) in SPLIT_MAP.items():
            target_path = args.out_dir / filename
            download_split(config, split, target_path, force=args.force)
            progress.advance(task)

    console.print("\n[bold green]✅ OPeRA dataset download complete![/bold green]")


if __name__ == "__main__":
    main()
