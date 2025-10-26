# Quick Start: Train OPeRA-SSR-Twin System on AWS

## Prerequisites

1. **AWS Account** with GPU quota (g5.xlarge or g4dn.xlarge)
2. **S3 Bucket** for model storage
3. **OpenAI API Key** (for persona summarization with GPT-4o-mini)
4. **HuggingFace Token** (for downloading base models)

## 1-Command AWS Training

```bash
# On local machine
make launch                    # Launches EC2 instance
# Note the instance IP

# On EC2 instance (after SSH)
export OPENAI_API_KEY="sk-..."
export HF_TOKEN="hf_..."
export TRAINING_S3_BUCKET="darpan-training-$(whoami)"

# Run complete pipeline (3-4 hours)
bash scripts/aws/train_complete_pipeline.sh
```

## Step-by-Step AWS Training

### Phase 1: Launch & Setup (10 minutes)

```bash
# Local machine
cd ~/Desktop/Darpan\ Labs/mvp_v1.0

# Launch instance
make launch
# Output: Instance i-xxxxx launched at IP: 52.x.x.x

# SSH to instance
ssh -i ~/darpan-training.pem ubuntu@52.x.x.x

# On EC2: Clone repo
cd ~
git clone <YOUR_REPO_URL> mvp_v1.0
cd mvp_v1.0

# Setup environment
bash scripts/aws/setup_training_instance.sh
source venv/bin/activate
```

### Phase 2: Download OPeRA Dataset (5 minutes)

```bash
# On EC2
python scripts/01_download_opera.py
```

**Output:**
```
DATA/OPeRA/raw/
  ├── opera_users.parquet          (~50MB, demographics + personality)
  ├── opera_actions.parquet        (~200MB, shopping actions)
  ├── opera_sessions.parquet       (~100MB, session logs)
  ├── sample_sessions.jsonl        (~50MB, aligned sessions)
  ├── opera_rationales.jsonl       (~5MB, user explanations)
  └── opera_outcomes.jsonl         (~5MB, final choices)
```

### Phase 3: Preprocess Data (10 minutes)

```bash
# On EC2
python scripts/02_preprocess_opera.py \
  --survey DATA/OPeRA/raw/opera_users.parquet \
  --sessions DATA/OPeRA/raw/sample_sessions.jsonl \
  --rationales DATA/OPeRA/raw/opera_rationales.jsonl \
  --outcomes DATA/OPeRA/raw/opera_outcomes.jsonl \
  --out-dir DATA/OPeRA/processed
```

**Output:**
```
DATA/OPeRA/processed/
  ├── aligned_sequences.jsonl      (1000-5000 sessions)
  ├── persona_features.parquet     (12-D vectors for users)
  └── ssr_training_pairs.jsonl     (persona, stimulus, likert triplets)
```

### Phase 4: Discover Personas (15 minutes)

```bash
# On EC2
export OPENAI_API_KEY="sk-..."

python scripts/03_discover_personas.py \
  --features DATA/OPeRA/processed/persona_features.parquet \
  --out models/persona_profiles.json \
  --min-cluster-size 50 \
  --use-llm-summary
```

**Output:**
```json
{
  "personas": [
    {
      "id": "p01_deal_seeker",
      "label": "The Deal Seeker",
      "description": "Price-sensitive, waits for sales, compares extensively",
      "cluster_id": 0,
      "size": 1523,
      "psychographic_tags": ["thrifty", "patient", "analytical"],
      "ocean_scores": {"O": 0.6, "C": 0.8, "E": 0.4, "A": 0.5, "N": 0.3}
    },
    ...  // 8-12 personas
  ]
}
```

### Phase 5: Train SSR Model (30-45 minutes)

```bash
# On EC2
export HF_TOKEN="hf_..."

python scripts/04_train_ssr.py \
  --training-pairs DATA/OPeRA/processed/ssr_training_pairs.jsonl \
  --personas models/persona_profiles.json \
  --out models/ssr_reference.pkl \
  --epochs 10 \
  --batch-size 32
```

**Output:**
```
models/
  ├── ssr_reference.pkl            (~38MB, trained SSR model)
  ├── ssr_config.yaml              (model configuration)
  └── ssr_training_metrics.json   (loss, correlation, etc.)
```

### Phase 6: Train LLM Twins (1.5-2 hours)

```bash
# On EC2
python scripts/aws/train_production.py \
  --personas-file models/persona_profiles.json \
  --sft-data-dir DATA/sft \
  --output-dir artifacts/llm_adapters \
  --sync-s3
```

**Output:**
```
artifacts/llm_adapters/
  ├── p01_deal_seeker/
  │   ├── adapter_model.safetensors  (~16MB per twin)
  │   └── adapter_config.json
  ├── p02_premium_buyer/
  ...  // One adapter per persona
```

### Phase 7: Evaluate (10 minutes)

```bash
# On EC2
python scripts/07_evaluate.py \
  --ssr-model models/ssr_reference.pkl \
  --llm-adapters artifacts/llm_adapters \
  --test-data DATA/OPeRA/processed/aligned_sequences.jsonl \
  --out-dir reports
```

**Output:**
```
reports/
  ├── eval_dashboard.html          (interactive Plotly dashboard)
  ├── ks_similarity.json           (KS test results)
  ├── correlation_metrics.json     (Spearman correlation)
  └── separation_metrics.json      (silhouette, JSD, ARI)
```

**Expected Metrics:**
- KS Similarity: ≥0.80 (target)
- Spearman Correlation: ≥0.70 (target)
- Silhouette Score: ≥0.35 (target)

### Phase 8: Sync to S3 & Shutdown

```bash
# On EC2
export TRAINING_S3_BUCKET="darpan-training-$(whoami)"

# Sync all outputs
aws s3 sync models/ s3://$TRAINING_S3_BUCKET/models/
aws s3 sync artifacts/ s3://$TRAINING_S3_BUCKET/artifacts/
aws s3 sync reports/ s3://$TRAINING_S3_BUCKET/reports/

# Auto-shutdown (optional)
sudo shutdown -h +5
```

### Phase 9: Download & Demo (local machine)

```bash
# Download from S3
export TRAINING_S3_BUCKET="darpan-training-$(whoami)"
aws s3 sync s3://$TRAINING_S3_BUCKET/models/ models/
aws s3 sync s3://$TRAINING_S3_BUCKET/artifacts/ artifacts/
aws s3 sync s3://$TRAINING_S3_BUCKET/reports/ reports/

# Start demo app
streamlit run src/app/main.py
# Opens at http://localhost:8501
```

## Cost Breakdown (g5.xlarge spot)

| Phase | Duration | Cost @ $0.35/hr |
|-------|----------|-----------------|
| Setup | 10 min | $0.06 |
| Download OPeRA | 5 min | $0.03 |
| Preprocess | 10 min | $0.06 |
| Discover Personas | 15 min | $0.09 |
| Train SSR | 45 min | $0.26 |
| Train LLM Twins | 2 hr | $0.70 |
| Evaluate | 10 min | $0.06 |
| **Total** | **~3.5 hr** | **~$1.25** |

Add:
- S3 storage: ~$0.05/month for 3GB
- GPT-4o-mini API: ~$0.10 for persona summaries
- **Grand Total: ~$1.40 per training run**

## Troubleshooting

### "CUDA out of memory"
```bash
# Use g5.xlarge (24GB VRAM) instead of g4dn.xlarge (16GB)
# Or reduce batch size in training configs
```

### "OPeRA dataset not found"
```bash
# Ensure datasets library is installed
pip install datasets
# Rerun download script
python scripts/01_download_opera.py
```

### "OpenAI API key not set"
```bash
export OPENAI_API_KEY="sk-..."
# Or set in ~/.bashrc for persistence
echo 'export OPENAI_API_KEY="sk-..."' >> ~/.bashrc
```

### "Persona discovery finds <3 clusters"
```bash
# Reduce min_cluster_size
python scripts/03_discover_personas.py --min-cluster-size 30
```

### "SSR training not converging"
```bash
# Increase epochs or adjust learning rate
python scripts/04_train_ssr.py --epochs 20 --learning-rate 1e-5
```

## Files Created (End-to-End)

```
mvp_v1.0/
├── DATA/
│   └── OPeRA/
│       ├── raw/                          (Downloaded from HF)
│       │   ├── opera_users.parquet       ✅ Step 2
│       │   ├── opera_actions.parquet
│       │   ├── opera_sessions.parquet
│       │   ├── sample_sessions.jsonl
│       │   ├── opera_rationales.jsonl
│       │   └── opera_outcomes.jsonl
│       └── processed/                    (Aligned data)
│           ├── aligned_sequences.jsonl   ✅ Step 3
│           ├── persona_features.parquet
│           └── ssr_training_pairs.jsonl
│
├── models/
│   ├── persona_profiles.json             ✅ Step 4
│   ├── ssr_reference.pkl                 ✅ Step 5
│   └── ssr_config.yaml
│
├── artifacts/
│   └── llm_adapters/                     ✅ Step 6
│       ├── p01_deal_seeker/
│       ├── p02_premium_buyer/
│       └── ...
│
└── reports/
    ├── eval_dashboard.html               ✅ Step 7
    ├── ks_similarity.json
    ├── correlation_metrics.json
    └── separation_metrics.json
```

## Next: Deploy Demo App

After training completes:

```bash
# Local machine
streamlit run src/app/main.py
```

Visit `http://localhost:8501` to interact with your trained personas.

## Implementation Status

| Component | Status | File |
|-----------|--------|------|
| OPeRA Download | ✅ Done | scripts/01_download_opera.py |
| Data Preprocessing | ✅ Done | scripts/02_preprocess_opera.py |
| Schema Adapter | ✅ Done | src/data/opera/adapter.py |
| Alignment Module | ✅ Done | src/data/opera/alignment.py |
| Persona Discovery | ⏳ In Progress | scripts/03_discover_personas.py |
| SSR Trainer | ⏳ Next | scripts/04_train_ssr.py |
| Evaluation | ⏳ Next | scripts/07_evaluate.py |
| Streamlit App | ⏳ Next | src/app/main.py |
| AWS Scripts | ⏳ Next | scripts/aws/train_complete_pipeline.sh |

**Current Progress: 40% Complete**

---

**Ready to proceed?** I'll now build the remaining components step-by-step:
1. Persona Discovery (UMAP + HDBSCAN + GPT-4o summarization)
2. SSR Trainer (sentence-transformers fine-tuning)
3. Evaluation Framework
4. Streamlit Demo App
5. AWS Master Script

Should I continue with Persona Discovery next?
