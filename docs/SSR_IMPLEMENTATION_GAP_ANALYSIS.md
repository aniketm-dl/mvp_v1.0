# SSR Implementation Gap Analysis

**Date:** 2025-10-26
**Paper:** "LLMs Reproduce Human Purchase Intent via Semantic Similarity Elicitation of Likert Ratings"
**Current Codebase:** OPeRA-SSR MVP v1.0

## Executive Summary

The current implementation has a solid foundation but is missing key components from the paper's SSR methodology:

1. **Reference Statement Sets** - Core SSR component for Likert anchoring (MISSING)
2. **LLM Textual Elicitation** - Demographic-conditioned LLM responses (MISSING)
3. **Proper Contrastive Training** - Current uses stimulus-only, should be persona+stimulus (PARTIAL)
4. **Demographic Conditioning** - Prompting with persona attributes (MISSING)
5. **Correlation Attainment** - Test-retest reliability metric (MISSING)
6. **Subgroup Analysis** - Demographic fairness evaluation (MISSING)

## Detailed Gap Analysis

### 1. Reference Statement Sets (CRITICAL - MISSING)

**Paper's Approach:**
- Creates 6 reference statement sets (T1-T6) for each Likert scale point
- Each set has 5 anchor statements representing ratings 1-5
- Example (T1): ["I would never buy this" (1), ..., "I would definitely buy this" (5)]
- LLM responses are mapped to Likert via semantic similarity to these anchors
- See Paper Appendix C.1

**Current Implementation:**
```python
# src/ssr/trainer.py:138-150
def prepare_contrastive_data(self, pairs):
    for pair in pairs:
        likert_score = pair["likert_score"]
        normalized_score = (likert_score - 1) / 4.0  # 1-5 -> 0-1

        # PROBLEM: Uses stimulus text twice, no reference statements
        example = InputExample(
            texts=[pair["stimulus_text"], pair["stimulus_text"]],
            label=normalized_score,
        )
```

**Gap:** No reference statement infrastructure exists

**Impact:** HIGH - This is the core SSR methodology

**Fix Required:**
- Create reference statement sets for e-commerce domain
- Modify training to use (LLM_response, reference_statement) pairs
- Update embedding training to learn similarity between responses and anchors

---

### 2. LLM Textual Elicitation (CRITICAL - MISSING)

**Paper's Approach:**
- Prompt LLM with demographic conditioning: age, gender, income, education
- Elicit free-text response to stimulus (e.g., product description)
- Example prompt: "You are a 35-year-old male with income $75K. How do you feel about: 'Free shipping on orders over $50'?"
- Map text response to Likert via SSR (similarity to reference statements)
- See Paper Section 3.4 and Algorithm 1

**Current Implementation:**
```python
# src/data/opera/alignment.py:479-496
def extract_ssr_training_pairs(self, sessions, output_path):
    # PROBLEM: Directly uses satisfaction scores, no LLM elicitation
    pairs.append({
        "user_id": session.user_id,
        "persona_vec": persona_vec,  # 12-D vector
        "stimulus_text": stimulus_text,  # Last observation
        "likert_score": outcome["satisfaction"],  # Direct from dataset
        "rationale": final_step.rationale
    })
```

**Gap:**
- No LLM-based text generation step
- No demographic conditioning in prompts
- Rationales are from dataset, not LLM-generated with persona conditioning

**Impact:** HIGH - Missing the core "textual elicitation" step

**Fix Required:**
- Add LLM elicitation module (use gpt-4o-mini for cost efficiency)
- Create demographic-conditioned prompts from persona vectors
- Generate text responses before embedding
- Map responses to Likert via reference statement similarity

---

### 3. Contrastive Training (PARTIAL - NEEDS FIX)

**Paper's Approach:**
- Train on (persona_text, stimulus_text) similarity
- Use demographic-conditioned LLM responses as persona representation
- Contrastive loss between response embeddings and reference statement embeddings
- Likert score determines which reference statement is the positive example

**Current Implementation:**
```python
# src/ssr/trainer.py:138-150
example = InputExample(
    texts=[pair["stimulus_text"], pair["stimulus_text"]],  # WRONG: duplicate
    label=normalized_score,
)
```

**Gap:**
- Uses stimulus text twice (meaningless self-similarity)
- Should use (LLM_response, reference_statement) or (persona_text, stimulus_text)

**Impact:** MEDIUM - Training data structure incorrect

**Fix Required:**
- Change to (persona_description, stimulus_text) pairs
- Or use (LLM_response, reference_statement[likert-1]) pairs
- Properly encode persona vectors into text before embedding

---

### 4. Demographic Conditioning (MISSING)

**Paper's Approach:**
- Condition LLM prompts on demographics: age, gender, income, education
- Example: "You are a 28-year-old female, income $55K, bachelor's degree..."
- See Paper Section 4.2.1 and Appendix B

**Current Implementation:**
```python
# src/data/opera/alignment.py:446-463
def _compute_persona_vec(self, user_id, user_surveys):
    # Extracts demographics but doesn't use for conditioning
    demo_vec = [
        age_bracket,
        gender_encoded,
        income_bracket
    ]
    # Returns 12-D vector, not used in text prompts
```

**Gap:** Demographics extracted but not used for LLM conditioning

**Impact:** MEDIUM - Reduces persona differentiation

**Fix Required:**
- Add demographic-to-text conversion
- Create persona descriptions for prompting
- Use in LLM elicitation step

---

### 5. Evaluation: Correlation Attainment (MISSING)

**Paper's Metric:**
- Correlation Attainment = correlation(LLM_ratings, human_ratings) / test_retest_reliability
- Accounts for inherent human inconsistency
- Target: ≥ 0.90 (meaning LLM matches humans as well as humans match themselves)
- See Paper Section 4.1

**Current Implementation:**
```python
# scripts/07_evaluate.py:120-124
corr_results = corr_metrics.compute_all_metrics(predicted_ratings, actual_ratings)
console.print(f"  • Spearman ρ: {corr_results['spearman']['correlation']:.3f}")
# Only raw correlation, no attainment calculation
```

**Gap:** No test-retest reliability baseline or attainment metric

**Impact:** LOW - Nice-to-have for academic rigor

**Fix Required:**
- Collect test-retest data (re-rate same stimuli) OR use literature values (~0.75-0.80)
- Add correlation attainment = spearman / test_retest_baseline
- Update evaluation script

---

### 6. Demographic Subgroup Analysis (MISSING)

**Paper's Approach:**
- Test correlation separately for demographic subgroups
- Ensures fairness: model works equally well for men/women, age groups, etc.
- See Paper Section 4.2.2 and Figure 3

**Current Implementation:**
```python
# scripts/07_evaluate.py - Only overall metrics
corr_results = corr_metrics.compute_all_metrics(predicted_ratings, actual_ratings)
# No subgroup breakdown
```

**Gap:** No demographic stratification in evaluation

**Impact:** LOW - Important for fairness, not critical for MVP

**Fix Required:**
- Add subgroup evaluation loop
- Stratify by age, gender, income
- Report per-group correlations

---

## Priority Ranking

| Priority | Gap | Effort | Impact | Status |
|----------|-----|--------|--------|--------|
| P0 | Reference Statement Sets | Medium | Critical | Not Started |
| P0 | LLM Textual Elicitation | High | Critical | Not Started |
| P1 | Fix Contrastive Training | Low | High | Not Started |
| P1 | Demographic Conditioning | Medium | Medium | Not Started |
| P2 | Correlation Attainment | Low | Low | Not Started |
| P2 | Subgroup Analysis | Medium | Low | Not Started |

---

## Implementation Plan

### Phase 1: Core SSR Components (P0)

**Task 1.1: Create Reference Statement Sets**
- File: `src/ssr/reference_statements.py` (NEW)
- Content: 6 statement sets (T1-T6) with 5 anchors each (Likert 1-5)
- Domain: E-commerce purchase intent
- Example: "I would never buy this" → "I would definitely buy this"

**Task 1.2: Add LLM Elicitation Module**
- File: `src/ssr/llm_elicitation.py` (NEW)
- Function: `elicit_response(stimulus, demographics) -> text_response`
- Use OpenAI API (gpt-4o-mini for cost)
- Demographic-conditioned prompts

**Task 1.3: Update Training Data Pipeline**
- File: `src/data/opera/alignment.py`
- Modify: `extract_ssr_training_pairs()` to call LLM elicitation
- Generate: (LLM_response, reference_statement, likert_score) triplets

**Task 1.4: Fix Contrastive Training**
- File: `src/ssr/trainer.py`
- Modify: `prepare_contrastive_data()` to use proper pairs
- Use: (LLM_response, reference_statement[likert-1]) with similarity=1.0

### Phase 2: Enhanced Conditioning (P1)

**Task 2.1: Demographic Text Conversion**
- File: `src/personas/demographic_formatter.py` (NEW)
- Function: `persona_vec_to_text(vec) -> str`
- Output: "35-year-old male, income $75K, bachelor's degree"

**Task 2.2: Integrate Conditioning**
- File: `src/ssr/llm_elicitation.py`
- Update prompts to include persona descriptions
- Test with different demographic combinations

### Phase 3: Advanced Evaluation (P2)

**Task 3.1: Add Correlation Attainment**
- File: `src/evaluation/correlation.py`
- Add: `compute_attainment(pred, actual, test_retest_baseline=0.77)`
- Update: evaluation script to report attainment

**Task 3.2: Subgroup Analysis**
- File: `src/evaluation/subgroup_analysis.py` (NEW)
- Function: `evaluate_by_demographics(preds, actuals, demographics)`
- Report: correlation by age_bracket, gender, income

---

## Current vs Target Architecture

### Current (Simplified SSR)
```
OPeRA Sessions → Extract (persona_vec, stimulus, likert) →
  sentence-transformers (stimulus → embedding) →
  regression_head(embedding → likert_distribution)
```

### Target (Full SSR per Paper)
```
OPeRA Sessions → Extract demographics →
  LLM Elicitation (demographics + stimulus → text_response) →
  sentence-transformers (response → embedding) →
  Similarity(embedding, reference_statements) →
  Likert mapping via max similarity →
  Regression head training
```

---

## Testing Strategy

### Unit Tests
- `TESTS/test_reference_statements.py` - Validate statement sets
- `TESTS/test_llm_elicitation.py` - Mock LLM calls, test conditioning
- `TESTS/test_ssr_training.py` - Verify contrastive pairs correct

### Integration Tests
- `TESTS/test_end_to_end_ssr.py` - Full pipeline with small dataset
- `TESTS/test_evaluation_metrics.py` - Update for new metrics

### Quality Gates
- Correlation attainment ≥ 0.85 (target 0.90)
- KS similarity ≥ 0.80
- Demographic fairness: max_gap(correlations_by_group) < 0.10

---

## AWS Readiness Checklist

Current implementation AWS-ready for basic SSR, but needs updates for full paper implementation:

- [x] Docker container support (if needed)
- [x] S3 data sync scripts
- [x] EC2 training automation
- [ ] OpenAI API key management (for LLM elicitation)
- [ ] Cost estimation with LLM calls (~$0.01 per elicitation * N samples)
- [ ] Batch processing for LLM calls (rate limits)
- [ ] Error handling for API failures

**Estimated AWS Cost Impact:**
- Current: ~$0.50 (compute only)
- With LLM elicitation: ~$0.50 + $5-10 (OpenAI API for 500-1000 elicitations)
- Total: ~$5-10 per full training run

---

## Recommendations

### Immediate Actions (MVP)
1. Implement reference statement sets
2. Add basic LLM elicitation (100 samples for proof-of-concept)
3. Fix contrastive training pairs
4. Test end-to-end on small dataset

### Future Enhancements
1. Scale LLM elicitation to full dataset
2. Add demographic subgroup analysis
3. Implement correlation attainment
4. Optimize LLM costs (cache, batch, use cheaper models)

### Risk Mitigation
- **LLM Cost:** Start with small sample (100-500), extrapolate before full run
- **Quality:** Validate reference statements with domain experts
- **Time:** LLM calls add ~30min for 500 samples (parallel batching)

---

## Conclusion

The current implementation provides a working SSR foundation but deviates from the paper in key areas:

**Missing Core Components:**
- Reference statement sets (Appendix C.1)
- LLM textual elicitation (Section 3.4)
- Demographic conditioning (Section 4.2.1)

**Impact:** Model may underperform paper's reported accuracy without these components.

**Next Step:** Implement P0 tasks (reference statements + LLM elicitation) to align with paper methodology, then test on small dataset before full AWS training run.
