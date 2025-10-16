# Phase 1-3 Complete Setup Summary

**Status:** ✅ Ready to execute
**Created:** 2025-10-16
**Tested:** Dry-run validation complete

---

## 📁 Files Created

### Execution Scripts

1. **`run_phase_1_to_3_aws.sh`** (Executable)
   - Complete AWS execution pipeline
   - Launches EC2, runs all phases, downloads artifacts
   - Auto-cleanup option
   - **Usage:** `./run_phase_1_to_3_aws.sh` or `make phase-1-3-aws`

2. **`run_phase_1_to_3_local.sh`** (Executable)
   - Local execution pipeline (requires GPU)
   - Sequential phase execution with logging
   - **Usage:** `./run_phase_1_to_3_local.sh` or `make phase-1-3-local`

### Validation & Utilities

3. **`scripts/validate_phase_1_3.py`** (Executable)
   - Validates all pipeline outputs
   - Checks quality gates
   - Provides actionable feedback
   - **Usage:** `python3 scripts/validate_phase_1_3.py` or `make phase-1-3-validate`

### Documentation

4. **`PHASE_1_TO_3_COMPLETE.md`**
   - Complete user guide (12+ pages)
   - Covers both AWS and local execution
   - Troubleshooting, validation, next steps
   - **Read:** `cat PHASE_1_TO_3_COMPLETE.md` or open in editor

5. **`PHASE_1_TO_3_SUMMARY.md`** (This file)
   - Quick reference for setup
   - Command cheat sheet

### Makefile Targets

Added 6 new targets to `Makefile`:
- `make phase-1-3-aws` - Run complete pipeline on AWS
- `make phase-1-3-local` - Run complete pipeline locally
- `make phase-1-3-validate` - Validate outputs
- `make phase-1-parse` - Run Phase 1 only
- `make phase-2-encoder` - Run Phase 2 only
- `make phase-3-discovery` - Run Phase 3 only

---

## 🚀 Quick Start

### Option 1: AWS (Recommended)

```bash
# 1. Ensure AWS credentials are configured
aws sts get-caller-identity
export TRAINING_S3_BUCKET=darpan-training-aniketniranjanmishra

# 2. Run complete pipeline
make phase-1-3-aws

# Or directly:
./run_phase_1_to_3_aws.sh

# 3. Validate outputs
make phase-1-3-validate
```

**Time:** ~2 hours
**Cost:** ~$0.70-1.00

### Option 2: Local (with GPU)

```bash
# 1. Ensure GPU is available
nvidia-smi

# 2. Run complete pipeline
make phase-1-3-local

# Or directly:
./run_phase_1_to_3_local.sh

# 3. Validate outputs
make phase-1-3-validate
```

**Time:** ~3-4 hours
**Cost:** $0 (uses local GPU)

---

## 📊 Pipeline Overview

```
Phase 1: OPeRA Data Parsing
  ↓
  Input:  DATA/OPeRA/raw/*.parquet
  Output: DATA/OPeRA/processed/*.parquet
  Time:   10-15 minutes

Phase 2: Behavioral Encoder Training
  ↓
  Input:  DATA/OPeRA/processed/
  Output: artifacts/encoder/best.ckpt
  Time:   90-180 minutes (AWS: 90 min, Local: 120-180 min)

Phase 3E.1: Session Embedding Generation
  ↓
  Input:  artifacts/encoder/best.ckpt
  Output: artifacts/encoder/session_embeddings.parquet
  Time:   5-10 minutes

Phase 3E.2: Clustering (HDBSCAN)
  ↓
  Input:  artifacts/encoder/session_embeddings.parquet
  Output: artifacts/discovery/labels/
  Time:   3-5 minutes

Phase 3E.3: Persona Synthesis
  ↓
  Input:  Cluster labels + embeddings
  Output: DATA/personas_discovered/registry.json
          DATA/personas_discovered/disc_*.json
  Time:   2-3 minutes

Total: ~2-4 hours
```

---

## ✅ Expected Outputs

After successful completion, you should have:

```
artifacts/
├── encoder/
│   ├── best.ckpt                    # ✓ Trained encoder
│   ├── session_embeddings.parquet   # ✓ Session embeddings
│   └── logs/                        # ✓ Training logs
└── discovery/
    ├── report.md                    # ✓ Quality report
    ├── metrics.json                 # ✓ Separation metrics
    └── labels_text.json             # ✓ Cluster labels

DATA/
├── OPeRA/
│   └── processed/                   # ✓ Parsed OPeRA data
└── personas_discovered/
    ├── registry.json                # ✓ Persona registry
    └── disc_*.json                  # ✓ Individual personas (10-25 files)
```

---

## 🔍 Validation Checklist

Run `make phase-1-3-validate` or manually check:

**Phase 1:**
- [ ] `DATA/OPeRA/processed/` contains .parquet files
- [ ] Files are readable and non-empty

**Phase 2:**
- [ ] `artifacts/encoder/best.ckpt` exists
- [ ] Validation accuracy ≥ 70%
- [ ] Training logs show convergence

**Phase 3:**
- [ ] `DATA/personas_discovered/registry.json` exists
- [ ] 10-25 personas discovered
- [ ] Silhouette score ≥ 0.45
- [ ] Davies-Bouldin ≤ 0.8
- [ ] Noise fraction < 20%

---

## 📝 Command Cheat Sheet

### Full Pipeline
```bash
# AWS execution
make phase-1-3-aws

# Local execution
make phase-1-3-local

# Validate outputs
make phase-1-3-validate
```

### Individual Phases
```bash
# Run Phase 1 only
make phase-1-parse

# Run Phase 2 only (requires Phase 1 complete)
make phase-2-encoder

# Run Phase 3 only (requires Phase 2 complete)
make phase-3-discovery
```

### Check Outputs
```bash
# View discovery report
cat artifacts/discovery/report.md

# List discovered personas
cat DATA/personas_discovered/registry.json | python3 -m json.tool

# Check metrics
cat artifacts/discovery/metrics.json | python3 -m json.tool

# Check encoder performance
tail -20 artifacts/encoder/logs/version_0/metrics.csv
```

### AWS Management
```bash
# List S3 contents
aws s3 ls s3://$TRAINING_S3_BUCKET/phase_1_3/

# Download specific artifacts
aws s3 sync s3://$TRAINING_S3_BUCKET/phase_1_3/<timestamp>/ ./artifacts/

# Check costs
make cost-status
```

---

## 🐛 Troubleshooting

### AWS Issues

**Spot instance failed:**
```bash
export MAX_SPOT_PRICE=0.60  # Increase max price
./run_phase_1_to_3_aws.sh
```

**SSH timeout:**
```bash
# Wait longer (instance may be initializing)
# Or check security group allows SSH (port 22)
```

**S3 permission denied:**
```bash
# Verify bucket access
aws s3 ls s3://$TRAINING_S3_BUCKET/
```

### Local Issues

**CUDA out of memory:**
```bash
# Reduce batch size in CONFIGS/encoder.yaml
# Change from 64 to 32 or 16
```

**Discovery gates fail:**
```bash
# Adjust clustering parameters in CONFIGS/discovery.yaml
# Lower min_cluster_size or min_samples
```

**Missing dependencies:**
```bash
pip install hdbscan umap-learn leidenalg python-igraph pytorch-lightning
```

---

## 📊 Quality Metrics

The pipeline enforces these quality gates:

### Encoder (Phase 2)
- ✓ Next action accuracy: ≥ 70%
- ✓ Validation loss: Converged
- ✓ No NaN gradients

### Discovery (Phase 3)
- ✓ Silhouette score: ≥ 0.45
- ✓ Davies-Bouldin index: ≤ 0.8
- ✓ Calinski-Harabasz: ≥ 100
- ✓ Noise fraction: < 20%
- ✓ Bootstrap stability: ≥ 0.75

All gates are automatically checked. See `artifacts/discovery/report.md` for details.

---

## 🎯 Next Steps After Completion

### 1. Review Outputs
```bash
# Read discovery report
cat artifacts/discovery/report.md

# Inspect personas
ls -la DATA/personas_discovered/
cat DATA/personas_discovered/registry.json
```

### 2. Validate Quality
```bash
# Run validation script
make phase-1-3-validate

# Should output: "✅ ALL VALIDATIONS PASSED"
```

### 3. Enable Discovered Personas (Optional)

Edit `CONFIGS/discovery.yaml`:
```yaml
persona_source: discovered  # or hybrid
use_discovered_personas: true
```

### 4. Proceed to Phase 4

You are now ready for **Phase 4: Multi-turn SFT Dataset Generation**

The Phase 4 workflow will use:
- `DATA/personas_discovered/registry.json`
- `artifacts/encoder/session_embeddings.parquet`

---

## 📚 Additional Resources

- **Complete Guide:** [PHASE_1_TO_3_COMPLETE.md](PHASE_1_TO_3_COMPLETE.md)
- **Project Overview:** [README.md](README.md)
- **AWS Setup:** [AWS_QUICK_REFERENCE.md](AWS_QUICK_REFERENCE.md)
- **End-to-End Workflow:** [END_TO_END_WORKFLOW.md](END_TO_END_WORKFLOW.md)
- **Engineering Spec:** [SPECS/WHAT_IF_SIMULATOR_SPEC.md](SPECS/WHAT_IF_SIMULATOR_SPEC.md)

---

## 🔄 Re-running the Pipeline

### Full re-run (clean slate):
```bash
# Remove previous outputs
rm -rf artifacts/encoder artifacts/discovery
rm -rf DATA/personas_discovered

# Run again
make phase-1-3-aws  # or make phase-1-3-local
```

### Partial re-run:
```bash
# Only re-run Phase 3 (keep encoder)
make phase-3-discovery

# Only re-run Phase 2 & 3 (keep parsed data)
make phase-2-encoder
make phase-3-discovery
```

---

## 💡 Tips for Success

1. **Start with AWS** - More reliable, consistent GPU, reproducible
2. **Monitor progress** - SSH into EC2 to check logs during execution
3. **Backup configs** - Copy `CONFIGS/` before modifying
4. **Validate early** - Run `make phase-1-3-validate` immediately after completion
5. **Review report** - Read `artifacts/discovery/report.md` for insights

---

## 📞 Support

### Common Questions

**Q: Can I skip Phase 1 if I already have parsed data?**
A: Yes! Run `make phase-2-encoder` directly.

**Q: How do I customize discovery parameters?**
A: Edit `CONFIGS/discovery.yaml` before running Phase 3.

**Q: What if quality gates fail?**
A: Review `artifacts/discovery/report.md` for specific issues and adjust clustering parameters.

**Q: Can I use discovered personas immediately?**
A: Yes! Set `use_discovered_personas: true` in `CONFIGS/discovery.yaml`.

---

## ✨ Summary

You now have:
- ✅ Complete AWS execution script (`run_phase_1_to_3_aws.sh`)
- ✅ Complete local execution script (`run_phase_1_to_3_local.sh`)
- ✅ Validation script (`scripts/validate_phase_1_3.py`)
- ✅ Comprehensive documentation (`PHASE_1_TO_3_COMPLETE.md`)
- ✅ Makefile integration (`make phase-1-3-*`)

**Ready to run:**
```bash
make phase-1-3-aws     # AWS mode (recommended)
# or
make phase-1-3-local   # Local mode
```

**Then validate:**
```bash
make phase-1-3-validate
```

**You're all set! 🚀**

---

**Last Updated:** 2025-10-16
**Status:** ✅ Production ready
**Tested:** Dry-run validated
