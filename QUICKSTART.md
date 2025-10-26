# OPeRA-SSR Quick Start Guide

This guide will get you from zero to a working SSR system in under 2 hours.

---

## Prerequisites

```bash
# Python 3.9+
python --version

# Git
git --version

# AWS CLI (for AWS training)
aws --version
```

---

## Option 1: Local Training (Recommended for Development)

### Step 1: Install Dependencies

```bash
cd mvp_v1.0
pip install -e .
```

**Expected time:** 2-3 minutes

### Step 2: Set OpenAI API Key

```bash
export OPENAI_API_KEY='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'
```

### Step 3: Download OPeRA Dataset

```bash
python scripts/01_download_opera.py
```

**Expected time:** 5-10 minutes  
**Output:** `DATA/OPeRA/raw/` directory with 3 parquet files

### Step 4: Preprocess Data

```bash
python scripts/02_preprocess_opera.py \
  --survey DATA/OPeRA/raw/opera_users.parquet \
  --sessions DATA/OPeRA/raw/sample_sessions.jsonl \
  --rationales DATA/OPeRA/raw/opera_rationales.jsonl \
  --outcomes DATA/OPeRA/raw/opera_outcomes.jsonl \
  --out-dir DATA/OPeRA/processed
```

**Expected time:** 10-15 minutes  
**Output:**
- `aligned_sequences.jsonl`
- `persona_features.parquet`
- `ssr_training_pairs.jsonl`

### Step 5: Discover Personas

```bash
python scripts/03_discover_personas.py \
  --features DATA/OPeRA/processed/persona_features.parquet \
  --out models/persona_profiles.json \
  --use-llm-summary
```

**Expected time:** 15-20 minutes  
**Output:** `models/persona_profiles.json` with 8-12 personas

### Step 6: Train SSR Model

```bash
python scripts/04_train_ssr.py \
  --training-pairs DATA/OPeRA/processed/ssr_training_pairs.jsonl \
  --out models/ssr_reference \
  --embedding-epochs 10 \
  --regression-epochs 20
```

**Expected time:** 20-30 minutes  
**Output:** `models/ssr_reference/` directory

### Step 7: Evaluate Model

```bash
python scripts/07_evaluate.py \
  --ssr-model models/ssr_reference \
  --test-data DATA/OPeRA/processed/aligned_sequences.jsonl \
  --out-dir reports
```

**Expected time:** 5-10 minutes  
**Output:**
- `reports/evaluation_results.json`
- `reports/evaluation_dashboard.html`

### Step 8: Launch Demo

```bash
streamlit run src/app/main.py
```

**Access:** http://localhost:8501

---

## Option 2: AWS Training (One-Command)

### Prerequisites

```bash
export OPENAI_API_KEY='sk-proj-...'
export HF_TOKEN='hf_...'  # Get from huggingface.co/settings/tokens
export TRAINING_S3_BUCKET='darpan-training-USERNAME'
```

### Launch Training Pipeline

```bash
bash scripts/aws/train_complete_pipeline.sh --auto-shutdown
```

**Expected time:** ~1.5 hours  
**Cost:** ~$0.50 (g5.xlarge spot instance)

**What it does:**
1. Downloads OPeRA data
2. Preprocesses & aligns sequences
3. Discovers personas (UMAP + HDBSCAN + GPT-4o)
4. Trains SSR model
5. Evaluates on test set
6. Syncs to S3
7. Auto-shuts down instance

### Download Results

```bash
aws s3 sync s3://$TRAINING_S3_BUCKET/models/ models/
aws s3 sync s3://$TRAINING_S3_BUCKET/reports/ reports/
```

---

## Verification Checklist

After training, verify:

- [ ] `models/persona_profiles.json` exists with 8-12 personas
- [ ] `models/ssr_reference/embedding_model/` directory exists
- [ ] `models/ssr_reference/regression_head.pt` file exists
- [ ] `reports/evaluation_results.json` shows Spearman ≥ 0.70
- [ ] Streamlit app loads without errors

---

## Quick Test

```python
from src.ssr.inference import SSRInference

ssr = SSRInference("models/ssr_reference")

prediction = ssr.predict("Free shipping on all orders over $50")
print(prediction)

# Expected output:
# {
#   'mean': 3.8,
#   'std': 0.9,
#   'mode': 4,
#   'distribution': [0.05, 0.10, 0.25, 0.40, 0.20]
# }
```

---

## Common Issues

### Issue: "OPENAI_API_KEY not set"

**Solution:**
```bash
export OPENAI_API_KEY='sk-proj-...'
```

### Issue: "HuggingFace dataset not found"

**Solution:**
```bash
# Retry download with --force flag
python scripts/01_download_opera.py --force
```

### Issue: "Too few training pairs"

**Solution:**
```bash
# Lower min-steps threshold
python scripts/02_preprocess_opera.py --min-steps 2
```

### Issue: "Silhouette score too low (<0.35)"

**Solution:**
```bash
# Adjust HDBSCAN parameters
python scripts/03_discover_personas.py --min-cluster-size 30
```

### Issue: "Correlation below target"

**Solution:**
```bash
# Train longer
python scripts/04_train_ssr.py --embedding-epochs 15 --regression-epochs 30

# Or use larger base model
python scripts/04_train_ssr.py --base-model sentence-transformers/all-mpnet-base-v2
```

---

## Next Steps

1. **Explore Personas:**
   - Open `models/persona_profiles.json`
   - View in Streamlit Persona Explorer tab

2. **Test Scenarios:**
   - Use Streamlit demo to test e-commerce scenarios
   - Compare multiple variants

3. **Review Evaluation:**
   - Open `reports/evaluation_dashboard.html` in browser
   - Check correlation scatter plots

4. **Integrate API:**
   - See `src/api/service.py` for FastAPI endpoint
   - Use `SSRInference` class for programmatic access

---

## Documentation

- `IMPLEMENTATION_SUMMARY.md` - Complete system overview
- `docs/mvp_scope.md` - Detailed specification
- `IMPLEMENTATION_COMPLETE.md` - Step-by-step completion guide
- `AWS_SSR_TRAINING_GUIDE.md` - AWS training details

---

## Support

**Common Commands:**

```bash
# Re-run evaluation
python scripts/07_evaluate.py

# Test inference
python -c "from src.ssr.inference import SSRInference; ssr = SSRInference('models/ssr_reference'); print(ssr.predict('Free shipping'))"

# Launch demo
streamlit run src/app/main.py

# Run tests
pytest TESTS/ -v
```

**Expected Performance:**
- Inference: <50ms per prediction
- Spearman correlation: ≥ 0.70
- KS similarity: ≥ 0.80
- MAE: < 0.50

---

**Ready to Go!** 🚀

If all steps completed successfully, you now have a fully functional OPeRA-SSR system.
