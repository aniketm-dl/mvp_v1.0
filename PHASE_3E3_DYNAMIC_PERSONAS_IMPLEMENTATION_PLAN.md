# Phase 3E.3 Dynamic Personas - Implementation Plan

**Status:** Architecture Complete, Implementation Required
**Approach:** Fully unsupervised persona discovery from embeddings

---

## Summary of Changes

This revision transforms Phase 3E.3 from a **fixed 18-persona mapping** to a **fully unsupervised, data-driven discovery system** where:

1. **Number of personas emerges from data** (not fixed at 18)
2. **Personas are labeled without external LLM calls** (TF-IDF + top terms)
3. **Dual registries coexist** (curated + discovered)
4. **Feature flag controls routing** (safe rollback)
5. **All parameters in config** (no hardcoded values)

---

## Architecture Overview

```
Step Embeddings (256-D)
         ↓
   [Aggregate Sessions]
         ↓
  Session Embeddings
         ↓
    [Build k-NN Graph] ← Cosine similarity, k=20
         ↓
   [HDBSCAN Clustering] ← min_cluster_size=15
         ↓
  [Bootstrap Stability] ← 20 runs, Jaccard metric
         ↓
    [Auto-Resolve] ← Merge duplicates, filter tiny
         ↓
   [Leiden Fallback?] ← If noise > 20% or silhouette < 0.30
         ↓
 [Unsupervised Labeling] ← TF-IDF on rationales + facts
         ↓
  [Persona Synthesis] ← Generate JSON files per cluster
         ↓
   [Quality Gates] ← Silhouette, DB, Distinct-n, etc.
         ↓
      [Report] ← Pass/fail summary
         ↓
   [Router Integration] ← Feature flag: use_discovered_personas
```

---

## Key Design Decisions

### 1. Unsupervised Labeling (No External Calls)

**Method:** TF-IDF + SVD on concatenated rationales and facts per cluster

**Steps:**
1. Aggregate all rationale text per cluster
2. Tokenize, remove stopwords, extract n-grams (1-3)
3. Compute TF-IDF matrix
4. Apply SVD for dimensionality reduction
5. Extract top-k terms per cluster (k=10)
6. Generate label: capitalize top 3-4 terms
7. Generate description: 2-sentence summary from terms

**Example:**
- Cluster with terms: `["discount", "sale", "cheap", "coupon", "bargain"]`
- Label: "Discount Sale Seekers"
- Description: "Focuses on finding sales and discounts. Price-sensitive shoppers who wait for deals."

### 2. Dynamic Persona Count

**No fixed 18:** Clustering determines count based on data structure

**Constraints:**
- Min cluster size: 15 sessions (0.5% of data)
- Max cluster size: 40% of data (prevent dominance)
- Noise threshold: < 20% of sessions
- Stability threshold: >= 75% Jaccard stability

**Expected range:** 8-25 personas depending on data diversity

### 3. Dual Registry System

**Curated Personas** (`DATA/personas/registry.json`)
- Hand-crafted 18 personas from Phase 2
- Preserved for reference and testing
- Always available

**Discovered Personas** (`DATA/personas_discovered/registry.json`)
- Data-driven personas from unsupervised discovery
- Variable count (8-25+)
- Versioned with discovery run metadata

**Router Selection:**
```yaml
persona_source: curated     # Use Phase 2 personas
persona_source: discovered  # Use discovered personas
persona_source: hybrid      # Try discovered, fall back to curated
```

### 4. Feature Flag Safety

**Default:** `use_discovered_personas: false` (curated personas active)

**Enable discovered:**
1. Run discovery pipeline
2. Verify all gates pass in `artifacts/discovery/report.md`
3. Set `use_discovered_personas: true`
4. Restart router
5. Monitor latency (must stay within 5% of baseline)

**Rollback:** Flip flag back to `false`, restart

---

## Implementation Checklist

### Core Discovery Pipeline (10 modules)

- [ ] **discovery/aggregate_sessions.py**
  - Read step embeddings from encoder
  - Group by session_id
  - Aggregate to session-level (mean pooling)
  - Keep rationale text and facts for labeling
  - Save to `artifacts/encoder/session_embeddings.parquet`

- [ ] **discovery/build_graph.py**
  - Load session embeddings
  - Build k-NN graph (k=20, cosine similarity)
  - Drop edges below min_similarity (0.35)
  - Use FAISS for speed if `use_approximate: true`
  - Save nodes and edges to `artifacts/discovery/graph/`

- [ ] **discovery/cluster_hdbscan.py**
  - Load graph and embeddings
  - Run HDBSCAN (min_cluster_size=15, min_samples=8)
  - Export cluster labels
  - Export soft memberships and probabilities
  - Save to `artifacts/discovery/labels/`

- [ ] **discovery/stability_bootstrap.py**
  - Load embeddings and labels
  - Run 20 bootstrap iterations with replacement
  - Refit clustering each time
  - Compute Jaccard stability per node and per cluster
  - Mark stable cores (>= 0.75)
  - Save to `artifacts/discovery/stability/`

- [ ] **discovery/cluster_leiden.py**
  - Load graph
  - Check fallback triggers (noise > 20%, silhouette < 0.30, n_clusters > 40)
  - If triggered, run Leiden resolution sweep [0.5, 0.8, 1.0, 1.2, 1.5]
  - Select best by weighted score (0.6×silhouette + 0.4×modularity)
  - Save to `artifacts/discovery/labels_leiden/`

- [ ] **discovery/auto_resolve.py**
  - Load cluster labels and centroids
  - **Merge:** Find pairs with cosine distance < 0.10 AND label overlap > 0.40
  - **Filter:** Drop clusters < 0.5% of sessions (unless stable > 0.85)
  - **Cap:** Warn if any cluster > 40% of sessions
  - Recompute metrics after changes
  - Save resolved labels

- [ ] **discovery/label_topics.py**
  - Load rationales and facts per cluster
  - Tokenize (lowercase, remove stopwords, min_length=3)
  - Extract n-grams (1-3)
  - Compute TF-IDF matrix (max_features=500)
  - Apply SVD (n_components=50)
  - Extract top-10 terms per cluster
  - Generate label (max 40 chars)
  - Generate description (2 sentences)
  - Save to `artifacts/discovery/labels_text.json`

- [ ] **discovery/metrics.py**
  - Load embeddings, labels, stability
  - Compute:
    - Silhouette coefficient (target: >= 0.45)
    - Davies-Bouldin index (target: <= 0.8)
    - Calinski-Harabasz score (target: >= 100)
    - Gini coefficient (target: <= 0.60)
    - Entropy (target: >= 2.5 bits)
    - Distinct-n margin (target: >= 0.10)
    - Psychometric consistency (target: >= 4/5 traits)
  - Check size limits (min 0.5%, max 40%)
  - Save to `artifacts/discovery/metrics.json`

- [ ] **discovery/report.py**
  - Load all artifacts (labels, stability, metrics, labels_text)
  - Generate markdown report with sections:
    - Executive summary
    - Clustering details (algorithm, n_clusters, sizes)
    - Stability analysis (per-cluster cores)
    - Label quality (top terms per cluster)
    - Metrics and gates (pass/fail table)
    - Cluster table (ID, label, size, stability, status)
    - Merge history (if auto_resolve ran)
    - Recommendations (fix suggestions if gates fail)
    - Next steps
  - Save to `artifacts/discovery/report.md`

### Persona Synthesis (2 modules)

- [ ] **scripts/personas/synthesize_from_cluster.py**
  - Load cluster labels, centroids, stability, labels_text
  - For each stable cluster:
    - Generate persona_id: `disc_{hash(centroid)[:8]}`
    - Extract demographics (mode of age_group, gender, location)
    - Compute psychographics (mean OCEAN scores, clip to [0,1])
    - Extract shopping_values (map top terms to categories)
    - Mine decision_heuristics ("if X then Y" patterns from rationales)
    - Sample evaluation_probes (5 prompts from cluster sessions)
    - Write to `DATA/personas_discovered/{persona_id}.json`
  - Update registry: `DATA/personas_discovered/registry.json`
    - List all personas with IDs, labels, sizes, metrics, file paths

- [ ] **scripts/personas/migrate_phase2_guardrails.py**
  - Update Phase 2 validators to accept discovered personas
  - Allow dual registries (curated + discovered)
  - Add `persona_source` config key (curated | discovered | hybrid)
  - Ensure loaders can read either registry
  - Preserve curated personas as-is

### Router Updates (2 modules)

- [ ] **services/router/embedding_loader.py** (update existing)
  - Add mode: load discovered personas when `use_discovered_personas: true`
  - Load centroids from `DATA/personas_discovered/registry.json`
  - Implement FAISS index for fast nearest-neighbor
  - Cache centroids in memory
  - Lazy load on first request

- [ ] **services/router/mix_of_twins.py** (update existing)
  - Route by nearest cluster centroid (cosine similarity)
  - If confidence < min_confidence (0.15), route to generic fallback
  - Support hybrid mode (try discovered, fall back to curated)
  - Maintain legacy API compatibility

### Tests (2 test suites)

- [ ] **discovery/__tests__/test_discovery_pipeline.py**
  - Test aggregate_sessions (step → session aggregation)
  - Test build_graph (k-NN construction, edge filtering)
  - Test cluster_hdbscan (basic clustering, soft memberships)
  - Test stability_bootstrap (Jaccard computation, stable cores)
  - Test auto_resolve (merge logic, filtering)
  - Test label_topics (TF-IDF, term extraction)
  - Test metrics (all gates, pass/fail logic)
  - Test determinism (same seed → same results)

- [ ] **services/router/__tests__/test_router_dynamic_personas.py**
  - Test discovered persona loading
  - Test routing with dynamic personas
  - Test fallback to curated personas
  - Test confidence threshold
  - Benchmark latency (p50, p95 within 5% of baseline)
  - Test feature flag toggle (no restart required)

---

## Configuration Reference

See `CONFIGS/discovery.yaml` for all parameters:

### Key Settings

```yaml
# Persona source
persona_source: curated  # or discovered or hybrid
use_discovered_personas: false  # Feature flag

# Clustering
clustering:
  hdbscan:
    min_cluster_size: 15
    min_samples: 8

# Stability
stability:
  n_bootstrap: 20
  metric: jaccard
  min_stability: 0.75

# Auto-resolve
auto_resolve:
  merge:
    centroid_distance_threshold: 0.10
    label_overlap_threshold: 0.40
  filter:
    min_size_frac: 0.005
    max_size_frac: 0.40

# Metrics gates
metrics:
  clustering_quality:
    silhouette:
      min_score: 0.45
    davies_bouldin:
      max_score: 0.8
  distribution:
    max_gini: 0.60
    min_entropy: 2.5
```

---

## Data Contracts

### Input: Session Embeddings

**File:** `artifacts/encoder/session_embeddings.parquet`

**Columns:**
- `session_id` (string): Unique session identifier
- `user_id` (string): User identifier
- `t` (timestamp): Session timestamp
- `emb` (float array): 256-D embedding
- `split` (string): train | val | test
- `rationales_agg` (string): Concatenated rationales for labeling
- `facts_agg` (string): Concatenated facts for labeling
- Optional demographics: `age_group`, `gender`, `location_type`

### Output: Discovered Persona Registry

**File:** `DATA/personas_discovered/registry.json`

```json
{
  "version": "mvp_v1_discovered",
  "discovery_run": {
    "timestamp": "2025-10-16T13:00:00Z",
    "seed": 17,
    "n_sessions": 10000,
    "algorithm": "hdbscan"
  },
  "personas": [
    {
      "persona_id": "disc_a1b2c3d4",
      "name": "Discount Sale Seekers",
      "file_path": "DATA/personas_discovered/disc_a1b2c3d4.json",
      "cluster_id": 0,
      "size": 1250,
      "size_frac": 0.125,
      "stability": 0.82,
      "silhouette_contrib": 0.51,
      "status": "production"  # or "experimental"
    },
    ...
  ],
  "summary": {
    "n_personas": 12,
    "n_production": 10,
    "n_experimental": 2,
    "gates_passed": true
  }
}
```

### Output: Persona File

**File:** `DATA/personas_discovered/disc_a1b2c3d4.json`

```json
{
  "persona_id": "disc_a1b2c3d4",
  "name": "Discount Sale Seekers",
  "version": "mvp_v1_discovered",
  "discovery_metadata": {
    "cluster_id": 0,
    "size": 1250,
    "stability": 0.82,
    "centroid_hash": "a1b2c3d4"
  },
  "demographics": {
    "age_group": "25-34",
    "gender": "mixed",
    "location_type": "urban"
  },
  "psychographics": {
    "ocean": {
      "O": 0.6,
      "C": 0.7,
      "E": 0.4,
      "A": 0.5,
      "N": 0.3
    }
  },
  "shopping_values": ["savings", "discounts", "deals", "value", "price"],
  "constraints": "Prefers products on sale. Waits for discounts.",
  "decision_heuristics": [
    "If price > $50, check for coupon codes",
    "If discount < 20%, consider alternatives"
  ],
  "evaluation_probes": [
    "Product A is $30, Product B is $50 with 20% off. Which do you choose?",
    ...
  ],
  "embedding_seed": "a1b2c3d4"
}
```

---

## Commands to Run

### Full Pipeline

```bash
# 1. Aggregate sessions
PYTHONPATH=. python discovery/aggregate_sessions.py \
  --steps artifacts/encoder/embeddings.parquet \
  --out artifacts/encoder/session_embeddings.parquet \
  --config CONFIGS/discovery.yaml

# 2. Build graph
PYTHONPATH=. python discovery/build_graph.py \
  --emb artifacts/encoder/session_embeddings.parquet \
  --out artifacts/discovery/graph \
  --config CONFIGS/discovery.yaml

# 3. Cluster with HDBSCAN
PYTHONPATH=. python discovery/cluster_hdbscan.py \
  --graph artifacts/discovery/graph \
  --out artifacts/discovery/labels \
  --config CONFIGS/discovery.yaml

# 4. Bootstrap stability
PYTHONPATH=. python discovery/stability_bootstrap.py \
  --emb artifacts/encoder/session_embeddings.parquet \
  --labels artifacts/discovery/labels \
  --out artifacts/discovery/stability \
  --config CONFIGS/discovery.yaml

# 5. Auto-resolve (merge/filter)
PYTHONPATH=. python discovery/auto_resolve.py \
  --labels artifacts/discovery/labels \
  --stability artifacts/discovery/stability \
  --out artifacts/discovery/labels_resolved \
  --config CONFIGS/discovery.yaml

# 6. Leiden fallback (if needed)
PYTHONPATH=. python discovery/cluster_leiden.py \
  --graph artifacts/discovery/graph \
  --out artifacts/discovery/labels_leiden \
  --config CONFIGS/discovery.yaml

# 7. Unsupervised labeling
PYTHONPATH=. python discovery/label_topics.py \
  --emb artifacts/encoder/session_embeddings.parquet \
  --labels artifacts/discovery/labels_resolved \
  --out artifacts/discovery/labels_text.json \
  --config CONFIGS/discovery.yaml

# 8. Compute metrics
PYTHONPATH=. python discovery/metrics.py \
  --emb artifacts/encoder/session_embeddings.parquet \
  --labels artifacts/discovery/labels_resolved \
  --stability artifacts/discovery/stability \
  --out artifacts/discovery/metrics.json \
  --config CONFIGS/discovery.yaml

# 9. Synthesize personas
PYTHONPATH=. python scripts/personas/synthesize_from_cluster.py \
  --labels artifacts/discovery/labels_resolved \
  --labels_text artifacts/discovery/labels_text.json \
  --metrics artifacts/discovery/metrics.json \
  --out DATA/personas_discovered \
  --config CONFIGS/discovery.yaml

# 10. Generate report
PYTHONPATH=. python discovery/report.py \
  --metrics artifacts/discovery/metrics.json \
  --stability artifacts/discovery/stability \
  --registry DATA/personas_discovered/registry.json \
  --out artifacts/discovery/report.md \
  --config CONFIGS/discovery.yaml

# 11. Run tests
pytest discovery/__tests__/test_discovery_pipeline.py -v
pytest services/router/__tests__/test_router_dynamic_personas.py -v
```

---

## Quality Gates

All gates must pass before enabling `use_discovered_personas: true`

| Gate | Target | Failure Action |
|------|--------|----------------|
| **Silhouette** | >= 0.45 | Increase min_cluster_size |
| **Davies-Bouldin** | <= 0.8 | Retrain encoder with higher persona loss |
| **Calinski-Harabasz** | >= 100 | Check if too few clusters |
| **Gini** | <= 0.60 | Merge dominant clusters |
| **Entropy** | >= 2.5 | Increase min_cluster_size |
| **Distinct-n** | >= 0.10 | Tighten label overlap threshold |
| **Psychometric** | >= 4/5 | Check OCEAN computation |
| **Size limits** | 0.5%-40% | Filter tiny/huge clusters |

---

## Failure Modes and Fixes

### 1. Too Much Noise (> 20%)

**Symptoms:** Many sessions labeled as noise (-1)

**Fixes:**
- Lower `min_samples` (8 → 5)
- Lower `min_similarity` threshold (0.35 → 0.30)
- Switch to Leiden fallback

### 2. One Giant Cluster

**Symptoms:** Single cluster dominates (> 40% of sessions)

**Fixes:**
- Increase `min_cluster_size` (15 → 25)
- Raise `centroid_distance_threshold` (0.10 → 0.15)
- Retrain encoder with higher diversity loss

### 3. Low Distinctiveness

**Symptoms:** Distinct-n margin < 0.10

**Fixes:**
- Filter more stopwords
- Increase `min_df` for n-grams (2 → 5)
- Tighten `label_overlap_threshold` (0.40 → 0.50)

### 4. Latency Regression (> 5%)

**Symptoms:** Router p95 latency increases

**Fixes:**
- Enable FAISS indexing
- Cache centroids on warmup
- Reduce number of discovered personas (merge similar)

---

## Performance Targets

| Metric | Baseline | Target | Max Allowed |
|--------|----------|--------|-------------|
| Router p50 | 2.0ms | 2.0ms | 2.1ms (+5%) |
| Router p95 | 5.0ms | 5.0ms | 5.25ms (+5%) |
| Discovery memory | N/A | < 4GB | 4GB |
| Discovery time | N/A | < 10min | 15min |

---

## Next Steps

1. **Implement 10 core discovery modules** (aggregate → report)
2. **Implement 2 persona synthesis modules**
3. **Update 2 router modules** for discovered personas
4. **Write 2 test suites** (discovery + router)
5. **Run full pipeline** on sample data
6. **Review report** and fix gate failures
7. **Enable feature flag** and monitor

---

## Dependencies

Update `pyproject.toml`:

```toml
dependencies = [
  # ... existing ...
  "hdbscan>=0.8.33",
  "igraph>=0.11.0",
  "leidenalg>=0.10.0",
  "faiss-cpu>=1.7.4",
  "networkx>=3.0",
  "nltk>=3.8",  # For stopwords
]
```

---

**Status:** Architecture and config complete. Ready for module implementation.

**Estimated effort:** 3-5 days for full implementation + testing + documentation.
