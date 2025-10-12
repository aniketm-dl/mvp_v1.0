# Google Colab Training Checklist

Use this checklist to track your progress through the Colab training workflow.

---

## Prerequisites Setup (10 minutes)

- [ ] **Sign up for Google Colab Pro** ($9.99/month)
  - Visit: https://colab.research.google.com/signup
  - Subscribe to Colab Pro for better GPU access

- [ ] **Create HuggingFace account** (free)
  - Visit: https://huggingface.co/join

- [ ] **Accept Llama-2 license**
  - Visit: https://huggingface.co/meta-llama/Llama-2-7b-chat-hf
  - Click "Agree and access repository"
  - Wait 5 minutes for access to propagate

- [ ] **Generate HuggingFace token**
  - Visit: https://huggingface.co/settings/tokens
  - Create token with "read" access
  - Copy and save it somewhere safe (you'll need it later)

---

## Prepare Code for Upload (2 minutes)

- [ ] **Activate virtual environment**
  ```bash
  cd /path/to/darpan-whatif-simulator
  source .venv/bin/activate
  ```

- [ ] **Package codebase**
  ```bash
  python scripts/colab/package_for_colab.py
  ```

- [ ] **Verify package created**
  - Check: `colab_packages/darpan-whatif-simulator_TIMESTAMP.zip`
  - Size should be ~5-15MB

---

## Upload to Google Drive (5 minutes)

- [ ] **Open Google Drive**
  - Visit: https://drive.google.com/

- [ ] **Upload package**
  - Click "New" > "File upload"
  - Select the zip from `colab_packages/`
  - Wait for upload to complete

- [ ] **Note the file location**
  - Default: `MyDrive/darpan-whatif-simulator_TIMESTAMP.zip`
  - You'll need this path in Colab

---

## Setup Colab Notebook (5 minutes)

- [ ] **Open Google Colab**
  - Visit: https://colab.research.google.com/

- [ ] **Upload notebook**
  - Click "File" > "Upload notebook"
  - Select: `notebooks/train_on_colab.ipynb` from your local machine

- [ ] **Configure runtime**
  - Click "Runtime" > "Change runtime type"
  - Hardware accelerator: **GPU**
  - GPU type: **T4** (or V100/A100 if available)
  - Click "Save"

- [ ] **Connect to runtime**
  - Click "Connect" button in top-right
  - Wait for connection

---

## Test Setup (15 minutes)

- [ ] **Run Cell 1: Check GPU**
  - Should show nvidia-smi output
  - Verify GPU name (T4, V100, or A100)

- [ ] **Run Cell 2: Mount Google Drive**
  - Click the authorization link
  - Select your Google account
  - Allow access

- [ ] **Run Cell 3: Extract code**
  - Update path if you uploaded to a different location
  - Verify it extracts successfully

- [ ] **Run Cell 4: Install dependencies**
  - Takes ~2-3 minutes
  - Should complete without errors

- [ ] **Run Cell 5: Authenticate with HuggingFace**
  - Paste your HuggingFace token when prompted
  - Press Enter

- [ ] **Run Cell 6: Verify Llama-2 access**
  - Should show: "✅ Llama-2 access verified!"
  - If not, wait 5 more minutes and try again

- [ ] **Run Cell 7: Check training data**
  - Should find 18 .jsonl files in DATA/sft/

---

## Test Training (10-15 minutes)

- [ ] **Run Cell 8: Train one persona (bargain_hunter)**
  - **IMPORTANT: Do this before training all 18!**
  - Takes ~5-15 minutes depending on GPU
  - Watch for any errors

- [ ] **Run Cell 9: Verify test training**
  - Should show: "✅ Test training successful!"
  - Adapter size should be ~5-10MB

---

## Full Training (2-4 hours) ⏰

- [ ] **Run Cell 10: Train ALL 18 personas**
  - This will take 2-4 hours depending on GPU
  - Keep browser tab open (or enable background execution)
  - You can continue working on other things

**Expected times:**
- T4 GPU: ~3-4 hours
- V100 GPU: ~2-3 hours
- A100 GPU: ~1.5-2 hours

---

## Package & Download (10 minutes)

- [ ] **Run Cell 11: Verify all adapters**
  - Should show 18/18 successfully trained
  - Total size: ~100-150MB

- [ ] **Run Cell 12: Package adapters**
  - Creates: `artifacts/llm_adapters_llama2.zip`

- [ ] **Run Cell 13: Save to Google Drive**
  - Copies zip to: `MyDrive/llm_adapters_llama2.zip`

- [ ] **Download from Google Drive**
  - Visit: https://drive.google.com/
  - Find: `llm_adapters_llama2.zip`
  - Right-click > "Download"
  - Save to: `~/Downloads/`

---

## Test Locally (10 minutes)

- [ ] **Extract adapters**
  ```bash
  cd /path/to/darpan-whatif-simulator
  source .venv/bin/activate

  python scripts/colab/download_adapters.py \
    --zip ~/Downloads/llm_adapters_llama2.zip \
    --backup
  ```

- [ ] **Verify extraction**
  - Should show: "✅ Found 18 valid adapters"
  - Check: `artifacts/llm_adapters/`

- [ ] **Verify config**
  ```bash
  cat CONFIGS/serve/llm.yaml
  ```
  - Should show:
    - `use_stub: false`
    - `base_model: "meta-llama/Llama-2-7b-chat-hf"`

- [ ] **Test interactive CLI**
  ```bash
  python interact_cli.py
  ```
  - **Note:** First run downloads Llama-2 base model (~13GB)
  - This only happens once

- [ ] **Chat with a persona**
  - Select persona #1 (Bargain Hunter)
  - Try: "Should I buy this $50 product or wait for a sale?"
  - Should get a natural, persona-appropriate response

---

## Success Criteria ✅

You know it's working when:

✅ All 18 adapters trained successfully
✅ No errors during extraction
✅ `interact_cli.py` runs without "bus error"
✅ Personas respond naturally (not generic stub responses)
✅ Responses match persona characteristics
✅ Can chat back and forth naturally

---

## If Something Goes Wrong

### Training failed on Colab?
- Check: Did you accept Llama-2 license?
- Check: Is your HuggingFace token valid?
- Check: Did test training (Cell 8) succeed?
- Try: Restart runtime and try again

### Can't download adapters?
- Check: Is zip file in Google Drive?
- Check: Is file size reasonable (~100-150MB)?
- Try: Download again

### Bus error locally?
- Check: Is config pointing to Llama-2?
- Check: Are adapter files intact?
- Try: Re-extract with `--backup` flag
- Try: Set `use_stub: true` temporarily

### Need help?
- Read: `DOCS/COLAB_WORKFLOW.md` (troubleshooting section)
- Ask Claude Code: "Help me debug this Colab training issue: [paste error]"

---

## Next Steps After Success

1. **Test all personas**
   - Run `python interact_cli.py`
   - Chat with each persona
   - Verify distinct personalities

2. **Run evaluations**
   - Ask Claude Code: "Run separation metrics on these adapters"

3. **Test API**
   ```bash
   uvicorn src.api.service:app --reload
   ```

4. **Start iterating**
   - Modify personas
   - Improve training data
   - Re-train on Colab

---

## Time Tracking

Track your actual times here:

- Prerequisites setup: ______ minutes
- Code packaging: ______ minutes
- Upload to Drive: ______ minutes
- Colab setup: ______ minutes
- Test training: ______ minutes
- Full training: ______ hours ______ minutes
- Download: ______ minutes
- Local testing: ______ minutes

**Total time:** ______ hours ______ minutes

---

**Status:**

- [ ] Not started
- [ ] In progress
- [ ] Training on Colab now (started at: ____:____)
- [ ] Adapters downloaded
- [x] **Complete!** 🎉

---

**Notes:**
