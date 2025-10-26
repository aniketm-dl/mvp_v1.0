#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.correlation import CorrelationMetrics
from src.evaluation.dashboard import EvaluationDashboard
from src.evaluation.human_metrics import (
    bootstrap_test_retest,
    compute_human_distributions,
    convert_human_stats_to_dataframe,
    load_human_ratings,
)
from src.evaluation.ks_test import KSSimilarityTest
from src.evaluation.reporting import (
    aggregate_flr_predictions,
    compute_overall_pmf,
    compute_subgroup_metrics,
    ensure_human_demographics,
    load_flr_responses,
)
from src.ssr.anchor_mapper import SSRAnchorMapper
from src.ssr.evaluation_utils import (
    aggregate_anchor_predictions,
    load_synthetic_responses,
)
from src.ssr.inference import SSRInference
console = Console()


def _parse_labelled_paths(entries: List[str]) -> List[Dict[str, object]]:
    parsed: List[Dict[str, object]] = []
    for entry in entries:
        if "=" not in entry:
            raise ValueError(
                f"Invalid scenario definition '{entry}'. Expected format label=path."
            )
        label, path_str = entry.split("=", 1)
        parsed.append({"label": label.strip(), "path": Path(path_str.strip())})
    return parsed


def evaluate_ssr_model(
    ssr_model_path: Path,
    human_data_path: Path,
    output_dir: Path,
    *,
    bootstrap_iters: int = 200,
    random_seed: int = 42,
    ks_significance: float = 0.05,
    synthetic_responses_path: Optional[Path] = None,
    anchor_temperature: float = 1.0,
    anchor_epsilon: float = 1e-6,
    anchor_scenarios: Optional[List[Dict[str, object]]] = None,
    flr_scenarios: Optional[List[Dict[str, object]]] = None,
    include_regression: bool = False,
) -> dict:
    """Evaluate SSR predictions against human Likert distributions."""
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]")
    console.print("[bold cyan]SSR Model Evaluation[/bold cyan]")
    console.print("[bold cyan]" + "=" * 80 + "[/bold cyan]\n")

    random.seed(random_seed)
    np.random.seed(random_seed)

    evaluation_started_at = datetime.utcnow().isoformat()

    console.print(f"[cyan]📂 Loading human ratings from {human_data_path}...[/cyan]")
    human_df = load_human_ratings(human_data_path)
    if human_df.empty:
        raise ValueError("Human ratings file contained no records.")
    console.print(f"  ✅ Loaded {len(human_df):,} human ratings\n")

    human_df = ensure_human_demographics(human_df)
    human_stats = compute_human_distributions(human_df)
    human_summary_df = convert_human_stats_to_dataframe(human_stats)
    if human_summary_df.empty:
        raise ValueError("No human distributions could be computed.")

    concepts = sorted(human_stats.keys())
    console.print(f"[cyan]🧪 Concepts detected: {len(concepts):,}[/cyan]\n")

    scenario_definitions: List[Dict[str, object]] = []

    anchor_configs = anchor_scenarios or []
    if synthetic_responses_path:
        anchor_configs = anchor_configs + [{"label": "persona", "path": synthetic_responses_path}]

    anchor_mapper = None
    if anchor_configs:
        if not os.getenv("OPENAI_API_KEY"):
            raise EnvironmentError(
                "OPENAI_API_KEY is required for anchor-based evaluation (SSR mapping). "
                "Set the environment variable before running."
            )
        console.print("[cyan]🔧 Preparing anchor-based mapper (text-embedding-3-small)...[/cyan]\n")
        anchor_mapper = SSRAnchorMapper(
            temperature=anchor_temperature,
            epsilon=anchor_epsilon,
        )
        for config in anchor_configs:
            label = config.get("label") or "anchor"
            path: Path = Path(config["path"])  # type: ignore[index]
            if not path.exists():
                raise FileNotFoundError(f"Anchor scenario '{label}' not found at {path}")
            console.print(f"[cyan]🔁 Loading anchor scenario '{label}' from {path}...[/cyan]")
            responses = load_synthetic_responses(path)
            if not responses:
                raise ValueError(
                    f"Scenario '{label}' contained no usable LLM responses. "
                    "Ensure preprocessing ran with --use-llm options."
                )
            data = aggregate_anchor_predictions(
                responses,
                anchor_mapper,
                temperature=anchor_temperature,
                epsilon=anchor_epsilon,
            )
            metadata = data["metadata"].copy()
            metadata.update(
                {
                    "label": label,
                    "scenario_type": "anchor",
                    "source_path": str(path),
                    "num_responses": len(responses),
                    "num_concepts": len(data["predictions"]),
                }
            )
            scenario_definitions.append(
                {
                    "label": label,
                    "type": "anchor",
                    "predictions": data["predictions"],
                    "metadata": metadata,
                }
            )
            console.print(f"  ✅ Scenario '{label}' ready ({len(responses)} responses)\n")

    include_regression = include_regression or not scenario_definitions
    ssr_model_info = None
    ssr = None
    if include_regression:
        console.print("[cyan]🔧 Loading SSR regression model...[/cyan]")
        ssr = SSRInference(ssr_model_path)
        ssr_model_info = ssr.get_model_info()
        console.print(f"  ✅ Model loaded: {ssr_model_info['base_model']}\n")

        predictions = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Predicting concepts (regression)...", total=len(concepts))
            for concept in concepts:
                pred = ssr.predict(concept, return_distribution=True)
                predictions.append(
                    {
                        "stimulus_text": concept,
                        "pred_mean": pred["mean"],
                        "pred_distribution": np.array(pred["distribution"], dtype=float),
                        "pred_mode": pred["mode"],
                        "pred_std": pred["std"],
                        "num_samples": 1,
                        "responses": [],
                    }
                )
                progress.advance(task, 1)

        scenario_definitions.append(
            {
                "label": "regression_head",
                "type": "regression",
                "predictions": predictions,
                "metadata": {
                    "scenario_type": "regression",
                    "num_concepts": len(predictions),
                    "base_model": ssr_model_info["base_model"],
                    "device": ssr_model_info.get("device"),
                },
            }
        )
        console.print("  ✅ Regression baseline ready\n")

    flr_configs = flr_scenarios or []
    for config in flr_configs:
        label = config.get("label") or "flr"
        path: Path = Path(config["path"])  # type: ignore[index]
        if not path.exists():
            raise FileNotFoundError(f"FLR scenario '{label}' not found at {path}")
        console.print(f"[cyan]🧮 Loading FLR scenario '{label}' from {path}...[/cyan]")
        responses = load_flr_responses(path)
        if not responses:
            raise ValueError(f"FLR scenario '{label}' contained no ratings.")
        data = aggregate_flr_predictions(responses)
        metadata = data["metadata"].copy()
        metadata.update(
            {
                "label": label,
                "scenario_type": "flr",
                "source_path": str(path),
                "num_concepts": len(data["predictions"]),
            }
        )
        scenario_definitions.append(
            {
                "label": label,
                "type": "flr",
                "predictions": data["predictions"],
                "metadata": metadata,
            }
        )
        console.print(f"  ✅ FLR baseline '{label}' ready ({len(responses)} ratings)\n")

    if not scenario_definitions:
        raise RuntimeError(
            "No evaluation scenarios were configured. Provide anchor, FLR, or regression options."
        )

    ks_test = KSSimilarityTest(significance_level=ks_significance)
    corr_metrics = CorrelationMetrics(min_samples=10)
    ceiling, retest_samples = bootstrap_test_retest(
        human_df,
        num_bootstrap=bootstrap_iters,
        random_state=random_seed,
    )

    def process_scenario(scenario: Dict[str, object]) -> Dict[str, object]:
        predictions: List[Dict[str, object]] = scenario["predictions"]  # type: ignore[index]
        pred_records = []
        for item in predictions:
            dist = np.array(item["pred_distribution"], dtype=float)
            pred_records.append(
                {
                    "stimulus_text": item["stimulus_text"],
                    "pred_mean": item["pred_mean"],
                    "pred_distribution": dist,
                    "pred_mode": item["pred_mode"],
                    "pred_std": item["pred_std"],
                    "num_samples": item.get("num_samples", 0),
                    "responses": item.get("responses", []),
                }
            )
        pred_df = pd.DataFrame(pred_records)
        merged = human_summary_df.merge(pred_df, on="stimulus_text", how="inner")
        if merged.empty:
            raise ValueError(
                f"Scenario '{scenario['label']}' has no overlap with human data."
            )

        ks_records = []
        for _, row in merged.iterrows():
            pred_dist = np.array(row["pred_distribution"], dtype=float)
            human_pmf = np.array(row["human_pmf"], dtype=float)
            ks_res = ks_test.test_distributions(pred_dist, human_pmf)
            ks_records.append(
                {
                    "stimulus_text": row["stimulus_text"],
                    "ks_similarity": ks_res["similarity"],
                    "ks_statistic": ks_res["ks_statistic"],
                    "passes_threshold": ks_res["similarity"] >= 0.80,
                }
            )
        ks_df = pd.DataFrame(ks_records)
        merged = merged.merge(ks_df, on="stimulus_text", how="left")

        pred_means = merged["pred_mean"].to_numpy(dtype=float)
        human_means = merged["human_mean"].to_numpy(dtype=float)
        errors = pred_means - human_means
        mae = float(np.mean(np.abs(errors)))
        rmse = float(np.sqrt(np.mean(errors**2)))

        corr_results = corr_metrics.compute_all_metrics(pred_means, human_means)
        pearson_corr = corr_results["pearson"]["correlation"]
        spearman_corr = corr_results["spearman"]["correlation"]
        attainment = pearson_corr / ceiling if ceiling > 0 else 0.0
        attainment = float(min(attainment, 1.0)) if attainment > 0 else 0.0

        mean_ks = float(ks_df["ks_similarity"].mean())
        median_ks = float(ks_df["ks_similarity"].median())
        ks_pass_rate = float((ks_df["passes_threshold"].sum()) / len(ks_df))

        concept_records = []
        for _, row in merged.iterrows():
            concept_records.append(
                {
                    "stimulus_text": row["stimulus_text"],
                    "human_mean": float(row["human_mean"]),
                    "human_counts": row["human_counts"].tolist(),
                    "human_pmf": row["human_pmf"].tolist(),
                    "human_n": int(row["human_n"]),
                    "pred_mean": float(row["pred_mean"]),
                    "pred_distribution": [float(x) for x in row["pred_distribution"]],
                    "pred_mode": int(row["pred_mode"]),
                    "pred_std": float(row["pred_std"]),
                    "num_samples": int(row.get("num_samples", 0) or 0),
                    "responses": row.get("responses", []),
                    "ks_similarity": float(row["ks_similarity"]),
                    "ks_statistic": float(row["ks_statistic"]),
                }
            )

        overall_pmf = compute_overall_pmf(predictions)
        subgroup_df = compute_subgroup_metrics(scenario["label"], predictions, human_df)

        scenario_metrics = {
            "spearman": corr_results["spearman"],
            "pearson": corr_results["pearson"],
            "mae": mae,
            "rmse": rmse,
            "mean_ks_similarity": mean_ks,
            "median_ks_similarity": median_ks,
            "ks_pass_rate": ks_pass_rate,
            "correlation_attainment": attainment,
        }

        return {
            "label": scenario["label"],
            "type": scenario["type"],
            "metadata": scenario["metadata"],
            "metrics": scenario_metrics,
            "concept_records": concept_records,
            "overall_pmf": overall_pmf,
            "ks_df": ks_df,
            "merged_df": merged,
            "subgroup_df": subgroup_df,
        }

    scenario_results: List[Dict[str, object]] = []
    for scenario in scenario_definitions:
        scenario_results.append(process_scenario(scenario))
        console.print(
            f"[green]✅ Evaluated scenario '{scenario['label']}' ({scenario['type']})[/green]"
        )

    summary_table = Table(title="Scenario Summary", show_header=True, header_style="bold magenta")
    summary_table.add_column("Scenario", style="cyan")
    summary_table.add_column("Type", justify="left", style="cyan")
    summary_table.add_column("Spearman", justify="right", style="green")
    summary_table.add_column("Pearson", justify="right", style="green")
    summary_table.add_column("MAE", justify="right", style="green")
    summary_table.add_column("RMSE", justify="right", style="green")
    summary_table.add_column("Mean KS", justify="right", style="green")
    summary_table.add_column("KS Pass %", justify="right", style="green")

    summary_rows = []
    for scenario in scenario_results:
        metrics = scenario["metrics"]
        spearman = metrics["spearman"]["correlation"]
        pearson = metrics["pearson"]["correlation"]
        summary_table.add_row(
            scenario["label"],
            scenario["type"],
            f"{spearman:.3f}",
            f"{pearson:.3f}",
            f"{metrics['mae']:.3f}",
            f"{metrics['rmse']:.3f}",
            f"{metrics['mean_ks_similarity']:.3f}",
            f"{metrics['ks_pass_rate'] * 100:.1f}%",
        )
        summary_rows.append(
            {
                "scenario": scenario["label"],
                "type": scenario["type"],
                "spearman": spearman,
                "pearson": pearson,
                "mae": metrics["mae"],
                "rmse": metrics["rmse"],
                "mean_ks": metrics["mean_ks_similarity"],
                "median_ks": metrics["median_ks_similarity"],
                "ks_pass_rate": metrics["ks_pass_rate"],
                "correlation_attainment": metrics["correlation_attainment"],
            }
        )

    console.print()
    console.print(summary_table)
    console.print()

    output_dir.mkdir(parents=True, exist_ok=True)

    # Persist scenario-specific artefacts
    dashboard = EvaluationDashboard(output_dir)
    for scenario in scenario_results:
        label = scenario["label"]
        concept_records = scenario["concept_records"]
        concept_df = pd.DataFrame(concept_records)
        csv_df = concept_df.copy()
        csv_df["human_counts"] = csv_df["human_counts"].apply(lambda x: "|".join(map(str, x)))
        csv_df["human_pmf"] = csv_df["human_pmf"].apply(lambda x: "|".join(f"{v:.4f}" for v in x))
        csv_df["pred_distribution"] = csv_df["pred_distribution"].apply(lambda x: "|".join(f"{v:.4f}" for v in x))
        csv_df["responses"] = csv_df["responses"].apply(lambda items: json.dumps(items, ensure_ascii=False))
        concept_path = output_dir / f"concept_evaluation_{label}.csv"
        csv_df.to_csv(concept_path, index=False)

        subgroup_df = scenario["subgroup_df"]
        subgroup_path = output_dir / f"subgroup_metrics_{label}.csv"
        subgroup_df.to_csv(subgroup_path, index=False)

        pmf = scenario["overall_pmf"]
        pmf_path = output_dir / f"pmf_summary_{label}.csv"
        pmf_df = pd.DataFrame({"likert": [1, 2, 3, 4, 5], "probability": pmf})
        pmf_df.to_csv(pmf_path, index=False)

        ks_df = scenario["ks_df"]
        ks_chart = dashboard.create_ks_similarity_chart(
            {
                "individual_results": [
                    {
                        "label": rec["stimulus_text"],
                        "similarity": rec["ks_similarity"],
                        "passes_threshold": rec["ks_similarity"] >= 0.80,
                    }
                    for rec in ks_df.to_dict("records")
                ]
            },
            title=f"KS Similarity by Concept – {label}",
        )
        ks_chart.write_html(output_dir / f"ks_similarity_{label}.html")

        merged_df = scenario["merged_df"]
        scatter = dashboard.create_correlation_scatter(
            predicted=merged_df["pred_mean"].to_numpy(dtype=float),
            actual=merged_df["human_mean"].to_numpy(dtype=float),
            correlation=scenario["metrics"]["spearman"]["correlation"],
            p_value=scenario["metrics"]["spearman"].get("p_value"),
            title=f"Predicted vs Human Means – {label}",
        )
        scatter.write_html(output_dir / f"prediction_vs_human_{label}.html")

        top_idx = merged_df["human_n"].idxmax()
        top_row = merged_df.loc[top_idx]
        dist_fig = dashboard.create_distribution_comparison(
            predicted_dist=np.array(top_row["pred_distribution"]),
            actual_dist=np.array(top_row["human_pmf"]),
            persona_label=f"{label} :: {top_row['stimulus_text'][:80]}",
        )
        dist_fig.write_html(output_dir / f"distribution_comparison_{label}.html")

    scenario_summary_df = pd.DataFrame(summary_rows)
    scenario_summary_df.to_csv(output_dir / "scenario_summary.csv", index=False)

    # Build JSON report
    json_results: Dict[str, object] = {
        "evaluation_started_at": evaluation_started_at,
        "random_seed": random_seed,
        "bootstrap_iterations": bootstrap_iters,
        "test_retest_ceiling": ceiling,
        "human_samples": int(len(human_df)),
        "concepts_evaluated": int(len(concepts)),
        "scenarios": [],
    }

    if ssr_model_info:
        json_results["regression_model"] = ssr_model_info
    if anchor_mapper:
        json_results["anchor_metadata"] = anchor_mapper.get_metadata()

    for scenario in scenario_results:
        scenario_entry = {
            "label": scenario["label"],
            "type": scenario["type"],
            "metadata": scenario["metadata"],
            "metrics": scenario["metrics"],
            "overall_pmf": scenario["overall_pmf"].tolist(),
            "concepts": scenario["concept_records"],
            "subgroups": scenario["subgroup_df"].to_dict("records"),
        }
        json_results["scenarios"].append(scenario_entry)

    json_path = output_dir / "evaluation_results.json"
    with json_path.open("w") as fh:
        json.dump(json_results, fh, indent=2)
    console.print(f"[green]✅ Saved consolidated report to {json_path}[/green]\n")

    return json_results


def main():
    parser = argparse.ArgumentParser(description="Evaluate SSR model against human Likert ratings.")
    parser.add_argument(
        "--ssr-model",
        type=str,
        default="models/ssr_reference",
        help="Path to trained SSR model directory",
    )
    parser.add_argument(
        "--human-data",
        type=str,
        default="DATA/OPeRA/processed/ssr_training_pairs.jsonl",
        help="JSONL file containing human ratings (stimulus_text, likert_score)",
    )
    parser.add_argument(
        "--synthetic-responses",
        type=str,
        default=None,
        help="JSONL file containing persona-conditioned responses (legacy flag).",
    )
    parser.add_argument(
        "--anchor-scenario",
        action="append",
        default=[],
        help="Additional anchor scenarios label=path (persona ablations, alternate LLMs).",
    )
    parser.add_argument(
        "--flr-scenario",
        action="append",
        default=[],
        help="FLR baseline scenarios label=path with flr_rating fields.",
    )
    parser.add_argument(
        "--include-regression",
        action="store_true",
        help="Include regression-head predictions as baseline scenario.",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="reports",
        help="Output directory for evaluation artefacts",
    )
    parser.add_argument(
        "--bootstrap-iters",
        type=int,
        default=200,
        help="Number of bootstrap iterations for test-retest ceiling",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--ks-significance",
        type=float,
        default=0.05,
        help="Significance level for KS similarity calculations",
    )
    parser.add_argument(
        "--anchor-temperature",
        type=float,
        default=1.0,
        help="Temperature applied to anchor pmfs (SSR mapping)",
    )
    parser.add_argument(
        "--anchor-epsilon",
        type=float,
        default=1e-6,
        help="Small epsilon added before normalising anchor pmfs",
    )

    args = parser.parse_args()

    ssr_model_path = Path(args.ssr_model)
    human_data_path = Path(args.human_data)
    output_dir = Path(args.out_dir)
    synthetic_path = Path(args.synthetic_responses) if args.synthetic_responses else None
    anchor_scenarios = _parse_labelled_paths(args.anchor_scenario) if args.anchor_scenario else None
    flr_scenarios = _parse_labelled_paths(args.flr_scenario) if args.flr_scenario else None

    evaluate_ssr_model(
        ssr_model_path,
        human_data_path,
        output_dir,
        bootstrap_iters=args.bootstrap_iters,
        random_seed=args.random_seed,
        ks_significance=args.ks_significance,
        synthetic_responses_path=synthetic_path,
        anchor_temperature=args.anchor_temperature,
        anchor_epsilon=args.anchor_epsilon,
        anchor_scenarios=anchor_scenarios,
        flr_scenarios=flr_scenarios,
        include_regression=args.include_regression,
    )


if __name__ == "__main__":
    main()
