# Encoder Ablation Checklist

## Overview

This checklist documents the ablation experiments for the multi-view encoder, following the OPeRA methodology to verify that each view contributes meaningful signal.

## Ablation Configurations

### 1. Full Model (Baseline)
- **Config**: All views enabled
- **Components**:
  - ✅ Sequence encoder (observations + actions)
  - ✅ Rationale encoder
  - ✅ Persona encoder
  - ✅ Catalog encoder
- **Expected**: Best performance

### 2. No Persona (`disable_persona=True`)
- **Config**: Zero out persona embedding before fusion
- **Components**:
  - ✅ Sequence encoder
  - ✅ Rationale encoder
  - ❌ Persona encoder (zeroed)
  - ✅ Catalog encoder
- **Expected**: Drop in next-action accuracy and persona alignment metrics
- **Hypothesis**: Persona provides user-specific context that improves action prediction

### 3. No Rationale (`disable_rationale=True`)
- **Config**: Zero out rationale embedding before fusion
- **Components**:
  - ✅ Sequence encoder
  - ❌ Rationale encoder (zeroed)
  - ✅ Persona encoder
  - ✅ Catalog encoder
- **Expected**: Drop in next-action accuracy
- **Hypothesis**: Rationale provides intent signal that complements behavioral patterns

### 4. No Alignment (`disable_persona=True, disable_rationale=True`)
- **Config**: Zero out both persona and rationale
- **Components**:
  - ✅ Sequence encoder
  - ❌ Rationale encoder (zeroed)
  - ❌ Persona encoder (zeroed)
  - ✅ Catalog encoder
- **Expected**: Largest performance drop
- **Hypothesis**: Only sequence + catalog is insufficient for strong predictions

## Metrics to Track

### Primary Metrics
1. **Next-Action Top-1 Accuracy**
   - Full model baseline: Target ≥ 0.70
   - Ablation degradation: Expected 5-15% drop per view

2. **Persona Alignment Recall@10**
   - Full model baseline: Target ≥ 0.50
   - No persona: Expected major drop (>30%)
   - No rationale: Expected minor drop (5-10%)

### Secondary Metrics
3. **Next-Action Top-3 Accuracy**
   - Track softmax confidence distribution

4. **Embedding Quality**
   - Mean norm (should be stable ~1.0 after normalization)
   - Standard deviation (higher variance = more expressive)

## Expected Results (OPeRA-style)

Based on OPeRA findings, we expect:

| Ablation | Top-1 Acc | Δ from Full | Recall@10 | Δ from Full |
|----------|-----------|-------------|-----------|-------------|
| Full | 0.72 | - | 0.55 | - |
| No Persona | 0.65 | -0.07 | 0.25 | -0.30 |
| No Rationale | 0.68 | -0.04 | 0.50 | -0.05 |
| No Alignment | 0.60 | -0.12 | 0.20 | -0.35 |

**Key Findings to Validate:**
1. Persona provides strongest signal for alignment (large recall drop)
2. Rationale provides moderate signal for action prediction
3. Both views contribute independently (no alignment ≠ sum of individual drops)

## How to Run Ablations

### Via Config
Edit `CONFIGS/encoder.yaml`:
```yaml
ablation:
  enabled: true
  ablations:
    - name: "full"
      disable_persona: false
      disable_rationale: false
    - name: "no_persona"
      disable_persona: true
      disable_rationale: false
    - name: "no_rationale"
      disable_persona: false
      disable_rationale: true
    - name: "no_alignment"
      disable_persona: true
      disable_rationale: true
```

### Via Evaluation Script
```bash
python src/metrics/encoder_eval.py \
  --ckpt artifacts/encoder/best.ckpt \
  --data DATA/OPeRA/processed \
  --config CONFIGS/encoder.yaml \
  --out artifacts/encoder/eval
```

### Manual Testing
```python
from src.models.encoder.fuser import MultiViewEncoder

# Forward with ablation
outputs = model(
    seq_tokens,
    rationale_tokens,
    persona_vec,
    catalog_vec,
    disable_persona=True  # Ablate persona
)
```

## Validation Criteria

### Pass Criteria
✅ **Full model** achieves top-1 accuracy > 0.60
✅ **No persona** drops by ≥5% in top-1 accuracy
✅ **No rationale** drops by ≥3% in top-1 accuracy
✅ **No alignment** shows worst performance (cumulative effect)
✅ Persona alignment recall@10 drops by ≥20% when persona is disabled

### Fail Criteria
❌ No performance gap between ablations (views not used)
❌ Ablations improve performance (bug in implementation)
❌ Full model performs worse than ablations (fusion broken)
❌ All ablations perform identically (zeroing not working)

## Common Issues and Debugging

### Issue: No ablation gap
**Possible causes:**
- Ablation flags not propagated correctly
- Fusion MLP not using zeroed embeddings
- Loss weights dominate one objective

**Debug steps:**
1. Verify zeroing in `FusionMLP.forward()`
2. Check that fused embeddings differ across ablations
3. Print intermediate embeddings to confirm zeros

### Issue: Full model underperforms
**Possible causes:**
- Insufficient training epochs
- Learning rate too high/low
- Loss weight imbalance

**Debug steps:**
1. Check training curves for convergence
2. Verify loss components are balanced (similar magnitudes)
3. Inspect embedding norms (should be ~1.0)

### Issue: Collapsed embeddings
**Possible causes:**
- InfoNCE temperature too low
- Not enough negatives in batch
- Gradient clipping too aggressive

**Debug steps:**
1. Increase temperature (0.07 → 0.1)
2. Increase batch size
3. Check embedding std (should be >0.1)

## Reporting Template

```markdown
## Ablation Results

**Model**: encoder-epoch42-val0.720
**Dataset**: OPeRA test split (N=XXX steps)
**Date**: YYYY-MM-DD

### Performance Summary

| Ablation | Top-1 | Top-3 | Top-5 | Recall@10 |
|----------|-------|-------|-------|-----------|
| Full     | 0.72  | 0.88  | 0.94  | 0.55      |
| No Persona | 0.65  | 0.84  | 0.91  | 0.25      |
| No Rationale | 0.68  | 0.86  | 0.92  | 0.50      |
| No Alignment | 0.60  | 0.80  | 0.89  | 0.20      |

### Key Findings

1. **Persona signal is strong**: Removing persona drops top-1 by 7% and recall by 30%
2. **Rationale provides intent**: Rationale ablation shows 4% top-1 drop
3. **Views are complementary**: Combined ablation (12% drop) > sum of individual drops

### Conclusion

✅ All views contribute meaningful signal
✅ Ablation gaps align with OPeRA expectations
✅ Model ready for production use
```

## References

- OPeRA paper: Observation-Persona-Rationale-Action alignment
- InfoNCE: Contrastive learning for alignment
- Multi-view learning: Fusion strategies
