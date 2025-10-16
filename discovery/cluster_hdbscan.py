from __future__ import annotations
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple
import yaml
import numpy as np
import pickle

try:
    import hdbscan
    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False
    print("WARNING: hdbscan not installed. Install with: pip install hdbscan")

try:
    import igraph as ig
    import leidenalg
    LEIDEN_AVAILABLE = True
except ImportError:
    LEIDEN_AVAILABLE = False
    print("WARNING: leiden not installed. Install with: pip install igraph leidenalg")


def load_graph(graph_path: Path) -> Dict[str, Any]:
    """Load graph from pickle."""
    with open(graph_path, "rb") as f:
        graph = pickle.load(f)
    print(f"Loaded graph: N={graph['N']}, k={graph['k']}")
    return graph


def cluster_hdbscan(
    distance_matrix: np.ndarray,
    min_cluster_size: int,
    min_samples: int,
    cluster_selection_method: str,
    cluster_selection_epsilon: float,
    alpha: float,
    seed: int
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Run HDBSCAN clustering on precomputed distance matrix.

    Returns:
        labels: (N,) array of cluster labels (-1 = noise)
        stats: Dict with clustering statistics
    """
    if not HDBSCAN_AVAILABLE:
        raise ImportError("hdbscan not installed")

    print(f"Running HDBSCAN: min_cluster_size={min_cluster_size}, min_samples={min_samples}")

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric="precomputed",
        cluster_selection_method=cluster_selection_method,
        cluster_selection_epsilon=cluster_selection_epsilon,
        alpha=alpha,
        gen_min_span_tree=True
    )

    labels = clusterer.fit_predict(distance_matrix)

    # Compute stats
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = (labels == -1).sum()
    cluster_sizes = {
        int(label): int((labels == label).sum())
        for label in set(labels) if label != -1
    }

    stats = {
        "n_clusters": n_clusters,
        "n_noise": n_noise,
        "noise_frac": n_noise / len(labels),
        "cluster_sizes": cluster_sizes,
        "probabilities": clusterer.probabilities_,
        "outlier_scores": clusterer.outlier_scores_
    }

    print(f"  Found {n_clusters} clusters, {n_noise} noise points ({100 * stats['noise_frac']:.1f}%)")
    print(f"  Cluster sizes: {cluster_sizes}")

    return labels, stats


def cluster_leiden(
    adjacency: np.ndarray,
    resolution: float,
    n_iterations: int,
    seed: int
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Run Leiden clustering on adjacency matrix as fallback.

    Leiden is a community detection algorithm that works well on graphs.
    Use this if HDBSCAN produces too many fragments.

    Returns:
        labels: (N,) array of cluster labels
        stats: Dict with clustering statistics
    """
    if not LEIDEN_AVAILABLE:
        raise ImportError("igraph and leidenalg not installed")

    print(f"Running Leiden fallback: resolution={resolution}, n_iterations={n_iterations}")

    # Convert adjacency to igraph
    # Only include edges with non-zero weight
    sources, targets = np.nonzero(adjacency)
    weights = adjacency[sources, targets]

    # Create directed graph (will be treated as undirected)
    g = ig.Graph(directed=False)
    g.add_vertices(adjacency.shape[0])
    edges = list(zip(sources.tolist(), targets.tolist()))
    g.add_edges(edges)
    g.es["weight"] = weights.tolist()

    # Run Leiden
    np.random.seed(seed)
    partition = leidenalg.find_partition(
        g,
        leidenalg.RBConfigurationVertexPartition,
        resolution_parameter=resolution,
        n_iterations=n_iterations,
        seed=seed,
        weights="weight"
    )

    labels = np.array(partition.membership)

    # Compute stats
    n_clusters = len(set(labels))
    cluster_sizes = {
        int(label): int((labels == label).sum())
        for label in set(labels)
    }

    stats = {
        "n_clusters": n_clusters,
        "n_noise": 0,  # Leiden doesn't produce noise
        "noise_frac": 0.0,
        "cluster_sizes": cluster_sizes,
        "modularity": partition.modularity
    }

    print(f"  Found {n_clusters} clusters")
    print(f"  Cluster sizes: {cluster_sizes}")
    print(f"  Modularity: {stats['modularity']:.4f}")

    return labels, stats


def save_labels(labels: np.ndarray, stats: Dict[str, Any], output_path: Path) -> None:
    """Save labels and stats to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "labels": labels,
        "stats": stats
    }
    with open(output_path, "wb") as f:
        pickle.dump(data, f)
    print(f"Saved labels to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Run HDBSCAN clustering (with Leiden fallback)"
    )
    parser.add_argument(
        "--graph",
        type=Path,
        required=True,
        help="Path to graph pickle"
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
        default=Path("artifacts/discovery/labels.pkl"),
        help="Output path for labels"
    )
    parser.add_argument(
        "--use-leiden",
        action="store_true",
        help="Force use of Leiden instead of HDBSCAN"
    )

    args = parser.parse_args()

    # Load config
    with open(args.config) as f:
        config = yaml.safe_load(f)

    clustering_config = config["clustering"]

    # Load graph
    graph = load_graph(args.graph)

    # Run clustering
    if args.use_leiden or not HDBSCAN_AVAILABLE:
        print("Using Leiden algorithm")
        leiden_config = clustering_config["leiden"]
        labels, stats = cluster_leiden(
            adjacency=graph["adjacency"],
            resolution=leiden_config["resolution"],
            n_iterations=leiden_config["n_iterations"],
            seed=leiden_config["seed"]
        )
        stats["algorithm"] = "leiden"
    else:
        print("Using HDBSCAN algorithm")
        hdbscan_config = clustering_config["hdbscan"]
        labels, stats = cluster_hdbscan(
            distance_matrix=graph["distance_matrix"],
            min_cluster_size=hdbscan_config["min_cluster_size"],
            min_samples=hdbscan_config["min_samples"],
            cluster_selection_method=hdbscan_config["cluster_selection_method"],
            cluster_selection_epsilon=hdbscan_config["cluster_selection_epsilon"],
            alpha=hdbscan_config["alpha"],
            seed=config["seed"]
        )
        stats["algorithm"] = "hdbscan"

        # Check if we should fall back to Leiden (too fragmented)
        if stats["n_clusters"] > 30 or stats["noise_frac"] > 0.25:
            print(f"\n⚠ HDBSCAN produced fragmented clusters (n={stats['n_clusters']}, noise={100*stats['noise_frac']:.1f}%)")
            print("Falling back to Leiden...")
            leiden_config = clustering_config["leiden"]
            labels, stats = cluster_leiden(
                adjacency=graph["adjacency"],
                resolution=leiden_config["resolution"],
                n_iterations=leiden_config["n_iterations"],
                seed=leiden_config["seed"]
            )
            stats["algorithm"] = "leiden_fallback"

    # Save
    save_labels(labels, stats, args.out)

    print(f"\n✓ Clustering complete")
    print(f"  Algorithm: {stats['algorithm']}")
    print(f"  Clusters: {stats['n_clusters']}")
    print(f"  Noise: {stats['n_noise']} ({100 * stats['noise_frac']:.1f}%)")


if __name__ == "__main__":
    main()
