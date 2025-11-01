"""
Comprehensive tests for the clustering and explainability system.
"""

from __future__ import annotations

import pytest
import numpy as np
import json
from pathlib import Path

# Test imports
from src.models.mixture import (
    cosine_similarity,
    euclidean_distance,
    compute_all_distances,
    get_twin_center,
    get_all_twin_centers,
    get_twin_labels,
    load_twin_bank,
)
from src.metrics.explainability import (
    compute_feature_importance,
    generate_natural_language_explanation,
    compute_all_twin_distances,
    explain_assignment,
    compare_twins,
)
from src.metrics.hierarchy import (
    compute_hierarchical_clustering,
    generate_decision_tree,
    analyze_persona_hierarchy,
    create_cluster_summary,
)


def test_euclidean_distance():
    """Test Euclidean distance computation."""
    vec1 = [0, 0, 0]
    vec2 = [3, 4, 0]

    dist = euclidean_distance(vec1, vec2)
    assert abs(dist - 5.0) < 1e-6  # 3-4-5 triangle


def test_compute_all_distances():
    """Test distance computation to all twins."""
    query = [0.5] * 15

    bank = {
        "twins": [
            {"id": "k0", "label": "Budget", "center": [0.4] * 15},
            {"id": "k1", "label": "Premium", "center": [0.6] * 15},
        ]
    }

    distances = compute_all_distances(query, bank, metric="cosine")

    assert len(distances) == 2
    assert distances[0]["twin_id"] in ["k0", "k1"]
    assert "distance" in distances[0]
    assert "similarity" in distances[0]

    # Distances should be sorted (closest first)
    assert distances[0]["distance"] <= distances[1]["distance"]


def test_get_twin_center():
    """Test retrieving a specific twin center."""
    bank = {
        "twins": [
            {"id": "k0", "label": "Budget", "center": [0.1, 0.2, 0.3]},
            {"id": "k1", "label": "Premium", "center": [0.4, 0.5, 0.6]},
        ]
    }

    center = get_twin_center("k1", bank)
    assert center == [0.4, 0.5, 0.6]

    # Test missing twin
    center_missing = get_twin_center("k999", bank)
    assert len(center_missing) == 15  # Returns default


def test_get_all_twin_centers():
    """Test getting all twin centers as dict."""
    bank = {
        "twins": [
            {"id": "k0", "label": "Budget", "center": [0.1, 0.2]},
            {"id": "k1", "label": "Premium", "center": [0.3, 0.4]},
        ]
    }

    centers = get_all_twin_centers(bank)

    assert len(centers) == 2
    assert centers["k0"] == [0.1, 0.2]
    assert centers["k1"] == [0.3, 0.4]


def test_get_twin_labels():
    """Test getting all twin labels."""
    bank = {
        "twins": [
            {"id": "k0", "label": "Budget-Conscious"},
            {"id": "k1", "label": "Premium Quality"},
        ]
    }

    labels = get_twin_labels(bank)

    assert len(labels) == 2
    assert labels["k0"] == "Budget-Conscious"
    assert labels["k1"] == "Premium Quality"


def test_compute_feature_importance():
    """Test feature importance calculation."""
    user_emb = np.array([0.8, 0.2, 0.5, 0.3, 0.6])
    twin_center = np.array([0.7, 0.3, 0.4, 0.2, 0.7])
    feature_names = ["f1", "f2", "f3", "f4", "f5"]

    importances = compute_feature_importance(
        user_emb,
        twin_center,
        feature_names,
        method="cosine_decomposition"
    )

    assert len(importances) == 5
    assert all("feature" in imp for imp in importances)
    assert all("importance" in imp for imp in importances)
    assert all("user_value" in imp for imp in importances)
    assert all("twin_value" in imp for imp in importances)

    # Should be sorted by importance (descending)
    for i in range(len(importances) - 1):
        assert abs(importances[i]["importance"]) >= abs(importances[i + 1]["importance"])


def test_generate_natural_language_explanation():
    """Test natural language explanation generation."""
    user_emb = np.array([0.3, 0.2, 0.15] + [0.8, 0.2, 0.3, 0.1] + [0.3, 0.5, 0.6])
    twin_center = np.array([0.35, 0.25, 0.15] + [0.9, 0.2, 0.3, 0.1] + [0.3, 0.4, 0.5])

    feature_names = [
        "search_freq", "filter_freq", "sort_freq",
        "price_sensitivity", "quality_focus", "convenience_priority", "brand_loyalty",
        "age_group", "income_level", "location_type"
    ]

    importances = compute_feature_importance(user_emb, twin_center, feature_names)

    explanation = generate_natural_language_explanation(
        user_emb,
        twin_center,
        "Budget-Conscious",
        feature_names,
        importances,
        top_k=3
    )

    assert isinstance(explanation, str)
    assert "Budget-Conscious" in explanation
    assert "persona" in explanation.lower()


def test_compute_all_twin_distances():
    """Test computing distances to all twins."""
    user_emb = np.array([0.5] * 10)
    twin_centers = np.array([
        [0.4] * 10,
        [0.6] * 10,
        [0.2] * 10,
    ])
    twin_labels = ["Budget", "Premium", "Explorer"]

    distances = compute_all_twin_distances(
        user_emb,
        twin_centers,
        twin_labels,
        metric="cosine"
    )

    assert len(distances) == 3
    assert distances[0]["distance"] <= distances[1]["distance"]  # Sorted

    # All should have required fields
    for dist in distances:
        assert "twin_id" in dist
        assert "label" in dist
        assert "distance" in dist
        assert "similarity" in dist


def test_explain_assignment():
    """Test complete assignment explanation."""
    np.random.seed(42)

    # Create simple 3D embeddings for testing
    user_emb = np.array([0.5, 0.5, 0.5])
    twin_centers = np.array([
        [0.4, 0.4, 0.4],
        [0.8, 0.8, 0.8],
        [0.1, 0.1, 0.1],
    ])
    twin_labels = ["Budget", "Premium", "Explorer"]
    feature_names = ["f1", "f2", "f3"]

    explanation = explain_assignment(
        user_emb,
        assigned_twin_idx=0,
        twin_centers=twin_centers,
        twin_labels=twin_labels,
        feature_names=feature_names,
    )

    assert "primary_twin" in explanation
    assert explanation["primary_twin"]["twin_id"] == "k0"
    assert explanation["primary_twin"]["label"] == "Budget"

    assert "feature_importance" in explanation
    assert len(explanation["feature_importance"]) <= 5

    assert "natural_language" in explanation
    assert isinstance(explanation["natural_language"], str)

    assert "all_distances" in explanation
    assert len(explanation["all_distances"]) == 3

    assert "alternatives" in explanation
    assert len(explanation["alternatives"]) <= 3

    assert "confidence" in explanation
    assert isinstance(explanation["confidence"], float)


def test_compare_twins():
    """Test twin comparison."""
    twin1 = np.array([0.8, 0.2, 0.5, 0.3])
    twin2 = np.array([0.2, 0.8, 0.3, 0.7])
    feature_names = ["price_sensitivity", "quality_focus", "speed", "loyalty"]

    comparison = compare_twins(
        twin1,
        twin2,
        "Budget",
        "Premium",
        feature_names,
        top_k=3
    )

    assert comparison["twin1"] == "Budget"
    assert comparison["twin2"] == "Premium"
    assert "euclidean_distance" in comparison
    assert "cosine_similarity" in comparison
    assert "top_differences" in comparison
    assert len(comparison["top_differences"]) == 3


def test_compute_hierarchical_clustering():
    """Test hierarchical clustering computation."""
    # Create 3 well-separated clusters
    np.random.seed(42)
    cluster1 = np.random.normal([0, 0], 0.1, (20, 2))
    cluster2 = np.random.normal([3, 3], 0.1, (20, 2))
    cluster3 = np.random.normal([0, 3], 0.1, (20, 2))

    embeddings = np.vstack([cluster1, cluster2, cluster3])

    result = compute_hierarchical_clustering(embeddings, method="ward", metric="euclidean")

    assert "linkage_matrix" in result
    assert "dendrogram_data" in result
    assert "cluster_cuts" in result

    # Check dendrogram data structure
    dend = result["dendrogram_data"]
    assert "icoord" in dend
    assert "dcoord" in dend
    assert "leaves" in dend


def test_generate_decision_tree():
    """Test decision tree generation."""
    np.random.seed(42)

    twin_centers = np.array([
        [0.8, 0.2, 0.5],
        [0.2, 0.8, 0.3],
        [0.5, 0.5, 0.8],
    ])
    twin_labels = ["Budget", "Premium", "Explorer"]
    feature_names = ["price_sensitivity", "quality_focus", "convenience"]

    tree_data = generate_decision_tree(
        twin_centers,
        twin_labels,
        feature_names,
        max_depth=3
    )

    assert "tree_structure" in tree_data
    assert "tree_text" in tree_data
    assert "feature_importances" in tree_data

    # Check tree structure
    tree = tree_data["tree_structure"]
    assert "type" in tree
    assert tree["type"] in ["decision", "leaf"]


def test_analyze_persona_hierarchy():
    """Test persona hierarchy analysis."""
    twin_centers = np.array([
        [0.8, 0.2, 0.5, 0.3],
        [0.2, 0.8, 0.3, 0.7],
        [0.5, 0.5, 0.8, 0.4],
    ])
    twin_labels = ["Budget", "Premium", "Explorer"]
    feature_names = ["price_sensitivity", "quality_focus", "convenience", "loyalty"]

    analysis = analyze_persona_hierarchy(twin_centers, twin_labels, feature_names)

    assert "pairwise_distances" in analysis
    assert "closest_pairs" in analysis
    assert "farthest_pairs" in analysis
    assert "feature_differentiation" in analysis

    # Check pairwise distances shape
    dist_matrix = analysis["pairwise_distances"]
    assert len(dist_matrix) == 3
    assert len(dist_matrix[0]) == 3

    # Check pairs
    assert len(analysis["closest_pairs"]) == 5
    assert len(analysis["farthest_pairs"]) == 5


def test_create_cluster_summary():
    """Test cluster summary creation."""
    np.random.seed(42)

    # Create embeddings with clear cluster assignments
    n_per_cluster = 30
    cluster1 = np.random.normal([0.8, 0.2], 0.1, (n_per_cluster, 2))
    cluster2 = np.random.normal([0.2, 0.8], 0.1, (n_per_cluster, 2))

    embeddings = np.vstack([cluster1, cluster2])
    labels = np.array([0] * n_per_cluster + [1] * n_per_cluster)

    twin_centers = np.array([
        [0.8, 0.2],
        [0.2, 0.8],
    ])
    twin_labels = ["Budget", "Premium"]
    feature_names = ["price_sensitivity", "quality_focus"]

    summaries = create_cluster_summary(
        embeddings,
        labels,
        twin_centers,
        twin_labels,
        feature_names
    )

    assert len(summaries) == 2

    for summary in summaries:
        assert "twin_id" in summary
        assert "label" in summary
        assert "n_users" in summary
        assert "percentage" in summary
        assert "cohesion" in summary
        assert "top_features" in summary
        assert "center" in summary

    # Check percentages sum to ~100%
    total_pct = sum(s["percentage"] for s in summaries)
    assert abs(total_pct - 100.0) < 0.1


def test_load_twin_bank():
    """Test loading twin bank (uses default if file missing)."""
    bank = load_twin_bank()

    assert "version" in bank
    assert "twins" in bank
    assert len(bank["twins"]) > 0

    # Check twin structure
    twin = bank["twins"][0]
    assert "id" in twin
    assert "label" in twin
    assert "center" in twin


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
