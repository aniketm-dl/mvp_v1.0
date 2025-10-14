# Google Colab Quick Start

**TL;DR:** Train your 18 personas on Google Colab GPU in 2-4 hours.

---

## Prerequisites (One-time Setup)

1. **Google Colab Pro:** https://colab.research.google.com/signup ($9.99/month)
2. **HuggingFace Token:** https://huggingface.co/settings/tokens (free)
3. **Llama-2 Access:** https://huggingface.co/meta-llama/Llama-2-7b-chat-hf (click "Agree and access")

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

1. Go to: https://drive.google.com/
2. Upload the zip file from `colab_packages/`

---

### 3️⃣ Train on Colab

1. Open: https://colab.research.google.com/
2. Upload notebook: `notebooks/train_on_colab.ipynb`
3. **Runtime > Change runtime type > GPU > T4**
4. Run all cells sequentially
5. Wait 2-4 hours (you can close the tab)

**Critical cells:**
- Cell 5: Paste your HuggingFace token
- Cell 8: Test with 1 persona first (~10 min)
- Cell 10: Train all 18 personas (~2-4 hours)
- Cell 13: Saves adapters to Google Drive

---

### 4️⃣ Download Adapters (Local)

1. Download `llm_adapters_llama2.zip` from Google Drive
2. Extract:

```bash
cd /path/to/darpan-whatif-simulator
source .venv/bin/activate

python scripts/colab/download_adapters.py \
  --zip ~/Downloads/llm_adapters_llama2.zip \
  --backup
```

---

### 5️⃣ Test Locally

```bash
source .venv/bin/activate
python interact_cli.py
```

**First run:** Will download Llama-2 base model (~13GB, one-time)

---

## Troubleshooting

### "Llama-2 access denied"
- Accept license: https://huggingface.co/meta-llama/Llama-2-7b-chat-hf
- Wait 5 minutes
- Get new token: https://huggingface.co/settings/tokens

### "Out of memory"
- Use T4 GPU (most reliable)
- If still failing, ask Claude Code to add 4-bit quantization

### "Bus error" locally
- Check: `cat CONFIGS/serve/llm.yaml`
- Should show: `base_model: "meta-llama/Llama-2-7b-chat-hf"`
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
- **HuggingFace:** Free
- **Llama-2 model:** Free

**Total:** $9.99/month (cancel anytime)

---

## Time Estimates

| Task | Time |
|------|------|
| Package code | 1 min |
| Upload to Drive | 2-5 min |
| Setup Colab | 5 min |
| Test training (1 persona) | 5-15 min |
| Full training (18 personas) | 2-4 hours |
| Download & extract | 5-10 min |

**Total first run:** ~2.5-4.5 hours (mostly unattended)

---

## Pro Tips

✅ **Always test with 1 persona first** (Cell 8) before training all 18

✅ **Keep browser tab open** during training (or enable background execution in Colab Pro)

✅ **Use `--backup` flag** when extracting adapters (keeps old versions just in case)

✅ **Use Claude Code** for all development work locally - only use Colab for GPU training

---

**Full docs:** See `DOCS/COLAB_WORKFLOW.md` for detailed guide
