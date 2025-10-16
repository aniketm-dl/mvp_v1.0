from __future__ import annotations
import argparse
from pathlib import Path
from typing import Dict, Any
import yaml
import numpy as np
import pandas as pd
import pickle
import json
from datetime import datetime

from discovery.quality_gates import run_all_gates


def load_all_artifacts(
    emb_path: Path,
    graph_path: Path,
    labels_path: Path,
    stability_path: Path,
    classifier_path: Path
) -> Dict[str, Any]:
    """Load all discovery artifacts."""
    print("Loading artifacts...")

    # Embeddings
    df = pd.read_parquet(emb_path)
    emb_cols = [c for c in df.columns if c.startswith("emb_")]
    embeddings = df[emb_cols].values
    metadata = df[[c for c in df.columns if not c.startswith("emb_")]]

    # Graph
    with open(graph_path, "rb") as f:
        graph = pickle.load(f)

    # Labels
    with open(labels_path, "rb") as f:
        labels_data = pickle.load(f)

    # Stability
    with open(stability_path, "rb") as f:
        stability_data = pickle.load(f)

    # Classifier
    with open(classifier_path, "rb") as f:
        classifier_data = pickle.load(f)

    return {
        "embeddings": embeddings,
        "metadata": metadata,
        "graph": graph,
        "labels": labels_data["labels"],
        "labels_stats": labels_data["stats"],
        "stability_scores": stability_data["stability_scores"],
        "labels_stable": stability_data["labels_stable"],
        "stability_stats": stability_data["stats"],
        "classifier_model": classifier_data["model"],
        "classifier_results": classifier_data["results"]
    }


def generate_report(
    artifacts: Dict[str, Any],
    gate_config: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Generate comprehensive discovery report in Markdown.

    Includes:
    1. Executive summary
    2. Clustering statistics
    3. Stability analysis
    4. Persona classifier results
    5. Quality gates results
    6. Recommendations
    """
    report = []

    # Header
    report.append("# Discovery Pipeline Report")
    report.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"\n**Embedding Dimension:** {artifacts['embeddings'].shape[1]}")
    report.append(f"**Total Sessions:** {len(artifacts['embeddings'])}")
    report.append("\n---\n")

    # Executive Summary
    report.append("## Executive Summary\n")

    n_clusters = artifacts["labels_stats"]["n_clusters"]
    n_noise = artifacts["labels_stats"]["n_noise"]
    algorithm = artifacts["labels_stats"]["algorithm"]

    report.append(f"- **Clustering Algorithm:** {algorithm}")
    report.append(f"- **Clusters Found:** {n_clusters}")
    report.append(f"- **Noise Points:** {n_noise} ({100 * artifacts['labels_stats']['noise_frac']:.1f}%)")

    stability_stats = artifacts["stability_stats"]["cores"]
    report.append(f"- **Stable Cores:** {stability_stats['n_stable']} / {len(artifacts['embeddings'])} ({100 * stability_stats['stable_frac']:.1f}%)")

    classifier_acc = artifacts["classifier_results"]["test_accuracy"]
    report.append(f"- **Persona Classifier Accuracy:** {classifier_acc:.4f}")

    report.append("\n---\n")

    # Clustering Details
    report.append("## Clustering Details\n")

    report.append(f"### Cluster Sizes\n")
    cluster_sizes = artifacts["labels_stats"]["cluster_sizes"]
    for cid, size in sorted(cluster_sizes.items()):
        report.append(f"- Cluster {cid}: {size} sessions")

    report.append(f"\n### Algorithm: {algorithm}\n")
    if algorithm == "hdbscan":
        report.append("HDBSCAN is a density-based clustering algorithm that finds clusters of varying density and marks outliers as noise.")
    elif algorithm == "leiden" or algorithm == "leiden_fallback":
        report.append("Leiden is a community detection algorithm optimized for graph structures. Used as fallback when HDBSCAN fragments.")

    report.append("\n---\n")

    # Stability Analysis
    report.append("## Stability Analysis\n")

    boot_stats = artifacts["stability_stats"]["bootstrap"]
    report.append(f"**Bootstrap Runs:** {boot_stats['n_bootstrap']}")
    report.append(f"**Mean Stability Score:** {boot_stats['mean_stability']:.4f}")
    report.append(f"**Median Stability Score:** {boot_stats['median_stability']:.4f}")
    report.append(f"\n### Stable Cores by Cluster\n")

    for cid, c_stats in sorted(stability_stats["cluster_stability"].items()):
        report.append(f"- Cluster {cid}: {c_stats['stable']}/{c_stats['total']} ({100 * c_stats['frac']:.1f}% stable)")

    report.append("\n---\n")

    # Persona Classifier
    report.append("## Persona Classifier\n")

    classifier_results = artifacts["classifier_results"]
    report.append(f"**Model Type:** {classifier_results['model_type']}")
    report.append(f"**Train Accuracy:** {classifier_results['train_accuracy']:.4f}")
    report.append(f"**Test Accuracy:** {classifier_results['test_accuracy']:.4f}")

    # Confusion analysis
    confusion_analysis = classifier_results.get("confusion_analysis", {})

    report.append(f"\n### High Confusion Pairs\n")
    high_conf = confusion_analysis.get("high_confusion_pairs", [])
    if high_conf:
        report.append("These persona pairs are frequently confused by the classifier, suggesting potential merge:\n")
        for pair in high_conf[:10]:
            report.append(f"- **{pair['persona_1']}** ↔ **{pair['persona_2']}**: {100 * pair['confusion_rate']:.1f}% confusion")
    else:
        report.append("✓ No high confusion pairs detected (all < 10% confusion)")

    report.append(f"\n### Low Recall Personas\n")
    low_recall = confusion_analysis.get("low_recall_personas", [])
    if low_recall:
        report.append("These personas have low recall, suggesting they might need splitting or refinement:\n")
        for p in low_recall:
            report.append(f"- **{p['persona']}**: {100 * p['recall']:.1f}% recall")
    else:
        report.append("✓ All personas have recall >= 70%")

    report.append("\n---\n")

    # Quality Gates
    report.append("## Quality Gates\n")

    # Run gates
    gate_results = run_all_gates(
        embeddings=artifacts["embeddings"],
        labels=artifacts["labels"],
        gate_config=gate_config
    )

    report.append(f"**Gates Passed:** {gate_results['n_passed']} / {gate_results['n_gates']}\n")

    for gate_name, gate_result in gate_results["gates"].items():
        status = "✓ PASS" if gate_result["passed"] else "✗ FAIL"
        report.append(f"### {gate_name.replace('_', ' ').title()}\n")
        report.append(f"**Status:** {status}")
        report.append(f"**Message:** {gate_result['message']}\n")

        # Additional details
        if "score" in gate_result:
            report.append(f"- Score: {gate_result['score']:.4f}")
            report.append(f"- Threshold: {gate_result['threshold']}\n")

    overall_status = "✓ ALL GATES PASSED" if gate_results["all_passed"] else "✗ SOME GATES FAILED"
    report.append(f"\n**Overall Status:** {overall_status}\n")

    report.append("\n---\n")

    # Recommendations
    report.append("## Recommendations\n")

    recommendations = []

    # Check classifier accuracy
    if classifier_acc < 0.85:
        recommendations.append(
            "- **Low Classifier Accuracy:** Consider retraining encoder with higher persona alignment loss weight, "
            "or refining persona definitions to increase separation."
        )

    # Check stability
    if stability_stats["stable_frac"] < 0.75:
        recommendations.append(
            "- **Low Stability:** Many clusters have unstable membership. Consider increasing min_cluster_size "
            "in HDBSCAN or resolution in Leiden."
        )

    # Check confusion pairs
    if len(high_conf) > 5:
        recommendations.append(
            f"- **High Confusion:** {len(high_conf)} persona pairs have high confusion. "
            "Review top pairs for potential merge."
        )

    # Check noise
    if artifacts["labels_stats"]["noise_frac"] > 0.15:
        recommendations.append(
            f"- **High Noise:** {100 * artifacts['labels_stats']['noise_frac']:.1f}% of sessions are marked as noise. "
            "This might indicate poor embedding quality or overly strict clustering parameters."
        )

    # Check gates
    if not gate_results["all_passed"]:
        failed_gates = [name for name, res in gate_results["gates"].items() if not res["passed"]]
        recommendations.append(
            f"- **Failed Gates:** {', '.join(failed_gates)}. Address these metrics before promoting clusters to production."
        )

    if recommendations:
        for rec in recommendations:
            report.append(rec + "\n")
    else:
        report.append("✓ **All metrics look good!** Clusters are ready for router integration.\n")

    report.append("\n---\n")

    # Next Steps
    report.append("## Next Steps\n")
    report.append("1. Review confusion matrix and merge/split suggestions")
    report.append("2. If gates pass, update `twin_bank.json` with new cluster centers")
    report.append("3. Enable feature flag `use_encoder_embeddings: true` in router config")
    report.append("4. Monitor router latency and twin assignment stability in production")
    report.append("5. Run nightly discovery pipeline to track cluster drift")

    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(report))

    print(f"✓ Report generated: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate discovery pipeline report"
    )
    parser.add_argument(
        "--emb",
        type=Path,
        required=True,
        help="Path to embeddings parquet"
    )
    parser.add_argument(
        "--graph",
        type=Path,
        required=True,
        help="Path to graph pickle"
    )
    parser.add_argument(
        "--labels",
        type=Path,
        required=True,
        help="Path to labels pickle"
    )
    parser.add_argument(
        "--stability",
        type=Path,
        required=True,
        help="Path to stability pickle"
    )
    parser.add_argument(
        "--classifier",
        type=Path,
        required=True,
        help="Path to classifier pickle"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("CONFIGS/discovery.yaml"),
        help="Path to discovery config"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("artifacts/discovery/report.md"),
        help="Output path for report"
    )

    args = parser.parse_args()

    # Load config
    with open(args.config) as f:
        config = yaml.safe_load(f)

    # Load artifacts
    artifacts = load_all_artifacts(
        emb_path=args.emb,
        graph_path=args.graph,
        labels_path=args.labels,
        stability_path=args.stability,
        classifier_path=args.classifier
    )

    # Generate report
    generate_report(
        artifacts=artifacts,
        gate_config=config["gates"],
        output_path=args.out
    )


if __name__ == "__main__":
    main()
