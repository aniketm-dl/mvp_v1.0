"""
Feature importance and explainability for persona assignments.
Provides attribution, natural language explanations, and debugging insights.
"""

from __future__ import annotations

import numpy as np
from typing import Dict, List, Any, Optional, Tuple


def compute_feature_importance(
    user_embedding: np.ndarray,
    twin_center: np.ndarray,
    feature_names: List[str],
    method: str = "cosine_decomposition",
) -> List[Dict[str, Any]]:
    """
    Compute feature-level importance scores for why a user matched a twin.

    Args:
        user_embedding: (D,) user's embedding vector
        twin_center: (D,) twin center embedding
        feature_names: List of feature names for each dimension
        method: Attribution method ("cosine_decomposition", "euclidean", "difference")

    Returns:
        List of feature importance dicts sorted by importance (descending)
    """
    if method == "cosine_decomposition":
        # Decompose cosine similarity into per-feature contributions
        dot_product = user_embedding * twin_center
        user_norm = np.linalg.norm(user_embedding)
        twin_norm = np.linalg.norm(twin_center)

        if user_norm > 0 and twin_norm > 0:
            # Each feature's contribution to cosine similarity
            contributions = dot_product / (user_norm * twin_norm)
        else:
            contributions = np.zeros_like(dot_product)

    elif method == "euclidean":
        # L2 distance contributions (negative = closer)
        contributions = -np.abs(user_embedding - twin_center)

    elif method == "difference":
        # Simple difference (positive = user > twin)
        contributions = user_embedding - twin_center

    else:
        raise ValueError(f"Unknown method: {method}")

    # Build feature importance list
    importances = []
    for i, feature_name in enumerate(feature_names):
        importances.append({
            "feature": feature_name,
            "importance": float(contributions[i]),
            "user_value": float(user_embedding[i]),
            "twin_value": float(twin_center[i]),
            "difference": float(user_embedding[i] - twin_center[i]),
        })

    # Sort by absolute importance (descending)
    importances.sort(key=lambda x: abs(x["importance"]), reverse=True)

    return importances


def generate_natural_language_explanation(
    user_embedding: np.ndarray,
    twin_center: np.ndarray,
    twin_label: str,
    feature_names: List[str],
    feature_importances: List[Dict[str, Any]],
    top_k: int = 3,
) -> str:
    """
    Generate human-readable explanation for persona assignment.

    Args:
        user_embedding: User's embedding
        twin_center: Twin center embedding
        twin_label: Twin persona label (e.g., "Budget-Conscious")
        feature_names: List of feature names
        feature_importances: Output from compute_feature_importance
        top_k: Number of top features to mention

    Returns:
        Natural language explanation string
    """
    # Get top K features
    top_features = feature_importances[:top_k]

    # Build explanation
    explanation_parts = [
        f"You were assigned to the '{twin_label}' persona because:"
    ]

    for i, feat in enumerate(top_features, 1):
        feature = feat["feature"]
        user_val = feat["user_value"]
        twin_val = feat["twin_value"]
        diff = feat["difference"]

        # Interpret the feature
        if "price_sensitivity" in feature.lower():
            if diff > 0.1:
                explanation_parts.append(f"{i}. You show high price sensitivity ({user_val:.2f})")
            elif diff < -0.1:
                explanation_parts.append(f"{i}. You show low price sensitivity ({user_val:.2f})")
            else:
                explanation_parts.append(f"{i}. Your price sensitivity ({user_val:.2f}) closely matches this persona")

        elif "quality" in feature.lower():
            if diff > 0.1:
                explanation_parts.append(f"{i}. You prioritize quality more than average ({user_val:.2f})")
            elif diff < -0.1:
                explanation_parts.append(f"{i}. You prioritize quality less than typical ({user_val:.2f})")
            else:
                explanation_parts.append(f"{i}. Your quality focus ({user_val:.2f}) aligns with this persona")

        elif "search" in feature.lower() or "browse" in feature.lower():
            if user_val > 0.3:
                explanation_parts.append(f"{i}. You frequently search and browse products ({user_val:.2f})")
            else:
                explanation_parts.append(f"{i}. You prefer quick, focused shopping ({user_val:.2f})")

        elif "compare" in feature.lower():
            if user_val > 0.2:
                explanation_parts.append(f"{i}. You often compare multiple options ({user_val:.2f})")
            else:
                explanation_parts.append(f"{i}. You make quick decisions without much comparison ({user_val:.2f})")

        elif "purchase" in feature.lower():
            if user_val > 0.15:
                explanation_parts.append(f"{i}. You have a high purchase rate ({user_val:.2f})")
            else:
                explanation_parts.append(f"{i}. You browse more than you buy ({user_val:.2f})")

        else:
            # Generic explanation
            if abs(diff) > 0.1:
                direction = "higher" if diff > 0 else "lower"
                explanation_parts.append(
                    f"{i}. Your {feature} ({user_val:.2f}) is {direction} than typical for this persona"
                )
            else:
                explanation_parts.append(f"{i}. Your {feature} ({user_val:.2f}) matches this persona well")

    return "\n".join(explanation_parts)


def compute_all_twin_distances(
    user_embedding: np.ndarray,
    twin_centers: np.ndarray,
    twin_labels: List[str],
    metric: str = "cosine",
) -> List[Dict[str, Any]]:
    """
    Compute distances from user to all twin centers.

    Args:
        user_embedding: (D,) user embedding
        twin_centers: (K, D) array of twin centers
        twin_labels: List of K twin labels
        metric: Distance metric ("cosine", "euclidean", "manhattan")

    Returns:
        List of dicts with twin_id, label, distance, similarity sorted by distance
    """
    distances = []

    for i, (center, label) in enumerate(zip(twin_centers, twin_labels)):
        if metric == "cosine":
            # Cosine similarity (convert to distance)
            similarity = np.dot(user_embedding, center) / (
                np.linalg.norm(user_embedding) * np.linalg.norm(center) + 1e-8
            )
            distance = 1 - similarity
        elif metric == "euclidean":
            distance = np.linalg.norm(user_embedding - center)
            similarity = 1 / (1 + distance)  # Convert to similarity-like score
        elif metric == "manhattan":
            distance = np.sum(np.abs(user_embedding - center))
            similarity = 1 / (1 + distance)
        else:
            raise ValueError(f"Unknown metric: {metric}")

        distances.append({
            "twin_id": f"k{i}",
            "label": label,
            "distance": float(distance),
            "similarity": float(similarity),
        })

    # Sort by distance (ascending = closer first)
    distances.sort(key=lambda x: x["distance"])

    return distances


def explain_assignment(
    user_embedding: np.ndarray,
    assigned_twin_idx: int,
    twin_centers: np.ndarray,
    twin_labels: List[str],
    feature_names: List[str],
    top_k_features: int = 5,
    top_k_alternatives: int = 3,
) -> Dict[str, Any]:
    """
    Complete explainability report for a user's persona assignment.

    Args:
        user_embedding: User's embedding vector
        assigned_twin_idx: Index of assigned twin
        twin_centers: All twin center vectors
        twin_labels: All twin labels
        feature_names: Feature dimension names
        top_k_features: Number of features to highlight
        top_k_alternatives: Number of alternative personas to show

    Returns:
        Complete explanation dict with:
            - primary_twin: Assigned twin info
            - feature_importance: Top features driving assignment
            - natural_language: Human-readable explanation
            - all_distances: Distances to all twins
            - alternatives: Top alternative personas
            - confidence: Confidence score
    """
    assigned_center = twin_centers[assigned_twin_idx]
    assigned_label = twin_labels[assigned_twin_idx]

    # Feature importance for assigned twin
    importances = compute_feature_importance(
        user_embedding,
        assigned_center,
        feature_names,
        method="cosine_decomposition",
    )

    # Natural language explanation
    nl_explanation = generate_natural_language_explanation(
        user_embedding,
        assigned_center,
        assigned_label,
        feature_names,
        importances,
        top_k=top_k_features,
    )

    # Distances to all twins
    all_distances = compute_all_twin_distances(
        user_embedding,
        twin_centers,
        twin_labels,
        metric="cosine",
    )

    # Alternative personas (next closest)
    alternatives = all_distances[1:top_k_alternatives + 1]

    # Confidence score (based on similarity gap)
    primary_similarity = all_distances[0]["similarity"]
    second_similarity = all_distances[1]["similarity"] if len(all_distances) > 1 else 0
    confidence = float(primary_similarity - second_similarity)

    return {
        "primary_twin": {
            "twin_id": f"k{assigned_twin_idx}",
            "label": assigned_label,
            "distance": all_distances[0]["distance"],
            "similarity": all_distances[0]["similarity"],
        },
        "feature_importance": importances[:top_k_features],
        "natural_language": nl_explanation,
        "all_distances": all_distances,
        "alternatives": alternatives,
        "confidence": confidence,
        "metadata": {
            "n_features": len(feature_names),
            "n_twins": len(twin_labels),
        },
    }


def compare_twins(
    twin_center1: np.ndarray,
    twin_center2: np.ndarray,
    twin_label1: str,
    twin_label2: str,
    feature_names: List[str],
    top_k: int = 5,
) -> Dict[str, Any]:
    """
    Compare two twins and explain their differences.

    Args:
        twin_center1: First twin center
        twin_center2: Second twin center
        twin_label1: First twin label
        twin_label2: Second twin label
        feature_names: Feature names
        top_k: Number of top differentiating features

    Returns:
        Comparison analysis
    """
    # Compute differences
    differences = twin_center1 - twin_center2
    abs_differences = np.abs(differences)

    # Get top differentiating features
    top_indices = np.argsort(abs_differences)[-top_k:][::-1]

    top_diffs = []
    for idx in top_indices:
        top_diffs.append({
            "feature": feature_names[idx],
            f"{twin_label1}_value": float(twin_center1[idx]),
            f"{twin_label2}_value": float(twin_center2[idx]),
            "difference": float(differences[idx]),
            "abs_difference": float(abs_differences[idx]),
        })

    # Overall distance
    euclidean_dist = float(np.linalg.norm(twin_center1 - twin_center2))
    cosine_sim = float(
        np.dot(twin_center1, twin_center2) /
        (np.linalg.norm(twin_center1) * np.linalg.norm(twin_center2) + 1e-8)
    )

    return {
        "twin1": twin_label1,
        "twin2": twin_label2,
        "euclidean_distance": euclidean_dist,
        "cosine_similarity": cosine_sim,
        "top_differences": top_diffs,
    }


if __name__ == "__main__":
    # Demo with synthetic data
    np.random.seed(42)

    feature_names = [
        "search_freq", "filter_freq", "sort_freq", "view_freq",
        "compare_freq", "add_to_cart_freq", "purchase_freq", "other_freq",
        "price_sensitivity", "quality_focus", "convenience_priority", "brand_loyalty",
        "age_group", "income_level", "location_type"
    ]

    # Budget-conscious user
    user_emb = np.array([
        0.3, 0.25, 0.15, 0.1,  # behavior: lots of search/filter
        0.1, 0.05, 0.03, 0.02,  # behavior: less purchase
        0.8, 0.3, 0.4, 0.2,    # psychographic: high price sensitivity
        0.3, 0.4, 0.5          # demographic
    ])

    # Twin centers
    budget_twin = np.array([
        0.35, 0.3, 0.15, 0.08,
        0.08, 0.03, 0.01, 0.0,
        0.9, 0.2, 0.3, 0.1,
        0.3, 0.3, 0.5
    ])

    premium_twin = np.array([
        0.15, 0.1, 0.05, 0.2,
        0.15, 0.2, 0.15, 0.0,
        0.2, 0.9, 0.6, 0.8,
        0.5, 0.9, 0.7
    ])

    twin_centers = np.array([budget_twin, premium_twin])
    twin_labels = ["Budget-Conscious", "Premium Quality"]

    # Generate explanation
    explanation = explain_assignment(
        user_emb,
        assigned_twin_idx=0,
        twin_centers=twin_centers,
        twin_labels=twin_labels,
        feature_names=feature_names,
    )

    import json
    print("=" * 60)
    print("PERSONA ASSIGNMENT EXPLANATION")
    print("=" * 60)
    print(json.dumps(explanation, indent=2))

    print("\n" + "=" * 60)
    print("TWIN COMPARISON")
    print("=" * 60)
    comparison = compare_twins(
        budget_twin,
        premium_twin,
        "Budget-Conscious",
        "Premium Quality",
        feature_names,
    )
    print(json.dumps(comparison, indent=2))
