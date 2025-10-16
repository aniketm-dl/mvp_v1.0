# Phase 3E.3 Quick Start Guide

**Goal:** Replace 15-D embeddings with 256-D encoder embeddings via discovery pipeline

---

## Prerequisites

✅ Phase 3E.1 Complete - OPeRA parser and dataloader
✅ Phase 3E.2 Complete - Multi-view encoder trained
✅ Encoder checkpoint available at `artifacts/encoder/best.ckpt`

---

## Installation

```bash
# Install new dependencies
pip install hdbscan igraph leidenalg pyarrow umap-learn tqdm

# Or with uv (if using)
uv add hdbscan igraph leidenalg pyarrow umap-learn tqdm
```

---

## Three-Step Workflow

### Step 1: Export Embeddings

```bash
python scripts/export_embeddings.py \
  --ckpt artifacts/encoder/best.ckpt \
  --data DATA/OPeRA/processed \
  --config CONFIGS/encoder.yaml \
  --out artifacts/encoder/embeddings.parquet
```

**Output:** `artifacts/encoder/embeddings.parquet` (256-D embeddings + metadata)

---

### Step 2: Run Discovery Pipeline

```bash
./scripts/run_discovery_pipeline.sh
```

**This runs:**
1. k-NN graph construction (k=15, cosine similarity)
2. HDBSCAN clustering (with Leiden fallback)
3. Bootstrap stability (20 runs)
4. Persona classifier (confusion analysis)
5. Discovery report with quality gates

**Output:** `artifacts/discovery/report.md`

---

### Step 3: Check Gates and Enable Router

```bash
# Check if gates passed
cat artifacts/discovery/report.md | grep "ALL GATES"
```

**If passed:**

1. Edit `CONFIGS/discovery.yaml`:
   ```yaml
   router:
     use_encoder_embeddings: true  # Flip from false to true
   ```

2. Test router:
   ```python
   from services.router.mix_of_twins import MixtureOfTwins

   router = MixtureOfTwins()
   result = router.route({"embedding": [0.1] * 256})
   print(f"Backend: {result['backend']}")  # Should show "encoder"
   ```

3. Monitor latency and twin assignments

**If failed:** Review report recommendations and fix issues

---

## Rollback

If issues arise after enabling new embeddings:

1. Edit `CONFIGS/discovery.yaml`:
   ```yaml
   router:
     use_encoder_embeddings: false  # Revert
   ```

2. Restart services - router will use legacy 15-D embeddings

---

## Quality Gates

Must pass before production:

| Gate | Target | Status |
|------|--------|--------|
| Silhouette | >= 0.45 | Check report |
| Davies-Bouldin | <= 0.8 | Check report |
| Distinct-n | >= 0.10 | Check report |
| Psychometric | >= 4/5 | Check report |
| Behavior Tasks | >= 75% | Check report |

---

## Troubleshooting

### Fragmented Clusters (n_clusters > 30)

**Fix:** Edit `CONFIGS/discovery.yaml`:
```yaml
clustering:
  hdbscan:
    min_cluster_size: 20  # Increase from 10
```

### Low Silhouette (< 0.45)

**Fix:** Retrain encoder with higher persona alignment:
```yaml
# In CONFIGS/encoder.yaml
loss:
  persona_alignment:
    weight: 0.8  # Increase from 0.5
```

### Persona Confusion (accuracy < 85%)

**Fix:** Review confusion pairs in report, merge similar personas

---

## Key Files

### Created in Phase 3E.3

```
discovery/
├── build_graph.py              # k-NN graph
├── cluster_hdbscan.py          # Clustering
├── stability_bootstrap.py      # Stability
├── persona_classifier.py       # Confusion
├── quality_gates.py            # 5 gates
├── report.py                   # Report generator
└── README.md                   # Full documentation

services/router/
├── embedding_loader.py         # Load embeddings
└── mix_of_twins.py            # Mixture router

CONFIGS/
└── discovery.yaml              # All settings

scripts/
├── export_embeddings.py        # Export from encoder
└── run_discovery_pipeline.sh   # Full pipeline
```

### Modified

```
pyproject.toml                  # Added dependencies
```

---

## Testing

```bash
# Run discovery tests
pytest discovery/__tests__/test_discovery_pipeline.py -v

# Run router tests
pytest services/router/test_*.py -v  # If tests exist

# Run full test suite
pytest TESTS/ -v
```

---

## Monitoring

After enabling new embeddings:

1. **Latency:** Should stay <2ms (lazy loading helps)
2. **Twin Assignment:** Check if primary twins are stable
3. **Quality:** Run nightly discovery to track drift

---

## Next Steps

1. ✅ Complete Phase 3E.3 - **DONE**
2. ⏳ Train encoder on full OPeRA dataset
3. ⏳ Run full discovery pipeline
4. ⏳ Enable router feature flag
5. ⏳ Monitor production metrics
6. ⏳ Set up nightly discovery cron job

---

## Support

- **Full Docs:** `discovery/README.md`
- **Completion Report:** `PHASE_3E3_COMPLETE.md`
- **Config Reference:** `CONFIGS/discovery.yaml`

---

**Status:** ✅ Phase 3E.3 infrastructure complete, ready for encoder training and production deployment
