# Airline Digital Twin Evaluation Guide

## Overview

The evaluation framework validates that airline twins behave rationally, consistently, and realistically.

## Test Categories

### 1. Monotonicity Tests

**Purpose:** Verify that higher discounts never decrease acceptance probability.

**Logic:** If a twin accepts an offer at 10% discount with probability 0.6, they should accept at 20% discount with probability ≥ 0.6.

**Example:**
```python
# Twin evaluates legroom offer at multiple discount levels
Discounts: [10%, 20%, 30%, 40%]
Probabilities: [0.55, 0.70, 0.82, 0.90]  # ✅ Monotonic

# Violation example:
Probabilities: [0.55, 0.70, 0.65, 0.90]  # ❌ Dropped at 30%
```

**Pass Criteria:** ≥95% of test cases pass (5% tolerance for small variations)

---

### 2. Face Validity Tests

**Purpose:** Verify twins behave according to their psychographic profiles.

**Scenarios:**

**Scenario A: Comfort vs Value on Legroom**
- **Twin A:** `twin_002` (Comfort seeker, 35-44, business class)
- **Twin B:** `twin_006` (Value conscious, 35-44, eco-plus)
- **Offer:** Extra legroom at 15% discount
- **Expected:** Twin A (comfort) ≥ Twin B (value)
- **Rationale:** Comfort-seekers prioritize physical comfort; value-conscious passengers need larger discounts

**Scenario B: Business vs Leisure on Priority Boarding**
- **Twin A:** `twin_009` (Business-oriented, 25-34, business traveler)
- **Twin B:** `twin_003` (Leisure, 55+, personal travel)
- **Offer:** Priority boarding at 15% discount
- **Expected:** Twin A (business) ≥ Twin B (leisure)
- **Rationale:** Business travelers value efficiency; leisure travelers less time-pressured

**Pass Criteria:** ≥95% of scenarios match expected behavior

---

### 3. Stability Tests

**Purpose:** Verify deterministic behavior with fixed random seeds.

**Logic:** Same twin + same offer + same seed = same result, every time.

**Example:**
```python
# Run decision 3 times with seed=42
Trial 1: probability = 0.653
Trial 2: probability = 0.653  # ✅ Identical
Trial 3: probability = 0.653  # ✅ Identical
```

**Pass Criteria:** 100% stability (all repeated trials must be identical)

---

### 4. Cohort Coherence Tests (Future)

**Purpose:** Verify that twins from the same cohort behave similarly.

**Logic:** Twins with similar demographics/psychographics should have similar acceptance probabilities (within reasonable variance).

---

## Running Evaluation

### Quick Evaluation (Sample Tests)

```bash
# Run core test suite on sample twins
python src/airline/evaluator.py
```

This runs:
- 3 monotonicity tests (twins 001, 002, 006)
- 2 face validity scenarios
- 2 stability tests (twins 001, 005)

**Expected time:** 3-5 minutes (depending on LLM API speed)

**Expected cost:** ~$0.05-0.15 (depending on model)

---

### Full Evaluation with Report

```bash
# Run full suite and generate markdown report
python scripts/evaluate_twins.py \
  --save-report DATA/airline/evaluation_report.md \
  --save-json DATA/airline/evaluation_results.json
```

**Outputs:**
1. **Markdown report:** Human-readable evaluation summary with detailed test results
2. **JSON results:** Machine-readable data for further analysis

---

## Interpreting Results

### Success Criteria

| Category | Target | Critical? |
|----------|--------|-----------|
| Monotonicity | ≥95% | Yes |
| Face Validity | ≥95% | Yes |
| Stability | 100% | Yes |
| Overall | All critical pass | Yes |

### Example Output

```
================================================================================
EVALUATION SUMMARY
================================================================================
Monotonicity:     3/3 (100%)
Face Validity:    2/2 (100%)
Stability:        2/2 (100%)

Overall: ✅ PASSED
================================================================================
```

---

## Common Issues & Solutions

### Issue: Monotonicity Violations

**Symptom:** Probability drops at higher discount

**Possible causes:**
1. LLM being creative with rationale
2. Temperature too high (try lowering to 0.1)
3. Insufficient grounding in cohort priors

**Solution:**
```yaml
# Edit CONFIGS/airline/twin_config.yaml
llm:
  temperature: 0.1  # Lower = more deterministic
  model: gpt-4      # More reliable than gpt-3.5-turbo
```

---

### Issue: Face Validity Failures

**Symptom:** Twin behaves contrary to their profile

**Possible causes:**
1. Prompt doesn't emphasize psychographic tags strongly enough
2. Cohort priors contradict twin's individual traits
3. Context dominates over personality

**Solution:**
1. Review system prompt template
2. Add explicit instructions: "Your {tag} trait means you prioritize..."
3. Adjust discount ladder hints in cohort priors

---

### Issue: Stability Failures

**Symptom:** Different results with same seed

**Possible causes:**
1. Seed not supported by model (Claude doesn't support seed)
2. API-side caching issues
3. Non-deterministic sampling despite seed

**Solution:**
- Use OpenAI GPT-4 or GPT-3.5-turbo (seed support)
- Set temperature=0.0 for maximum determinism
- Verify seed is being passed to API

---

### Issue: High API Costs

**Symptom:** Evaluation costs more than expected

**Solutions:**
1. Use GPT-3.5-turbo instead of GPT-4 ($0.0001 vs $0.01 per decision)
2. Run sample tests first, then full suite only when needed
3. Cache results for repeated tests

---

## Custom Test Scenarios

You can add your own face validity tests by modifying `src/airline/evaluator.py`:

```python
# Add to run_face_validity_tests()
result = self.test_face_validity(
    scenario_name="your_scenario_name",
    twin_a_id="twin_xxx",
    twin_b_id="twin_yyy",
    offer_factory=create_wifi_offer,
    discount=0.25,
    context=context,
    expected_ordering="a_higher"  # or "b_higher"
)
```

---

## Advanced: Batch Evaluation

To test all 12 twins across all 5 offers:

```python
from src.airline.evaluator import TwinEvaluator

evaluator = TwinEvaluator(config_path, templates_dir, twins_dir)

# Test all twins
all_twin_ids = [f"twin_{i:03d}" for i in range(1, 13)]
offer_factories = [
    create_legroom_offer,
    create_wifi_offer,
    create_lounge_offer,
    create_priority_boarding_offer,
    create_baggage_offer
]

for twin_id in all_twin_ids:
    for offer_factory in offer_factories:
        result = evaluator.test_monotonicity(
            twin_id,
            offer_factory,
            [0.1, 0.2, 0.3],
            context
        )
        # Process result...
```

**Note:** This will make 60+ API calls (expensive!)

---

## Next Steps

After evaluation passes:

1. **Phase 6:** Build interactive CLI for batch decisions
2. **Phase 6:** Implement decision ledger for audit trail
3. **Phase 7:** Create comprehensive documentation
4. **Phase 7:** Build Jupyter notebook demo

---

## Reference

- **Evaluator code:** `src/airline/evaluator.py`
- **Evaluation script:** `scripts/evaluate_twins.py`
- **Unit tests:** `TESTS/airline/test_evaluator.py`
- **Config:** `CONFIGS/airline/twin_config.yaml`

---

**Questions?** Check the main README or open an issue.
