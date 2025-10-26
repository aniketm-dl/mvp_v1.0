# Darpan Labs - Legacy LLM Twin Simulator (ARCHIVED)

**Branch:** `archive`
**Status:** Archived - Preserved for Reference
**Date Archived:** October 26, 2025
**Reason:** Superseded by OPeRA-SSR-Twin system

---

## ⚠️ Important Notice

This branch contains the **legacy LLM Twin Simulator** system that was built before the OPeRA-SSR implementation. It is preserved here for:

1. **Historical reference** - Understanding the evolution of the system
2. **Comparison** - Comparing approaches (LLM fine-tuning vs SSR)
3. **Hybrid implementation** - Potential future integration

**For the current production system, see the `main` or `refactor/aws-workflow-automation` branches.**

---

## System Overview

The legacy LLM Twin Simulator uses:

- **Mistral-7B-Instruct-v0.2** base model
- **LoRA adapters** fine-tuned for 18+ personas
- **Synthetic persona definitions** (hand-crafted)
- **FastAPI simulation endpoints**
- **Mixture model** for user-persona matching
- **Policy heads** for fast ranking
- **ReasonGuard** for LLM output validation

---

## Architecture

```
Legacy LLM Twin Simulator
│
├── src/
│   ├── api/service.py                  # FastAPI endpoints
│   ├── models/
│   │   ├── mixture.py                  # Twin mixture model
│   │   ├── twin_bank.py                # LLM twin bank
│   │   ├── policy_heads.py             # Distilled policy heads
│   │   ├── encoder.py                  # Behavior encoder
│   │   └── calibration.py              # Probability calibration
│   ├── reasoning/
│   │   ├── llm_twin.py                 # LLM-based twins
│   │   ├── llm_runtime.py              # Runtime stub
│   │   ├── guard.py                    # ReasonGuard
│   │   ├── orchestrator.py             # Twin orchestration
│   │   └── reason_cache.py             # Caching layer
│   ├── simulate/
│   │   └── runner.py                   # Simulation runner
│   ├── features/
│   │   ├── cta_builder.py              # CTA feature builder
│   │   ├── candidate_features.py       # Candidate features
│   │   └── candidate_gen.py            # Candidate generation
│   └── profiles/
│       └── loader.py                   # Profile loading
│
├── DATA/
│   ├── personas.json                   # Synthetic persona definitions
│   ├── sft/                            # SFT training data
│   └── copy_variants.json              # Copy variants
│
├── CONFIGS/
│   ├── serve/
│   │   ├── api.yaml                    # API server config
│   │   └── policy.yaml                 # Policy heads config
│   ├── train/                          # Training configs
│   └── tests/gates.yaml                # Quality gates
│
├── scripts/
│   ├── train_llm_persona_sft.py        # LLM SFT training
│   ├── distill_policies.py             # Policy head distillation
│   ├── eval_llm_persona_sft.py         # LLM evaluation
│   └── train/                          # Training utilities
│
├── trained_models/v1.0/adapters/       # Trained LoRA adapters
│
├── darpan.py                           # Unified CLI
├── interact_cli.py                     # Interactive CLI
└── Makefile                            # Build commands
```

---

## Key Components

### 1. LLM Twin System

**File:** `src/reasoning/llm_twin.py`

LLM-based personas that:
- Use Mistral-7B + LoRA adapters
- Generate explanations for decisions
- Mimic specific shopper personas

**18+ Personas:**
- Bargain Hunter, Premium Loyalist, Deal Hunter
- Budget Optimizer, Bulk Buyer, Brand Switcher
- Eco-Conscious, Experiential Buyer, Gift Buyer
- Impulse Buyer, Local Supporter, Minimalist
- Mobile Shopper, Comparison Shopper, Research-Oriented
- Social Validator, Subscription Enthusiast, Trendsetter
- Convenience Seeker

### 2. Mixture Model

**File:** `src/models/mixture.py`

Matches users to personas using:
- 15-D fused embeddings (behavior + psychographic + demographic)
- Cosine similarity + softmax
- Weighted blending of twin outputs

### 3. Policy Heads (Fast Path)

**File:** `src/models/policy_heads.py`

Distilled linear heads for:
- Fast ranking without LLM calls
- 100x faster than full LLM inference
- Optional fallback to LLM for explanations

### 4. ReasonGuard

**File:** `src/reasoning/guard.py`

Validates LLM outputs:
- Max 20 tokens
- No hallucinated numbers
- Context grounding required
- Banned term filtering

### 5. Simulation API

**File:** `src/api/service.py`

FastAPI endpoints:
- `POST /simulate` - Run what-if scenarios
- `POST /match` - Match user to personas
- `POST /twin/chat` - Chat with specific twin
- `POST /twin/decide` - Twin decision making
- `GET /twin/personas` - List all personas

---

## How It Works

### Training Pipeline

1. **Persona Definition** (`DATA/personas.json`)
   - Hand-crafted synthetic personas
   - Behavior patterns, psychographics, demographics

2. **SFT Data Generation** (`scripts/prepare_llm_sft_data.py`)
   - Generate training examples for each persona
   - Format as conversational data

3. **LLM Fine-Tuning** (`scripts/train_llm_persona_sft.py`)
   - Fine-tune Mistral-7B with LoRA
   - One adapter per persona
   - Epochs: 1-3, Batch size: 4

4. **Policy Head Distillation** (`scripts/distill_policies.py`)
   - Extract LLM decisions on many scenarios
   - Train linear heads to mimic decisions
   - Saves to `artifacts/policy_heads/`

### Inference Pipeline

1. **User Input** → Feature extraction (CTA, profile, context)
2. **Mixture Model** → Match user to personas (weights)
3. **Fast Path** (if policy heads enabled):
   - Use linear heads for ranking
   - Optionally call LLM for explanations
4. **Slow Path** (if policy heads disabled):
   - Call all relevant LLM twins
   - Blend outputs via mixture weights
5. **ReasonGuard** → Validate explanations
6. **Return** → Predictions + explanations + deltas

---

## Quality Gates

**File:** `CONFIGS/tests/gates.yaml`

Targets:
- **Silhouette Score** ≥ 0.35 (persona separation)
- **Jensen-Shannon Divergence** ≥ 0.10 (distribution difference)
- **Adjusted Rand Index** ≥ 0.80 (clustering stability)

Run gates:
```bash
make gate
```

---

## Training Commands

### Train All Personas (AWS)

```bash
# 1. Launch AWS instance
make launch

# 2. SSH into instance
ssh -i ~/darpan-training.pem ubuntu@<INSTANCE_IP>

# 3. Setup environment
make setup-instance

# 4. Train all personas
make train

# 5. Download trained models
make download
```

### Train Single Persona (Local)

```bash
python scripts/train_llm_persona_sft.py \
  --persona_id bargain_hunter \
  --train_data DATA/sft/bargain_hunter.jsonl \
  --output_dir artifacts/llm_adapters/bargain_hunter \
  --base_model mistralai/Mistral-7B-Instruct-v0.2 \
  --epochs 3 \
  --learning_rate 2e-4
```

### Distill Policy Heads

```bash
# 1. Generate distillation data
python scripts/generate_distill_data_from_llm.py \
  --out DATA/distill_llm.jsonl

# 2. Train policy heads
python scripts/distill_policies.py \
  --input DATA/distill_llm.jsonl \
  --outdir artifacts/policy_heads \
  --buckets 16
```

---

## Running the System

### Start API Server

```bash
uvicorn src.api.service:app --reload --host 0.0.0.0 --port 8000
```

### Interactive CLI

```bash
python darpan.py chat --persona bargain_hunter
```

### Simulation Example

```bash
curl -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "u123",
    "scenarios": [
      {"variant_id": "base"},
      {"variant_id": "10pct_off", "context_overrides": {"price_mean": 90}}
    ],
    "explain": "blend"
  }'
```

---

## Configuration

### API Server (`CONFIGS/serve/api.yaml`)

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  workers: 4

models:
  base_model: "mistralai/Mistral-7B-Instruct-v0.2"
  adapter_dir: "artifacts/llm_adapters"
  use_cache: true

features:
  use_policy_heads: true
  explain_mode: "blend"
```

### Policy Heads (`CONFIGS/serve/policy.yaml`)

```yaml
policy:
  use_heads: true
  temperature: 0.0
  fallback_to_llm: true  # For explanations
```

---

## Testing

```bash
# Unit tests
pytest TESTS/ -v

# Specific tests
pytest TESTS/test_mixture.py -v
pytest TESTS/test_twin_endpoints.py -v
pytest TESTS/test_reason_guard.py -v

# Quality gates
make gate

# Full test suite
make all-checks
```

---

## Key Differences from OPeRA-SSR

| Feature | Legacy LLM Twin | OPeRA-SSR (New) |
|---------|----------------|-----------------|
| **Personas** | Hand-crafted synthetic | Data-driven from real OPeRA users |
| **Model** | Mistral-7B + LoRA | sentence-transformers + regression |
| **Training** | LLM fine-tuning (GPU) | Contrastive + regression (CPU/GPU) |
| **Inference** | 100-500ms per call | <50ms per call |
| **Explanations** | LLM-generated text | Statistical distributions |
| **Data** | Synthetic scenarios | Real user behavior (HuggingFace) |
| **Persona Discovery** | Manual | UMAP + HDBSCAN + GPT-4o-mini |
| **Cost** | ~$0.50 per training run | ~$0.20 per training run |
| **Accuracy** | Qualitative | Quantitative (KS ≥ 0.80, Spearman ≥ 0.70) |

---

## Why Was This Archived?

The OPeRA-SSR approach offers several advantages:

1. **Data-Driven Personas** - Real user data instead of synthetic definitions
2. **Faster Inference** - 10x faster predictions (<50ms vs 500ms)
3. **Lower Cost** - No GPU needed for inference, cheaper training
4. **Measurable Quality** - Statistical metrics (KS similarity, correlations)
5. **Scalability** - Can handle more personas without linear cost increase

However, the legacy system has value for:
- **Rich Explanations** - LLM-generated natural language
- **Conversational Interaction** - Can chat with personas
- **Complex Reasoning** - Handle nuanced decision-making

---

## Potential Future: Hybrid System

Combine the best of both:

```
User Query
  ↓
SSR Model (Fast Ranking)
  ↓
Top K Candidates
  ↓
LLM Twin (Rich Explanation)
  ↓
Final Output: Ranking + Explanation
```

Implementation would be in `src/twins/hybrid.py` (not yet built).

---

## Documentation Files

**System Docs:**
- `README.md` - Original main README
- `USAGE_GUIDE.md` - Detailed usage instructions
- `END_TO_END_WORKFLOW.md` - Complete workflow

**Training Docs:**
- `docs/TRAINING.md` - Training guide
- `docs/AWS_SETUP.md` - AWS account setup
- `RETRAIN_AND_TEST_GUIDE.md` - Retraining workflow

**Phase Docs:**
- `PHASE_1_COMPLETE.md` through `PHASE_3E3_COMPLETE.md` - Development phases

**API Docs:**
- `docs/API.md` - API reference
- `API/SCHEMAS.md` - Request/response schemas

---

## Known Issues (Archived)

1. **GPU Memory** - Mistral-7B requires 16GB+ VRAM
2. **Slow Inference** - Even with policy heads, LLM calls are expensive
3. **Persona Drift** - Hand-crafted personas may not match real users
4. **Limited Scalability** - Each new persona requires GPU training
5. **Quality Metrics** - Hard to measure separation objectively

These issues are addressed in the OPeRA-SSR system.

---

## Migration to OPeRA-SSR

If you want to migrate from this system to OPeRA-SSR:

1. **Switch branches:**
   ```bash
   git checkout main
   # or
   git checkout refactor/aws-workflow-automation
   ```

2. **Follow new quickstart:**
   ```bash
   # See QUICKSTART.md on main branch
   python scripts/01_download_opera.py
   python scripts/02_preprocess_opera.py
   python scripts/03_discover_personas.py
   python scripts/04_train_ssr.py
   streamlit run src/app/main.py
   ```

3. **Comparison:**
   - Old LLM twins: Rich explanations, slower, more expensive
   - New SSR: Fast predictions, data-driven, cheaper

---

## Support

This branch is **archived and no longer maintained**.

For support with the current OPeRA-SSR system:
- See `main` branch README
- Check `IMPLEMENTATION_SUMMARY.md` on main branch
- Review `docs/mvp_scope.md` for specification

---

## Preservation Note

This branch is preserved as-is with:
- ✅ All legacy LLM twin code
- ✅ Trained LoRA adapters
- ✅ Original documentation
- ✅ Training scripts
- ✅ API endpoints
- ✅ CLI tools
- ✅ Configuration files

**Everything needed to run the legacy system is here.**

To use it:
```bash
git checkout archive
make setup
make serve  # Start API
# or
python darpan.py chat  # Interactive CLI
```

---

**Archived by:** Claude Code
**Date:** October 26, 2025
**Reason:** Superseded by OPeRA-SSR-Twin MVP
**Status:** Complete, functional, preserved for reference

---

