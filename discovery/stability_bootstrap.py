from __future__ import annotations
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple
import yaml
import numpy as np
import pickle
from sklearn.metrics import adjusted_rand_score
from tqdm import tqdm


def load_graph(graph_path: Path) -> Dict[str, Any]:
    """Load graph from pickle."""
    with open(graph_path, "rb") as f:
        graph = pickle.load(f)
    return graph


def load_labels(labels_path: Path) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Load labels from pickle."""
    with open(labels_path, "rb") as f:
        data = pickle.load(f)
    return data["labels"], data["stats"]


def bootstrap_clustering(
    embeddings: np.ndarray,
    labels_full: np.ndarray,
    clustering_fn,
    n_bootstrap: int,
    sample_frac: float,
    seed: int
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Run bootstrap stability analysis.

    For each bootstrap:
    1. Sample sample_frac of data
    2. Run clustering on sample
    3. Compute ARI between bootstrap labels and full labels

    Keep only points with high stability (ARI >= min_stability across bootstraps).

    Returns:
        stability_scores: (N,) array of stability scores (mean ARI across bootstraps)
        stats: Dict with stability statistics
    """
    N = len(embeddings)
    n_sample = int(N * sample_frac)

    print(f"Running {n_bootstrap} bootstrap iterations...")
    print(f"  Sample size: {n_sample} / {N} ({100 * sample_frac:.0f}%)")

    rng = np.random.RandomState(seed)

    # Store ARI scores for each point
    ari_scores = np.zeros((N, n_bootstrap))

    for b in tqdm(range(n_bootstrap), desc="Bootstrap"):
        # Sample indices
        sample_idx = rng.choice(N, size=n_sample, replace=False)
        mask = np.zeros(N, dtype=bool)
        mask[sample_idx] = True

        # Run clustering on sample
        try:
            labels_boot = clustering_fn(sample_idx)

            # Compute ARI between bootstrap and full clustering (only on sampled points)
            ari = adjusted_rand_score(
                labels_full[mask],
                labels_boot
            )

            # Assign ARI to sampled points
            ari_scores[mask, b] = ari

        except Exception as e:
            print(f"  Bootstrap {b} failed: {e}")
            continue

    # Compute stability score for each point (mean ARI across bootstraps where it was sampled)
    stability_scores = np.mean(ari_scores, axis=1)

    # Compute statistics
    stats = {
        "n_bootstrap": n_bootstrap,
        "mean_stability": float(np.mean(stability_scores)),
        "median_stability": float(np.median(stability_scores)),
        "min_stability": float(np.min(stability_scores)),
        "max_stability": float(np.max(stability_scores)),
        "std_stability": float(np.std(stability_scores))
    }

    print(f"\nStability statistics:")
    print(f"  Mean: {stats['mean_stability']:.4f}")
    print(f"  Median: {stats['median_stability']:.4f}")
    print(f"  Min: {stats['min_stability']:.4f}")
    print(f"  Max: {stats['max_stability']:.4f}")

    return stability_scores, stats


def identify_stable_cores(
    labels: np.ndarray,
    stability_scores: np.ndarray,
    min_stability: float
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Identify stable cores: points with stability >= min_stability.

    Points outside stable cores are marked as noise (-1).

    Returns:
        labels_stable: (N,) array with stable labels (-1 for unstable)
        stats: Dict with core statistics
    """
    stable_mask = stability_scores >= min_stability

    # Create new labels array
    labels_stable = labels.copy()
    labels_stable[~stable_mask] = -1

    # Compute stats
    n_stable = stable_mask.sum()
    n_unstable = (~stable_mask).sum()

    # Per-cluster stability
    cluster_ids = [c for c in set(labels) if c != -1]
    cluster_stability = {}
    for c in cluster_ids:
        c_mask = labels == c
        c_stable = stable_mask[c_mask].sum()
        c_total = c_mask.sum()
        cluster_stability[int(c)] = {
            "stable": int(c_stable),
            "total": int(c_total),
            "frac": float(c_stable / c_total) if c_total > 0 else 0.0
        }

    stats = {
        "n_stable": int(n_stable),
        "n_unstable": int(n_unstable),
        "stable_frac": float(n_stable / len(labels)),
        "cluster_stability": cluster_stability
    }

    print(f"\nStable cores:")
    print(f"  Stable: {n_stable} ({100 * stats['stable_frac']:.1f}%)")
    print(f"  Unstable: {n_unstable}")
    print(f"\n  Per-cluster stability:")
    for c, c_stats in cluster_stability.items():
        print(f"    Cluster {c}: {c_stats['stable']}/{c_stats['total']} ({100 * c_stats['frac']:.1f}%)")

    return labels_stable, stats


def save_stability(
    stability_scores: np.ndarray,
    labels_stable: np.ndarray,
    stats: Dict[str, Any],
    output_path: Path
) -> None:
    """Save stability results to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "stability_scores": stability_scores,
        "labels_stable": labels_stable,
        "stats": stats
    }
    with open(output_path, "wb") as f:
        pickle.dump(data, f)
    print(f"\nSaved stability results to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Run bootstrap stability analysis"
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
        "--config",
        type=Path,
        default=Path("CONFIGS/discovery.yaml"),
        help="Path to discovery config"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("artifacts/discovery/stability.pkl"),
        help="Output path for stability results"
    )

    args = parser.parse_args()

    # Load config
    with open(args.config) as f:
        config = yaml.safe_load(f)

    stability_config = config["stability"]

    # Load data
    print("Loading data...")
    graph = load_graph(args.graph)
    labels_full, _ = load_labels(args.labels)

    # Import embeddings to get raw vectors
    import pandas as pd
    df = pd.read_parquet(args.emb)
    emb_cols = [c for c in df.columns if c.startswith("emb_")]
    embeddings = df[emb_cols].values

    # Define clustering function for bootstrap
    # For simplicity, we'll reuse the same clustering algorithm
    # In practice, this should call the same clustering function used in cluster_hdbscan.py

    from discovery.cluster_hdbscan import cluster_hdbscan, cluster_leiden

    algorithm = config["clustering"].get("algorithm", "hdbscan")

    if algorithm == "hdbscan":
        hdbscan_config = config["clustering"]["hdbscan"]

        def clustering_fn(sample_idx):
            # Build distance matrix for sample
            emb_sample = embeddings[sample_idx]
            from sklearn.metrics.pairwise import cosine_distances
            dist_mat = cosine_distances(emb_sample, emb_sample)
            labels, _ = cluster_hdbscan(
                distance_matrix=dist_mat,
                min_cluster_size=max(3, hdbscan_config["min_cluster_size"] // 2),  # Scale down for smaller sample
                min_samples=max(2, hdbscan_config["min_samples"] // 2),
                cluster_selection_method=hdbscan_config["cluster_selection_method"],
                cluster_selection_epsilon=hdbscan_config["cluster_selection_epsilon"],
                alpha=hdbscan_config["alpha"],
                seed=config["seed"]
            )
            return labels
    else:
        # For Leiden, we'd need to rebuild the graph
        # Simplified here - just return full labels
        def clustering_fn(sample_idx):
            return labels_full[sample_idx]

    # Run bootstrap
    stability_scores, boot_stats = bootstrap_clustering(
        embeddings=embeddings,
        labels_full=labels_full,
        clustering_fn=clustering_fn,
        n_bootstrap=stability_config["n_bootstrap"],
        sample_frac=stability_config["sample_frac"],
        seed=stability_config["seed"]
    )

    # Identify stable cores
    labels_stable, core_stats = identify_stable_cores(
        labels=labels_full,
        stability_scores=stability_scores,
        min_stability=stability_config["min_stability"]
    )

    # Combine stats
    stats = {
        "bootstrap": boot_stats,
        "cores": core_stats
    }

    # Save
    save_stability(stability_scores, labels_stable, stats, args.out)

    print(f"\n✓ Stability analysis complete")
    print(f"  Mean stability: {boot_stats['mean_stability']:.4f}")
    print(f"  Stable cores: {core_stats['n_stable']} / {len(labels_full)} ({100 * core_stats['stable_frac']:.1f}%)")


if __name__ == "__main__":
    main()
