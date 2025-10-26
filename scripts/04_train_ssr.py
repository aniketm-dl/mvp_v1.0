#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ssr.trainer import SSRTrainer

console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="Train SSR (Semantic Similarity Rating) model for Likert prediction."
    )
    parser.add_argument(
        "--training-pairs",
        type=str,
        default="DATA/OPeRA/processed/ssr_training_pairs.jsonl",
        help="Path to SSR training pairs JSONL",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="models/ssr_reference",
        help="Output directory for trained model",
    )
    parser.add_argument(
        "--base-model",
        type=str,
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="Base sentence-transformers model",
    )
    parser.add_argument(
        "--embedding-epochs",
        type=int,
        default=10,
        help="Epochs for embedding fine-tuning",
    )
    parser.add_argument(
        "--regression-epochs",
        type=int,
        default=20,
        help="Epochs for regression head training",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for training",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=2e-5,
        help="Learning rate for embedding fine-tuning",
    )
    parser.add_argument(
        "--use-references",
        action="store_true",
        help="Use reference statement sets for contrastive training (SSR paper methodology)",
    )

    args = parser.parse_args()

    console.print("\n[bold cyan]🚀 SSR Model Training Pipeline[/bold cyan]")
    console.print(f"   Training data: {args.training_pairs}")
    console.print(f"   Base model: {args.base_model}")
    console.print(f"   Use reference statements: {args.use_references}")
    console.print(f"   Output: {args.out}\n")

    if args.use_references:
        console.print("[bold green]✨ SSR Paper Methodology Enabled[/bold green]")
        console.print("   • Using reference statement sets for contrastive training")
        console.print("   • Expecting LLM-elicited responses in training data")
        console.print("   • See: SSR_IMPLEMENTATION_GAP_ANALYSIS.md for details\n")

    # Initialize trainer
    console.print("[bold cyan]📦 Initializing SSR trainer...[/bold cyan]")
    trainer = SSRTrainer(
        base_model=args.base_model,
        output_dir=Path(args.out),
    )

    console.print(f"  ✅ Trainer initialized")
    console.print(f"  • Device: {trainer.device}")
    console.print(f"  • Embedding dim: {trainer.embedding_dim}\n")

    # Load training data
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Loading training data...", total=None)
        train_pairs, val_pairs = trainer.load_training_data(Path(args.training_pairs))
        progress.update(task, completed=True)

    console.print(f"  ✅ Loaded training data")
    console.print(f"  • Train: {len(train_pairs)} pairs")
    console.print(f"  • Val: {len(val_pairs)} pairs\n")

    if len(train_pairs) < 100:
        console.print("[bold yellow]⚠️  Warning: Very few training pairs. Results may be poor.[/bold yellow]")
        console.print("   Consider downloading more OPeRA data or reducing preprocessing filters.\n")

    # Phase 1: Fine-tune embedding model
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold cyan]PHASE 1: Fine-tuning Embedding Model (Contrastive Learning)[/bold cyan]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]\n")

    embedding_metrics = trainer.train_embedding_model(
        train_pairs=train_pairs,
        val_pairs=val_pairs,
        epochs=args.embedding_epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        use_references=args.use_references,
    )

    console.print("\n[bold green]✅ Phase 1 complete![/bold green]\n")

    # Phase 2: Train regression head
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold cyan]PHASE 2: Training Regression Head (Likert Prediction)[/bold cyan]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]\n")

    regression_metrics = trainer.train_regression_head(
        train_pairs=train_pairs,
        val_pairs=val_pairs,
        epochs=args.regression_epochs,
        batch_size=args.batch_size * 2,  # Larger batch for regression
        learning_rate=1e-3,
    )

    console.print("\n[bold green]✅ Phase 2 complete![/bold green]\n")

    # Save complete model
    console.print("[bold cyan]💾 Saving complete SSR model...[/bold cyan]")
    trainer.save_complete_model(Path(args.out))
    console.print(f"  ✅ Model saved to: {args.out}\n")

    # Display training summary
    table = Table(title="Training Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="green")

    table.add_row("Training Pairs", f"{len(train_pairs):,}")
    table.add_row("Validation Pairs", f"{len(val_pairs):,}")
    table.add_row("Embedding Epochs", str(args.embedding_epochs))
    table.add_row("Regression Epochs", str(args.regression_epochs))
    table.add_row("Best Val Correlation", f"{regression_metrics['best_val_correlation']:.3f}")
    table.add_row("Best Epoch", str(regression_metrics['best_epoch']))
    table.add_row("Final Train Loss", f"{regression_metrics['final_train_loss']:.4f}")
    table.add_row("Final Val Loss", f"{regression_metrics['final_val_loss']:.4f}")

    console.print(table)
    console.print()

    # Quality assessment
    console.print("[bold cyan]✨ Quality Assessment:[/bold cyan]")
    val_corr = regression_metrics['best_val_correlation']

    if val_corr >= 0.70:
        console.print("   ✅ [bold green]Correlation: EXCELLENT (≥0.70 target achieved!)[/bold green]")
    elif val_corr >= 0.60:
        console.print("   ✅ [bold green]Correlation: GOOD (≥0.60)[/bold green]")
    elif val_corr >= 0.50:
        console.print("   ⚠️  [bold yellow]Correlation: ACCEPTABLE (≥0.50)[/bold yellow]")
    else:
        console.print("   ❌ [bold red]Correlation: POOR (<0.50)[/bold red]")
        console.print("   💡 Try: More training data, longer training, or different base model\n")

    # Test inference
    console.print("\n[bold cyan]🧪 Testing inference...[/bold cyan]")

    test_stimuli = [
        "Free shipping on all orders",
        "50% off laptops",
        "Premium quality electronics",
    ]

    for stimulus in test_stimuli:
        dist, metrics = trainer.predict_likert_distribution(stimulus)
        console.print(f"\n  Stimulus: [bold]{stimulus}[/bold]")
        console.print(f"  • Predicted rating: {metrics['mean']:.2f} ± {metrics['std']:.2f}")
        console.print(f"  • Mode: {metrics['mode']}")
        console.print(f"  • Distribution: {[f'{p:.2f}' for p in dist]}")

    console.print("\n[bold green]✅ SSR training complete![/bold green]\n")

    # Next steps
    console.print("[bold cyan]📝 Next Steps:[/bold cyan]")
    console.print("   1. Run evaluation: python scripts/07_evaluate.py")
    console.print("   2. Test with API: python src/api/service.py")
    console.print("   3. Launch demo app: streamlit run src/app/main.py\n")


if __name__ == "__main__":
    main()
