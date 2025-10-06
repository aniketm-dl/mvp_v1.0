# Google Colab Quick Start - Mistral Edition

**TL;DR:** Train your 18 personas on Google Colab GPU using Mistral-7B-Instruct in 2-4 hours.

---

## Why Mistral Instead of Llama-2?

✅ **No gated access** - Works immediately, no approval wait
✅ **Better performance** - Often outperforms Llama-2-7b
✅ **Same size** - 7B parameters
✅ **Apache 2.0 license** - Fully open and permissive
✅ **Faster training** - Slightly more efficient

---

## Prerequisites (One-time Setup)

1. **Google Colab Pro:** https://colab.research.google.com/signup ($9.99/month)
2. **HuggingFace Token:** https://huggingface.co/settings/tokens (free - no approval needed!)

---

## 5-Step Workflow

### 1️⃣ Package Your Code (Local)

```bash
cd /path/to/darpan-whatif-simulator
source .venv/bin/activate
python scripts/colab/package_for_colab.py
```

**Output:** `colab_packages/darpan-whatif-simulator_TIMESTAMP.zip`

---

### 2️⃣ Upload to Google Drive

**Option A: Upload zip file**
1. Go to: https://drive.google.com/
2. Upload the zip file from `colab_packages/`

**Option B: Use GitHub**
- Code is already on GitHub: https://github.com/aniketm-dl/mvp_v1.0
- Skip this step and clone directly in Colab!

---

### 3️⃣ Train on Colab

1. Open: https://colab.research.google.com/
2. Upload notebook: `notebooks/train_mistral_on_colab.ipynb`
3. **Runtime > Change runtime type > GPU > T4**
4. Choose either:
   - **Cell 3A:** Extract from Google Drive
   - **Cell 3B:** Clone from GitHub ✨ (easier!)
5. Run all cells sequentially
6. Wait 2-4 hours (you can close the tab)

**Critical cells:**
- Cell 5: Paste your HuggingFace token
- Cell 6: Verify Mistral access (should work immediately!)
- Cell 8: Test with 1 persona first (~10 min)
- Cell 10: Train all 18 personas (~2-4 hours)
- Cell 13: Saves adapters to Google Drive

---

### 4️⃣ Download Adapters (Local)

1. Download `llm_adapters_mistral.zip` from Google Drive
2. Extract:

```bash
cd /path/to/darpan-whatif-simulator
source .venv/bin/activate

python scripts/colab/download_adapters.py \
  --zip ~/Downloads/llm_adapters_mistral.zip \
  --backup
```

---

### 5️⃣ Test Locally

```bash
source .venv/bin/activate
python interact_cli.py
```

**First run:** Will download Mistral base model (~13GB, one-time)

---

## Troubleshooting

### "Mistral access denied" (Unlikely!)
- Mistral is NOT gated - should work immediately
- Try getting a fresh token: https://huggingface.co/settings/tokens
- Make sure token has "read" permission

### "Out of memory"
- Use T4 GPU (most reliable)
- If still failing, reduce batch size in training script

### "Bus error" locally
- Check: `cat CONFIGS/serve/llm.yaml`
- Should show: `base_model: "mistralai/Mistral-7B-Instruct-v0.2"`
- Re-extract adapters with `--backup` flag

---

## When to Re-train

**Re-train when you:**
- Add/modify personas
- Change training data (DATA/sft/*.jsonl)
- Want to try different hyperparameters

**Don't need to re-train when:**
- Changing API code
- Modifying prompts/templates
- Testing different scenarios

---

## Cost

- **Google Colab Pro:** $9.99/month
- **Training:** Free (included)
- **HuggingFace:** Free (no approval needed!)
- **Mistral model:** Free

**Total:** $9.99/month (cancel anytime)

---

## Time Estimates

| Task | Time |
|------|------|
| Package code | 1 min |
| Upload to Drive (or skip with GitHub) | 0-5 min |
| Setup Colab | 5 min |
| Test training (1 persona) | 5-15 min |
| Full training (18 personas) | 2-4 hours |
| Download & extract | 5-10 min |

**Total first run:** ~2.5-4.5 hours (mostly unattended)

---

## Pro Tips

✅ **Use GitHub clone option** in Colab (faster than Drive upload)

✅ **Always test with 1 persona first** (Cell 8) before training all 18

✅ **Keep browser tab open** during training (or enable background execution in Colab Pro)

✅ **Use `--backup` flag** when extracting adapters

✅ **Use Claude Code** for all development work locally - only use Colab for GPU training

---

## Mistral vs Llama-2

| Feature | Mistral-7B | Llama-2-7b |
|---------|------------|------------|
| **Access** | ✅ Instant | ❌ Gated (wait for approval) |
| **License** | Apache 2.0 | Llama 2 (more restrictive) |
| **Performance** | ✅ Better | Good |
| **Training speed** | ✅ Slightly faster | Standard |
| **Parameters** | 7B | 7B |
| **Instruction following** | ✅ Excellent | Good |

**Verdict:** Mistral is the better choice for this project!

---

**Full docs:** See `DOCS/MISTRAL_WORKFLOW.md` for detailed guide
