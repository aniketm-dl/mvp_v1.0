# Airline Digital Twin System

**Prompt-only LLM-powered passenger personas for offer acceptance prediction**

Predict how different airline passengers would respond to offers (extra legroom, WiFi, lounge access, etc.) based on their demographics, psychographics, and past experiences — with natural language explanations.

---

## 🎯 What This Does

Ask a question like:

> "Would a **comfort-seeking 35-year-old business traveler** accept **extra legroom** at **20% off** on a **long flight**?"

Get an answer like:

```
Decision: YES
Probability: 0.82
Rationale: "As someone who prioritizes comfort on long flights,
           the 20% discount makes this an attractive offer."
```

---

## ✨ Key Features

- **🚀 Zero Training:** No fine-tuning or model training required
- **📊 Data-Grounded:** Every twin backed by real passenger cohort statistics
- **🔄 Deterministic:** Same inputs + seed = same outputs (reproducible)
- **💬 Explainable:** Natural language rationales for every decision
- **✅ Validated:** Comprehensive test suite ensures rational behavior
- **💰 Cost-Effective:** ~$0.001-0.02 per decision depending on model

---

## 🚀 Quick Start

### 1. Setup

```bash
# Clone repo
git clone https://github.com/aniketm-dl/mvp_v1.0.git
cd mvp_v1.0

# Set up OpenAI API key
cp .env.example .env
nano .env  # Add your OpenAI API key

# Load environment
source .env

# Verify
echo $OPENAI_API_KEY
```

### 2. Make Your First Decision

```bash
python scripts/ask_twin_decision.py \
  --twin twin_002 \
  --offer legroom \
  --discount 0.20 \
  --flight-length long \
  --trip-purpose business
```

**Output:**
```
================================================================================
DECISION RESULT
================================================================================
Twin: Comfort seeker 35-44 male business traveler (business)
Offer: Extra Legroom Seat
Discount: 20% off
Final Price: $20.00

Decision: YES
Probability: 0.85
Rationale: I prioritize comfort on long flights and this discount makes
           it worthwhile for the added space.

Context: long business flight
================================================================================
```

### 3. Compare Multiple Twins

```bash
python scripts/compare_twins.py \
  --twins twin_002,twin_006,twin_011 \
  --offer legroom \
  --discount 0.20
```

See how different personas (comfort-seeker, value-conscious, etc.) respond to the same offer.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[Setup Guide](AIRLINE_SETUP.md)** | Complete installation and API key setup |
| **[Architecture](AIRLINE_ARCHITECTURE.md)** | System design and technical details |
| **[Evaluation](AIRLINE_EVALUATION.md)** | Testing framework and validation |
| **[Quick Reference](#quick-reference)** | Common commands and examples (below) |

---

## 📋 Available Twins

12 diverse passenger personas covering key archetypes:

| ID | Description | Key Traits |
|----|-------------|------------|
| twin_001 | 18-24 male business traveler (eco) | Punctuality sensitive |
| twin_002 | 35-44 male business traveler (business) | Comfort seeker |
| twin_003 | 55+ female leisure traveler (eco) | Punctuality sensitive |
| twin_006 | 35-44 male leisure traveler (eco-plus) | Value conscious |
| twin_009 | 25-34 male business traveler (business) | Business-oriented |
| twin_011 | 55+ female leisure traveler (eco-plus) | Value + punctuality |
| ... | ... | ... |

See `DATA/airline/twins/` for complete list.

---

## 🎁 Available Offers

| Offer | Description | Default Price | Typical Acceptance |
|-------|-------------|---------------|-------------------|
| `legroom` | Extra Legroom Seat | $25 | Comfort-seekers: 10-15% discount |
| `wifi` | Inflight WiFi Access | $15 | Digital-first: 10-15% discount |
| `lounge` | Airport Lounge Access | $40 | Business travelers: 15-20% discount |
| `boarding` | Priority Boarding | $20 | Punctuality-sensitive: 10-15% discount |
| `baggage` | Extra Checked Baggage | $30 | Service-reliability: 15% discount |

---

## 🎮 Usage Examples

### Single Decision

```bash
# Ask twin_006 (value-conscious) about WiFi at 25% off
python scripts/ask_twin_decision.py \
  --twin twin_006 \
  --offer wifi \
  --discount 0.25 \
  --flight-length medium \
  --trip-purpose leisure \
  --seed 42
```

### Batch Processing

```bash
# Test all twins on legroom offer
python scripts/batch_decisions.py \
  --all-twins \
  --offer legroom \
  --discount 0.20

# Test single twin on all offers
python scripts/batch_decisions.py \
  --twin twin_002 \
  --all-offers \
  --discounts 0.10,0.20,0.30
```

### Run Evaluation

```bash
# Validate twin behavior
python scripts/evaluate_twins.py \
  --save-report DATA/airline/evaluation_report.md
```

Tests:
- ✅ Monotonicity (higher discount → higher acceptance)
- ✅ Face validity (traits match behavior)
- ✅ Stability (deterministic with seed)

---

## 🏗️ Project Structure

```
mvp_v1.0/
├── DATA/airline/
│   ├── demo_airline.parquet         # Raw dataset (400 samples)
│   ├── twins/                        # 12 twin persona cards (JSON)
│   ├── cohorts/                      # Cohort priors (JSONL)
│   └── decisions/                    # Decision ledger (CSV)
│
├── PROMPTS/airline/
│   ├── system_prompt.txt             # System prompt template
│   └── user_offer_prompt.txt         # User prompt template
│
├── CONFIGS/airline/
│   └── twin_config.yaml              # LLM settings, tag rules, discount ladders
│
├── src/airline/
│   ├── bands.py                      # Age/distance/delay banding
│   ├── psychographics.py             # Behavioral tag derivation
│   ├── cohorts.py                    # Cohort prior computation
│   ├── twin_card.py                  # Twin persona data structure
│   ├── schemas.py                    # Offer and decision schemas
│   ├── prompt_composer.py            # Prompt assembly
│   ├── llm_gateway.py                # LLM API integration
│   ├── evaluator.py                  # Evaluation framework
│   └── ledger.py                     # Decision audit trail
│
├── scripts/
│   ├── ask_twin_decision.py          # Single decision CLI
│   ├── compare_twins.py              # Multi-twin comparison
│   ├── batch_decisions.py            # Batch processing
│   ├── evaluate_twins.py             # Run evaluation suite
│   └── generate_twin_cards.py        # Twin card generator
│
└── DOCS/
    ├── AIRLINE_SETUP.md              # Setup guide
    ├── AIRLINE_ARCHITECTURE.md       # Technical architecture
    ├── AIRLINE_EVALUATION.md         # Testing guide
    └── AIRLINE_README.md             # This file
```

---

## 🔬 How It Works

### 1. Data Preparation (Phase 1)

```
Raw Airline Data (400 passengers)
    ↓
Add Age/Distance/Delay Bands
    ↓
Derive 7 Psychographic Tags
    (punctuality_sensitive, comfort_seeker, value_conscious, etc.)
    ↓
Compute 24 Cohort Priors
    (satisfaction rates, rating means, price sensitivity)
    ↓
Enriched Dataset
```

### 2. Twin Generation (Phase 2)

Sample diverse passengers (stratified by satisfaction, class, travel type) and create rich persona cards with:
- Demographics (age, gender)
- Travel profile (class, distance, delays)
- Psychographic tags (behavioral traits)
- Recent experience (14 service ratings)
- Cohort grounding (statistics from similar passengers)

### 3. Prompt Composition (Phase 3)

Transform twin card + offer into LLM prompt:

```
System Prompt:
  "You are a 35-year-old male business traveler who values comfort.
   Your recent experiences: seat_comfort=4/5, leg_room=3/5...
   Similar passengers (60% satisfied) typically accept legroom at 15% discount.
   Price sensitivity: LOW"

User Prompt:
  "You are offered Extra Legroom ($25 → $20, 20% off) on a long business flight.
   Would you accept? Respond with JSON: {decision, probability, rationale}"
```

### 4. LLM Decision (Phase 4)

Call OpenAI/Anthropic API with retry logic, parse JSON response, validate schema.

### 5. Logging & Analysis (Phase 6)

Log every decision to CSV ledger with full context for audit trail and analysis.

---

## 📊 Validation Results

Our evaluation framework ensures twins behave rationally:

| Test Category | Pass Rate | Description |
|--------------|-----------|-------------|
| **Monotonicity** | ≥95% | Higher discounts don't decrease acceptance |
| **Face Validity** | ≥95% | Twins behave according to their traits |
| **Stability** | 100% | Deterministic with same seed |

**Example:** Comfort-seeker (twin_002) accepts legroom at lower discount than value-conscious (twin_006) accepts lounge. ✅

---

## 💰 Cost Estimates

| Model | Per Decision | 100 Decisions | 1000 Decisions |
|-------|-------------|---------------|----------------|
| GPT-4 | $0.01-0.02 | $1-2 | $10-20 |
| GPT-3.5-turbo | $0.0001-0.0003 | $0.01-0.03 | $0.10-0.30 |
| Claude 3 Sonnet | $0.001-0.003 | $0.10-0.30 | $1-3 |

**Recommendation:** Use GPT-3.5-turbo for testing, GPT-4 for production.

---

## 🎓 Key Learnings & Design Decisions

### Why Prompt-Only (No Training)?

✅ **Faster iteration:** Edit prompts, not retrain models
✅ **Lower upfront cost:** No GPU training (~$0.50+ per model)
✅ **Better explainability:** Natural language rationales
✅ **Leverages SOTA:** GPT-4 reasoning > small fine-tuned models

### Why Cohort Priors?

Grounding twins in real behavioral data:
- Reduces stereotyping (not just "25-34 male")
- Improves realism (reflects actual variance)
- Provides guardrails (discount thresholds)

### Why 12 Twins?

- Sufficient diversity (age × class × travel × psychographics)
- Manageable evaluation cost (~$1-5 for full suite)
- Easy to extend (generate more with `generate_twin_cards.py`)

---

## 🚀 Next Steps

### For Research

- [ ] Scale to 100+ twins for broader coverage
- [ ] Test on real A/B test data (if available)
- [ ] Compare vs. traditional choice models (logit, random forest)

### For Production

- [ ] Deploy FastAPI endpoint for real-time decisions
- [ ] Add caching layer for common queries
- [ ] Monitor decision quality over time
- [ ] Integrate with offer optimization system

### For Extension

- [ ] Support hotel, restaurant, retail datasets
- [ ] Add multi-step decision flows (sequential offers)
- [ ] Implement counterfactual explanations ("What if discount was 30%?")

---

## 🤝 Contributing

We welcome contributions! Areas to improve:

1. **New psychographic tags:** Add more behavioral profiles
2. **Better prompts:** Refine system/user templates
3. **More test scenarios:** Expand face validity tests
4. **Performance:** Optimize LLM calls (caching, batching)
5. **Visualization:** Build interactive dashboard

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

---

## 📝 Citation

If you use this system in research, please cite:

```bibtex
@software{airline_digital_twins,
  title = {Airline Digital Twin System: Prompt-Only LLM Personas},
  author = {Darpan Labs},
  year = {2024},
  url = {https://github.com/aniketm-dl/mvp_v1.0}
}
```

---

## 📄 License

MIT License - see [LICENSE](../LICENSE) for details.

---

## 🆘 Support

- **Documentation:** [DOCS/](.)
- **Issues:** [GitHub Issues](https://github.com/aniketm-dl/mvp_v1.0/issues)
- **Email:** support@darpanlabs.com

---

## 🙏 Acknowledgments

- **Dataset:** Kaggle Airline Passenger Satisfaction Dataset
- **Inspiration:** Stanford HAI research on LLM-based synthetic users
- **LLM APIs:** OpenAI (GPT-4) and Anthropic (Claude)

---

**Built with ❤️ by Darpan Labs**

*Making AI personas accessible, explainable, and production-ready.*
