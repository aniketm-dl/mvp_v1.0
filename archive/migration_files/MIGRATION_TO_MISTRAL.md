# Migration from Llama-2 to Mistral-7B

This document explains the changes made to switch from Llama-2-7b-chat-hf to Mistral-7B-Instruct-v0.2.

---

## Why Mistral?

**Problem:** Llama-2 is behind Meta's gated access - requires approval which can take hours or days.

**Solution:** Mistral-7B-Instruct-v0.2 offers:
- ✅ **Instant access** - No approval needed
- ✅ **Better performance** - Often outperforms Llama-2
- ✅ **Same size** - 7B parameters
- ✅ **Apache 2.0 license** - Fully permissive
- ✅ **Faster training** - More efficient architecture

---

## What Changed

### Configuration Files

#### `CONFIGS/serve/llm.yaml`
```yaml
# OLD
base_model: "meta-llama/Llama-2-7b-chat-hf"

# NEW
base_model: "mistralai/Mistral-7B-Instruct-v0.2"
```

#### `.colabrc`
```ini
# OLD
[training]
base_model = "meta-llama/Llama-2-7b-chat-hf"

# NEW
[training]
base_model = "mistralai/Mistral-7B-Instruct-v0.2"
```

---

### Training Scripts

#### `scripts/train_all_adapters.py`
```python
# OLD
base_model = "meta-llama/Llama-2-7b-chat-hf"

# NEW
base_model = "mistralai/Mistral-7B-Instruct-v0.2"
```

#### `scripts/train_llm_persona_sft.py`
- Updated `find_targets()` to prioritize Mistral layer names
- Kept backward compatibility with Llama and GPT-2

---

### Notebooks

#### **NEW:** `notebooks/train_mistral_on_colab.ipynb`
- Complete training notebook for Mistral
- Includes GitHub clone option for faster setup
- No gated access steps needed
- Updated test prompts for Mistral's instruction format

#### **KEPT:** `notebooks/train_on_colab.ipynb`
- Original Llama-2 notebook preserved for reference
- Use `train_mistral_on_colab.ipynb` instead

---

### Documentation

#### **NEW:** `DOCS/MISTRAL_QUICKSTART.md`
- Quick start guide for Mistral training
- Updated workflows and commands
- Comparison table: Mistral vs Llama-2

#### **UPDATED:** `README.md`
- Points to Mistral as recommended model
- Links to GitHub repo: https://github.com/aniketm-dl/mvp_v1.0
- Updated quick start section

#### **UPDATED:** `scripts/colab/download_adapters.py`
- Recognizes both Mistral and Llama adapters
- Provides appropriate warnings

---

## How to Use

### For New Training (Recommended)

Use Mistral - it's faster and doesn't need approval!

```bash
# 1. Package code
python scripts/colab/package_for_colab.py

# 2. Upload notebooks/train_mistral_on_colab.ipynb to Colab

# 3. In Colab, clone from GitHub (faster):
!git clone https://github.com/aniketm-dl/mvp_v1.0.git
cd mvp_v1.0

# 4. Follow notebook cells

# 5. Download and extract
python scripts/colab/download_adapters.py \
  --zip ~/Downloads/llm_adapters_mistral.zip \
  --backup
```

### For Existing Llama-2 Setup

If you already have Llama-2 approval:

1. **Option A:** Continue using Llama-2
   - Keep current config
   - Use `notebooks/train_on_colab.ipynb`
   - Everything still works

2. **Option B:** Switch to Mistral (recommended)
   - Config already updated
   - Use `notebooks/train_mistral_on_colab.ipynb`
   - Re-train adapters with Mistral
   - Better performance!

---

## Backward Compatibility

✅ **Training script** supports both models automatically
- Auto-detects GPT-2, Llama, or Mistral layers
- No code changes needed

✅ **Old adapters** still work
- Llama-2 adapters: Set config to `meta-llama/Llama-2-7b-chat-hf`
- GPT-2 adapters: Set config to `gpt2`
- Mistral adapters: Set config to `mistralai/Mistral-7B-Instruct-v0.2`

✅ **Documentation** preserved
- Old Llama-2 docs kept for reference
- New Mistral docs added alongside

---

## GitHub Integration

**Repository:** https://github.com/aniketm-dl/mvp_v1.0

**Benefit:** Clone directly in Colab instead of uploading zip files!

```python
# In Colab (Cell 3B)
!git clone https://github.com/aniketm-dl/mvp_v1.0.git
cd mvp_v1.0
```

Faster and easier than Google Drive uploads!

---

## Technical Details

### Model Architecture

Both models use similar architectures with slight differences:

| Component | Llama-2-7b | Mistral-7B |
|-----------|------------|------------|
| **Parameters** | 7.0B | 7.2B |
| **Attention** | GQA | GQA |
| **Context window** | 4096 | 8192 (better!) |
| **Vocab size** | 32000 | 32000 |
| **LoRA targets** | q_proj, v_proj | q_proj, v_proj |

### Training Compatibility

The same training code works for both because:
1. Same transformer architecture family
2. Same tokenization approach
3. Same LoRA target layers
4. `find_targets()` function auto-detects layer names

### Prompt Format

**Llama-2:**
```
You are {persona}. Be concise. 1 sentence.
User: {prompt}
Assistant:
```

**Mistral (recommended):**
```
[INST] You are {persona}. Be concise. 1-2 sentences. {prompt} [/INST]
```

The code handles both formats automatically.

---

## Performance Comparison

Based on typical benchmarks:

| Metric | Llama-2-7b-chat | Mistral-7B-Instruct |
|--------|-----------------|---------------------|
| **MMLU** | 48.3 | 60.1 ✅ |
| **GSM8K** | 14.6 | 40.7 ✅ |
| **HumanEval** | 12.8 | 30.5 ✅ |
| **Training speed** | 1.0x | 1.1-1.2x ✅ |
| **Instruction following** | Good | Excellent ✅ |

**Verdict:** Mistral is significantly better across the board.

---

## Migration Checklist

If switching from an existing Llama-2 setup:

- [ ] Verify `CONFIGS/serve/llm.yaml` shows Mistral
- [ ] Use `notebooks/train_mistral_on_colab.ipynb` for training
- [ ] Update local code: `git pull origin main`
- [ ] Re-train adapters on Colab with Mistral
- [ ] Download `llm_adapters_mistral.zip`
- [ ] Extract with backup: `--backup` flag
- [ ] Test with `python interact_cli.py`
- [ ] Compare quality with old adapters
- [ ] Delete old Llama-2 adapters if satisfied

---

## FAQ

### Q: Do I need to delete Llama-2 code?
**A:** No! Everything is backward compatible. Both models work.

### Q: Can I use both Llama-2 and Mistral?
**A:** Yes! Just change `base_model` in config and restart.

### Q: Will my old adapters still work?
**A:** Yes, as long as you point config to the right base model.

### Q: Should I retrain with Mistral?
**A:** Yes, recommended! Better performance and no access wait.

### Q: How much better is Mistral?
**A:** 10-20% better on instruction tasks, similar persona quality.

### Q: Does this cost more?
**A:** No, same Colab Pro cost. Mistral is free like Llama-2.

---

## Summary

**What you need to know:**
1. ✅ Mistral is now the default model
2. ✅ No approval wait - works immediately
3. ✅ Use `notebooks/train_mistral_on_colab.ipynb`
4. ✅ Clone from GitHub in Colab (faster)
5. ✅ Better performance than Llama-2
6. ✅ Everything else stays the same

**Quick start:**
```bash
# Read the guide
cat DOCS/MISTRAL_QUICKSTART.md

# Follow the 5 steps
# Your 18 Mistral-powered twins will be ready in 2-4 hours!
```

---

**Questions?** Ask Claude Code for help with migration!
