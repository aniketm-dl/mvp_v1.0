# Discovery Pipeline - Phase 3E.3

Replace 15-D fused vector with 256-D encoder embeddings. Build discovery and clustering with stability checks.

## Overview

The discovery pipeline:
1. Exports session embeddings from trained encoder
2. Builds k-NN graph with cosine similarity
3. Runs HDBSCAN (or Leiden fallback) clustering
4. Checks stability via bootstrap sampling
5. Trains persona classifier to detect confusion
6. Runs quality gates (silhouette, Davies-Bouldin, Distinct-n, psychometric, behavior)
7. Generates comprehensive report with recommendations

## Architecture

```
DATA/OPeRA/processed → Encoder → 256-D embeddings
                                       ↓
                                  k-NN Graph
                                       ↓
                            HDBSCAN / Leiden Clustering
                                       ↓
                              Bootstrap Stability
                                       ↓
                              Quality Gates
                                       ↓
                                    Report
                                       ↓
                          Router Integration (feature flag)
```

## Pipeline Steps

### 1. Export Embeddings

```bash
python scripts/export_embeddings.py \
  --ckpt artifacts/encoder/best.ckpt \
  --data DATA/OPeRA/processed \
  --config CONFIGS/encoder.yaml \
  --out artifacts/encoder/embeddings.parquet
```

**Output:** `artifacts/encoder/embeddings.parquet` with columns:
- `split`: train/val/test
- `user_id`, `session_id`, `persona_id`: metadata
- `emb_0` ... `emb_255`: 256-D embedding

### 2. Build k-NN Graph

```bash
python discovery/build_graph.py \
  --emb artifacts/encoder/embeddings.parquet \
  --config CONFIGS/discovery.yaml \
  --out artifacts/discovery/graph.pkl
```

**Config:**
- `k=15`: Number of nearest neighbors
- `metric=cosine`: Similarity metric
- `min_similarity=0.35`: Drop edges below threshold

**Output:** `artifacts/discovery/graph.pkl` with:
- `indices`, `distances`, `similarities`: k-NN results
- `adjacency`: Symmetric adjacency matrix
- `distance_matrix`: For HDBSCAN (precomputed)

### 3. Clustering

```bash
python discovery/cluster_hdbscan.py \
  --graph artifacts/discovery/graph.pkl \
  --config CONFIGS/discovery.yaml \
  --out artifacts/discovery/labels.pkl
```

**Algorithms:**
- **HDBSCAN** (primary): Density-based, finds varying-density clusters
- **Leiden** (fallback): Graph-based, used if HDBSCAN fragments

**Fallback triggers:**
- `n_clusters > 30`: Too fragmented
- `noise_frac > 0.25`: Too much noise

**Output:** `artifacts/discovery/labels.pkl` with:
- `labels`: (N,) cluster assignments (-1 = noise)
- `stats`: n_clusters, noise_frac, cluster_sizes, algorithm

### 4. Bootstrap Stability

```bash
python discovery/stability_bootstrap.py \
  --emb artifacts/encoder/embeddings.parquet \
  --graph artifacts/discovery/graph.pkl \
  --labels artifacts/discovery/labels.pkl \
  --config CONFIGS/discovery.yaml \
  --out artifacts/discovery/stability.pkl
```

**Method:**
- Run 20 bootstrap iterations
- Sample 80% of data each time
- Compute ARI vs full clustering
- Keep stable cores (ARI >= 0.75)

**Output:** `artifacts/discovery/stability.pkl` with:
- `stability_scores`: (N,) per-point stability
- `labels_stable`: Cluster labels with unstable points marked as noise
- `stats`: mean/median stability, per-cluster cores

### 5. Persona Classifier

```bash
python discovery/persona_classifier.py \
  --emb artifacts/encoder/embeddings.parquet \
  --config CONFIGS/discovery.yaml \
  --out artifacts/discovery/persona_classifier.pkl
```

**Purpose:** Detect which personas are confused (potential merge/split)

**Output:** `artifacts/discovery/persona_classifier.pkl` with:
- `model`: Trained logistic regression classifier
- `results`:
  - `test_accuracy`: Must be >= 0.85
  - `confusion_matrix`: (18, 18) normalized confusion
  - `confusion_analysis`:
    - `high_confusion_pairs`: Persona pairs with >10% confusion
    - `low_recall_personas`: Personas with <70% recall

### 6. Generate Report

```bash
python discovery/report.py \
  --emb artifacts/encoder/embeddings.parquet \
  --graph artifacts/discovery/graph.pkl \
  --labels artifacts/discovery/labels.pkl \
  --stability artifacts/discovery/stability.pkl \
  --classifier artifacts/discovery/persona_classifier.pkl \
  --config CONFIGS/discovery.yaml \
  --out artifacts/discovery/report.md
```

**Report Sections:**
1. Executive Summary
2. Clustering Details
3. Stability Analysis
4. Persona Classifier Results
5. Quality Gates
6. Recommendations
7. Next Steps

## Quality Gates

All gates must pass before promoting clusters to production.

### 1. Silhouette Coefficient
- **Target:** >= 0.45
- **Measures:** Cluster separation
- **Range:** [-1, 1], higher is better

### 2. Davies-Bouldin Index
- **Target:** <= 0.8
- **Measures:** Cluster compactness vs separation
- **Range:** [0, ∞), lower is better

### 3. Distinct-n
- **Target:** Margin >= 0.10
- **Measures:** Uniqueness of cluster responses
- **Method:** Compare trigram sets between cluster and nearest neighbor

### 4. Psychometric Alignment
- **Target:** >= 4/5 traits aligned
- **Measures:** OCEAN score deltas match persona definitions
- **Method:** Check if cluster OCEAN scores match assigned persona

### 5. Behavior Tasks
- **Target:** >= 75% accuracy
- **Measures:** Predictions on validated tasks from Twin-2K-500
- **Method:** Small set of ground-truth behavior probes

## Router Integration

### Feature Flag

In `CONFIGS/discovery.yaml`:

```yaml
router:
  use_encoder_embeddings: false  # Start disabled
```

### Switch to New Embeddings

1. Verify all gates pass
2. Flip flag to `true`
3. Restart router service
4. Monitor latency and twin assignments

### Rollback

If issues arise:
1. Flip flag back to `false`
2. Restart router service
3. Reverts to legacy 15-D embeddings from `twin_bank.json`

### Router API

```python
from services.router.mix_of_twins import MixtureOfTwins

router = MixtureOfTwins(config_path="CONFIGS/discovery.yaml")

# Route session
session_data = {"embedding": [0.1, 0.2, ..., 0.15]}  # 15-D or 256-D
result = router.route(session_data)

# Result:
# {
#   "responsibilities": {"twin_a": 0.5, "twin_b": 0.3, ...},
#   "primary": {"id": "twin_a", "label": "...", "weight": 0.5},
#   "embedding_dim": 256,
#   "backend": "encoder"
# }
```

## Configuration

See `CONFIGS/discovery.yaml` for all parameters:

```yaml
embeddings:
  source: artifacts/encoder/embeddings.parquet
  dim: 256
  session_agg: mean

graph:
  k: 15
  metric: cosine
  min_similarity: 0.35

clustering:
  algorithm: hdbscan
  hdbscan:
    min_cluster_size: 10
    min_samples: 5

stability:
  n_bootstrap: 20
  sample_frac: 0.8
  min_stability: 0.75

gates:
  silhouette:
    min_score: 0.45
  davies_bouldin:
    max_score: 0.8

router:
  use_encoder_embeddings: false
  temperature: 0.5
```

## Dependencies

Install required packages:

```bash
pip install hdbscan igraph leidenalg scikit-learn pandas pyarrow
```

Or with uv:

```bash
uv add hdbscan igraph leidenalg scikit-learn pandas pyarrow
```

## Testing

Run all tests:

```bash
pytest discovery/__tests__/test_discovery_pipeline.py -v
```

## Failure Modes and Fixes

### Fragmented Clusters
**Symptom:** n_clusters > 30 or noise_frac > 0.25
**Fix:**
- Increase `min_cluster_size` or `min_samples` in HDBSCAN
- Use Leiden fallback with lower resolution
- Check embedding quality (retrain encoder)

### Low Silhouette
**Symptom:** silhouette < 0.45
**Fix:**
- Increase persona alignment loss weight in encoder training
- Refine persona definitions for better separation
- Increase embedding dim to 384

### Persona Confusion
**Symptom:** test_accuracy < 0.85 or many high_confusion_pairs
**Fix:**
- Merge confused personas (e.g., bargain_hunter + budget_optimizer)
- Add more discriminative features to persona view
- Retrain encoder with higher InfoNCE temperature

### Low Stability
**Symptom:** stable_frac < 0.75
**Fix:**
- Increase bootstrap iterations (n_bootstrap = 50)
- Use stricter min_stability threshold
- Filter out unstable clusters before production

## Nightly Pipeline

Run discovery nightly to track cluster drift:

```bash
#!/bin/bash
# nightly_discovery.sh

DATE=$(date +%Y%m%d)
OUT_DIR="artifacts/discovery/${DATE}"

python discovery/build_graph.py --out ${OUT_DIR}/graph.pkl
python discovery/cluster_hdbscan.py --graph ${OUT_DIR}/graph.pkl --out ${OUT_DIR}/labels.pkl
python discovery/stability_bootstrap.py --labels ${OUT_DIR}/labels.pkl --out ${OUT_DIR}/stability.pkl
python discovery/persona_classifier.py --out ${OUT_DIR}/classifier.pkl
python discovery/report.py --out ${OUT_DIR}/report.md

# Alert if gates fail
if grep -q "✗" ${OUT_DIR}/report.md; then
  echo "Quality gates failed! Check ${OUT_DIR}/report.md"
  exit 1
fi
```

## References

- **HDBSCAN:** McInnes et al., 2017 - Density-based clustering
- **Leiden:** Traag et al., 2019 - Graph community detection
- **InfoNCE:** Oord et al., 2018 - Contrastive alignment loss
- **OPeRA:** Observation-Persona-Rationale-Action dataset
