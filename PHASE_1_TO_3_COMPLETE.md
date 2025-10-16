# Phase 1-3 Complete Pipeline: OPeRA → Encoder → Persona Discovery

**Complete execution guide for running Phases 1-3 from scratch**

---

## 📋 Overview

This pipeline executes three critical phases:

1. **Phase 1**: Parse and process OPeRA e-commerce dataset
2. **Phase 2**: Train multi-view behavioral encoder
3. **Phase 3**: Discover personas via unsupervised clustering

**Total Time:** 2-4 hours (AWS) or 4-6 hours (Local with GPU)
**Total Cost:** ~$0.70-1.00 (AWS), $0 (Local)

---

## 🎯 Two Execution Modes

### Mode 1: AWS (Recommended) ⭐
- **Pros**: Faster, consistent GPU, automated
- **Cons**: Small cost (~$1), requires AWS setup
- **Use Case**: Production runs, reproducibility

### Mode 2: Local
- **Pros**: Free, no AWS needed
- **Cons**: Slower, requires local GPU
- **Use Case**: Development, testing

---

## 🚀 Mode 1: AWS Execution

### Prerequisites

```bash
# 1. AWS credentials configured
aws sts get-caller-identity

# 2. S3 bucket exists
export TRAINING_S3_BUCKET=darpan-training-aniketniranjanmishra
aws s3 ls s3://$TRAINING_S3_BUCKET/

# 3. Project setup
cd "/Users/aniketniranjanmishra/Desktop/Darpan Labs/mvp_v1.0"
source venv/bin/activate
```

### Single Command Execution

```bash
./run_phase_1_to_3_aws.sh
```

### What It Does

1. **Launches AWS GPU instance** (g5.xlarge spot)
2. **Clones repository** and sets up environment
3. **Phase 1**: Downloads and parses OPeRA data
4. **Phase 2**: Trains behavioral encoder (~90 min)
5. **Phase 3E.1**: Generates session embeddings
6. **Phase 3E.2**: Clusters sessions (HDBSCAN)
7. **Phase 3E.3**: Synthesizes discovered personas
8. **Uploads to S3**: All artifacts backed up
9. **Downloads locally**: Artifacts synced to local machine
10. **Cleanup**: Optional instance termination

### Expected Output

```
artifacts/
├── encoder/
│   ├── best.ckpt                    # Trained encoder checkpoint
│   ├── session_embeddings.parquet   # Session-level embeddings
│   └── logs/                        # Training logs
└── discovery/
    ├── report.md                    # Quality metrics report
    ├── labels_text.json             # Cluster labels
    └── metrics.json                 # Separation metrics

DATA/
└── personas_discovered/
    ├── registry.json                # Persona registry
    ├── disc_a1b2c3d4.json          # Individual persona files
    ├── disc_e5f6g7h8.json
    └── ...
```

### Time & Cost Breakdown

| Phase | Time | Cost |
|-------|------|------|
| Setup & Launch | 5 min | $0.03 |
| Phase 1 (Parse) | 10 min | $0.06 |
| Phase 2 (Encoder) | 90 min | $0.52 |
| Phase 3 (Discovery) | 15 min | $0.09 |
| Upload to S3 | 5 min | $0.03 |
| **Total** | **~2 hours** | **~$0.73** |

---

## 💻 Mode 2: Local Execution

### Prerequisites

```bash
# 1. GPU with 16GB+ VRAM
nvidia-smi  # Verify GPU

# 2. Disk space: 100GB+ free
df -h .

# 3. Python 3.10+
python3 --version

# 4. Project setup
cd "/Users/aniketniranjanmishra/Desktop/Darpan Labs/mvp_v1.0"
source venv/bin/activate
```

### Single Command Execution

```bash
./run_phase_1_to_3_local.sh
```

### What It Does

Same pipeline as AWS mode, but runs locally:
1. Installs dependencies
2. Executes Phases 1-3 sequentially
3. Saves all outputs locally
4. Generates logs for debugging

### Time Breakdown (Local)

| Phase | Time |
|-------|------|
| Phase 1 (Parse) | 10-15 min |
| Phase 2 (Encoder) | 2-3 hours |
| Phase 3 (Discovery) | 15-20 min |
| **Total** | **~3-4 hours** |

---

## 📊 Pipeline Details

### Phase 1: OPeRA Data Parsing

**Input:** Raw OPeRA dataset (e-commerce browsing sessions)
**Output:** Processed parquet files with:
- User sessions
- Actions (view, add_to_cart, purchase)
- Rationales (extracted text)
- Catalog features

**Script:** `scripts/parse_opera.py`
**Config:** `CONFIGS/opera.yaml`

**Key Metrics:**
- Sessions processed: ~50,000+
- Steps per session: 5-20
- Features: 30+ per step

### Phase 2: Behavioral Encoder Training

**Architecture:** Multi-view transformer encoder
- **Sequence encoder**: Temporal action patterns
- **Rationale encoder**: Text-based reasoning
- **Persona encoder**: Psychographic features
- **Catalog encoder**: Product features
- **Fusion layer**: Combines all views

**Training:**
- Epochs: 10 (with early stopping)
- Batch size: 32-64
- Loss: Multi-objective (next action + psychometric + separation)
- Optimization: AdamW with cosine annealing

**Script:** `scripts/train/encoder_train.py`
**Config:** `CONFIGS/encoder.yaml`

**Key Metrics:**
- Next action accuracy: >75%
- Psychometric MSE: <0.05
- Separation silhouette: >0.40

### Phase 3: Unsupervised Persona Discovery

**Step 3E.1: Session Embedding Generation**
- Loads trained encoder
- Runs inference on all sessions
- Aggregates step embeddings to session level
- Output: 256-D embeddings per session

**Step 3E.2: Clustering**
- **Primary**: HDBSCAN (density-based)
  - Min cluster size: 15
  - Min samples: 8
- **Fallback**: Leiden algorithm (modularity-based)
- **Validation**: Bootstrap stability (20 iterations)

**Step 3E.3: Persona Synthesis**
- Labels clusters via TF-IDF on rationales
- Computes centroids and statistics
- Generates persona JSON files
- Quality gates enforcement

**Script:** `scripts/run_dynamic_discovery.py`
**Config:** `CONFIGS/discovery.yaml`

**Key Metrics:**
- Clusters discovered: 10-25
- Silhouette score: ≥0.45
- Davies-Bouldin: ≤0.8
- Noise sessions: <20%

---

## ✅ Validation & Quality Gates

### Automatic Checks

The pipeline enforces quality gates at each phase:

**Phase 2 (Encoder):**
- ✓ Action accuracy ≥ 70%
- ✓ Validation loss converged
- ✓ No NaN gradients

**Phase 3 (Discovery):**
- ✓ Silhouette ≥ 0.45
- ✓ Davies-Bouldin ≤ 0.8
- ✓ Calinski-Harabasz ≥ 100
- ✓ Noise fraction < 20%
- ✓ Bootstrap stability ≥ 0.75

### Manual Validation

After pipeline completes, review:

```bash
# 1. Discovery report
cat artifacts/discovery/report.md

# 2. Discovered personas
cat DATA/personas_discovered/registry.json
python3 -c "
import json
with open('DATA/personas_discovered/registry.json') as f:
    data = json.load(f)
    print(f'Discovered {len(data[\"personas\"])} personas')
    for p in data['personas'][:5]:
        print(f'  - {p[\"persona_id\"]}: {p[\"name\"]} (n={p[\"size\"]})')
"

# 3. Metrics
cat artifacts/discovery/metrics.json | python3 -m json.tool

# 4. Encoder performance
cat artifacts/encoder/logs/version_0/metrics.csv | tail -20
```

---

## 🐛 Troubleshooting

### AWS Issues

**Problem:** Spot instance request failed (price-too-low)
```bash
# Solution: Increase max spot price
export MAX_SPOT_PRICE=0.60
./run_phase_1_to_3_aws.sh
```

**Problem:** SSH connection timeout
```bash
# Solution: Wait longer or check security group
aws ec2 describe-security-groups --group-ids sg-xxx
# Ensure port 22 is open
```

**Problem:** S3 upload permission denied
```bash
# Solution: Check AWS credentials and bucket policy
aws s3 ls s3://$TRAINING_S3_BUCKET/
aws sts get-caller-identity
```

### Local Issues

**Problem:** CUDA out of memory
```bash
# Solution: Reduce batch size in CONFIGS/encoder.yaml
# Change batch_size from 64 to 32 or 16
```

**Problem:** HDBSCAN not installed
```bash
pip install hdbscan
# Or on Mac with Apple Silicon:
conda install hdbscan
```

**Problem:** Training is slow
```bash
# Check GPU usage
nvidia-smi

# Should see 80-100% GPU utilization
# If not, check PyTorch CUDA:
python3 -c "import torch; print(torch.cuda.is_available())"
```

**Problem:** Discovery fails with "insufficient data"
```bash
# Check session embeddings
python3 -c "
import pandas as pd
df = pd.read_parquet('artifacts/encoder/session_embeddings.parquet')
print(f'Sessions: {len(df)}')
print(f'Embedding dim: {len([c for c in df.columns if c.startswith(\"emb_\")])}')
"

# Need at least 200 sessions for reliable clustering
```

---

## 📁 Output Files Reference

### Encoder Artifacts

```
artifacts/encoder/
├── best.ckpt                       # Best model checkpoint (use for inference)
├── checkpoints/
│   ├── encoder-epoch=05-val_next_action_acc=0.782.ckpt
│   └── last.ckpt                   # Latest checkpoint (fallback)
├── logs/
│   └── version_0/
│       ├── metrics.csv             # Training metrics
│       └── hparams.yaml            # Hyperparameters
└── session_embeddings.parquet      # Generated embeddings
```

### Discovery Artifacts

```
artifacts/discovery/
├── report.md                       # Human-readable report
├── metrics.json                    # Quality metrics
├── labels_text.json                # Cluster labels & terms
├── graph/
│   └── adjacency.pkl               # k-NN graph
├── labels/
│   ├── hdbscan_labels.npy          # HDBSCAN assignments
│   └── probabilities.npy           # Soft memberships
└── stability/
    └── bootstrap_results.pkl       # Stability analysis
```

### Discovered Personas

```
DATA/personas_discovered/
├── registry.json                   # Master registry
├── disc_a1b2c3d4.json              # Individual persona files
├── disc_e5f6g7h8.json
└── ...

# Each persona file contains:
{
  "persona_id": "disc_a1b2c3d4",
  "name": "Price Delivery Value",
  "version": "mvp_v1_discovered",
  "cluster_id": 3,
  "size": 487,
  "shopping_values": ["price", "delivery", "value", "fast", "quality"],
  "embedding_seed": "a1b2c3d4"
}
```

---

## 🔄 Re-running Pipeline

### Full Re-run

```bash
# Clean previous outputs
rm -rf artifacts/encoder artifacts/discovery
rm -rf DATA/personas_discovered

# Run again
./run_phase_1_to_3_aws.sh  # or _local.sh
```

### Partial Re-run

**Only Phase 3 (already have encoder):**
```bash
# Update config
sed -i 's|step_embeddings_path:.*|step_embeddings_path: artifacts/encoder/session_embeddings.parquet|' CONFIGS/discovery.yaml

# Run discovery only
python3 scripts/run_dynamic_discovery.py
```

**Only re-generate embeddings:**
```bash
python3 << 'PYTHON'
from scripts.train.encoder_train import EncoderLightningModule
# ... (see local script for full code)
PYTHON
```

---

## 📚 Next Steps After Completion

### 1. Validate Outputs

```bash
# Check discovered personas
ls -la DATA/personas_discovered/

# Review quality metrics
cat artifacts/discovery/report.md
```

### 2. Enable Discovered Personas (Optional)

Update `CONFIGS/discovery.yaml`:
```yaml
persona_source: discovered  # or hybrid
use_discovered_personas: true
```

### 3. Proceed to Phase 4

Now ready for **Phase 4: Multi-turn SFT Dataset Generation**

```bash
# Phase 4 will use:
# - DATA/personas_discovered/registry.json
# - artifacts/encoder/session_embeddings.parquet
```

---

## 🔍 Understanding the Output

### Persona Discovery Report

The `artifacts/discovery/report.md` contains:

1. **Executive Summary**
   - Number of personas discovered
   - Quality gate status
   - Noise fraction

2. **Clustering Details**
   - Algorithm used (HDBSCAN vs Leiden)
   - Parameters
   - Cluster sizes

3. **Quality Metrics**
   - Silhouette score (separation)
   - Davies-Bouldin score (compactness)
   - Calinski-Harabasz score (variance ratio)

4. **Persona Table**
   - ID, name, size, top terms
   - Shopping values
   - Example sessions

5. **Recommendations**
   - Whether to enable discovered personas
   - Suggested config changes
   - Next steps

---

## 💡 Tips for Success

### 1. Start with AWS
- More reliable and faster
- Consistent GPU performance
- Easy to reproduce

### 2. Monitor Progress
```bash
# During AWS execution, you can SSH to check:
ssh -i ~/darpan-training.pem ubuntu@<IP>

# Then:
cd mvp_v1.0
tail -f artifacts/encoder/logs/version_0/metrics.csv
```

### 3. Cost Optimization
- Use spot instances (already configured)
- Terminate immediately after downloading
- Compress before S3 upload

### 4. Quality Tuning

If discovery quality gates fail, adjust `CONFIGS/discovery.yaml`:

```yaml
clustering:
  hdbscan:
    min_cluster_size: 10  # Lower for more clusters
    min_samples: 5        # Lower for looser clusters
```

### 5. Backup Everything
```bash
# Before running, backup configs
cp -r CONFIGS CONFIGS.backup

# After completion, backup artifacts to S3
aws s3 sync artifacts/ s3://$TRAINING_S3_BUCKET/backup/artifacts_$(date +%Y%m%d)/
```

---

## 📊 Expected Timeline

### AWS Mode
```
[00:00] Script starts
[00:05] Instance launched and SSH ready
[00:10] Environment setup complete
[00:20] Phase 1 complete (OPeRA parsed)
[02:00] Phase 2 complete (Encoder trained)
[02:10] Phase 3E.1 complete (Embeddings generated)
[02:25] Phase 3E.2 & 3E.3 complete (Personas discovered)
[02:30] Artifacts uploaded to S3
[02:35] Artifacts downloaded locally
[02:36] ✅ Pipeline complete
```

### Local Mode
```
[00:00] Script starts
[00:05] Dependencies installed
[00:15] Phase 1 complete
[03:00] Phase 2 complete (slower on local GPU)
[03:10] Phase 3E.1 complete
[03:25] Phase 3E.2 & 3E.3 complete
[03:26] ✅ Pipeline complete
```

---

## 🎓 Learning Resources

- **OPeRA Dataset**: https://github.com/facebookresearch/OPeRA
- **HDBSCAN**: https://hdbscan.readthedocs.io/
- **PyTorch Lightning**: https://pytorch-lightning.readthedocs.io/
- **Multi-View Learning**: See `SPECS/WHAT_IF_SIMULATOR_SPEC.md`

---

## 📞 Support

### Common Questions

**Q: Can I run this without AWS?**
A: Yes! Use `run_phase_1_to_3_local.sh`

**Q: What if I don't have a GPU?**
A: AWS mode is recommended. Local CPU-only will be very slow (10+ hours)

**Q: Can I customize discovery parameters?**
A: Yes, edit `CONFIGS/discovery.yaml` before running

**Q: How do I use discovered personas?**
A: Enable in config: `use_discovered_personas: true`

**Q: What if quality gates fail?**
A: Review `artifacts/discovery/report.md` and adjust clustering parameters

---

**Last Updated:** 2025-10-16
**Status:** ✅ Ready for production use
**Tested:** AWS (g5.xlarge), Local (NVIDIA RTX 3090)
