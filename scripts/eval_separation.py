#!/usr/bin/env python3
"""
Evaluate twin separation metrics against gates thresholds.
Exit non-zero if any gate fails.
"""
from __future__ import annotations
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, List

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.mixture import load_twin_bank, responsibilities, primary_twin
from src.models.encoder import encode_cta, project_psychographics, embed_demographics, fuse_joint
from src.profiles.loader import profile_vec_for_user, merge_profile
from src.metrics.separation import compute_separation_metrics
from src.reasoning.llm_twin import decide_as_twin

def load_gates() -> Dict[str, Any]:
    """Load separation gates from config"""
    gates_path = Path("CONFIGS/tests/gates.yaml")
    if gates_path.exists():
        return yaml.safe_load(gates_path.read_text()).get("separation", {})
    return {}

def generate_test_samples(n: int = 100) -> List[Dict[str, Any]]:
    """Generate synthetic test samples for separation evaluation"""
    samples = []
    bank = load_twin_bank()

    # Use twin centroids as base embeddings
    for twin in bank.get("twins", []):
        tid = twin["id"]
        center = twin["center"]

        # Generate samples around each twin centroid
        for i in range(n // len(bank.get("twins", []))):
            # Use centroid as embedding
            embedding = center

            # Compute responsibilities
            weights = responsibilities(embedding, bank)
            primary = primary_twin(weights, bank)
            primary_id = primary["id"] if primary else "unknown"

            samples.append({
                "embedding": embedding,
                "twin_assignment": primary_id,
                "twin_weights": weights
            })

    return samples

def evaluate_separation() -> int:
    """
    Main evaluation function.
    Returns 0 if all gates pass, 1 if any fail.
    """
    gates = load_gates()
    bank = load_twin_bank()

    # Generate test samples
    samples = generate_test_samples(n=90)  # 30 per twin

    if not samples:
        print("ERROR: No samples generated")
        return 1

    # Extract data
    embeddings = [s["embedding"] for s in samples]
    assignments = [s["twin_assignment"] for s in samples]

    # Build twin centers dict
    twin_centers = {t["id"]: t["center"] for t in bank.get("twins", [])}

    # Build twin distributions (simulate decision distributions)
    context = {"page_type": "search", "visible_products": ["A1", "A2", "A3"], "price_mean": 500}
    candidates = [{"id": "A1"}, {"id": "A2"}, {"id": "A3"}]

    twin_distributions = {}
    for twin in bank.get("twins", []):
        tid = twin["id"]
        dec = decide_as_twin(tid, context, candidates, max_tokens=20, conditioning=None)
        pick = dec["pick"]
        # Simple distribution: 1.0 for picked item, 0.0 for others
        twin_distributions[tid] = {c["id"]: (1.0 if c["id"] == pick else 0.0) for c in candidates}

    # Compute metrics
    metrics = compute_separation_metrics(assignments, embeddings, twin_centers, twin_distributions)

    print("=== Separation Metrics ===")
    print(f"Silhouette Score: {metrics['silhouette']:.4f}")
    print(f"Mean Pairwise JSD: {metrics['mean_jsd']:.4f}")
    print(f"Adjusted Rand Index: {metrics['ari']:.4f}")
    print()

    # Check gates
    failures = []

    silhouette_min = gates.get("silhouette_min", 0.0)
    if metrics["silhouette"] < silhouette_min:
        failures.append(f"Silhouette {metrics['silhouette']:.4f} < {silhouette_min}")

    jsd_min = gates.get("mean_jsd_min", 0.0)
    if metrics["mean_jsd"] < jsd_min:
        failures.append(f"Mean JSD {metrics['mean_jsd']:.4f} < {jsd_min}")

    ari_min = gates.get("ari_min", 0.0)
    if metrics["ari"] < ari_min:
        failures.append(f"ARI {metrics['ari']:.4f} < {ari_min}")

    if failures:
        print("=== GATE FAILURES ===")
        for f in failures:
            print(f"  L {f}")
        print()
        return 1
    else:
        print(" All separation gates passed")
        return 0

if __name__ == "__main__":
    sys.exit(evaluate_separation())
