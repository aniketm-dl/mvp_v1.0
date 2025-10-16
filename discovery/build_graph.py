from __future__ import annotations
import argparse
from pathlib import Path
from typing import Dict, Any, Tuple
import yaml
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors
import pickle


def load_embeddings(emb_path: Path) -> Tuple[np.ndarray, pd.DataFrame]:
    """
    Load embeddings from parquet file.

    Returns:
        embeddings: (N, D) array of embeddings
        metadata: DataFrame with user_id, session_id, persona_id, etc.
    """
    df = pd.read_parquet(emb_path)

    # Separate metadata from embeddings
    emb_cols = [c for c in df.columns if c.startswith("emb_")]
    meta_cols = [c for c in df.columns if not c.startswith("emb_")]

    embeddings = df[emb_cols].values
    metadata = df[meta_cols]

    print(f"Loaded {len(embeddings)} embeddings with dim={embeddings.shape[1]}")
    return embeddings, metadata


def build_knn_graph(
    embeddings: np.ndarray,
    k: int,
    metric: str,
    min_similarity: float,
    approximate: bool,
    seed: int
) -> Dict[str, Any]:
    """
    Build k-NN graph with cosine similarity.

    Drop edges below min_similarity threshold to remove weak connections.

    Returns:
        graph: Dict with keys:
            - indices: (N, k) array of neighbor indices
            - distances: (N, k) array of distances (1 - cosine_sim for metric='cosine')
            - similarities: (N, k) array of cosine similarities
            - adjacency: (N, N) sparse adjacency matrix
    """
    N, D = embeddings.shape
    print(f"Building k-NN graph: N={N}, k={k}, metric={metric}")

    # Use NearestNeighbors for efficiency
    # For cosine similarity, use metric='cosine' which computes 1 - cosine_sim as distance
    nn = NearestNeighbors(
        n_neighbors=k + 1,  # +1 to include self
        metric=metric,
        algorithm="auto",
        n_jobs=-1
    )
    nn.fit(embeddings)

    # Find k nearest neighbors
    distances, indices = nn.kneighbors(embeddings)

    # Remove self (first neighbor)
    distances = distances[:, 1:]
    indices = indices[:, 1:]

    # Convert distances to similarities
    if metric == "cosine":
        # distance = 1 - cosine_sim, so cosine_sim = 1 - distance
        similarities = 1.0 - distances
    else:
        # For euclidean, convert to similarity using Gaussian kernel
        # similarity = exp(-distance^2 / (2 * sigma^2))
        # Use median distance as sigma
        sigma = np.median(distances)
        similarities = np.exp(-(distances ** 2) / (2 * sigma ** 2))

    # Apply threshold: drop edges below min_similarity
    print(f"Applying similarity threshold: {min_similarity}")
    mask = similarities >= min_similarity
    n_edges_before = similarities.size
    n_edges_after = mask.sum()
    print(f"Edges: {n_edges_before} → {n_edges_after} ({100 * n_edges_after / n_edges_before:.1f}% retained)")

    # Build adjacency matrix (sparse)
    # For clustering, we'll use a full dense similarity matrix
    # but only with edges above threshold
    adj_matrix = np.zeros((N, N))
    for i in range(N):
        for j_idx, (j, sim) in enumerate(zip(indices[i], similarities[i])):
            if mask[i, j_idx]:
                adj_matrix[i, j] = sim
                adj_matrix[j, i] = sim  # Symmetric

    # Convert adjacency to distance matrix for HDBSCAN
    # HDBSCAN expects distances, not similarities
    # distance = 1 - similarity for cosine
    dist_matrix = 1.0 - adj_matrix

    # Ensure diagonal is zero
    np.fill_diagonal(dist_matrix, 0.0)

    graph = {
        "indices": indices,
        "distances": distances,
        "similarities": similarities,
        "mask": mask,
        "adjacency": adj_matrix,
        "distance_matrix": dist_matrix,
        "N": N,
        "k": k,
        "metric": metric,
        "min_similarity": min_similarity
    }

    return graph


def save_graph(graph: Dict[str, Any], output_path: Path) -> None:
    """Save graph to disk using pickle."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        pickle.dump(graph, f)
    print(f"Saved graph to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Build k-NN graph from embeddings"
    )
    parser.add_argument(
        "--emb",
        type=Path,
        required=True,
        help="Path to embeddings parquet"
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
        default=Path("artifacts/discovery/graph.pkl"),
        help="Output path for graph"
    )

    args = parser.parse_args()

    # Load config
    with open(args.config) as f:
        config = yaml.safe_load(f)

    graph_config = config["graph"]

    # Load embeddings
    embeddings, metadata = load_embeddings(args.emb)

    # Build graph
    graph = build_knn_graph(
        embeddings=embeddings,
        k=graph_config["k"],
        metric=graph_config["metric"],
        min_similarity=graph_config["min_similarity"],
        approximate=graph_config["approximate"],
        seed=graph_config["seed"]
    )

    # Add metadata to graph
    graph["metadata"] = metadata

    # Save
    save_graph(graph, args.out)

    print(f"\n✓ Built k-NN graph")
    print(f"  Nodes: {graph['N']}")
    print(f"  k: {graph['k']}")
    print(f"  Edges retained: {graph['mask'].sum()} / {graph['mask'].size}")
    print(f"  Density: {graph['adjacency'].sum() / (graph['N'] * (graph['N'] - 1)):.4f}")


if __name__ == "__main__":
    main()
