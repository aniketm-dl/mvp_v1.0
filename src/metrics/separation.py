from __future__ import annotations
import math
from typing import Dict, Any, List, Tuple
from collections import defaultdict
import numpy as np

def silhouette_score(twin_assignments: List[str], embeddings: List[List[float]], twin_centers: Dict[str, List[float]]) -> float:
    """
    Compute silhouette score for twin assignments.

    Args:
        twin_assignments: List of twin IDs for each sample
        embeddings: List of embedding vectors
        twin_centers: Dict mapping twin_id -> centroid vector

    Returns:
        Silhouette score in [-1, 1], higher is better
    """
    if not embeddings or len(set(twin_assignments)) < 2:
        return 0.0

    n = len(embeddings)
    clusters = defaultdict(list)
    for i, tid in enumerate(twin_assignments):
        clusters[tid].append(i)

    def euclidean(v1, v2):
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))

    scores = []
    for i in range(n):
        my_cluster = twin_assignments[i]
        cluster_indices = clusters[my_cluster]

        # a(i): mean distance to points in same cluster
        if len(cluster_indices) > 1:
            a_i = sum(euclidean(embeddings[i], embeddings[j]) for j in cluster_indices if j != i) / (len(cluster_indices) - 1)
        else:
            a_i = 0.0

        # b(i): mean distance to nearest other cluster
        other_clusters = [tid for tid in clusters.keys() if tid != my_cluster]
        if not other_clusters:
            b_i = 0.0
        else:
            b_vals = []
            for tid in other_clusters:
                indices = clusters[tid]
                mean_dist = sum(euclidean(embeddings[i], embeddings[j]) for j in indices) / len(indices)
                b_vals.append(mean_dist)
            b_i = min(b_vals)

        # s(i) = (b - a) / max(a, b)
        if max(a_i, b_i) > 0:
            s_i = (b_i - a_i) / max(a_i, b_i)
        else:
            s_i = 0.0
        scores.append(s_i)

    return sum(scores) / len(scores) if scores else 0.0

def jensen_shannon_divergence(p: List[float], q: List[float]) -> float:
    """Compute JSD between two probability distributions"""
    def kl_div(p_arr, q_arr):
        kl = 0.0
        for pi, qi in zip(p_arr, q_arr):
            if pi > 0 and qi > 0:
                kl += pi * math.log(pi / qi)
        return kl

    # Ensure same length
    n = max(len(p), len(q))
    p_ext = list(p) + [0.0] * (n - len(p))
    q_ext = list(q) + [0.0] * (n - len(q))

    # Normalize
    p_sum = sum(p_ext) or 1.0
    q_sum = sum(q_ext) or 1.0
    p_norm = [x / p_sum for x in p_ext]
    q_norm = [x / q_sum for x in q_ext]

    # M = (P + Q) / 2
    m = [(pi + qi) / 2.0 for pi, qi in zip(p_norm, q_norm)]

    # JSD = (KL(P||M) + KL(Q||M)) / 2
    jsd = (kl_div(p_norm, m) + kl_div(q_norm, m)) / 2.0
    return jsd

def mean_pairwise_jsd(twin_distributions: Dict[str, Dict[str, float]]) -> float:
    """
    Compute mean pairwise JSD between twin probability distributions.

    Args:
        twin_distributions: {twin_id: {candidate_id: prob}}

    Returns:
        Mean JSD across all twin pairs
    """
    twins = sorted(twin_distributions.keys())
    if len(twins) < 2:
        return 0.0

    # Get all candidate IDs
    all_cids = set()
    for probs in twin_distributions.values():
        all_cids.update(probs.keys())
    all_cids = sorted(all_cids)

    # Build prob vectors
    twin_vecs = {}
    for tid in twins:
        probs = twin_distributions[tid]
        vec = [probs.get(cid, 0.0) for cid in all_cids]
        twin_vecs[tid] = vec

    # Pairwise JSD
    jsds = []
    for i in range(len(twins)):
        for j in range(i + 1, len(twins)):
            jsd = jensen_shannon_divergence(twin_vecs[twins[i]], twin_vecs[twins[j]])
            jsds.append(jsd)

    return sum(jsds) / len(jsds) if jsds else 0.0

def adjusted_rand_index(true_labels: List[str], pred_labels: List[str]) -> float:
    """
    Compute Adjusted Rand Index.

    Args:
        true_labels: Ground truth cluster labels
        pred_labels: Predicted cluster labels

    Returns:
        ARI in [-1, 1], 1 is perfect, 0 is random
    """
    if len(true_labels) != len(pred_labels) or not true_labels:
        return 0.0

    n = len(true_labels)

    # Build contingency table
    true_clusters = defaultdict(set)
    pred_clusters = defaultdict(set)
    for i in range(n):
        true_clusters[true_labels[i]].add(i)
        pred_clusters[pred_labels[i]].add(i)

    # Compute a, b, c, d counts
    def comb2(n):
        return n * (n - 1) // 2

    # TP: pairs in same cluster in both
    tp = 0
    for t_cluster in true_clusters.values():
        for p_cluster in pred_clusters.values():
            intersection = t_cluster & p_cluster
            if len(intersection) >= 2:
                tp += comb2(len(intersection))

    # Sum of combinations for true and pred
    sum_comb_true = sum(comb2(len(c)) for c in true_clusters.values())
    sum_comb_pred = sum(comb2(len(c)) for c in pred_clusters.values())

    # Expected index
    total_comb = comb2(n)
    if total_comb == 0:
        return 0.0
    expected_index = sum_comb_true * sum_comb_pred / total_comb

    # Max index
    max_index = (sum_comb_true + sum_comb_pred) / 2.0

    # ARI
    if max_index == expected_index:
        return 1.0 if tp == max_index else 0.0

    ari = (tp - expected_index) / (max_index - expected_index)
    return ari

def compute_separation_metrics(
    twin_assignments: List[str],
    embeddings: List[List[float]],
    twin_centers: Dict[str, List[float]],
    twin_distributions: Dict[str, Dict[str, float]]
) -> Dict[str, float]:
    """
    Compute all separation metrics.

    Returns:
        {
            "silhouette": float,
            "mean_jsd": float,
            "ari": float  # only if ground truth available
        }
    """
    metrics = {}

    # Silhouette
    metrics["silhouette"] = silhouette_score(twin_assignments, embeddings, twin_centers)

    # Mean pairwise JSD
    metrics["mean_jsd"] = mean_pairwise_jsd(twin_distributions)

    # ARI requires ground truth - for now we use twin_assignments as both true and pred
    # In real scenario, you'd pass separate ground_truth parameter
    metrics["ari"] = adjusted_rand_index(twin_assignments, twin_assignments)

    return metrics
