# Google Colab Training Workflow

Complete guide for training Digital Twin adapters on Google Colab and using them locally with Claude Code.

---

## 📋 Table of Contents

1. [Why Use Google Colab?](#why-use-google-colab)
2. [Prerequisites](#prerequisites)
3. [Step-by-Step Workflow](#step-by-step-workflow)
4. [Using Claude Code with Colab](#using-claude-code-with-colab)
5. [Troubleshooting](#troubleshooting)
6. [Cost & Time Estimates](#cost--time-estimates)

---

## Why Use Google Colab?

**Local laptop limitations:**
- Llama-2-7b requires 16GB+ GPU memory
- Training 18 personas would take 10-20 hours on CPU
- Risk of thermal throttling

**Google Colab Pro advantages:**
- T4 GPU (16GB): ~3-4 hours total training time
- V100/A100 GPU: ~1.5-2.5 hours total training time
- No thermal throttling
- Can run in background while you work on other things

---

## Prerequisites

### 1. Google Colab Pro Account
- Sign up at: https://colab.research.google.com/signup
- **Cost:** $9.99/month (cancel anytime)
- Provides access to better GPUs (T4, V100, A100)

### 2. HuggingFace Account
- Sign up at: https://huggingface.co/join
- **Free account is sufficient**

### 3. Llama-2 Access
1. Go to: https://huggingface.co/meta-llama/Llama-2-7b-chat-hf
2. Click **"Agree and access repository"**
3. Accept Meta's license terms

### 4. HuggingFace Token
1. Go to: https://huggingface.co/settings/tokens
2. Create new token with **"read"** access
3. Save it somewhere safe (you'll need it in Colab)

---

## Step-by-Step Workflow

### Phase 1: Prepare Code for Upload (Local Machine)

#### Option A: Using Python Script (Cross-platform)

```bash
# Activate your virtual environment
source .venv/bin/activate  # Mac/Linux
# OR
.venv\Scripts\activate     # Windows

# Package the codebase
python scripts/colab/package_for_colab.py
```

#### Option B: Using Bash Script (Mac/Linux only)

```bash
bash scripts/colab/package_for_colab.sh
```

**Output:** Creates `colab_packages/darpan-whatif-simulator_TIMESTAMP.zip` (~5-15MB)

---

### Phase 2: Upload to Google Drive

1. Go to: https://drive.google.com/
2. Click **"New" > "File upload"**
3. Upload the zip file from `colab_packages/`
4. Wait for upload to complete

---

### Phase 3: Train on Google Colab

#### 3.1 Open Colab Notebook

1. Go to: https://colab.research.google.com/
2. Click **"File" > "Upload notebook"**
3. Upload: `notebooks/train_on_colab.ipynb` from your local project

#### 3.2 Configure Runtime

1. Click **"Runtime" > "Change runtime type"**
2. Select:
   - **Hardware accelerator:** GPU
   - **GPU type:** T4, V100, or A100 (if available)
3. Click **"Save"**

#### 3.3 Run the Notebook

**Execute cells sequentially:**

1. **Cell 1:** Check GPU availability
   - Should show nvidia-smi output with GPU info

2. **Cell 2:** Mount Google Drive
   - Will prompt for authorization - click the link and allow access

3. **Cell 3:** Extract your code
   - Update the path if you uploaded to a different location

4. **Cell 4:** Install dependencies
   - Takes ~2-3 minutes

5. **Cell 5:** Authenticate with HuggingFace
   - Paste your HuggingFace token when prompted

6. **Cell 6:** Verify Llama-2 access
   - Should show "✅ Llama-2 access verified!"

7. **Cell 8:** Test train one persona
   - **Important:** Run this first to verify everything works!
   - Takes ~5-15 minutes depending on GPU

8. **Cell 10:** Train ALL 18 personas
   - **⏰ Time estimates:**
     - T4 GPU: 3-4 hours
     - V100 GPU: 2-3 hours
     - A100 GPU: 1.5-2 hours
   - Keep the browser tab open (Colab will notify when done)

9. **Cell 12:** Package adapters for download
   - Creates a zip file (~100-150MB)

10. **Cell 13:** Save to Google Drive
    - Copies the zip to your Google Drive

---

### Phase 4: Download Trained Adapters (Local Machine)

#### 4.1 Download from Google Drive

1. Go to: https://drive.google.com/
2. Find: `llm_adapters_llama2.zip`
3. Right-click > **"Download"**
4. Save to: `~/Downloads/`

#### 4.2 Extract Adapters

```bash
# Navigate to your project
cd /path/to/darpan-whatif-simulator

# Extract adapters (with automatic backup)
python scripts/colab/download_adapters.py \
  --zip ~/Downloads/llm_adapters_llama2.zip \
  --backup
```

**This will:**
- Backup existing adapters (if any)
- Extract new Llama-2 adapters to `artifacts/llm_adapters/`
- Verify all 18 adapters were extracted successfully

---

### Phase 5: Test Locally

```bash
# Make sure config is correct
cat CONFIGS/serve/llm.yaml
# Should show:
#   use_stub: false
#   base_model: "meta-llama/Llama-2-7b-chat-hf"

# Activate venv
source .venv/bin/activate

# Run interactive CLI
python interact_cli.py
```

**Note:** First run will download Llama-2 base model (~13GB) - this only happens once.

---

## Using Claude Code with Colab

### Workflow Overview

```
┌──────────────────┐
│  Claude Code     │  ← Development, testing, iteration
│  (Local Mac)     │  ← Code changes, debugging
└────────┬─────────┘
         │
         │ 1. Make code changes locally
         │
         ▼
┌──────────────────┐
│  Package Script  │  ← scripts/colab/package_for_colab.py
│  (Local)         │
└────────┬─────────┘
         │
         │ 2. Upload to Google Drive
         │
         ▼
┌──────────────────┐
│  Google Colab    │  ← Training (GPU-intensive)
│  (Cloud)         │  ← 2-4 hour training run
└────────┬─────────┘
         │
         │ 3. Download trained adapters
         │
         ▼
┌──────────────────┐
│  Claude Code     │  ← Test, evaluate, iterate
│  (Local Mac)     │  ← interact_cli.py, API testing
└──────────────────┘
```

### Typical Development Cycle

#### 1️⃣ Use Claude Code for Local Development

**What Claude Code is great for:**
- Editing training scripts
- Modifying personas (DATA/personas.json)
- Creating new training data (DATA/sft/*.jsonl)
- Debugging adapter loading issues
- Testing API endpoints
- Running evaluation scripts

**Example Claude Code session:**

```
You: "Add a new persona called 'The Sustainability Expert'"

Claude Code will:
- Read DATA/personas.json
- Add new persona definition
- Create training data file DATA/sft/sustainability_expert.jsonl
- Update training scripts if needed
```

#### 2️⃣ Package and Upload to Colab

```bash
# After making changes with Claude Code
python scripts/colab/package_for_colab.py

# Upload the new zip to Google Drive
# (replaces the old one)
```

#### 3️⃣ Train on Colab

- Open your existing Colab notebook
- **Runtime > Restart runtime** (to clear old code)
- Re-run all cells with the new code

#### 4️⃣ Download and Test with Claude Code

```bash
# Download trained adapters
python scripts/colab/download_adapters.py \
  --zip ~/Downloads/llm_adapters_llama2.zip \
  --backup

# Test with Claude Code
python interact_cli.py
```

**Ask Claude Code to:**
- Test the new persona
- Compare responses across personas
- Run evaluation metrics
- Debug any issues

---

### Best Practices

#### ✅ Do:

1. **Use Claude Code for everything except GPU training**
   - Code editing, debugging, testing, evaluation
   - Claude Code has full access to your local codebase

2. **Make incremental changes**
   - Test locally first (with stub mode or small model)
   - Only train on Colab when you're confident

3. **Keep training data in sync**
   - Always package the latest DATA/sft/*.jsonl files
   - Claude Code can help generate better training data

4. **Version your adapters**
   - Use `--backup` flag when extracting new adapters
   - Keep old adapters in case new ones are worse

5. **Use Claude Code to analyze results**
   ```
   You: "Compare the responses of bargain_hunter and premium_loyalist
        for this scenario: [paste scenario]"

   Claude Code will:
   - Load both adapters
   - Run test scenarios
   - Show differences
   - Suggest improvements
   ```

#### ❌ Don't:

1. **Don't try to train locally** (unless you have a powerful GPU)
   - Llama-2 training needs 16GB+ GPU memory
   - Will be 10x slower on CPU

2. **Don't manually edit Colab notebooks for code changes**
   - Make changes locally with Claude Code
   - Re-package and upload

3. **Don't skip the test training step in Colab**
   - Always test with one persona first
   - Catches errors before wasting 4 hours

---

## Troubleshooting

### Issue: "Llama-2 access denied" in Colab

**Solution:**
1. Accept license: https://huggingface.co/meta-llama/Llama-2-7b-chat-hf
2. Wait 5-10 minutes for access to propagate
3. Use a new HuggingFace token
4. Re-authenticate in Colab notebook

---

### Issue: "Out of memory" error during training

**Solutions:**

**Option 1:** Use smaller batch size
```python
# In scripts/train_llm_persona_sft.py, line 65
per_device_train_batch_size=1,  # Changed from 2
```

**Option 2:** Upgrade Colab GPU
- Click "Runtime" > "Change runtime type"
- Try to get V100 or A100 (limited availability)

**Option 3:** Use 4-bit quantization
```python
# Add to scripts/train_llm_persona_sft.py before loading model
from transformers import BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16
)

model = AutoModelForCausalLM.from_pretrained(
    a.base_model,
    quantization_config=quantization_config
)
```

---

### Issue: Colab disconnects during training

**Solutions:**

1. **Keep browser tab active**
   - Don't let computer sleep
   - Keep Colab tab in foreground

2. **Enable background execution** (Colab Pro feature)
   - Will continue even if you close browser

3. **Add checkpoint saving**
   - Ask Claude Code to modify training script to save checkpoints
   - Can resume if interrupted

---

### Issue: Downloaded adapters don't work locally

**Check list:**

1. **Verify base_model in CONFIGS/serve/llm.yaml matches training**
   ```bash
   cat CONFIGS/serve/llm.yaml
   # Should show: meta-llama/Llama-2-7b-chat-hf
   ```

2. **Check adapter files exist**
   ```bash
   ls artifacts/llm_adapters/bargain_hunter/
   # Should see: adapter_model.safetensors, adapter_config.json
   ```

3. **Verify adapter_config.json has correct base model**
   ```bash
   cat artifacts/llm_adapters/bargain_hunter/adapter_config.json
   # Should show: "base_model_name_or_path": "meta-llama/Llama-2-7b-chat-hf"
   ```

4. **Check stub mode is off**
   ```bash
   cat CONFIGS/serve/llm.yaml | grep use_stub
   # Should show: use_stub: false
   ```

---

### Issue: "Bus error" when running interact_cli.py

**This is usually because:**
1. Using GPT-2 adapters with Llama-2 config (or vice versa)
2. Corrupted adapter files

**Solution:**
```bash
# Re-download and extract adapters
python scripts/colab/download_adapters.py \
  --zip ~/Downloads/llm_adapters_llama2.zip \
  --backup

# OR switch back to stub mode temporarily
# Edit CONFIGS/serve/llm.yaml:
#   use_stub: true
```

---

## Cost & Time Estimates

### Google Colab Pro

**Monthly subscription:** $9.99/month
- Access to T4, V100, A100 GPUs
- Longer runtime limits
- Background execution

**Training costs:**
- One-time training: ~$0 (included in subscription)
- Re-training after changes: ~$0 (included in subscription)

**Worth it if:**
- You'll iterate on personas 2+ times
- You want faster development cycles
- Your laptop doesn't have a good GPU

---

### Time Estimates

| Phase | Time | Notes |
|-------|------|-------|
| **Package code** | 1 min | Automated script |
| **Upload to Drive** | 2-5 min | Depends on internet speed |
| **Colab setup** | 5-10 min | One-time setup |
| **Test training (1 persona)** | 5-15 min | Verify everything works |
| **Full training (18 personas)** | 1.5-4 hours | Depends on GPU |
| **Download adapters** | 5-10 min | ~150MB download |
| **Extract & test** | 2-5 min | Automated script |

**Total for first run:** ~2-5 hours (mostly unattended)

**Subsequent iterations:** ~1.5-4 hours (only re-training time)

---

### GPU Comparison

| GPU | Memory | Training Time (18 personas) | Availability |
|-----|--------|------------------------------|--------------|
| **T4** | 16GB | 3-4 hours | ✅ Always available |
| **V100** | 16GB | 2-3 hours | 🟡 Sometimes available |
| **A100** | 40GB | 1.5-2 hours | 🔴 Rarely available |

**Tip:** T4 is perfectly fine for this project. The time difference isn't worth waiting for A100.

---

## Quick Reference

### Commands

```bash
# Package code for Colab
python scripts/colab/package_for_colab.py

# Extract downloaded adapters
python scripts/colab/download_adapters.py --zip ~/Downloads/llm_adapters_llama2.zip --backup

# Test locally
python interact_cli.py

# Test API
uvicorn src.api.service:app --reload
```

### Key Files

- **Colab notebook:** `notebooks/train_on_colab.ipynb`
- **Package script:** `scripts/colab/package_for_colab.py`
- **Download script:** `scripts/colab/download_adapters.py`
- **Config:** `CONFIGS/serve/llm.yaml`
- **Personas:** `DATA/personas.json`
- **Training data:** `DATA/sft/*.jsonl`

---

## Summary

**Use Claude Code for:**
- ✅ All local development and code changes
- ✅ Creating and editing training data
- ✅ Testing and evaluation
- ✅ Debugging issues
- ✅ Generating reports and analysis

**Use Google Colab for:**
- ✅ Training adapters (GPU-intensive)
- ✅ Experiments with large models
- ✅ Batch processing

**This hybrid workflow gives you:**
- 🚀 Fast iteration with Claude Code locally
- 💪 Powerful GPU training on Colab
- 💰 Cost-effective development
- 🔄 Seamless workflow between local and cloud

---

**Questions?** Ask Claude Code for help with any step!
