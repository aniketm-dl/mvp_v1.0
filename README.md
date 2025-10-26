# Darpan Labs - OPeRA-SSR Digital Twins

**Semantic Similarity Rating system for predicting user responses to e-commerce scenarios using real behavioral data.**

Train data-driven personas from the OPeRA dataset and predict how users would rate new products, promotions, and ad copy.

---

## 🚀 Quick Start

### Option 1: Local Training (2 hours)

```bash
# 1. Install dependencies
pip install -e .

# 2. Set OpenAI API key (for persona summarization)
export OPENAI_API_KEY='your-key-here'

# 3. Download OPeRA dataset
python scripts/01_download_opera.py

# 4. Preprocess data
python scripts/02_preprocess_opera.py

# 5. Discover personas
python scripts/03_discover_personas.py --use-llm-summary

# 6. Train SSR model
python scripts/04_train_ssr.py

# 7. Evaluate model
python scripts/07_evaluate.py

# 8. Launch demo
streamlit run src/app/main.py
```

### Option 2: AWS One-Command Training (~$0.50)

```bash
export OPENAI_API_KEY='your-key-here'
export TRAINING_S3_BUCKET='darpan-training-yourusername'

bash scripts/aws/train_complete_pipeline.sh --auto-shutdown
```

---

## 📊 What This Does

### The Problem

E-commerce companies need to answer questions like:
- "How would users respond to a 20% price increase?"
- "Which ad copy performs better for budget-conscious shoppers?"
- "How do free shipping offers impact purchase decisions?"

### The Solution

Train a **Semantic Similarity Rating (SSR)** model that:
1. **Discovers personas** from real user behavior (OPeRA dataset)
2. **Predicts ratings** (1-5 Likert scale) for any scenario
3. **Provides distributions** showing confidence and variability
4. **Runs fast** (<50ms per prediction)

### Example

```python
from src.ssr.inference import SSRInference

ssr = SSRInference("models/ssr_reference")

# Predict rating for a scenario
prediction = ssr.predict("Free shipping on all orders over $50")

print(f"Mean rating: {prediction['mean']:.2f}")
print(f"Mode (most likely): {prediction['mode']}")
print(f"Distribution: {prediction['distribution']}")

# Output:
# Mean rating: 3.82
# Mode (most likely): 4
# Distribution: [0.05, 0.10, 0.25, 0.40, 0.20]
```

---

## 🏗️ Architecture

### Pipeline Overview

```
1. OPeRA Dataset (HuggingFace)
   ↓
2. Data Alignment & Feature Extraction
   ↓
3. Persona Discovery (UMAP + HDBSCAN)
   ↓
4. GPT-4o-mini Persona Summarization
   ↓
5. SSR Model Training (sentence-transformers)
   ↓
6. Evaluation (KS Similarity, Correlations)
   ↓
7. Streamlit Demo App
```

### Directory Structure

```
mvp_v1.0/
├── src/
│   ├── data/opera/          # OPeRA dataset pipeline
│   ├── personas/            # Persona discovery (UMAP + HDBSCAN)
│   ├── ssr/                 # SSR model (training + inference)
│   ├── evaluation/          # Metrics (KS, correlations, dashboards)
│   └── app/                 # Streamlit demo
│
├── scripts/
│   ├── 01_download_opera.py        # Download OPeRA from HuggingFace
│   ├── 02_preprocess_opera.py      # Align & extract features
│   ├── 03_discover_personas.py     # UMAP + HDBSCAN + GPT-4o
│   ├── 04_train_ssr.py             # Train SSR model
│   ├── 07_evaluate.py              # Evaluate on test set
│   └── aws/
│       └── train_complete_pipeline.sh  # One-command AWS training
│
├── DATA/OPeRA/
│   ├── raw/                 # Downloaded from HuggingFace
│   └── processed/           # Aligned sequences, features, pairs
│
├── models/
│   ├── ssr_reference/       # Trained SSR model
│   └── persona_profiles.json  # Discovered personas
│
├── reports/
│   ├── evaluation_results.json        # Metrics
│   └── evaluation_dashboard.html     # Interactive dashboard
│
└── docs/
    ├── AWS_SETUP.md         # AWS account setup
    ├── TRAINING.md          # Training guide
    ├── EVALUATION.md        # Evaluation metrics
    └── mvp_scope.md         # Complete specification
```

---

## 📋 Prerequisites

### Local Machine

```bash
# Python 3.9+
python --version

# Install dependencies
pip install -e .
```

### OpenAI API Key

For persona summarization with GPT-4o-mini:

1. Go to https://platform.openai.com/api-keys
2. Create new API key
3. Export it:
   ```bash
   export OPENAI_API_KEY='sk-proj-...'
   ```

### AWS (Optional - for cloud training)

1. Sign up at https://aws.amazon.com
2. Create IAM user with EC2 + S3 permissions
3. Configure AWS CLI:
   ```bash
   aws configure
   ```
4. Create S3 bucket:
   ```bash
   aws s3 mb s3://darpan-training-$(whoami)
   export TRAINING_S3_BUCKET=darpan-training-$(whoami)
   ```

---

## 💻 Usage

### Core Pipeline

```bash
# Download OPeRA dataset (~5-10 min)
python scripts/01_download_opera.py

# Preprocess & align data (~10-15 min)
python scripts/02_preprocess_opera.py

# Discover personas (~15-20 min)
python scripts/03_discover_personas.py --use-llm-summary

# Train SSR model (~20-30 min)
python scripts/04_train_ssr.py \
  --embedding-epochs 10 \
  --regression-epochs 20

# Evaluate model (~5-10 min)
python scripts/07_evaluate.py

# Launch demo
streamlit run src/app/main.py
```

### API Usage

```python
from src.ssr.inference import SSRInference

# Load model
ssr = SSRInference("models/ssr_reference")

# Single prediction
pred = ssr.predict("20% off laptops")
print(pred)
# {
#   'mean': 4.1,
#   'std': 0.8,
#   'mode': 4,
#   'distribution': [0.03, 0.07, 0.20, 0.50, 0.20]
# }

# Batch predictions
scenarios = ["Free shipping", "Buy 2 get 1", "Premium quality"]
predictions = ssr.predict_batch(scenarios, return_distributions=True)

# Scenario comparison
comparison = ssr.compare_scenarios(
    base_text="Regular price",
    variant_texts=["10% off", "20% off"],
    variant_ids=["discount_10", "discount_20"]
)

for variant in comparison['variants']:
    print(f"{variant['id']}: {variant['prediction']['mean']:.2f} "
          f"({variant['lift_percent']:+.1f}% lift)")
```

---

## 🎯 Key Features

### 1. Data-Driven Personas

Unlike hand-crafted personas, we discover them from real OPeRA user data:

- **UMAP** for dimensionality reduction (12-D → 2-D)
- **HDBSCAN** for density-based clustering
- **GPT-4o-mini** for natural language summaries

**Result:** 8-12 personas with real behavioral patterns

### 2. Fast Inference

SSR uses fine-tuned sentence-transformers:

- **<50ms** per prediction
- **No GPU** required for inference
- **Batch processing** supported
- **Scalable** to thousands of scenarios

### 3. Quantifiable Quality

Statistical validation:

- **Spearman correlation** ≥ 0.70 (rank correlation)
- **KS similarity** ≥ 0.80 (distribution matching)
- **MAE** < 0.50 (mean absolute error)
- **RMSE** < 0.60 (root mean squared error)

### 4. Interactive Demo

Streamlit app with:

- **Single prediction** - Test individual scenarios
- **Scenario comparison** - Compare multiple variants
- **Persona explorer** - Browse discovered personas
- **Quick templates** - Pre-built scenario examples

---

## 📊 Quality Gates

Run evaluation to check quality:

```bash
python scripts/07_evaluate.py
```

**Expected metrics:**

| Metric | Target | Description |
|--------|--------|-------------|
| Spearman ρ | ≥ 0.70 | Rank correlation (ordinal data) |
| Pearson r | ≥ 0.60 | Linear correlation |
| MAE | < 0.50 | Mean absolute error |
| RMSE | < 0.60 | Root mean squared error |
| KS Similarity | ≥ 0.80 | Distribution matching (1 - KS statistic) |

**View results:**

```bash
# Open interactive dashboard
open reports/evaluation_dashboard.html

# View JSON metrics
cat reports/evaluation_results.json
```

---

## 🧪 Testing

```bash
# Run unit tests
pytest TESTS/test_evaluation_metrics.py -v

# Quick test of SSR inference
python -c "from src.ssr.inference import SSRInference; \
           ssr = SSRInference('models/ssr_reference'); \
           print(ssr.predict('Free shipping'))"
```

---

## 🚀 AWS Training

### One-Command Pipeline

```bash
bash scripts/aws/train_complete_pipeline.sh --auto-shutdown
```

**What it does:**

1. Downloads OPeRA dataset
2. Preprocesses & aligns sequences
3. Discovers personas (UMAP + HDBSCAN + GPT-4o)
4. Trains SSR model
5. Evaluates on test set
6. Syncs to S3
7. Auto-shuts down instance

**Cost:** ~$0.50 (g5.xlarge spot @ $0.35/hr for ~1.5 hours)

### Download Results

```bash
aws s3 sync s3://$TRAINING_S3_BUCKET/models/ models/
aws s3 sync s3://$TRAINING_S3_BUCKET/reports/ reports/
```

---

## 📚 Documentation

- **[Quick Start (Local)](QUICKSTART.md)** - Step-by-step local setup
- **[Quick Start (AWS)](QUICKSTART_AWS.md)** - AWS cloud training
- **[Implementation Summary](IMPLEMENTATION_SUMMARY.md)** - Complete technical docs
- **[AWS Setup Guide](AWS_SSR_TRAINING_GUIDE.md)** - Detailed AWS instructions
- **[Complete Specification](docs/mvp_scope.md)** - Full system spec

---

## 🔧 Configuration

Key configuration files:

```
CONFIGS/
├── opera/            # OPeRA dataset configs
└── ssr/              # SSR model configs (if created)
```

---

## ⚡ Performance

| Metric | Value |
|--------|-------|
| **Inference time** | <50ms |
| **Training time (local)** | ~2 hours |
| **Training time (AWS)** | ~1.5 hours |
| **Training cost (AWS)** | ~$0.50 |
| **Model size** | ~90MB |
| **Personas discovered** | 8-12 |
| **Test accuracy** | Spearman ≥ 0.70 |

---

## 🤝 Legacy System

This project supersedes a previous LLM Twin Simulator system.

For the legacy system (Mistral-7B + LoRA adapters), see the **`archive`** branch:

```bash
git checkout archive
cat ARCHIVE_README.md
```

**Key differences:**

| Feature | Legacy LLM Twin | OPeRA-SSR (Current) |
|---------|-----------------|---------------------|
| Personas | Hand-crafted | Data-driven from OPeRA |
| Model | Mistral-7B + LoRA | sentence-transformers |
| Inference | 100-500ms | <50ms |
| Training | GPU required | CPU/GPU optional |
| Cost | ~$1/training | ~$0.50/training |
| Accuracy | Qualitative | Quantitative (KS ≥ 0.80) |

---

## 🆘 Troubleshooting

### "OPENAI_API_KEY not set"

```bash
export OPENAI_API_KEY='your-key-here'
```

### "HuggingFace dataset not found"

Retry download:
```bash
python scripts/01_download_opera.py --force
```

### "Correlation below target"

Train longer or use larger model:
```bash
python scripts/04_train_ssr.py \
  --embedding-epochs 15 \
  --regression-epochs 30 \
  --base-model sentence-transformers/all-mpnet-base-v2
```

### "Silhouette score too low"

Adjust clustering parameters:
```bash
python scripts/03_discover_personas.py --min-cluster-size 30
```

---

## 📞 Support

- **Documentation:** [docs/](docs/)
- **GitHub Issues:** https://github.com/aniketm-dl/mvp_v1.0/issues
- **Email:** support@darpanlabs.com

---

## 📝 License

MIT License - see [LICENSE](LICENSE)

---

**Built with ❤️ by Darpan Labs**

*Making behavioral prediction accessible, accurate, and affordable.*
