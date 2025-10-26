#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from src.data.opera.alignment import OPeRAAligner
from src.ssr.llm_elicitation import LLMElicitationEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="Preprocess OPeRA data with LLM elicitation for SSR (per paper methodology)."
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
    parser.add_argument(
        "--max-llm-sessions",
        type=int,
        default=500,
        help="Max sessions to elicit with LLM for cost control (None processes all).",
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        default="gpt-4o-mini",
        help="OpenAI model for elicitation",
    )
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Skip LLM elicitation (use standard extraction)",
    )
    parser.add_argument(
        "--llm-provider",
        type=str,
        default="openai",
        choices=["openai", "google", "gemini"],
        help="LLM provider backend",
    )
    parser.add_argument(
        "--llm-temperature",
        type=float,
        default=0.5,
        help="Sampling temperature for LLM responses",
    )
    parser.add_argument(
        "--samples-per-prompt",
        type=int,
        default=2,
        help="Number of completions to draw per persona/stimulus prompt",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Base random seed for deterministic elicitation",
    )

    args = parser.parse_args()

    console.print("\n[bold cyan]🔧 OPeRA Data Preprocessing Pipeline (with LLM Elicitation)[/bold cyan]\n")

    # Check for OpenAI API key
    if not args.skip_llm and not os.getenv("OPENAI_API_KEY"):
        console.print("[bold yellow]⚠️  Warning: OPENAI_API_KEY not set[/bold yellow]")
        console.print("   LLM elicitation will be skipped. Set the key to enable SSR paper methodology.")
        console.print("   Example: export OPENAI_API_KEY='sk-proj-...'\n")
        args.skip_llm = True

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

    # Save standard outputs
    console.print("[bold cyan]💾 Saving processed data...[/bold cyan]\n")

    out_sequences = out_dir / "aligned_sequences.jsonl"
    num_saved = aligner.save_aligned(out_sequences, aligned_sessions)
    console.print(f"  ✅ Saved aligned sequences: {out_sequences} ({num_saved} sessions)")

    out_features = out_dir / "persona_features.parquet"
    num_users_feat = aligner.extract_persona_features(aligned_sessions, out_features)
    console.print(f"  ✅ Saved persona features: {out_features} ({num_users_feat} users)")

    # SSR training pairs: with or without LLM elicitation
    console.print()

    console.print("[bold cyan]📊 Extracting SSR training pairs (human ratings)...[/bold cyan]\n")
    out_ssr_pairs = out_dir / "ssr_training_pairs.jsonl"
    num_pairs_standard = aligner.extract_ssr_training_pairs(aligned_sessions, out_ssr_pairs)
    console.print(f"  ✅ Saved SSR training pairs: {out_ssr_pairs} ({num_pairs_standard} pairs)\n")

    num_pairs_llm = 0

    if not args.skip_llm:
        console.print("[bold cyan]🤖 Extracting SSR training pairs with LLM elicitation...[/bold cyan]")
        console.print(f"   Provider: {args.llm_provider}")
        console.print(f"   Model: {args.llm_model}")
        console.print(f"   Samples per prompt: {args.samples_per_prompt}")
        if args.max_llm_sessions:
            approx_cost = args.max_llm_sessions * args.samples_per_prompt * 0.01
            console.print(f"   Session cap: {args.max_llm_sessions} (est. cost ≈ ${approx_cost:.2f})\n")
        else:
            console.print("   Session cap: unlimited (set --max-llm-sessions to bound cost)\n")

        # Initialize LLM elicitor
        try:
            elicitor = LLMElicitationEngine(
                model=args.llm_model,
                temperature=args.llm_temperature,
                samples_per_prompt=args.samples_per_prompt,
                provider=args.llm_provider,
                seed=args.seed,
            )
            console.print(f"  ✅ LLM elicitation engine ready\n")

        except Exception as e:
            console.print(f"[bold red]❌ Failed to initialize LLM: {e}[/bold red]")
            console.print("   Falling back to standard extraction (already completed above).\n")
            elicitor = None

        if elicitor:
            out_ssr_pairs_llm = out_dir / "ssr_training_pairs_llm.jsonl"
            num_pairs_llm = aligner.extract_ssr_training_pairs_with_llm(
                aligned_sessions,
                out_ssr_pairs_llm,
                elicitor=elicitor,
                max_samples=args.max_llm_sessions,
                samples_per_prompt=args.samples_per_prompt,
                temperature=args.llm_temperature,
                seed=args.seed,
            )

            console.print(
                f"\n  ✅ Saved SSR training pairs (LLM-elicited): "
                f"{out_ssr_pairs_llm} ({num_pairs_llm} pairs)\n"
            )

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
    table.add_row("SSR Training Pairs (standard)", str(num_pairs_standard))
    if not args.skip_llm and num_pairs_llm:
        table.add_row("SSR Training Pairs (LLM-elicited)", str(num_pairs_llm))

    console.print(table)
    console.print("\n[bold green]✅ OPeRA preprocessing complete![/bold green]\n")

    # Next steps
    console.print("[bold cyan]📝 Next Steps:[/bold cyan]")
    console.print("   1. Discover personas: python scripts/03_discover_personas.py")

    if args.skip_llm:
        console.print("   2. Train SSR model: python scripts/04_train_ssr.py")
    else:
        console.print(
            "   2. Train SSR model (with LLM data): "
            "python scripts/04_train_ssr.py --training-pairs "
            f"{out_dir}/ssr_training_pairs_llm.jsonl --use-references"
        )

    console.print("   3. Evaluate model: python scripts/07_evaluate.py\n")


if __name__ == "__main__":
    main()
