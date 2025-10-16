from __future__ import annotations
from typing import Dict, Any, List, Optional
import numpy as np
import json
from pathlib import Path
from sklearn.metrics import silhouette_score, davies_bouldin_score
from collections import Counter


def gate_silhouette(
    embeddings: np.ndarray,
    labels: np.ndarray,
    min_score: float
) -> Dict[str, Any]:
    """
    Silhouette coefficient gate.

    Measures how well-separated clusters are.
    Range: [-1, 1], higher is better.
    Target: >= 0.45

    Returns:
        result: Dict with score and pass/fail
    """
    # Remove noise points (-1)
    mask = labels != -1
    if mask.sum() < 2:
        return {
            "score": 0.0,
            "threshold": min_score,
            "passed": False,
            "message": "Not enough non-noise points"
        }

    emb_clean = embeddings[mask]
    labels_clean = labels[mask]

    # Need at least 2 clusters
    n_clusters = len(set(labels_clean))
    if n_clusters < 2:
        return {
            "score": 0.0,
            "threshold": min_score,
            "passed": False,
            "message": f"Only {n_clusters} cluster(s) found"
        }

    score = silhouette_score(emb_clean, labels_clean, metric="cosine")
    passed = score >= min_score

    return {
        "score": float(score),
        "threshold": min_score,
        "passed": passed,
        "message": f"Silhouette = {score:.4f} (threshold: {min_score})"
    }


def gate_davies_bouldin(
    embeddings: np.ndarray,
    labels: np.ndarray,
    max_score: float
) -> Dict[str, Any]:
    """
    Davies-Bouldin index gate.

    Measures cluster separation vs compactness.
    Range: [0, ∞), lower is better.
    Target: <= 0.8

    Returns:
        result: Dict with score and pass/fail
    """
    # Remove noise points
    mask = labels != -1
    if mask.sum() < 2:
        return {
            "score": float("inf"),
            "threshold": max_score,
            "passed": False,
            "message": "Not enough non-noise points"
        }

    emb_clean = embeddings[mask]
    labels_clean = labels[mask]

    # Need at least 2 clusters
    n_clusters = len(set(labels_clean))
    if n_clusters < 2:
        return {
            "score": float("inf"),
            "threshold": max_score,
            "passed": False,
            "message": f"Only {n_clusters} cluster(s) found"
        }

    score = davies_bouldin_score(emb_clean, labels_clean)
    passed = score <= max_score

    return {
        "score": float(score),
        "threshold": max_score,
        "passed": passed,
        "message": f"Davies-Bouldin = {score:.4f} (threshold: <= {max_score})"
    }


def compute_distinct_n(text: str, n: int) -> set:
    """
    Compute distinct n-grams from text.

    Args:
        text: Input text
        n: N-gram size

    Returns:
        Set of n-grams
    """
    tokens = text.lower().split()
    ngrams = set()
    for i in range(len(tokens) - n + 1):
        ngram = " ".join(tokens[i:i+n])
        ngrams.add(ngram)
    return ngrams


def gate_distinct_n(
    cluster_responses: Dict[int, List[str]],
    n: int,
    min_margin: float
) -> Dict[str, Any]:
    """
    Distinct-n gate.

    Measures uniqueness of cluster responses.
    For each cluster, compute % of unique n-grams compared to nearest neighbor cluster.
    Margin = (cluster_unique - neighbor_unique) / total_unique

    Target: margin >= 0.10 (10% more unique than nearest neighbor)

    Args:
        cluster_responses: Dict mapping cluster_id -> list of response strings
        n: N-gram size (e.g., 3 for trigrams)
        min_margin: Minimum margin required

    Returns:
        result: Dict with margins and pass/fail
    """
    cluster_ids = list(cluster_responses.keys())
    if len(cluster_ids) < 2:
        return {
            "margins": {},
            "mean_margin": 0.0,
            "threshold": min_margin,
            "passed": False,
            "message": "Need at least 2 clusters"
        }

    # Compute distinct n-grams for each cluster
    cluster_ngrams = {}
    for cid, responses in cluster_responses.items():
        all_ngrams = set()
        for resp in responses:
            all_ngrams |= compute_distinct_n(resp, n)
        cluster_ngrams[cid] = all_ngrams

    # For each cluster, find margin vs nearest neighbor
    margins = {}
    for cid in cluster_ids:
        cid_ngrams = cluster_ngrams[cid]

        # Find nearest neighbor (highest ngram overlap)
        max_overlap = 0
        nearest_neighbor = None
        for other_cid in cluster_ids:
            if other_cid == cid:
                continue
            overlap = len(cid_ngrams & cluster_ngrams[other_cid])
            if overlap > max_overlap:
                max_overlap = overlap
                nearest_neighbor = other_cid

        if nearest_neighbor is None:
            margins[cid] = 1.0  # Only cluster, perfect margin
            continue

        # Compute margin
        nn_ngrams = cluster_ngrams[nearest_neighbor]
        union = cid_ngrams | nn_ngrams
        cid_unique = len(cid_ngrams - nn_ngrams)
        nn_unique = len(nn_ngrams - cid_ngrams)
        total_unique = len(union)

        if total_unique == 0:
            margin = 0.0
        else:
            margin = (cid_unique - nn_unique) / total_unique

        margins[cid] = float(margin)

    # Check if all margins meet threshold
    mean_margin = float(np.mean(list(margins.values())))
    passed = all(m >= min_margin for m in margins.values())

    return {
        "margins": margins,
        "mean_margin": mean_margin,
        "threshold": min_margin,
        "passed": passed,
        "message": f"Mean Distinct-{n} margin = {mean_margin:.4f} (threshold: >= {min_margin})"
    }


def gate_psychometric_alignment(
    cluster_ocean_scores: Dict[int, Dict[str, float]],
    persona_ocean_scores: Dict[str, Dict[str, float]],
    cluster_to_persona_map: Dict[int, str],
    traits: List[str],
    min_aligned_traits: int
) -> Dict[str, Any]:
    """
    Psychometric alignment gate.

    Check if OCEAN score deltas match expected direction.
    For each cluster-persona pair, check if traits align.

    Args:
        cluster_ocean_scores: Dict mapping cluster_id -> OCEAN scores
        persona_ocean_scores: Dict mapping persona_id -> OCEAN scores
        cluster_to_persona_map: Dict mapping cluster_id -> persona_id
        traits: List of traits to check (e.g., ["O", "C", "E", "A", "N"])
        min_aligned_traits: Minimum number of aligned traits required

    Returns:
        result: Dict with alignment counts and pass/fail
    """
    alignments = {}

    for cid, pid in cluster_to_persona_map.items():
        if cid not in cluster_ocean_scores or pid not in persona_ocean_scores:
            continue

        cluster_scores = cluster_ocean_scores[cid]
        persona_scores = persona_ocean_scores[pid]

        # Count aligned traits
        aligned_count = 0
        for trait in traits:
            if trait in cluster_scores and trait in persona_scores:
                # Check if direction matches (both high or both low)
                # High: >= 0.6, Low: <= 0.4
                c_val = cluster_scores[trait]
                p_val = persona_scores[trait]

                if (c_val >= 0.6 and p_val >= 0.6) or (c_val <= 0.4 and p_val <= 0.4):
                    aligned_count += 1

        alignments[cid] = {
            "persona": pid,
            "aligned": aligned_count,
            "total": len(traits),
            "passed": aligned_count >= min_aligned_traits
        }

    # Overall pass: all clusters pass
    passed = all(a["passed"] for a in alignments.values())
    mean_aligned = np.mean([a["aligned"] for a in alignments.values()]) if alignments else 0.0

    return {
        "alignments": alignments,
        "mean_aligned": float(mean_aligned),
        "threshold": min_aligned_traits,
        "passed": passed,
        "message": f"Mean aligned traits = {mean_aligned:.1f}/{len(traits)} (threshold: >= {min_aligned_traits})"
    }


def gate_behavior_tasks(
    cluster_predictions: Dict[int, List[Any]],
    ground_truth: List[Any],
    min_accuracy: float
) -> Dict[str, Any]:
    """
    Behavior task accuracy gate.

    Check if clusters predict ground truth on validated behavior tasks from Twin-2K-500.

    Args:
        cluster_predictions: Dict mapping cluster_id -> list of predictions
        ground_truth: List of ground truth labels
        min_accuracy: Minimum accuracy required

    Returns:
        result: Dict with accuracy and pass/fail
    """
    accuracies = {}

    for cid, preds in cluster_predictions.items():
        if len(preds) != len(ground_truth):
            accuracies[cid] = 0.0
            continue

        correct = sum(p == gt for p, gt in zip(preds, ground_truth))
        acc = correct / len(ground_truth)
        accuracies[cid] = float(acc)

    mean_acc = float(np.mean(list(accuracies.values()))) if accuracies else 0.0
    passed = mean_acc >= min_accuracy

    return {
        "accuracies": accuracies,
        "mean_accuracy": mean_acc,
        "threshold": min_accuracy,
        "passed": passed,
        "message": f"Mean behavior task accuracy = {mean_acc:.4f} (threshold: >= {min_accuracy})"
    }


def run_all_gates(
    embeddings: np.ndarray,
    labels: np.ndarray,
    gate_config: Dict[str, Any],
    cluster_responses: Optional[Dict[int, List[str]]] = None,
    cluster_ocean_scores: Optional[Dict[int, Dict[str, float]]] = None,
    persona_ocean_scores: Optional[Dict[str, Dict[str, float]]] = None,
    cluster_to_persona_map: Optional[Dict[int, str]] = None,
    cluster_predictions: Optional[Dict[int, List[Any]]] = None,
    ground_truth: Optional[List[Any]] = None
) -> Dict[str, Any]:
    """
    Run all enabled quality gates.

    Returns:
        results: Dict with results for each gate and overall pass/fail
    """
    results = {}

    # Silhouette
    if gate_config.get("silhouette", {}).get("enabled", False):
        results["silhouette"] = gate_silhouette(
            embeddings=embeddings,
            labels=labels,
            min_score=gate_config["silhouette"]["min_score"]
        )

    # Davies-Bouldin
    if gate_config.get("davies_bouldin", {}).get("enabled", False):
        results["davies_bouldin"] = gate_davies_bouldin(
            embeddings=embeddings,
            labels=labels,
            max_score=gate_config["davies_bouldin"]["max_score"]
        )

    # Distinct-n
    if gate_config.get("distinct_n", {}).get("enabled", False) and cluster_responses is not None:
        results["distinct_n"] = gate_distinct_n(
            cluster_responses=cluster_responses,
            n=gate_config["distinct_n"]["n"],
            min_margin=gate_config["distinct_n"]["min_margin"]
        )

    # Psychometric alignment
    if gate_config.get("psychometric", {}).get("enabled", False):
        if cluster_ocean_scores and persona_ocean_scores and cluster_to_persona_map:
            results["psychometric"] = gate_psychometric_alignment(
                cluster_ocean_scores=cluster_ocean_scores,
                persona_ocean_scores=persona_ocean_scores,
                cluster_to_persona_map=cluster_to_persona_map,
                traits=gate_config["psychometric"]["traits"],
                min_aligned_traits=gate_config["psychometric"]["min_aligned_traits"]
            )

    # Behavior tasks
    if gate_config.get("behavior_tasks", {}).get("enabled", False):
        if cluster_predictions and ground_truth:
            results["behavior_tasks"] = gate_behavior_tasks(
                cluster_predictions=cluster_predictions,
                ground_truth=ground_truth,
                min_accuracy=gate_config["behavior_tasks"]["min_accuracy"]
            )

    # Overall pass/fail
    all_passed = all(r["passed"] for r in results.values())

    return {
        "gates": results,
        "all_passed": all_passed,
        "n_gates": len(results),
        "n_passed": sum(r["passed"] for r in results.values())
    }
