#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from src.data.opera.alignment import OPeRAAligner

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="Preprocess OPeRA raw data into aligned sequences for SSR training."
    )
    parser.add_argument(
        "--survey",
        type=str,
        default="DATA/OPeRA/raw/opera_users.parquet",
        help="Path to survey/user data (parquet)",
    )
    parser.add_argument(
        "--sessions",
        type=str,
        default="DATA/OPeRA/raw/sample_sessions.jsonl",
        help="Path to session logs (JSONL)",
    )
    parser.add_argument(
        "--rationales",
        type=str,
        default="DATA/OPeRA/raw/opera_rationales.jsonl",
        help="Path to rationales (JSONL)",
    )
    parser.add_argument(
        "--outcomes",
        type=str,
        default="DATA/OPeRA/raw/opera_outcomes.jsonl",
        help="Path to outcomes (JSONL)",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="DATA/OPeRA/processed",
        help="Output directory for processed data",
    )
    parser.add_argument(
        "--min-steps",
        type=int,
        default=3,
        help="Minimum steps per session",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=100,
        help="Maximum steps per session",
    )

    args = parser.parse_args()

    console.print("\n[bold cyan]🔧 OPeRA Data Preprocessing Pipeline[/bold cyan]\n")

    # Initialize aligner
    aligner = OPeRAAligner(
        survey_path=Path(args.survey) if Path(args.survey).exists() else None,
        sessions_path=Path(args.sessions) if Path(args.sessions).exists() else None,
        rationales_path=Path(args.rationales) if Path(args.rationales).exists() else None,
        outcomes_path=Path(args.outcomes) if Path(args.outcomes).exists() else None,
        min_steps=args.min_steps,
        max_steps=args.max_steps,
    )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load data sources with progress tracking
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task1 = progress.add_task("Loading survey data...", total=None)
        num_users = aligner.load_survey_data()
        progress.update(task1, completed=True)
        console.print(f"  ✅ Loaded survey data: {num_users} users")

        task2 = progress.add_task("Loading session logs...", total=None)
        num_sessions = aligner.load_sessions_data()
        progress.update(task2, completed=True)
        console.print(f"  ✅ Loaded session logs: {num_sessions} sessions")

        task3 = progress.add_task("Loading rationales...", total=None)
        num_rationales = aligner.load_rationales_data()
        progress.update(task3, completed=True)
        console.print(f"  ✅ Loaded rationales: {num_rationales} entries")

        task4 = progress.add_task("Loading outcomes...", total=None)
        num_outcomes = aligner.load_outcomes_data()
        progress.update(task4, completed=True)
        console.print(f"  ✅ Loaded outcomes: {num_outcomes} entries")

    console.print()

    # Align sessions
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Aligning sessions with survey + rationales + outcomes...", total=None)
        aligned_sessions = aligner.align_all()
        progress.update(task, completed=True)

    console.print(f"  ✅ Aligned {len(aligned_sessions)} sessions successfully\n")

    if len(aligned_sessions) == 0:
        console.print("[bold red]❌ No sessions aligned. Check input data quality.[/bold red]")
        return

    # Save outputs
    console.print("[bold cyan]💾 Saving processed data...[/bold cyan]\n")

    out_sequences = out_dir / "aligned_sequences.jsonl"
    num_saved = aligner.save_aligned(out_sequences, aligned_sessions)
    console.print(f"  ✅ Saved aligned sequences: {out_sequences} ({num_saved} sessions)")

    out_features = out_dir / "persona_features.parquet"
    num_users_feat = aligner.extract_persona_features(aligned_sessions, out_features)
    console.print(f"  ✅ Saved persona features: {out_features} ({num_users_feat} users)")

    out_ssr_pairs = out_dir / "ssr_training_pairs.jsonl"
    num_pairs = aligner.extract_ssr_training_pairs(aligned_sessions, out_ssr_pairs)
    console.print(f"  ✅ Saved SSR training pairs: {out_ssr_pairs} ({num_pairs} pairs)")

    console.print()

    # Display statistics
    table = Table(title="Preprocessing Statistics", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", justify="right", style="green")

    table.add_row("Survey Users", str(num_users))
    table.add_row("Session Logs", str(num_sessions))
    table.add_row("Rationales", str(num_rationales))
    table.add_row("Outcomes", str(num_outcomes))
    table.add_row("Aligned Sessions", str(len(aligned_sessions)))
    table.add_row("Unique Users (features)", str(num_users_feat))
    table.add_row("SSR Training Pairs", str(num_pairs))

    console.print(table)
    console.print("\n[bold green]✅ OPeRA preprocessing complete![/bold green]\n")


if __name__ == "__main__":
    main()
