# ✅ Google Colab Setup Complete!

Your project is now ready for GPU training on Google Colab Pro.

---

## 📦 What's Been Set Up

### 1. Colab Training Notebook
- **File:** `notebooks/train_on_colab.ipynb`
- **Purpose:** Complete end-to-end training on Colab GPU
- **Features:**
  - GPU verification
  - Dependency installation
  - HuggingFace authentication
  - Test training (1 persona)
  - Full training (18 personas)
  - Package and download

### 2. Helper Scripts

#### Package for Upload
- **Python:** `scripts/colab/package_for_colab.py` (cross-platform)
- **Bash:** `scripts/colab/package_for_colab.sh` (Mac/Linux)
- **Purpose:** Create clean zip of codebase for Colab
- **Excludes:** venv, adapters, cache files, git

#### Download Adapters
- **File:** `scripts/colab/download_adapters.py`
- **Purpose:** Extract trained adapters from Colab zip
- **Features:**
  - Automatic backup of existing adapters
  - Verification of extracted files
  - Config validation

### 3. Configuration Files

#### LLM Config
- **File:** `CONFIGS/serve/llm.yaml`
- **Settings:**
  ```yaml
  use_stub: false
  base_model: "meta-llama/Llama-2-7b-chat-hf"
  temperature: 0.3
  top_p: 0.9
  max_new_tokens: 50
  ```

#### Training Scripts Updated
- `scripts/train_llm_persona_sft.py` - Supports both GPT-2 and Llama-2
- `scripts/train_all_adapters.py` - Uses Llama-2 by default

### 4. Documentation

#### Quick Start Guide
- **File:** `DOCS/COLAB_QUICKSTART.md`
- **Content:** 5-step workflow summary
- **Time to read:** 2 minutes

#### Complete Workflow Guide
- **File:** `DOCS/COLAB_WORKFLOW.md`
- **Content:**
  - Prerequisites setup
  - Step-by-step instructions
  - Claude Code integration
  - Troubleshooting
  - Cost estimates
- **Time to read:** 10-15 minutes

#### Updated README
- **File:** `README.md`
- **Added:** Links to Colab docs, workflow overview

---

## 🚀 Next Steps

### Step 1: Read the Quick Start
```bash
cat DOCS/COLAB_QUICKSTART.md
# Or open in your editor
```

### Step 2: Set Up Prerequisites (10 minutes)

1. **Google Colab Pro**
   - Visit: https://colab.research.google.com/signup
   - Subscribe: $9.99/month
   - Can cancel anytime

2. **HuggingFace Token**
   - Visit: https://huggingface.co/settings/tokens
   - Create token with "read" access
   - Save it somewhere safe

3. **Llama-2 Access**
   - Visit: https://huggingface.co/meta-llama/Llama-2-7b-chat-hf
   - Click "Agree and access repository"
   - Wait 5 minutes for access to propagate

### Step 3: Package Your Code (1 minute)

```bash
# From project root
source .venv/bin/activate
python scripts/colab/package_for_colab.py
```

**Output:** `colab_packages/darpan-whatif-simulator_TIMESTAMP.zip`

### Step 4: Upload to Google Drive (2-5 minutes)

1. Go to: https://drive.google.com/
2. Click "New" > "File upload"
3. Select the zip from `colab_packages/`
4. Wait for upload

### Step 5: Train on Colab (2-4 hours, unattended)

1. Go to: https://colab.research.google.com/
2. Upload notebook: `notebooks/train_on_colab.ipynb`
3. **Runtime > Change runtime type > GPU > T4**
4. Run all cells
5. When prompted, paste your HuggingFace token
6. Wait for training to complete (can close browser)

### Step 6: Download and Test (10 minutes)

```bash
# Download llm_adapters_llama2.zip from Google Drive
# Then extract:

cd /path/to/darpan-whatif-simulator
source .venv/bin/activate

python scripts/colab/download_adapters.py \
  --zip ~/Downloads/llm_adapters_llama2.zip \
  --backup

# Test
python interact_cli.py
```

---

## 💡 Working with Claude Code

### What Claude Code Can Do

1. **Help you iterate on personas**
   ```
   You: "Add a new persona called 'The Early Adopter'"

   Claude will:
   - Add to DATA/personas.json
   - Create training data
   - Update scripts if needed
   ```

2. **Generate better training data**
   ```
   You: "Generate 50 training examples for the Bargain Hunter persona"

   Claude will:
   - Create varied scenarios
   - Generate persona-appropriate responses
   - Save to DATA/sft/bargain_hunter.jsonl
   ```

3. **Debug issues**
   ```
   You: "The premium_loyalist adapter isn't loading. Why?"

   Claude will:
   - Check adapter files
   - Verify config
   - Test loading
   - Suggest fixes
   ```

4. **Analyze results**
   ```
   You: "Compare responses of all 18 personas for this scenario: [paste]"

   Claude will:
   - Load each adapter
   - Run the scenario
   - Show differences
   - Identify patterns
   ```

### The Hybrid Workflow

```
┌─────────────────────────────────────────────────┐
│                                                 │
│  LOCAL (with Claude Code)                       │
│  • Code changes                                 │
│  • Training data creation                       │
│  • Testing & debugging                          │
│  • Evaluation                                   │
│                                                 │
└─────────────┬───────────────────────────────────┘
              │
              │ Package & Upload
              ▼
┌─────────────────────────────────────────────────┐
│                                                 │
│  GOOGLE COLAB                                   │
│  • GPU training (2-4 hours)                     │
│  • Runs in background                           │
│  • No local resources used                      │
│                                                 │
└─────────────┬───────────────────────────────────┘
              │
              │ Download Adapters
              ▼
┌─────────────────────────────────────────────────┐
│                                                 │
│  LOCAL (with Claude Code)                       │
│  • Test new adapters                            │
│  • Compare with old versions                    │
│  • Run evaluations                              │
│  • Iterate if needed                            │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 📊 Expected Results

### After Training on Colab

**What you'll have:**
- 18 fine-tuned Llama-2 adapters (~5MB each, ~100MB total)
- Each adapter specialized for a specific persona
- Natural conversational ability
- Context-aware responses

**Performance improvements over stub mode:**
- 🗣️ Natural conversation flow
- 🎯 Persona consistency
- 💬 Contextual understanding
- 📝 Better reasoning
- 🔀 More variety in responses

### Example Conversation (Before vs After)

#### Before (Stub Mode):
```
You: "Should I buy from Amazon or local shop?"
Local Supporter: I choose products that align with my values [community_oriented].
```

#### After (Llama-2 Adapter):
```
You: "Should I buy from Amazon or local shop?"
Local Supporter: I'd definitely go with the local shop - supporting small
businesses keeps money in our community and creates real relationships, even
if it costs a bit more or takes longer to get.
```

---

## 🔧 Configuration Reference

### Project Structure After Setup

```
darpan-whatif-simulator/
├── notebooks/
│   └── train_on_colab.ipynb          ← Upload to Colab
├── scripts/
│   ├── colab/
│   │   ├── package_for_colab.py      ← Run before upload
│   │   ├── package_for_colab.sh      ← Alternative (Mac/Linux)
│   │   └── download_adapters.py      ← Run after training
│   ├── train_llm_persona_sft.py      ← Updated for Llama-2
│   └── train_all_adapters.py         ← Updated for Llama-2
├── CONFIGS/
│   └── serve/
│       └── llm.yaml                   ← Updated config
├── DOCS/
│   ├── COLAB_QUICKSTART.md           ← 5-step guide
│   ├── COLAB_WORKFLOW.md             ← Complete guide
│   └── SETUP_COMPLETE.md             ← This file
├── colab_packages/                    ← Generated by packaging
│   └── darpan-whatif-simulator_*.zip
└── artifacts/                         ← After training
    └── llm_adapters/                  ← 18 trained adapters
        ├── bargain_hunter/
        ├── premium_loyalist/
        └── ... (16 more)
```

---

## 💰 Cost Summary

| Item | Cost | Notes |
|------|------|-------|
| **Google Colab Pro** | $9.99/month | Cancel anytime |
| **HuggingFace** | Free | No credit card needed |
| **Llama-2 Model** | Free | Meta's open model |
| **Training** | $0 | Included in Colab Pro |
| **Storage** | ~0.5GB | For adapters |

**Total:** $9.99/month

**Worth it if:**
- ✅ You'll iterate 2+ times on personas
- ✅ You want 10x faster training
- ✅ Your laptop doesn't have GPU
- ✅ You want to preserve laptop battery/lifespan

---

## ⏱️ Time Estimates

### First-Time Setup
- Read documentation: 15 min
- Set up prerequisites: 10 min
- Package code: 1 min
- Upload to Drive: 5 min
- Setup Colab notebook: 5 min
- **Total:** ~35 minutes

### Training Run
- Test training (1 persona): 10-15 min
- Full training (18 personas): 2-4 hours ⏰
- Download & extract: 10 min
- **Total:** ~2.5-4.5 hours (mostly unattended)

### Subsequent Iterations
- Package updated code: 1 min
- Re-upload: 2 min
- Re-train: 2-4 hours ⏰
- Download & extract: 10 min
- **Total:** ~2.5-4.5 hours (mostly unattended)

---

## 🐛 Common Issues & Solutions

### Issue: Can't access Llama-2 on Colab
**Solution:**
1. Ensure you accepted license
2. Wait 5-10 minutes after accepting
3. Use a fresh HuggingFace token
4. Check token has "read" permission

### Issue: Out of memory during training
**Solution:**
1. Use T4 GPU (most reliable)
2. Close other Colab notebooks
3. Restart Colab runtime
4. Try off-peak hours (better GPU allocation)

### Issue: Colab disconnects during training
**Solution:**
1. Keep browser tab open
2. Don't let computer sleep
3. Use Colab Pro background execution
4. Add checkpoint saving (ask Claude Code)

### Issue: Local testing shows "bus error"
**Solution:**
```bash
# Verify config
cat CONFIGS/serve/llm.yaml
# Should show: meta-llama/Llama-2-7b-chat-hf

# Re-extract adapters with backup
python scripts/colab/download_adapters.py \
  --zip ~/Downloads/llm_adapters_llama2.zip \
  --backup
```

---

## 📞 Getting Help

### Ask Claude Code
Claude Code can help with:
- Understanding the workflow
- Debugging issues
- Generating training data
- Analyzing results
- Modifying configurations

Example prompts:
```
"Walk me through the Colab workflow step by step"
"The training failed with error X. How do I fix it?"
"Generate 100 training examples for a new persona"
"Compare the outputs of these 5 personas"
```

### Check Documentation
- **Quick reference:** `DOCS/COLAB_QUICKSTART.md`
- **Complete guide:** `DOCS/COLAB_WORKFLOW.md`
- **Project rules:** `.claude/CLAUDE.md`

---

## 🎉 You're Ready!

Everything is set up for GPU training on Google Colab. The hybrid workflow lets you:

✅ Use Claude Code for fast local development
✅ Use Colab GPU for heavy training
✅ Iterate quickly on personas
✅ Test everything locally

**Start with:** `cat DOCS/COLAB_QUICKSTART.md`

Good luck! 🚀
