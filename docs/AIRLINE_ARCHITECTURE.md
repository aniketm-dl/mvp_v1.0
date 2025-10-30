

# Airline Digital Twin System - Architecture Documentation

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [Design Decisions](#design-decisions)
6. [Extension Points](#extension-points)

---

## System Overview

The Airline Digital Twin System is a **prompt-only, LLM-powered simulation platform** that predicts how different airline passenger personas would respond to offers (e.g., extra legroom, WiFi, lounge access) under various contexts.

### Key Characteristics

- **Zero Training:** No fine-tuning or model training required
- **Data-Grounded:** Every twin is backed by real passenger cohort statistics
- **Deterministic:** Same inputs + same seed = same outputs
- **Explainable:** Natural language rationales for every decision
- **Validated:** Comprehensive test suite ensures rational behavior

### Tech Stack

- **Language:** Python 3.9+
- **LLM APIs:** OpenAI (GPT-4, GPT-3.5-turbo) or Anthropic (Claude)
- **Data Processing:** pandas, numpy
- **Configuration:** YAML
- **Testing:** pytest (not yet integrated, but compatible)

---

## Architecture Principles

### 1. Separation of Concerns

The system is organized into clear, independent layers:

```
┌─────────────────────────────────────────────┐
│   Scripts (CLI, Evaluation, Batch)          │  ← User Interface
├─────────────────────────────────────────────┤
│   Application Logic                          │
│   - Twin Cards                               │
│   - Prompt Composition                       │
│   - Decision Logic                           │
│   - Evaluation Framework                     │
├─────────────────────────────────────────────┤
│   Infrastructure                             │
│   - LLM Gateway (OpenAI/Anthropic)          │
│   - Decision Ledger (Audit Trail)           │
│   - Configuration Management                 │
├─────────────────────────────────────────────┤
│   Data Layer                                 │
│   - Raw Dataset                              │
│   - Processed Features (Bands, Tags)        │
│   - Cohort Priors                            │
│   - Twin Personas                            │
└─────────────────────────────────────────────┘
```

### 2. Data-First Grounding

Every twin decision is grounded in real data:

```
Twin Decision = f(
    Twin Profile      (individual demographics + psychographics),
    Cohort Priors     (aggregated statistics from similar passengers),
    Offer Details     (price, discount, constraints),
    Context           (flight length, purpose, time pressure),
    LLM Reasoning     (natural language integration)
)
```

### 3. Deterministic by Default

- Fixed random seeds for reproducibility
- Temperature = 0.2 for consistent LLM behavior
- Canonical sorting for stable outputs
- Immutable twin cards (never modified after creation)

### 4. Prompt Engineering Over Training

Instead of fine-tuning models, we:
- Craft rich system prompts with complete context
- Inject cohort statistics as "social proof"
- Use structured JSON output for parsing
- Let pre-trained LLMs handle reasoning

---

## Component Details

### Data Pipeline (`src/airline/bands.py`, `psychographics.py`, `cohorts.py`)

**Purpose:** Transform raw airline data into rich, grounded twin personas.

**Flow:**
```
Raw Data (400 passengers)
    ↓ bands.py
Add Age/Distance/Delay Bands
    ↓ psychographics.py
Derive 7 Behavioral Tags
    ↓ cohorts.py
Compute 24 Cohort Priors
    ↓
Enriched Dataset
```

**Key Features:**
- **Bands:** Quantize continuous variables (age, distance, delay) into interpretable buckets
- **Tags:** Rule-based psychographic profiling (e.g., "comfort_seeker", "value_conscious")
- **Cohorts:** Group similar passengers and compute aggregates (satisfaction rate, rating means, drivers)

**Example Cohort Prior:**
```json
{
  "cohort_key": "25-34_Male_Business_travel_Business_long",
  "n": 10,
  "satisfaction_rate": 0.60,
  "rating_means": {"seat_comfort": 3.8, "leg_room": 3.5, ...},
  "top_positive_drivers": ["baggage_handling", "cleanliness"],
  "price_sensitivity": "low",
  "discount_ladder_hints": {"legroom": 0.15, "wifi": 0.10, ...}
}
```

---

### Twin Card System (`src/airline/twin_card.py`)

**Purpose:** Represent a complete passenger persona with all context needed for decision-making.

**Structure:**
```python
TwinCard:
  - id: "twin_001"
  - label: "Punctuality sensitive 18-24 male business traveler (eco)"
  - demographics: {gender, age, age_band}
  - travel_profile: {customer_type, travel_type, class, distance, delays}
  - psychographics: ["punctuality_sensitive"]
  - recent_experience: {14 service ratings}
  - cohort_key: "18-24_Male_Business_travel_Eco_long"
  - cohort_priors: {full cohort statistics}
  - metadata: {created_at, data_source, satisfaction_label}
```

**Generation Strategy:**
- Stratified sampling from training set (80%)
- Ensures diversity across satisfaction, class, travel type
- 12 personas cover key archetypes

---

### Prompt System (`PROMPTS/airline/`, `src/airline/prompt_composer.py`)

**Purpose:** Transform twin cards and offers into LLM-ready prompts.

**Components:**

1. **System Prompt Template:**
   - Establishes persona and character
   - Injects complete twin profile
   - Provides cohort insights (satisfaction patterns, drivers, thresholds)
   - Specifies decision rules and JSON output format

2. **User Prompt Template:**
   - Presents offer details (name, type, discount, final price)
   - Describes context (flight length, purpose, pressure, delays)
   - Reinforces instructions to answer in character

3. **Prompt Composer:**
   - `format_twin_profile()`: Formats demographics, travel, psychographics, ratings
   - `format_cohort_insights()`: Formats cohort statistics, drivers, discount hints
   - `compose_prompts()`: Assembles complete system + user prompts

**Example System Prompt (excerpt):**
```
You are acting as a specific airline passenger described below.

===== YOUR PROFILE =====

Passenger ID: twin_001
Description: Punctuality sensitive 18-24 male business traveler (eco)

DEMOGRAPHICS:
  • Gender: Male
  • Age: 20 years old (18-24)

TRAVEL PROFILE:
  • Type: Business travel
  • Class: Eco
  • Distance: 4209 miles (long)

BEHAVIORAL PROFILE:
  • Punctuality Sensitive

RECENT EXPERIENCE:
  • Seat Comfort: 4/5
  • Leg Room: 3/5
  [... 12 more ratings ...]

===== INSIGHTS FROM SIMILAR PASSENGERS =====

Based on 5 similar passengers:
  • 0% were satisfied
  • Price sensitivity: HIGH
  • Typically accept legroom at 25% discount
  [... more insights ...]
```

---

### LLM Gateway (`src/airline/llm_gateway.py`)

**Purpose:** Abstract LLM API calls with retry logic and validation.

**Features:**
- **Multi-provider:** OpenAI and Anthropic support
- **Retry logic:** Exponential backoff on failures
- **JSON validation:** Strict schema enforcement
- **Metadata tracking:** Tokens, model, attempts
- **Determinism:** Seed support (OpenAI)

**API:**
```python
gateway = LLMGateway(config_path)

decision, metadata = gateway.get_decision(
    system_prompt,
    user_prompt,
    seed=42,
    max_retries=2
)

# Returns:
# decision = {"decision": "yes", "probability": 0.75, "rationale": "..."}
# metadata = {"provider": "openai", "model": "gpt-4", "usage": {...}}
```

**Error Handling:**
1. API call fails → Exponential backoff → Retry
2. JSON parse fails → Add explicit reminder → Retry once
3. All retries exhausted → Raise exception with details

---

### Evaluation Framework (`src/airline/evaluator.py`)

**Purpose:** Validate that twins behave rationally and consistently.

**Test Categories:**

1. **Monotonicity:** Higher discount → Higher/equal acceptance
2. **Face Validity:** Twins with specific traits behave as expected
3. **Stability:** Same seed → Identical results
4. **Cohort Coherence:** (Future) Similar twins behave similarly

**API:**
```python
evaluator = TwinEvaluator(config_path, templates_dir, twins_dir)

report = evaluator.run_all_tests()

# Returns EvaluationReport with:
# - monotonicity_results: List[TestResult]
# - face_validity_results: List[TestResult]
# - stability_results: List[TestResult]
# - Pass rates and overall pass/fail
```

---

### Decision Ledger (`src/airline/ledger.py`)

**Purpose:** Maintain complete audit trail of all decisions.

**Schema (CSV):**
```
timestamp, twin_id, twin_label, offer_name, offer_type, discount_pct,
original_price, final_price, flight_length, trip_purpose, time_pressure,
recent_delays, decision, probability, rationale, llm_provider, llm_model,
seed, prompt_hash, total_tokens, attempt
```

**Features:**
- Append-only log (never delete/modify)
- Prompt hash for reproducibility tracking
- Query API: get_twin_history(), get_offer_history()
- Statistics: summary_stats(), by_twin, by_offer
- Export: to JSON for analysis

---

## Data Flow

### End-to-End Decision Flow

```
1. User Request
   ↓
2. Load Twin Card (demographics, psychographics, cohort priors)
   ↓
3. Create Offer (type, discount, price, constraints)
   ↓
4. Create Context (flight length, purpose, pressure, delays)
   ↓
5. Compose Prompts (system + user)
   ↓
6. Call LLM API (with retry logic)
   ↓
7. Parse JSON Response (validate schema)
   ↓
8. Create TwinDecision (decision, probability, rationale)
   ↓
9. Log to Ledger (audit trail)
   ↓
10. Return to User
```

### Batch Processing Flow

```
User specifies: Twins × Offers × Discounts
   ↓
For each combination:
   ↓ (parallel or sequential)
   Execute Decision Flow
   ↓
   Log to Ledger
   ↓
Aggregate Results
   ↓
Display Comparison Table
```

### Evaluation Flow

```
Define Test Suite
   ↓
For each test:
   ↓
   Execute Decisions (with controlled parameters)
   ↓
   Compare actual vs expected behavior
   ↓
   Record TestResult (pass/fail + details)
   ↓
Aggregate into EvaluationReport
   ↓
Generate Markdown Report
```

---

## Design Decisions

### Why Prompt-Only (No Training)?

**Advantages:**
- ✅ **Faster iteration:** Change behavior by editing prompts, not retraining
- ✅ **Lower cost:** No GPU training costs (~$0.50+ per model)
- ✅ **Better explainability:** Natural language rationales, not black-box predictions
- ✅ **Easier debugging:** Inspect exact prompts, not model weights
- ✅ **Leverages state-of-the-art:** GPT-4 reasoning > small fine-tuned models

**Trade-offs:**
- ⚠️ **API costs:** ~$0.001-0.02 per decision (but still cheaper than training for small datasets)
- ⚠️ **Latency:** ~1-3 seconds per decision (vs <100ms for local models)
- ⚠️ **Dependency:** Requires external API (can't run fully offline)

**Decision:** Prompt-only is the right choice for this use case (small dataset, high need for explainability).

---

### Why Cohort Priors?

**Problem:** LLMs can produce stereotypes when prompted with demographics alone.

**Solution:** Ground each twin in real behavioral data from similar passengers.

**Benefits:**
- ✅ **Reduces stereotyping:** "25-34 male" ≠ all identical; cohort shows variance
- ✅ **Improves realism:** Twins reflect actual passenger behavior patterns
- ✅ **Provides guardrails:** Discount thresholds prevent random responses

**Example:**
```
Without priors: "I'm male, so I like sports and beer."
With priors:    "Similar passengers (60% satisfaction) value seat_comfort and leg_room."
```

---

### Why 12 Twins (Not More)?

**Reasoning:**
- **Sufficient diversity:** 12 covers key archetypes (age × class × travel type × psychographics)
- **Manageable evaluation:** Testing all twins is feasible (~$1-5 for full suite)
- **Stratified sampling:** Ensures representation of satisfied/dissatisfied, business/leisure, etc.

**Extensibility:** Easy to generate more twins if needed (just run `generate_twin_cards.py` with larger n_samples).

---

### Why CSV Ledger (Not Database)?

**Reasoning:**
- ✅ **Simple:** No setup, just append rows
- ✅ **Portable:** Easy to share, analyze in Excel/pandas
- ✅ **Auditable:** Human-readable, version-controllable

**When to upgrade to DB:**
- Millions of decisions (CSV performance degrades)
- Concurrent writes from multiple processes
- Complex querying needs (joins, aggregations)

---

## Extension Points

### Adding New Offers

1. Define offer factory in `src/airline/schemas.py`:
```python
def create_meal_upgrade_offer(discount_pct: float, price: float = 12.0) -> OfferDetails:
    return OfferDetails(
        name="Premium Meal Upgrade",
        offer_kind="service_addon",
        discount_pct=discount_pct,
        absolute_price_delta=price * (1 - discount_pct),
        constraints=["subject to availability"]
    )
```

2. Add discount ladder hints in `CONFIGS/airline/twin_config.yaml`:
```yaml
discount_ladders:
  meal_upgrade:
    amenity_lover: 0.15
    value_conscious: 0.35
    default: 0.25
```

3. Update `OFFER_FACTORIES` dict in CLI scripts.

---

### Adding New Psychographic Tags

1. Define rule in `src/airline/psychographics.py`:
```python
def tag_lounge_seeker(row: pd.Series) -> bool:
    """Tag passengers who value lounge access."""
    is_business = "business" in str(row.get("type_of_travel", "")).lower()
    long_flight = row.get("distance_band", "") == "long"
    return is_business and long_flight
```

2. Add to `derive_psychographic_tags()` function.

3. Twin cards regenerated automatically include new tags.

---

### Adding New Test Scenarios

In `src/airline/evaluator.py`:
```python
def run_face_validity_tests(self):
    # ...existing scenarios...

    # New scenario
    result = self.test_face_validity(
        scenario_name="lounge_seeker_vs_budget",
        twin_a_id="twin_xxx",  # Lounge seeker
        twin_b_id="twin_yyy",  # Budget traveler
        offer_factory=create_lounge_offer,
        discount=0.20,
        context=context,
        expected_ordering="a_higher"
    )
    results.append(result)
```

---

### Supporting New Datasets

1. Create new data loader (e.g., `src/airline/hotel_loader.py`)
2. Define schema (demographics, ratings, satisfaction)
3. Reuse band/tag/cohort logic (may need tweaks)
4. Generate new twin cards
5. Same prompt/LLM/evaluation infrastructure works!

---

### Switching LLM Providers

Edit `CONFIGS/airline/twin_config.yaml`:
```yaml
llm:
  provider: "anthropic"  # was "openai"
  model: "claude-3-sonnet-20240229"
  # ... other settings unchanged
```

Set API key:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

That's it! Gateway handles the rest.

---

## Summary

The Airline Digital Twin System demonstrates that **prompt engineering + data grounding** can produce reliable, explainable, and cost-effective synthetic user behavior prediction without any model training.

**Key takeaways:**
- Rich prompts > fine-tuning (for small datasets)
- Data grounding > demographics alone (reduces stereotyping)
- Evaluation matters (monotonicity, face validity, stability)
- Simple tools > complex infrastructure (CSV ledgers, YAML configs)

**Next steps for production:**
- Scale to more twins (100+)
- Add real-time API endpoint (FastAPI)
- Integrate with A/B testing platform
- Monitor decision quality over time

---

**Questions?** See other docs in `DOCS/` or open an issue on GitHub.
