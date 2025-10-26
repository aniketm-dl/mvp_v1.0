# AWS SSR Training Guide - Darpan Labs OPeRA-SSR-Twin System

## Quick Start (Complete Workflow)

```bash
# 1. Launch AWS Instance & Setup
make launch                    # Launch g5.xlarge spot instance
# Wait for instance to start, note the IP address

# 2. Setup Environment (on EC2)
ssh -i ~/darpan-training.pem ubuntu@<INSTANCE_IP>
cd ~
git clone <YOUR_REPO> mvp_v1.0
cd mvp_v1.0
bash scripts/aws/setup_ssr_training.sh

# 3. Run Complete Pipeline (on EC2)
./darpan.py ssr-pipeline --auto-shutdown

# 4. Download Results (local machine)
make download-ssr
```

## What This Builds

This system creates an **OPeRA-driven behavioral prediction platform** with:

1. **Persona Discovery**: 8-12 data-driven personas from real OPeRA user data
2. **SSR Engine**: Fast (<50ms) semantic similarity rating for choice predictions
3. **Hybrid Twins**: Fusion of SSR (fast) + LLM (explainable) predictions
4. **Evaluation Dashboard**: KS similarity + correlation metrics vs. human data
5. **Streamlit Demo**: Interactive "what-if" scenario testing

## Architecture Overview

```
OPeRA Raw Data (survey, sessions, rationales, outcomes)
    ↓
[02_preprocess_opera.py] → aligned_sequences.jsonl
    ↓
[03_discover_personas.py] → persona_profiles.json (8-12 clusters)
    ↓
[04_train_ssr.py] → ssr_reference.pkl (embedding model)
    ↓
[05_prepare_sft_data.py] → twin training data (JSONL)
    ↓
[06_train_twins.py] → LLM adapters (Mistral-7B LoRA)
    ↓
[hybrid.py] → SSR + LLM fusion
    ↓
[07_evaluate.py] → eval_dashboard.html (KS test, correlation)
    ↓
[08_deploy.py] → Streamlit app + FastAPI
```

## Step-by-Step Implementation

### Phase 1: Data Preparation (Implemented ✅)

**Files Created:**
- `docs/mvp_scope.md` - Complete project specification
- `src/data/opera/alignment.py` - Data alignment module
- `scripts/02_preprocess_opera.py` - Preprocessing pipeline

**What It Does:**
- Merges OPeRA survey + sessions + rationales + outcomes
- Builds 12-D persona vectors (OCEAN + psychographics + demographics)
- Extracts SSR training pairs (persona, stimulus, likert_score)

**Expected Outputs:**
```
DATA/OPeRA/processed/
  ├── aligned_sequences.jsonl       # Session sequences
  ├── persona_features.parquet      # 12-D feature vectors
  └── ssr_training_pairs.jsonl      # SSR training data
```

**Run It:**
```bash
python scripts/02_preprocess_opera.py \
  --survey DATA/OPeRA/raw/opera_survey.parquet \
  --sessions DATA/OPeRA/raw/sample_sessions.jsonl \
  --rationales DATA/OPeRA/raw/opera_rationales.jsonl \
  --outcomes DATA/OPeRA/raw/opera_outcomes.jsonl \
  --out-dir DATA/OPeRA/processed
```

### Phase 2: Persona Discovery (To Implement)

**Files Needed:**
- `src/personas/discovery.py` - UMAP + HDBSCAN clustering
- `src/personas/profiler.py` - Extract OCEAN scores, tags
- `scripts/03_discover_personas.py` - Orchestration script

**What It Will Do:**
- Load `persona_features.parquet` (12-D vectors)
- UMAP: Reduce to 2-D for visualization
- HDBSCAN: Find 8-12 density-based clusters
- LLM summarization: Generate persona descriptions (GPT-4o-mini)

**Expected Output:**
```json
{
  "personas": [
    {
      "id": "p01_deal_seeker",
      "label": "The Deal Seeker",
      "description": "Price-sensitive, waits for sales, compares prices",
      "cluster_id": 0,
      "size": 1523,
      "centroid": [0.2, -0.5, ...],
      "psychographic_tags": ["thrifty", "patient", "analytical"],
      "ocean_scores": {"O": 0.6, "C": 0.8, "E": 0.4, "A": 0.5, "N": 0.3}
    },
    ...
  ]
}
```

**Implementation Priority:** HIGH (blocks SSR training)

### Phase 3: SSR Engine (To Implement)

**Files Needed:**
- `src/ssr/embedder.py` - sentence-transformers wrapper
- `src/ssr/trainer.py` - Contrastive loss + regression head
- `src/ssr/inference.py` - Predict Likert distributions
- `scripts/04_train_ssr.py` - Training script

**What It Will Do:**
- Fine-tune `all-MiniLM-L6-v2` on SSR training pairs
- Learn: (persona_vec, stimulus_text) → P(Likert=1..5)
- Save: `models/ssr_reference.pkl` (~38MB)

**Training Config:**
```yaml
ssr:
  base_model: "sentence-transformers/all-MiniLM-L6-v2"
  embedding_dim: 384
  epochs: 10
  batch_size: 32
  learning_rate: 2e-5
  loss: "contrastive"  # or "triplet"
  regression_head: true  # Predict Likert distribution
```

**Expected Performance:**
- Inference: <50ms per prediction
- Correlation (predicted vs. actual): ≥0.70
- Generalizes to unseen ad copy / prices

**Implementation Priority:** HIGH (core innovation)

### Phase 4: Hybrid Twin System (To Implement)

**Files Needed:**
- `src/twins/hybrid.py` - Fuse SSR + LLM predictions
- `src/api/endpoints/ssr.py` - New API endpoint

**What It Will Do:**
```python
# Fast path: SSR (embedding-based)
p_ssr = ssr_model.predict(persona_id, stimulus)  # <50ms

# Slow path: LLM twin (reasoning-based)
p_llm, reason = llm_twin.decide(persona_id, candidates, context)  # 1-2s

# Fusion
alpha = 0.6  # Configurable weight
p_final = alpha * p_ssr + (1 - alpha) * p_llm
```

**API Endpoints:**
```python
POST /ssr/predict
{
  "persona_id": "p01",
  "stimulus": "Free shipping on all orders"
}
→ {"mean": 3.8, "distribution": [0.05, 0.10, 0.25, 0.40, 0.20]}

POST /simulate  # Enhanced with SSR
{
  "user_id": "u123",
  "scenarios": [...],
  "use_ssr": true,  # New parameter
  "ssr_alpha": 0.6  # Fusion weight
}
```

**Implementation Priority:** MEDIUM (integrates SSR with existing system)

### Phase 5: Evaluation (To Implement)

**Files Needed:**
- `src/evaluation/ks_test.py` - Kolmogorov-Smirnov similarity
- `src/evaluation/correlation.py` - Spearman correlation
- `src/evaluation/dashboard.py` - Plotly dashboard generator
- `scripts/07_evaluate.py` - Orchestration script

**What It Will Do:**
- Compare predicted vs. actual distributions (KS test)
- Measure rating prediction accuracy (correlation)
- Generate `reports/eval_dashboard.html`

**Metrics:**
- **KS Similarity ≥ 0.80**: Predicted distribution matches human behavior
- **Spearman ≥ 0.70**: Rating predictions align with actual ratings
- **Silhouette ≥ 0.35**: Personas are well-separated

**Implementation Priority:** HIGH (validation is critical for MVP)

### Phase 6: Streamlit Demo (To Implement)

**Files Needed:**
- `src/app/main.py` - Streamlit entry point
- `src/app/components/persona_selector.py` - UI component
- `src/app/components/scenario_builder.py` - Input forms
- `src/app/components/results_viewer.py` - Visualization
- `src/app/utils/api_client.py` - FastAPI client

**What It Will Do:**
```
┌──────────────────────────────────────────────┐
│  Darpan Labs - Digital Twin Simulator       │
├──────────────────────────────────────────────┤
│ Select Persona: [The Deal Seeker ▼]         │
│                                               │
│ Scenario Configuration:                       │
│   Base Price: [$799.00          ]            │
│   Promo:      [✓] 20% off                    │
│   Delivery:   [2 days           ]            │
│   Ad Copy:    [Limited time offer!]          │
│                                               │
│  [Run Simulation]                             │
│                                               │
│ Results:                                      │
│   Predicted Choice: Laptop A (67% prob)      │
│   Explanation: "Best specs for the price,    │
│                and the 20% discount makes    │
│                it a great deal."             │
│                                               │
│   Comparison:                                 │
│   • Base scenario: 50%                        │
│   • With promo: 67% (+17% lift)              │
│                                               │
│   [Distribution Chart]                        │
│    Option A: ████████████ 67%                │
│    Option B: ████ 20%                        │
│    Option C: ██ 13%                          │
└──────────────────────────────────────────────┘
```

**Launch:**
```bash
streamlit run src/app/main.py
# Opens at http://localhost:8501
```

**Implementation Priority:** MEDIUM (demo-critical but not training-critical)

## AWS Training Configuration

### Instance Recommendations

| Instance Type | GPU | VRAM | $/hour (spot) | Use Case |
|--------------|-----|------|---------------|----------|
| g4dn.xlarge  | T4  | 16GB | $0.18 | Budget (SSR only) |
| g5.xlarge    | A10G| 24GB | $0.35 | Recommended (SSR + LLM) |
| g5.2xlarge   | A10G| 24GB | $0.50 | Parallel training |

### Training Time Estimates

| Task | Duration | Cost (g5.xlarge) |
|------|----------|------------------|
| Preprocess OPeRA | 5-10 min | $0.03 |
| Discover Personas | 10-15 min | $0.09 |
| Train SSR | 30-45 min | $0.35 |
| Train 8-12 LLM Twins | 1.5-2 hrs | $0.70-1.00 |
| Evaluate | 5-10 min | $0.06 |
| **Total** | **~3 hours** | **~$1.50** |

### Storage Requirements

- **EBS Volume**: 150GB gp3 (100 GB base + 50 GB for models)
- **S3 Bucket**: 2-3 GB for trained models + data
- **Cost**: ~$0.10/day storage

## AWS Scripts (To Create)

### 1. setup_ssr_training.sh

```bash
#!/bin/bash
# Setup EC2 instance for SSR + LLM training

# Install system dependencies
sudo apt-get update && sudo apt-get install -y git git-lfs python3.10 python3-pip

# Clone repo
cd ~
git clone <REPO_URL> mvp_v1.0
cd mvp_v1.0

# Setup Python environment
python3.10 -m venv venv
source venv/bin/activate
pip install -e .

# Configure AWS CLI
aws configure

# Download OPeRA data (if not in repo)
make dataset-opera

echo "✅ Setup complete! Ready to train."
```

### 2. train_ssr_pipeline.sh

```bash
#!/bin/bash
# Run complete SSR + LLM training pipeline

set -e

source venv/bin/activate
cd ~/mvp_v1.0

# Phase 1: Preprocess OPeRA
echo "Step 1/6: Preprocessing OPeRA data..."
python scripts/02_preprocess_opera.py

# Phase 2: Discover Personas
echo "Step 2/6: Discovering personas..."
python scripts/03_discover_personas.py

# Phase 3: Train SSR
echo "Step 3/6: Training SSR model..."
python scripts/04_train_ssr.py

# Phase 4: Prepare Twin Data
echo "Step 4/6: Preparing twin training data..."
python scripts/05_prepare_sft_data.py

# Phase 5: Train LLM Twins
echo "Step 5/6: Training LLM twins (this takes 1.5-2 hours)..."
python scripts/aws/train_production.py --personas-from models/persona_profiles.json

# Phase 6: Evaluate
echo "Step 6/6: Evaluating models..."
python scripts/07_evaluate.py

# Sync to S3
echo "Syncing models to S3..."
aws s3 sync models/ s3://$TRAINING_S3_BUCKET/models/
aws s3 sync artifacts/ s3://$TRAINING_S3_BUCKET/artifacts/
aws s3 sync reports/ s3://$TRAINING_S3_BUCKET/reports/

echo "✅ Training pipeline complete!"

# Auto-shutdown if requested
if [ "$AUTO_SHUTDOWN" = "true" ]; then
  echo "Auto-shutting down in 5 minutes..."
  sudo shutdown -h +5
fi
```

### 3. download_ssr_models.sh (local machine)

```bash
#!/bin/bash
# Download trained SSR models + LLM adapters from S3

set -e

BUCKET=${TRAINING_S3_BUCKET:-darpan-training-$(whoami)}

echo "Downloading from S3: $BUCKET"

# Download SSR model
aws s3 sync s3://$BUCKET/models/ models/

# Download LLM adapters
aws s3 sync s3://$BUCKET/artifacts/llm_adapters/ artifacts/llm_adapters/

# Download evaluation reports
aws s3 sync s3://$BUCKET/reports/ reports/

echo "✅ Download complete!"
```

## Makefile Targets (To Add)

```makefile
##@ SSR Training Pipeline

ssr-pipeline: ## Run complete SSR training pipeline on EC2
	bash scripts/aws/train_ssr_pipeline.sh

ssr-preprocess: ## Preprocess OPeRA data
	python scripts/02_preprocess_opera.py

ssr-discover: ## Discover personas from OPeRA
	python scripts/03_discover_personas.py

ssr-train: ## Train SSR model
	python scripts/04_train_ssr.py

ssr-evaluate: ## Evaluate SSR + hybrid predictions
	python scripts/07_evaluate.py

download-ssr: ## Download SSR models from S3
	bash scripts/aws/download_ssr_models.sh

##@ Streamlit Demo

app-demo: ## Start Streamlit demo app
	streamlit run src/app/main.py

app-deploy: ## Deploy FastAPI + Streamlit together
	python scripts/08_deploy.py
```

## Critical Implementation Tasks

### Priority 1 (Must-Have for AWS Training)

1. ✅ **MVP Scope Doc** (`docs/mvp_scope.md`)
2. ✅ **OPeRA Alignment** (`src/data/opera/alignment.py`)
3. ✅ **Preprocessing Script** (`scripts/02_preprocess_opera.py`)
4. ⏳ **Persona Discovery** (`src/personas/discovery.py` + `scripts/03_discover_personas.py`)
5. ⏳ **SSR Trainer** (`src/ssr/trainer.py` + `scripts/04_train_ssr.py`)
6. ⏳ **SSR Inference** (`src/ssr/inference.py`)
7. ⏳ **Evaluation Module** (`src/evaluation/ks_test.py` + `scripts/07_evaluate.py`)
8. ⏳ **AWS Training Scripts** (`scripts/aws/train_ssr_pipeline.sh`)

### Priority 2 (Should-Have)

9. Hybrid Twin System (`src/twins/hybrid.py`)
10. SSR API Endpoint (`src/api/endpoints/ssr.py`)
11. Streamlit App (`src/app/main.py` + components)
12. Unit Tests (`TESTS/test_ssr_*.py`)

### Priority 3 (Nice-to-Have)

13. Evaluation Dashboard (`src/evaluation/dashboard.py`)
14. Deployment Script (`scripts/08_deploy.py`)
15. Jupyter Notebooks (`notebooks/01_opera_eda.ipynb`)

## Validation Checklist

Before deploying to AWS, ensure:

- [ ] `pyproject.toml` has all dependencies (sentence-transformers, streamlit, etc.)
- [ ] `DATA/OPeRA/raw/` contains sample data (for testing)
- [ ] `scripts/02_preprocess_opera.py` runs locally without errors
- [ ] AWS credentials are configured (`aws configure`)
- [ ] S3 bucket exists (`aws s3 mb s3://darpan-training-$(whoami)`)
- [ ] SSH key pair exists (`~/darpan-training.pem`)

## Next Steps

1. **Complete Persona Discovery** (2-3 hours coding)
   - Implement UMAP + HDBSCAN clustering
   - LLM summarization for persona descriptions

2. **Complete SSR Trainer** (4-6 hours coding)
   - sentence-transformers fine-tuning
   - Contrastive loss + regression head
   - Training loop + validation

3. **Create AWS Training Scripts** (2 hours)
   - `setup_ssr_training.sh`
   - `train_ssr_pipeline.sh`
   - Update Makefile

4. **Test End-to-End on AWS** (1 hour)
   - Launch instance
   - Run full pipeline
   - Validate outputs

5. **Build Streamlit Demo** (3-4 hours)
   - UI components
   - API integration
   - Deploy locally

**Total Implementation Time: ~15-20 hours**

## Questions for User

Before proceeding with full implementation:

1. **OPeRA Data**: Do you have real OPeRA dataset files, or should I create synthetic data generators for testing?

2. **LLM for Persona Summarization**: Should persona discovery use GPT-4o-mini (API cost ~$0.10), or local Mistral-7B (slower but free)?

3. **SSR Model Size**: Prefer lightweight (`all-MiniLM-L6-v2`, 80MB) or powerful (`e5-large-v2`, 1.3GB)?

4. **Deployment Target**: MVP demo-only (local Streamlit) or production-ready (Docker + load balancer)?

5. **Training Budget**: Comfortable with $1-2 per full training run (spot instances)?

---

**Status**: Foundation complete (data pipeline ✅, dependencies ✅, architecture ✅)
**Next**: Implement persona discovery + SSR trainer for full AWS runnable system

**Estimated Time to AWS-Trainable**: 8-12 hours coding + 3 hours AWS testing
