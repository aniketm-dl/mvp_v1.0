#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.correlation import CorrelationMetrics
from src.evaluation.dashboard import EvaluationDashboard
from src.evaluation.ks_test import KSSimilarityTest
from src.ssr.inference import SSRInference

console = Console()


def load_test_data(test_data_path: Path) -> pd.DataFrame:
    """
    Load test data from aligned sequences.

    Args:
        test_data_path: Path to aligned_sequences.jsonl

    Returns:
        DataFrame with user_id, stimulus_text, likert_score
    """
    console.print(f"[cyan]📂 Loading test data from {test_data_path}...[/cyan]")

    sequences = []
    with open(test_data_path, "r") as f:
        for line in f:
            seq = json.loads(line)
            sequences.append(seq)

    # Extract test pairs from sequences
    test_pairs = []
    for seq in sequences:
        user_id = seq["user_id"]
        for step in seq.get("steps", []):
            stimulus = step.get("stimulus_text", "")
            likert = step.get("likert_score")

            if stimulus and likert is not None:
                test_pairs.append({
                    "user_id": user_id,
                    "stimulus_text": stimulus,
                    "likert_score": likert,
                })

    df = pd.DataFrame(test_pairs)
    console.print(f"  ✅ Loaded {len(df):,} test pairs from {len(sequences):,} sequences\n")

    return df


def evaluate_ssr_model(
    ssr_model_path: Path,
    test_data: pd.DataFrame,
    output_dir: Path,
) -> dict:
    """
    Evaluate SSR model on test data.

    Args:
        ssr_model_path: Path to trained SSR model
        test_data: Test DataFrame
        output_dir: Output directory for results

    Returns:
        Dict with evaluation results
    """
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold cyan]SSR Model Evaluation[/bold cyan]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]\n")

    # Initialize model
    console.print("[cyan]🔧 Loading SSR model...[/cyan]")
    ssr = SSRInference(ssr_model_path)
    console.print(f"  ✅ Model loaded: {ssr.get_model_info()['base_model']}\n")

    # Generate predictions
    console.print("[cyan]🧪 Generating predictions...[/cyan]")

    predictions = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"Predicting {len(test_data)} samples...",
            total=len(test_data),
        )

        for idx, row in test_data.iterrows():
            pred = ssr.predict(row["stimulus_text"], return_distribution=True)
            predictions.append(pred)
            progress.advance(task, 1)

    console.print(f"  ✅ Generated {len(predictions):,} predictions\n")

    # Extract arrays for metrics
    predicted_ratings = np.array([p["mean"] for p in predictions])
    actual_ratings = test_data["likert_score"].values

    # Compute correlation metrics
    console.print("[cyan]📊 Computing correlation metrics...[/cyan]")
    corr_metrics = CorrelationMetrics(min_samples=10)
    corr_results = corr_metrics.compute_all_metrics(predicted_ratings, actual_ratings)

    console.print(f"  • Spearman ρ: {corr_results['spearman']['correlation']:.3f}")
    console.print(f"  • Pearson r: {corr_results['pearson']['correlation']:.3f}")
    console.print(f"  • MAE: {corr_results['error_metrics']['mae']:.3f}")
    console.print(f"  • RMSE: {corr_results['error_metrics']['rmse']:.3f}")
    console.print(f"  • {corr_results['interpretation']}\n")

    # Compute KS similarity (sample 100 predictions for distribution testing)
    console.print("[cyan]📊 Computing KS similarity...[/cyan]")
    ks_test = KSSimilarityTest(significance_level=0.05)

    # Sample predictions for KS test
    sample_size = min(100, len(predictions))
    sample_indices = np.random.choice(len(predictions), sample_size, replace=False)

    ks_similarities = []
    for idx in sample_indices:
        pred_dist = np.array(predictions[idx]["distribution"])
        # Use actual distribution (convert scalar to distribution)
        actual_rating = actual_ratings[idx]
        actual_dist = np.zeros(5)
        actual_dist[int(actual_rating) - 1] = 1.0  # One-hot encode

        ks_result = ks_test.test_distributions(pred_dist, actual_dist)
        ks_similarities.append(ks_result["similarity"])

    mean_ks = np.mean(ks_similarities)
    console.print(f"  • Mean KS Similarity: {mean_ks:.3f}")
    console.print(f"  • Target: ≥ 0.80\n")

    # Display results table
    table = Table(title="Evaluation Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="green")
    table.add_column("Target", justify="right", style="yellow")
    table.add_column("Status", justify="center")

    def status_emoji(value: float, target: float, higher_is_better: bool = True) -> str:
        if higher_is_better:
            return "✅" if value >= target else "❌"
        else:
            return "✅" if value <= target else "❌"

    table.add_row(
        "Spearman Correlation",
        f"{corr_results['spearman']['correlation']:.3f}",
        "≥ 0.70",
        status_emoji(corr_results['spearman']['correlation'], 0.70),
    )
    table.add_row(
        "Pearson Correlation",
        f"{corr_results['pearson']['correlation']:.3f}",
        "≥ 0.60",
        status_emoji(corr_results['pearson']['correlation'], 0.60),
    )
    table.add_row(
        "MAE",
        f"{corr_results['error_metrics']['mae']:.3f}",
        "< 0.50",
        status_emoji(corr_results['error_metrics']['mae'], 0.50, higher_is_better=False),
    )
    table.add_row(
        "RMSE",
        f"{corr_results['error_metrics']['rmse']:.3f}",
        "< 0.60",
        status_emoji(corr_results['error_metrics']['rmse'], 0.60, higher_is_better=False),
    )
    table.add_row(
        "KS Similarity",
        f"{mean_ks:.3f}",
        "≥ 0.80",
        status_emoji(mean_ks, 0.80),
    )

    console.print(table)
    console.print()

    # Quality assessment
    console.print("[bold cyan]✨ Overall Quality Assessment:[/bold cyan]")

    spearman_pass = corr_results['spearman']['correlation'] >= 0.70
    mae_pass = corr_results['error_metrics']['mae'] < 0.50
    ks_pass = mean_ks >= 0.80

    passes = sum([spearman_pass, mae_pass, ks_pass])

    if passes == 3:
        console.print("   ✅ [bold green]EXCELLENT: All quality targets achieved![/bold green]")
    elif passes == 2:
        console.print("   ✅ [bold green]GOOD: Most quality targets achieved[/bold green]")
    elif passes == 1:
        console.print("   ⚠️  [bold yellow]ACCEPTABLE: Some quality targets achieved[/bold yellow]")
    else:
        console.print("   ❌ [bold red]POOR: Quality targets not met[/bold red]")
        console.print("   💡 Consider: More training data, longer training, or hyperparameter tuning\n")

    # Save results
    results = {
        "model_path": str(ssr_model_path),
        "test_samples": len(test_data),
        "correlation": {
            "spearman": corr_results['spearman']['correlation'],
            "pearson": corr_results['pearson']['correlation'],
            "spearman_p_value": corr_results['spearman']['p_value'],
            "pearson_p_value": corr_results['pearson']['p_value'],
        },
        "error_metrics": corr_results['error_metrics'],
        "ks_similarity": {
            "mean": float(mean_ks),
            "samples": sample_size,
        },
        "quality_gates": {
            "spearman_pass": spearman_pass,
            "mae_pass": mae_pass,
            "ks_pass": ks_pass,
            "overall_pass": passes >= 2,
        },
    }

    results_path = output_dir / "evaluation_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    console.print(f"[cyan]💾 Results saved to: {results_path}[/cyan]\n")

    return {
        "correlation": corr_results,
        "ks_similarity": mean_ks,
        "predicted": predicted_ratings,
        "actual": actual_ratings,
    }


def generate_dashboard(
    eval_results: dict,
    output_dir: Path,
):
    """
    Generate evaluation dashboard.

    Args:
        eval_results: Evaluation results dict
        output_dir: Output directory
    """
    console.print("[cyan]📊 Generating evaluation dashboard...[/cyan]")

    dashboard = EvaluationDashboard(output_dir)

    # Mock KS results for dashboard (would be per-persona in real scenario)
    ks_results = {
        "individual_results": [
            {
                "label": "Overall",
                "similarity": eval_results["ks_similarity"],
                "passes_threshold": eval_results["ks_similarity"] >= 0.80,
            }
        ],
        "aggregate": {
            "mean_similarity": eval_results["ks_similarity"],
            "median_similarity": eval_results["ks_similarity"],
            "min_similarity": eval_results["ks_similarity"],
            "pass_rate": 1.0 if eval_results["ks_similarity"] >= 0.80 else 0.0,
        },
    }

    # Mock correlation results for dashboard
    corr_results = {
        "individual_results": [
            {
                "label": "Overall",
                "spearman": eval_results["correlation"]["spearman"],
                "passes_threshold": eval_results["correlation"]["passes_threshold"],
            }
        ],
        "aggregate": {
            "mean_spearman": eval_results["correlation"]["spearman"]["correlation"],
            "median_spearman": eval_results["correlation"]["spearman"]["correlation"],
            "min_spearman": eval_results["correlation"]["spearman"]["correlation"],
            "mean_mae": eval_results["correlation"]["error_metrics"]["mae"],
            "mean_rmse": eval_results["correlation"]["error_metrics"]["rmse"],
            "pass_rate": 1.0 if eval_results["correlation"]["passes_threshold"] else 0.0,
        },
    }

    # Create complete dashboard
    dashboard_path = dashboard.create_complete_dashboard(
        ks_results,
        corr_results,
        predicted=eval_results["predicted"],
        actual=eval_results["actual"],
    )

    console.print(f"  ✅ Dashboard: {dashboard_path}\n")

    # Save individual charts
    chart_paths = dashboard.save_individual_charts(
        ks_results,
        corr_results,
        predicted=eval_results["predicted"],
        actual=eval_results["actual"],
    )

    console.print(f"  ✅ Individual charts: {len(chart_paths)} files\n")


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate trained SSR model on test data."
    )
    parser.add_argument(
        "--ssr-model",
        type=str,
        default="models/ssr_reference",
        help="Path to trained SSR model directory",
    )
    parser.add_argument(
        "--test-data",
        type=str,
        default="DATA/OPeRA/processed/aligned_sequences.jsonl",
        help="Path to test data (aligned sequences)",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="reports",
        help="Output directory for evaluation results",
    )
    parser.add_argument(
        "--skip-dashboard",
        action="store_true",
        help="Skip dashboard generation",
    )

    args = parser.parse_args()

    console.print("\n[bold cyan]🧪 SSR Model Evaluation Pipeline[/bold cyan]")
    console.print(f"   SSR model: {args.ssr_model}")
    console.print(f"   Test data: {args.test_data}")
    console.print(f"   Output: {args.out_dir}\n")

    # Create output directory
    output_dir = Path(args.out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check if model exists
    model_path = Path(args.ssr_model)
    if not model_path.exists():
        console.print(f"[bold red]❌ SSR model not found: {model_path}[/bold red]")
        console.print("   Run training first: python scripts/04_train_ssr.py\n")
        sys.exit(1)

    # Check if test data exists
    test_data_path = Path(args.test_data)
    if not test_data_path.exists():
        console.print(f"[bold red]❌ Test data not found: {test_data_path}[/bold red]")
        console.print("   Run preprocessing first: python scripts/02_preprocess_opera.py\n")
        sys.exit(1)

    # Load test data
    test_data = load_test_data(test_data_path)

    # Evaluate model
    eval_results = evaluate_ssr_model(model_path, test_data, output_dir)

    # Generate dashboard
    if not args.skip_dashboard:
        generate_dashboard(eval_results, output_dir)

    # Final summary
    console.print("[bold green]✅ Evaluation complete![/bold green]\n")

    console.print("[bold cyan]📝 Next Steps:[/bold cyan]")
    console.print(f"   1. View dashboard: open {output_dir}/evaluation_dashboard.html")
    console.print(f"   2. Review results: cat {output_dir}/evaluation_results.json")
    console.print("   3. Launch demo app: streamlit run src/app/main.py\n")


if __name__ == "__main__":
    main()
