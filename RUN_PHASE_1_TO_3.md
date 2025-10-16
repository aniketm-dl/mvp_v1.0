# 🚀 Run Phase 1-3: Complete Discovery Pipeline on AWS

**Quick Start Guide for Running OPeRA Parsing, Encoder Training, and Persona Discovery**

---

## ⚡ TL;DR - Run Everything Now

```bash
# Ensure you're in the project directory
cd "/Users/aniketniranjanmishra/Desktop/Darpan Labs/mvp_v1.0"

# Option 1: AWS (Recommended - Faster, Consistent)
make phase-1-3-aws

# Option 2: Local (Requires GPU, Slower)
make phase-1-3-local

# Validate outputs
make phase-1-3-validate
```

**Done!** In 2-4 hours you'll have discovered personas ready for Phase 4.

---

## 📋 What This Does

This pipeline runs three critical phases in sequence:

### Phase 1: OPeRA Data Parsing (~10 min)
- Downloads OPeRA e-commerce browsing dataset
- Parses raw Parquet files
- Extracts sessions, actions, rationales
- **Output:** `DATA/OPeRA/processed/*.parquet`

### Phase 2: Behavioral Encoder Training (~90-180 min)
- Trains multi-view transformer encoder
- Learns behavioral embeddings from sessions
- Uses PyTorch Lightning for training
- **Output:** `artifacts/encoder/best.ckpt`

### Phase 3: Persona Discovery (~15 min)
- **3E.1:** Generates session embeddings
- **3E.2:** Clusters sessions (HDBSCAN)
- **3E.3:** Synthesizes personas from clusters
- **Output:** `DATA/personas_discovered/*.json`

**Total Time:** 2 hours (AWS) or 3-4 hours (Local)

---

## 🎯 Prerequisites

### For AWS Mode
- [x] AWS credentials configured
- [x] S3 bucket created
- [x] SSH key permissions (handled automatically)

### For Local Mode
- [x] NVIDIA GPU with 16GB+ VRAM
- [x] 100GB+ free disk space
- [x] Python 3.10+

### Verification
```bash
# Check AWS
aws sts get-caller-identity
export TRAINING_S3_BUCKET=darpan-training-aniketniranjanmishra
aws s3 ls s3://$TRAINING_S3_BUCKET/

# Check GPU (local mode)
nvidia-smi

# Check disk space
df -h .
```

---

## 🚀 Execution Methods

### Method 1: Makefile (Recommended)

```bash
# AWS execution
make phase-1-3-aws

# Local execution
make phase-1-3-local

# Individual phases
make phase-1-parse       # Phase 1 only
make phase-2-encoder     # Phase 2 only
make phase-3-discovery   # Phase 3 only

# Validation
make phase-1-3-validate
```

### Method 2: Direct Scripts

```bash
# AWS
./run_phase_1_to_3_aws.sh

# Local
./run_phase_1_to_3_local.sh

# Validation
python3 scripts/validate_phase_1_3.py
```

---

## 📊 What Happens During Execution

### AWS Mode Timeline

```
[00:00] 🚀 Script starts
[00:05] ✓ EC2 instance launched (g5.xlarge)
[00:10] ✓ Environment setup complete
[00:20] ✓ Phase 1: OPeRA data parsed
[02:00] ✓ Phase 2: Encoder trained
[02:10] ✓ Phase 3E.1: Embeddings generated
[02:25] ✓ Phase 3E.2-3: Personas discovered
[02:30] ✓ Artifacts uploaded to S3
[02:35] ✓ Artifacts downloaded locally
[02:36] ✅ Complete!
```

### Local Mode Timeline

```
[00:00] 🚀 Script starts
[00:05] ✓ Dependencies verified
[00:15] ✓ Phase 1: OPeRA data parsed
[03:00] ✓ Phase 2: Encoder trained (slower on local GPU)
[03:10] ✓ Phase 3E.1: Embeddings generated
[03:25] ✓ Phase 3E.2-3: Personas discovered
[03:26] ✅ Complete!
```

---

## ✅ Expected Outputs

After successful completion:

```
artifacts/
├── encoder/
│   ├── best.ckpt                    # ✓ Trained encoder checkpoint
│   ├── session_embeddings.parquet   # ✓ 256-D embeddings per session
│   └── logs/
│       └── version_0/
│           └── metrics.csv          # ✓ Training metrics
└── discovery/
    ├── report.md                    # ✓ Quality report with metrics
    ├── metrics.json                 # ✓ Separation scores
    └── labels_text.json             # ✓ Cluster labels

DATA/
├── OPeRA/
│   └── processed/                   # ✓ Parsed OPeRA sessions
└── personas_discovered/
    ├── registry.json                # ✓ Master persona registry
    ├── disc_a1b2c3d4.json          # ✓ Individual persona files
    ├── disc_e5f6g7h8.json          # ✓ (10-25 personas total)
    └── ...
```

---

## 🔍 Validation & Quality Checks

### Automatic Validation

```bash
make phase-1-3-validate
```

This checks:
- ✓ All output files exist
- ✓ Files are readable and non-empty
- ✓ Encoder accuracy ≥ 70%
- ✓ Silhouette score ≥ 0.45
- ✓ Davies-Bouldin ≤ 0.8
- ✓ 10-25 personas discovered
- ✓ Noise fraction < 20%

### Manual Review

```bash
# View discovery report
cat artifacts/discovery/report.md

# List personas
cat DATA/personas_discovered/registry.json | python3 -m json.tool

# Check metrics
python3 -c "
import json
with open('artifacts/discovery/metrics.json') as f:
    m = json.load(f)
print(f'Silhouette: {m[\"silhouette\"]:.3f} (target: ≥0.45)')
print(f'Davies-Bouldin: {m[\"davies_bouldin\"]:.3f} (target: ≤0.8)')
print(f'Calinski-Harabasz: {m[\"calinski_harabasz\"]:.1f} (target: ≥100)')
"
```

---

## 💰 Cost & Time

### AWS Mode
| Item | Value |
|------|-------|
| Instance Type | g5.xlarge spot |
| Region | ap-south-1 (Mumbai) |
| Spot Price | ~$0.35/hr |
| Duration | ~2 hours |
| **Total Cost** | **~$0.70** |
| Storage (S3) | ~$0.02/month |

### Local Mode
| Item | Value |
|------|-------|
| GPU Required | 16GB+ VRAM |
| Duration | ~3-4 hours |
| **Total Cost** | **$0** |

---

## 🐛 Troubleshooting

### AWS Issues

**Problem:** Spot instance request failed
```bash
# Increase max spot price
export MAX_SPOT_PRICE=0.60
./run_phase_1_to_3_aws.sh
```

**Problem:** SSH connection timeout
```bash
# Wait longer (instance initializing)
# Check security group allows port 22
aws ec2 describe-security-groups --group-name darpan-training-sg
```

**Problem:** S3 permission denied
```bash
# Verify credentials
aws sts get-caller-identity
# Test bucket access
aws s3 ls s3://$TRAINING_S3_BUCKET/
```

### Local Issues

**Problem:** CUDA out of memory
```bash
# Edit CONFIGS/encoder.yaml
# Reduce batch_size from 64 to 32 or 16
```

**Problem:** HDBSCAN not installed
```bash
pip install hdbscan umap-learn
# On Mac M1/M2:
conda install hdbscan
```

**Problem:** Training too slow
```bash
# Verify GPU usage
nvidia-smi
# Should show 80-100% GPU utilization

# Check PyTorch CUDA
python3 -c "import torch; print(torch.cuda.is_available())"
```

**Problem:** Discovery gates fail
```bash
# Adjust CONFIGS/discovery.yaml
# Lower min_cluster_size from 15 to 10
# Lower min_samples from 8 to 5
# Re-run Phase 3 only:
make phase-3-discovery
```

---

## 🎓 Understanding the Output

### Discovery Report

`artifacts/discovery/report.md` contains:

1. **Executive Summary**
   - Number of personas discovered
   - Quality gate status (PASS/FAIL)

2. **Quality Metrics**
   ```
   Silhouette: 0.52 ≥ 0.45 ✓
   Davies-Bouldin: 0.67 ≤ 0.8 ✓
   Calinski-Harabasz: 187.3 ≥ 100 ✓
   ```

3. **Discovered Personas**
   - ID, name, size, shopping values
   - Example: `disc_a1b2c3d4: Price Delivery Value (n=487)`

4. **Recommendations**
   - Whether to enable discovered personas
   - Suggested config changes

### Persona Files

Each `disc_*.json` contains:
```json
{
  "persona_id": "disc_a1b2c3d4",
  "name": "Price Delivery Value",
  "version": "mvp_v1_discovered",
  "cluster_id": 3,
  "size": 487,
  "shopping_values": [
    "price",
    "delivery",
    "value",
    "fast",
    "quality"
  ],
  "embedding_seed": "a1b2c3d4"
}
```

---

## 🔄 Re-running the Pipeline

### Full Re-run (Clean Slate)

```bash
# Remove all outputs
rm -rf artifacts/encoder artifacts/discovery
rm -rf DATA/personas_discovered DATA/OPeRA/processed

# Run again
make phase-1-3-aws  # or make phase-1-3-local
```

### Partial Re-run

```bash
# Re-run Phase 3 only (keep encoder)
make phase-3-discovery

# Re-run Phase 2 & 3 (keep parsed data)
make phase-2-encoder
make phase-3-discovery

# Re-run Phase 1 only
make phase-1-parse
```

---

## 📈 Next Steps After Completion

### 1. Validate Everything

```bash
make phase-1-3-validate
# Should output: "✅ ALL VALIDATIONS PASSED"
```

### 2. Review Quality

```bash
# Read report
cat artifacts/discovery/report.md

# Check personas
cat DATA/personas_discovered/registry.json

# Spot check a few persona files
cat DATA/personas_discovered/disc_*.json | head -50
```

### 3. Enable Discovered Personas (Optional)

Edit `CONFIGS/discovery.yaml`:
```yaml
# Change from:
persona_source: curated
use_discovered_personas: false

# To:
persona_source: discovered  # or 'hybrid' for both
use_discovered_personas: true
```

### 4. Backup to S3 (If Running Locally)

```bash
# Upload artifacts
aws s3 sync artifacts/ s3://$TRAINING_S3_BUCKET/backup/artifacts_$(date +%Y%m%d)/

# Upload personas
aws s3 sync DATA/personas_discovered/ s3://$TRAINING_S3_BUCKET/backup/personas_$(date +%Y%m%d)/
```

### 5. Proceed to Phase 4

You're now ready for **Phase 4: Multi-turn SFT Dataset Generation**

Phase 4 will use:
- `DATA/personas_discovered/registry.json`
- `artifacts/encoder/session_embeddings.parquet`
- Discovered persona profiles

---

## 💡 Pro Tips

### For AWS

1. **Monitor during execution:**
   ```bash
   # After instance launches, SSH to monitor:
   ssh -i ~/darpan-training.pem ubuntu@<IP>
   cd mvp_v1.0
   tail -f artifacts/encoder/logs/version_0/metrics.csv
   ```

2. **Cost optimization:**
   - Script uses spot instances (50-70% cheaper)
   - Auto-uploads to S3 (persistent storage)
   - Optional auto-termination after download

3. **Parallel execution:**
   - Run multiple experiments with different configs
   - Use separate S3 prefixes: `phase_1_3/<experiment_name>/`

### For Local

1. **Monitor GPU usage:**
   ```bash
   watch -n 1 nvidia-smi
   ```

2. **Use screen/tmux:**
   ```bash
   screen -S phase13
   ./run_phase_1_to_3_local.sh
   # Detach with Ctrl+A, D
   # Reattach with: screen -r phase13
   ```

3. **Free up VRAM:**
   ```bash
   # Close other GPU applications
   # Reduce batch size in configs
   # Use mixed precision (already configured)
   ```

---

## 📚 Additional Documentation

- **Complete Guide:** [PHASE_1_TO_3_COMPLETE.md](PHASE_1_TO_3_COMPLETE.md) (detailed)
- **Summary:** [PHASE_1_TO_3_SUMMARY.md](PHASE_1_TO_3_SUMMARY.md) (quick ref)
- **AWS Setup:** [AWS_QUICK_REFERENCE.md](AWS_QUICK_REFERENCE.md)
- **Full Workflow:** [END_TO_END_WORKFLOW.md](END_TO_END_WORKFLOW.md)
- **Project Status:** [PROJECT_STATUS.md](PROJECT_STATUS.md)

---

## 🎯 Success Criteria

✅ **Phase 1 Success:**
- `DATA/OPeRA/processed/` has Parquet files
- Files are readable with sessions data

✅ **Phase 2 Success:**
- `artifacts/encoder/best.ckpt` exists
- Validation accuracy ≥ 70%
- Training converged (losses decreased)

✅ **Phase 3 Success:**
- 10-25 personas discovered
- Silhouette ≥ 0.45
- Davies-Bouldin ≤ 0.8
- Noise < 20%
- Report says "ALL GATES PASSED"

✅ **Overall Success:**
- `make phase-1-3-validate` passes all checks
- Personas are distinct and well-separated
- Ready for Phase 4

---

## 🆘 Getting Help

### If Validation Fails

1. Check specific failure in validation output
2. Read `artifacts/discovery/report.md` for details
3. Adjust configs as suggested
4. Re-run failed phase only

### If Training Fails

1. Check `artifacts/encoder/logs/version_0/metrics.csv`
2. Look for NaN losses or divergence
3. Reduce learning rate or batch size
4. Re-run Phase 2

### If Discovery Fails

1. Check number of sessions in embeddings
2. Review clustering parameters
3. Try Leiden fallback (set noise > 20%)
4. Re-run Phase 3 with adjusted config

---

## ✅ You're Ready!

**To start now:**

```bash
# AWS (recommended)
make phase-1-3-aws

# Or local
make phase-1-3-local
```

**Monitor progress:**
- AWS: SSH to instance and tail logs
- Local: Watch terminal output

**Validate when done:**
```bash
make phase-1-3-validate
```

**Then proceed to Phase 4! 🚀**

---

**Created:** 2025-10-16
**Status:** ✅ Production ready
**Tested:** Validated dry-run
**Support:** See [PHASE_1_TO_3_COMPLETE.md](PHASE_1_TO_3_COMPLETE.md) for troubleshooting
