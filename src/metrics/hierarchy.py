"""
Hierarchical persona visualization and analysis.
Generates dendrograms, decision trees, and hierarchical cluster insights.
"""

from __future__ import annotations

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.spatial.distance import pdist, squareform
import json


def compute_hierarchical_clustering(
    embeddings: np.ndarray,
    method: str = "ward",
    metric: str = "euclidean",
) -> Dict[str, Any]:
    """
    Compute hierarchical clustering and return dendrogram data.

    Args:
        embeddings: (N, D) array of user embeddings
        method: Linkage method ("ward", "complete", "average", "single")
        metric: Distance metric ("euclidean", "cosine", "manhattan")

    Returns:
        Dict containing:
            - linkage_matrix: Hierarchical clustering linkage matrix
            - dendrogram_data: Dendrogram structure for visualization
            - cluster_assignments: Flat cluster assignments at different cuts
    """
    # Compute pairwise distances
    if metric == "cosine":
        # Convert to cosine distance
        distances = pdist(embeddings, metric="cosine")
    else:
        distances = pdist(embeddings, metric=metric)

    # Perform hierarchical clustering
    Z = linkage(distances, method=method)

    # Generate dendrogram data (without plotting)
    dend = dendrogram(Z, no_plot=True)

    # Get cluster assignments at different height cuts
    cluster_cuts = {}
    for n_clusters in [2, 3, 5, 7, 10, 15]:
        if n_clusters <= len(embeddings):
            clusters = fcluster(Z, n_clusters, criterion="maxclust")
            cluster_cuts[f"n{n_clusters}"] = clusters.tolist()

    return {
        "linkage_matrix": Z.tolist(),
        "dendrogram_data": {
            "icoord": dend["icoord"],
            "dcoord": dend["dcoord"],
            "ivl": dend["ivl"],
            "leaves": dend["leaves"],
            "color_list": dend["color_list"],
        },
        "cluster_cuts": cluster_cuts,
    }


def generate_decision_tree(
    twin_centers: np.ndarray,
    twin_labels: List[str],
    feature_names: List[str],
    max_depth: int = 3,
) -> Dict[str, Any]:
    """
    Generate a decision tree showing how personas split on key features.

    Args:
        twin_centers: (K, D) array of twin center embeddings
        twin_labels: List of twin label strings
        feature_names: List of feature dimension names
        max_depth: Maximum tree depth

    Returns:
        Decision tree structure as nested dict
    """
    from sklearn.tree import DecisionTreeClassifier, export_text
    import io

    # Create synthetic data by sampling around twin centers
    n_samples_per_twin = 100
    X_samples = []
    y_samples = []

    for i, center in enumerate(twin_centers):
        # Add small noise around each center
        noise = np.random.normal(0, 0.1, size=(n_samples_per_twin, len(center)))
        samples = center + noise
        X_samples.append(samples)
        y_samples.extend([i] * n_samples_per_twin)

    X = np.vstack(X_samples)
    y = np.array(y_samples)

    # Train decision tree
    clf = DecisionTreeClassifier(
        max_depth=max_depth,
        min_samples_split=20,
        min_samples_leaf=10,
        random_state=42,
    )
    clf.fit(X, y)

    # Extract tree structure
    tree_text = export_text(clf, feature_names=feature_names)

    # Build tree dict structure
    tree_dict = _build_tree_dict(clf, feature_names, twin_labels)

    return {
        "tree_structure": tree_dict,
        "tree_text": tree_text,
        "feature_importances": {
            feature_names[i]: float(imp)
            for i, imp in enumerate(clf.feature_importances_)
            if imp > 0.01  # Only include features with >1% importance
        },
    }


def _build_tree_dict(clf, feature_names: List[str], class_labels: List[str]) -> Dict[str, Any]:
    """Build nested dict representation of decision tree."""
    tree = clf.tree_

    def recurse(node: int) -> Dict[str, Any]:
        if tree.feature[node] == -2:  # Leaf node
            class_idx = np.argmax(tree.value[node])
            return {
                "type": "leaf",
                "class": class_labels[class_idx],
                "samples": int(tree.n_node_samples[node]),
                "value": tree.value[node].tolist(),
            }
        else:  # Decision node
            feature = feature_names[tree.feature[node]]
            threshold = float(tree.threshold[node])

            return {
                "type": "decision",
                "feature": feature,
                "threshold": threshold,
                "samples": int(tree.n_node_samples[node]),
                "left": recurse(tree.children_left[node]),
                "right": recurse(tree.children_right[node]),
            }

    return recurse(0)


def analyze_persona_hierarchy(
    twin_centers: np.ndarray,
    twin_labels: List[str],
    feature_names: List[str],
) -> Dict[str, Any]:
    """
    Analyze hierarchical relationships between personas.

    Args:
        twin_centers: (K, D) array of twin centers
        twin_labels: List of twin labels
        feature_names: List of feature dimension names

    Returns:
        Analysis containing:
            - pairwise_distances: Distance matrix between twins
            - closest_pairs: Most similar twin pairs
            - farthest_pairs: Most different twin pairs
            - feature_differentiation: Which features differentiate twins most
    """
    # Compute pairwise distances
    dist_matrix = squareform(pdist(twin_centers, metric="euclidean"))

    # Find closest and farthest pairs
    n_twins = len(twin_labels)
    pairs = []

    for i in range(n_twins):
        for j in range(i + 1, n_twins):
            pairs.append({
                "twin1": twin_labels[i],
                "twin2": twin_labels[j],
                "distance": float(dist_matrix[i, j]),
            })

    pairs_sorted = sorted(pairs, key=lambda x: x["distance"])
    closest_pairs = pairs_sorted[:5]
    farthest_pairs = pairs_sorted[-5:]

    # Analyze feature differentiation
    feature_variances = np.var(twin_centers, axis=0)
    feature_differentiation = {
        feature_names[i]: float(var)
        for i, var in enumerate(feature_variances)
    }
    feature_differentiation = dict(
        sorted(feature_differentiation.items(), key=lambda x: x[1], reverse=True)
    )

    return {
        "pairwise_distances": dist_matrix.tolist(),
        "closest_pairs": closest_pairs,
        "farthest_pairs": farthest_pairs,
        "feature_differentiation": feature_differentiation,
    }


def create_cluster_summary(
    embeddings: np.ndarray,
    labels: np.ndarray,
    twin_centers: np.ndarray,
    twin_labels: List[str],
    feature_names: List[str],
) -> List[Dict[str, Any]]:
    """
    Create summary statistics for each cluster/persona.

    Args:
        embeddings: (N, D) array of all user embeddings
        labels: (N,) array of cluster assignments
        twin_centers: (K, D) array of twin centers
        twin_labels: List of twin labels
        feature_names: List of feature names

    Returns:
        List of cluster summaries with statistics
    """
    summaries = []

    for twin_idx, twin_label in enumerate(twin_labels):
        # Get users assigned to this twin
        mask = labels == twin_idx
        if not np.any(mask):
            continue

        twin_embeddings = embeddings[mask]
        n_users = len(twin_embeddings)

        # Compute statistics
        mean_features = np.mean(twin_embeddings, axis=0)
        std_features = np.std(twin_embeddings, axis=0)

        # Top distinguishing features (highest deviation from overall mean)
        overall_mean = np.mean(embeddings, axis=0)
        feature_deviations = np.abs(mean_features - overall_mean)
        top_feature_indices = np.argsort(feature_deviations)[-5:][::-1]

        top_features = [
            {
                "feature": feature_names[idx],
                "value": float(mean_features[idx]),
                "deviation": float(feature_deviations[idx]),
                "std": float(std_features[idx]),
            }
            for idx in top_feature_indices
        ]

        # Intra-cluster distances
        intra_distances = pdist(twin_embeddings, metric="euclidean")
        cohesion = float(np.mean(intra_distances)) if len(intra_distances) > 0 else 0.0

        summaries.append({
            "twin_id": f"k{twin_idx}",
            "label": twin_label,
            "n_users": n_users,
            "percentage": float(n_users / len(embeddings) * 100),
            "cohesion": cohesion,
            "top_features": top_features,
            "center": twin_centers[twin_idx].tolist(),
        })

    return summaries


def generate_hierarchy_visualization_data(
    embeddings: np.ndarray,
    labels: np.ndarray,
    twin_centers: np.ndarray,
    twin_labels: List[str],
    feature_names: List[str],
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate complete hierarchy visualization data for API endpoint.

    Args:
        embeddings: User embeddings
        labels: Cluster assignments
        twin_centers: Twin center vectors
        twin_labels: Twin label strings
        feature_names: Feature dimension names
        config: Clustering configuration

    Returns:
        Complete hierarchy data structure
    """
    method = config.get("hierarchical_linkage", "ward")
    metric = config.get("hierarchical_metric", "euclidean")

    # Compute hierarchical clustering
    hierarchy = compute_hierarchical_clustering(twin_centers, method, metric)

    # Generate decision tree
    decision_tree = generate_decision_tree(
        twin_centers,
        twin_labels,
        feature_names,
        max_depth=3,
    )

    # Analyze persona relationships
    analysis = analyze_persona_hierarchy(twin_centers, twin_labels, feature_names)

    # Create cluster summaries
    summaries = create_cluster_summary(
        embeddings,
        labels,
        twin_centers,
        twin_labels,
        feature_names,
    )

    return {
        "hierarchical_clustering": hierarchy,
        "decision_tree": decision_tree,
        "persona_analysis": analysis,
        "cluster_summaries": summaries,
        "metadata": {
            "method": method,
            "metric": metric,
            "n_clusters": len(twin_labels),
            "n_users": len(embeddings),
        },
    }


if __name__ == "__main__":
    # Demo with synthetic data
    np.random.seed(42)

    # Create 3 well-separated clusters
    n_per_cluster = 50
    cluster1 = np.random.normal([0, 0, 0], 0.3, (n_per_cluster, 3))
    cluster2 = np.random.normal([3, 3, 0], 0.3, (n_per_cluster, 3))
    cluster3 = np.random.normal([0, 3, 3], 0.3, (n_per_cluster, 3))

    embeddings = np.vstack([cluster1, cluster2, cluster3])
    labels = np.array([0] * n_per_cluster + [1] * n_per_cluster + [2] * n_per_cluster)

    twin_centers = np.array([
        np.mean(cluster1, axis=0),
        np.mean(cluster2, axis=0),
        np.mean(cluster3, axis=0),
    ])

    twin_labels = ["Budget", "Premium", "Explorer"]
    feature_names = ["price_sensitivity", "quality_focus", "adventure_seeking"]

    config = {
        "hierarchical_linkage": "ward",
        "hierarchical_metric": "euclidean",
    }

    viz_data = generate_hierarchy_visualization_data(
        embeddings,
        labels,
        twin_centers,
        twin_labels,
        feature_names,
        config,
    )

    print(json.dumps(viz_data, indent=2))
