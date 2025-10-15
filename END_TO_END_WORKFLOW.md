# End-to-End Workflow: Data Prep → Training → Chat with Personas

**Complete execution order for Darpan Labs MVP v1.0**

---

## 📋 Overview

This document provides the **exact order** of files and commands to run from data preparation through training to chatting with personas.

---

## 🎯 Three Execution Paths

### Path 1: **Full Automation (Recommended)**
Single command runs everything on AWS.

### Path 2: **Local Training**
Train on your local machine if you have a GPU.

### Path 3: **Step-by-Step Manual**
Understand each step by running commands individually.

---

## Path 1: Full Automation (AWS) ⭐ RECOMMENDED

### Prerequisites
```bash
# Verify AWS setup
aws sts get-caller-identity
export TRAINING_S3_BUCKET=darpan-training-aniketniranjanmishra

# Navigate to project
cd "/Users/aniketniranjanmishra/Desktop/Darpan Labs/mvp_v1.0"
source venv/bin/activate
```

### Single Command Workflow
```bash
make workflow
```

This runs the complete pipeline:
1. Launch AWS GPU instance (g5.xlarge)
2. Setup environment on instance
3. Download Opera dataset
4. Generate personas
5. Prepare training data
6. Train all 18+ persona adapters
7. Upload to S3
8. Download trained models
9. Interactive chat

### Estimated Time & Cost
- **Time:** 2-3 hours total
- **Cost:** ~$0.60-0.75
- **Mostly automated:** Minimal interaction needed

---

## Path 2: Local Training (GPU Required)

### Prerequisites
- **GPU:** 16GB+ VRAM (NVIDIA)
- **Disk:** 100GB+ free space
- **Time:** 3-4 hours

### Step-by-Step Local Execution

#### 1. Download Opera Dataset
```bash
make dataset-opera
# Script: scripts/download_opera_dataset.py
# Output: DATA/opera/opera_events.parquet
# Time: ~5 minutes
```

#### 2. Discover Personas from Data
```bash
make personas-discover
# Script: scripts/opera/discover_personas_from_opera.py
# Output: DATA/personas.json (18+ personas)
# Time: ~2 minutes
```

Verify:
```bash
make personas-list
# Should show 18-24 personas with IDs and labels
```

#### 3. Prepare Training Data (SFT)
```bash
make prep-opera-sft
# Script: scripts/opera/prepare_sft_from_opera.py
# Output: DATA/sft/{twin_id}.jsonl for each persona
# Time: ~3 minutes
```

Verify:
```bash
ls -lh DATA/sft/
# Should see 18+ .jsonl files, each 50-200KB
```

#### 4. Train All Persona Adapters
```bash
make train-local-all
# Script: scripts/train_all_adapters.py
# → Calls: scripts/train_llm_persona_sft.py for each twin
# Output: artifacts/llm_adapters/{twin_id}/adapter_model.safetensors
# Time: ~3-4 hours (depends on GPU)
```

Progress monitoring:
```bash
# In another terminal
watch -n 30 'ls artifacts/llm_adapters/*/adapter_model.safetensors | wc -l'
# Should count from 0 to 18+
```

#### 5. Distill Policy Heads (Optional - for fast inference)
```bash
# Generate examples from LLM twins
python scripts/generate_distill_data_from_llm.py --out DATA/distill_llm.jsonl
# Time: ~10 minutes

# Train policy heads from examples
python scripts/distill_policies.py \
  --input DATA/distill_llm.jsonl \
  --outdir artifacts/policy_heads \
  --buckets 16 \
  --temp 1.0
# Time: ~2 minutes
# Output: artifacts/policy_heads/{twin_id}_head.json
```

#### 6. Evaluate Separation Quality
```bash
make gate
# Script: scripts/eval_separation.py
# Checks: Silhouette ≥ 0.35, JSD ≥ 0.10, ARI ≥ 0.80
# Time: ~1 minute
```

#### 7. Start API Server
```bash
make serve
# Starts: uvicorn src.api.service:app on http://localhost:8000
# API Docs: http://localhost:8000/docs
```

#### 8. Chat with Personas
```bash
# In another terminal
make chat
# Script: interact_cli.py
# Interactive: Choose persona and chat
```

Or use the CLI directly:
```bash
make interact
# Script: interact_cli.py
```

---

## Path 3: Step-by-Step Manual Execution

### Phase A: Environment Setup

```bash
# 1. Activate environment
cd "/Users/aniketniranjanmishra/Desktop/Darpan Labs/mvp_v1.0"
source venv/bin/activate

# 2. Verify dependencies
python -c "import torch; print('PyTorch:', torch.__version__)"
python -c "import transformers; print('Transformers:', transformers.__version__)"

# 3. Set environment variables
export TRAINING_S3_BUCKET=darpan-training-aniketniranjanmishra
```

### Phase B: Data Preparation

#### B1. Download Opera Dataset
```bash
python scripts/download_opera_dataset.py
```

**What it does:**
- Downloads Opera e-commerce browsing dataset
- Saves to `DATA/opera/opera_events.parquet`
- ~500MB compressed

**Output:**
```
DATA/opera/
└── opera_events.parquet
```

#### B2. Process Opera Data (Optional - for persona discovery)

```bash
# Extract user text for clustering
python scripts/opera/collect_user_text.py

# Build OCEAN personality scores
python scripts/opera/build_ocean_scores_v2.py

# Attach OCEAN to user actions
python scripts/opera/attach_ocean_to_actions.py

# Build user psychographic tags
python scripts/opera/build_user_tags.py

# Cluster users into personas
python scripts/opera/cluster_ocean_to_personas.py
```

**Or use the all-in-one command:**
```bash
python scripts/opera/discover_personas_from_opera.py \
  --augment \
  --min_rows 200 \
  --max_personas 24
```

**Output:**
```
DATA/personas.json
```

#### B3. Prepare SFT Training Data
```bash
python scripts/opera/prepare_sft_from_opera.py \
  --cfg CONFIGS/opera/fields.yaml
```

**What it does:**
- Reads Opera dataset
- Routes examples to personas by psychographic tags
- Creates JSONL training files (max 2000 examples per persona)

**Output:**
```
DATA/sft/
├── k0.jsonl
├── k1.jsonl
├── k2.jsonl
├── ... (18+ files)
└── ko_12345.jsonl
```

### Phase C: Model Training

#### C1. Train Individual Persona
```bash
python scripts/train_llm_persona_sft.py \
  --twin_id k0 \
  --base_model mistralai/Mistral-7B-Instruct-v0.2 \
  --epochs 1 \
  --max_length 512 \
  --lr 2e-4
```

**What it does:**
- Loads base model (Mistral-7B)
- Loads training data from `DATA/sft/k0.jsonl`
- Trains LoRA adapter (rank=8, alpha=16)
- Saves to `artifacts/llm_adapters/k0/`

**Output:**
```
artifacts/llm_adapters/k0/
├── adapter_config.json
├── adapter_model.safetensors
└── README.md
```

**Time:** ~10-15 minutes per persona

#### C2. Train All Personas (Sequential)
```bash
python scripts/train_all_adapters.py
```

**What it does:**
- Reads all personas from `DATA/personas.json`
- Trains each persona adapter sequentially
- Skips if training data doesn't exist
- Logs progress and errors

**Output:**
```
artifacts/llm_adapters/
├── k0/
├── k1/
├── k2/
├── ... (18+ directories)
└── ko_12345/
```

**Time:** ~3-4 hours for 18 personas

### Phase D: Policy Head Distillation (Optional)

#### D1. Generate Training Data from LLM Twins
```bash
python scripts/generate_distill_data_from_llm.py \
  --out DATA/distill_llm.jsonl \
  --num_examples 1000
```

**What it does:**
- Queries each LLM twin with synthetic scenarios
- Records decisions and probabilities
- Creates dataset for policy head training

**Output:**
```
DATA/distill_llm.jsonl
```

#### D2. Train Policy Heads
```bash
python scripts/distill_policies.py \
  --input DATA/distill_llm.jsonl \
  --outdir artifacts/policy_heads \
  --buckets 16 \
  --temp 1.0
```

**What it does:**
- Trains linear regression heads per twin
- Learns to predict probabilities from features
- Fast inference path (<200ms vs ~1s for LLM)

**Output:**
```
artifacts/policy_heads/
├── k0_head.json
├── k1_head.json
├── ... (18+ files)
└── ko_12345_head.json
```

### Phase E: Evaluation & Quality Checks

#### E1. Separation Metrics
```bash
python scripts/eval_separation.py
```

**What it does:**
- Computes silhouette score (cluster separation)
- Computes Jensen-Shannon divergence (probability difference)
- Computes Adjusted Rand Index (stability)

**Expected output:**
```
✅ Silhouette: 0.42 (≥ 0.35)
✅ Mean JSD: 0.15 (≥ 0.10)
✅ ARI: 0.85 (≥ 0.80)
All gates passed!
```

#### E2. Counterfactual Fairness
```bash
pytest TESTS/test_counterfactual_fairness.py -v
```

**What it does:**
- Tests that demographic changes don't unfairly shift predictions
- Ensures fairness across protected attributes

#### E3. Guard Tests
```bash
pytest TESTS/test_reason_guard.py -v
```

**What it does:**
- Validates reason quality (max 20 tokens)
- Checks for hallucinated numbers
- Verifies context grounding

### Phase F: Deployment

#### F1. Start API Server (Development)
```bash
uvicorn src.api.service:app \
  --reload \
  --host 0.0.0.0 \
  --port 8000
```

**Endpoints available:**
- `GET /health` - Health check
- `GET /twin/personas` - List all personas
- `POST /twin/chat` - Chat with specific twin
- `POST /twin/decide` - Get twin decision
- `POST /match` - Match user to primary twin
- `POST /simulate` - Run what-if scenarios

#### F2. Start API Server (Production)
```bash
uvicorn src.api.service:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
```

#### F3. Docker Deployment
```bash
# Build image
docker build -t darpan-mvp:latest .

# Run container
docker run -d \
  -p 8000:8000 \
  -e TRAINING_S3_BUCKET=darpan-training-aniketniranjanmishra \
  darpan-mvp:latest
```

### Phase G: Interactive Chat

#### G1. CLI Chat
```bash
python interact_cli.py
```

**What it does:**
- Lists all available personas
- Allows you to select one
- Interactive chat session
- Type 'back' to switch personas, 'quit' to exit

#### G2. Programmatic Chat
```python
from src.reasoning.llm_twin import chat_with_twin

reply = chat_with_twin(
    twin_id="k0",
    history=[],
    prompt="What do you think about this $1200 laptop?",
    conditioning={"psychographic_tags": ["budget_conscious"]}
)
print(reply)
```

#### G3. API Chat
```bash
curl -X POST http://localhost:8000/twin/chat \
  -H "Content-Type: application/json" \
  -d '{
    "twin_id": "k0",
    "history": [],
    "prompt": "What do you think about this $1200 laptop?",
    "conditioning": {
      "psychographic_tags": ["budget_conscious"]
    }
  }'
```

---

## 📊 File Execution Order Summary

### **Complete End-to-End Order**

```
1. scripts/download_opera_dataset.py
   ↓
2. scripts/opera/discover_personas_from_opera.py
   ↓
3. scripts/opera/prepare_sft_from_opera.py
   ↓
4. scripts/train_all_adapters.py
   ├→ scripts/train_llm_persona_sft.py (for each twin)
   ↓
5. scripts/generate_distill_data_from_llm.py (optional)
   ↓
6. scripts/distill_policies.py (optional)
   ↓
7. scripts/eval_separation.py
   ↓
8. uvicorn src.api.service:app
   ↓
9. interact_cli.py
```

---

## 🗂️ Directory Structure After Completion

```
mvp_v1.0/
├── DATA/
│   ├── opera/
│   │   └── opera_events.parquet         # Raw dataset
│   ├── personas.json                     # 18+ persona definitions
│   ├── sft/                              # Training data
│   │   ├── k0.jsonl
│   │   ├── k1.jsonl
│   │   └── ... (18+ files)
│   └── distill_llm.jsonl                 # Policy head training data
│
├── artifacts/
│   ├── llm_adapters/                     # Trained LoRA adapters
│   │   ├── k0/
│   │   │   ├── adapter_config.json
│   │   │   └── adapter_model.safetensors
│   │   ├── k1/
│   │   └── ... (18+ directories)
│   └── policy_heads/                     # Fast inference heads
│       ├── k0_head.json
│       ├── k1_head.json
│       └── ... (18+ files)
│
└── CONFIGS/
    ├── serve/
    │   ├── api.yaml
    │   ├── llm.yaml
    │   └── policy.yaml
    └── opera/
        └── fields.yaml
```

---

## 🚦 Checkpoints & Verification

### After Each Phase

**Phase B (Data Prep):**
```bash
ls DATA/personas.json           # Should exist
ls DATA/sft/*.jsonl | wc -l     # Should be 18+
```

**Phase C (Training):**
```bash
ls artifacts/llm_adapters/*/adapter_model.safetensors | wc -l  # Should be 18+
```

**Phase D (Policy Heads):**
```bash
ls artifacts/policy_heads/*.json | wc -l  # Should be 18+
```

**Phase E (Evaluation):**
```bash
make gate  # All gates should pass
```

**Phase F (Deployment):**
```bash
curl http://localhost:8000/health  # Should return {"status": "ok"}
```

**Phase G (Chat):**
```bash
make chat  # Should show interactive prompt
```

---

## ⏱️ Time Estimates

| Phase | Local (GPU) | AWS (g5.xlarge) |
|-------|-------------|-----------------|
| Data Prep | 10 min | 10 min |
| Training (18 personas) | 3-4 hours | 90 min |
| Policy Heads | 15 min | 15 min |
| Evaluation | 5 min | 5 min |
| **Total** | **4-5 hours** | **2 hours** |

---

## 💰 Cost Estimates

### AWS Training
- **Instance:** g5.xlarge spot (~$0.35/hr)
- **Duration:** ~2 hours
- **Total:** ~$0.70

### S3 Storage
- **Size:** ~400MB (18 adapters)
- **Cost:** ~$0.02/month

### Local Training
- **Cost:** $0 (uses your GPU)
- **Time:** 2x longer than AWS

---

## 🐛 Troubleshooting

### Common Issues

**Issue: "No module named 'src.models'"**
```bash
# Missing src/models directory
# See PROJECT_STATUS.md for details
```

**Issue: "DATA/personas.json not found"**
```bash
# Run persona discovery first
make personas-discover
```

**Issue: "CUDA out of memory"**
```bash
# Reduce batch size in scripts/train_llm_persona_sft.py
# Or use smaller model (gpt2 instead of Mistral-7B)
```

**Issue: "Training is slow"**
```bash
# Check GPU usage
nvidia-smi
# Should see 80-100% utilization
```

---

## 📚 Additional Resources

- **Full Documentation:** [README.md](README.md)
- **AWS Setup:** [AWS_SETUP_COMPLETE.md](AWS_SETUP_COMPLETE.md)
- **Project Status:** [PROJECT_STATUS.md](PROJECT_STATUS.md)
- **API Schemas:** [API/SCHEMAS.md](API/SCHEMAS.md)
- **Engineering Spec:** [SPECS/WHAT_IF_SIMULATOR_SPEC.md](SPECS/WHAT_IF_SIMULATOR_SPEC.md)

---

**Last Updated:** 2025-10-14
**Status:** ✅ Complete workflow documented
**Tested:** AWS Path (automated)
