# DATA Generation & Google Drive Persistence Guide

Complete guide for handling training data with Google Colab and Drive.

---

## Problem

The `DATA/` folder (487MB) contains training data and is too large for GitHub:
- `DATA/sft/` (11MB) - 2,700 training examples for 18 personas
- `DATA/opera/` (476MB) - OPeRA dataset from HuggingFace
- `DATA/personas.json` (15KB) - Persona definitions
- `DATA/twin_bank.json` (9.6KB) - Twin embeddings

**Solution:** Generate DATA on Colab once, save to Google Drive, reuse forever.

---

## Quick Summary

### First Training Session
```
Clone GitHub → Generate DATA → Train → Save to Drive
(~10 min setup)   (~5-10 min)  (2-4 hrs) (instant)
```

### Subsequent Sessions
```
Clone GitHub → Load DATA from Drive → Train
(~2 min)        (~30 sec instant!)    (2-4 hrs)
```

**Time saved:** 5-10 minutes per session after first time!

---

## Detailed Workflow

### Option 1: Automatic (Recommended) - Use Updated Notebook

**File:** `notebooks/train_mistral_on_colab_with_data.ipynb` ✨ NEW!

This notebook handles everything automatically:

1. **Step 7: Setup Training Data**
   - Checks if DATA exists in Drive
   - If yes: Syncs instantly from Drive
   - If no: Generates and saves to Drive

**Just run the notebook - it handles DATA automatically!**

---

### Option 2: Manual - Run Scripts Directly

If you prefer manual control:

#### A. Generate DATA on Colab

```python
# In Colab
!python scripts/colab/setup_training_data.py
```

This script:
1. Downloads OPeRA dataset from HuggingFace (~476MB, optional)
2. Generates `personas.json` (18 personas)
3. Generates `twin_bank.json` (embeddings)
4. Creates 2,700 training examples in `DATA/sft/`

**Time:** ~5-10 minutes

#### B. Save to Google Drive

```python
# Create Drive directory
!mkdir -p /content/drive/MyDrive/darpan_mvp_data

# Copy DATA to Drive
!cp -r DATA/* /content/drive/MyDrive/darpan_mvp_data/
```

**Time:** ~1-2 minutes

#### C. Load from Drive (future sessions)

```python
# Copy from Drive to Colab workspace
!cp -r /content/drive/MyDrive/darpan_mvp_data DATA/
```

**Time:** ~30 seconds

---

## What Gets Generated

### DATA Folder Structure (487MB total)

```
DATA/
├── personas.json              15KB    ✅ Generated
├── twin_bank.json            9.6KB    ✅ Generated
├── copy_variants.csv          160B    ✅ Generated
├── pins.json                   35B    ✅ Generated
├── train_runs.json            484B    ✅ Generated
├── distill_llm.jsonl         1.5KB    ✅ Generated
├── opera/                    476MB    ⚠️  Downloaded (optional)
│   ├── action_with_ocean/
│   ├── filtered_action/
│   ├── filtered_session/
│   └── filtered_user/
├── sft/                       11MB    ✅ Generated
│   ├── bargain_hunter.jsonl   46KB   (150 examples)
│   ├── premium_loyalist.jsonl 47KB   (150 examples)
│   ├── ... (16 more personas)
│   └── local_supporter.jsonl  47KB   (150 examples)
└── derived/                   84KB    ✅ Generated
    └── ... (cached computations)
```

---

## Generation Scripts

### 1. `scripts/generate_mvp_personas.py`

**What it generates:**
- `DATA/personas.json` - 18 persona definitions with:
  - ID, label, description
  - OCEAN personality scores
  - Psychographic tags
  - Shopping values
  - System prompts

- `DATA/twin_bank.json` - 15D behavioral embeddings for each persona

**How to run:**
```bash
python scripts/generate_mvp_personas.py
```

**Time:** ~5 seconds

---

### 2. `scripts/generate_mvp_training_data.py`

**What it generates:**
- `DATA/sft/*.jsonl` - 18 files (one per persona)
- 150 training examples per persona = 2,700 total
- Each example has:
  - Input prompt
  - Expected output (persona-specific response)
  - Metadata (tags, values, category)

**Example training data:**
```json
{
  "twin_id": "bargain_hunter",
  "input": "User: What do you think about this price?\nAssistant:",
  "output": "Price is my top priority. I always look for the best deal.",
  "meta": {
    "psychographic_tags": ["price_sensitive", "deal_seeker"],
    "category": "price",
    "shopping_values": ["savings", "value", "best_price"]
  }
}
```

**How to run:**
```bash
python scripts/generate_mvp_training_data.py
```

**Time:** ~30-60 seconds

**Requirements:**
- `DATA/personas.json` must exist (run script #1 first)

---

### 3. `scripts/colab/setup_training_data.py` (All-in-One)

**What it does:**
1. Checks if DATA already exists (skip if yes)
2. Downloads OPeRA dataset (optional, may skip if timeout)
3. Runs script #1 (personas)
4. Runs script #2 (training data)
5. Verifies everything was created

**How to run:**
```bash
python scripts/colab/setup_training_data.py
```

**Time:** ~5-10 minutes (first time only)

**This is what the notebook calls automatically!**

---

## Drive Persistence Workflow

### Directory Structure on Google Drive

```
Google Drive
└── MyDrive/
    └── darpan_mvp_data/              ← Your DATA folder persisted here
        ├── personas.json
        ├── twin_bank.json
        ├── sft/
        │   └── *.jsonl (18 files)
        └── opera/ (optional)
```

### How It Works

**First Session:**
```python
# Step 1: Generate DATA
!python scripts/colab/setup_training_data.py

# Step 2: Save to Drive
!mkdir -p /content/drive/MyDrive/darpan_mvp_data
!cp -r DATA/* /content/drive/MyDrive/darpan_mvp_data/
```

**Subsequent Sessions:**
```python
# Just load from Drive (instant!)
!cp -r /content/drive/MyDrive/darpan_mvp_data DATA/
```

**The new notebook does this automatically in Step 7!**

---

## OPeRA Dataset (Optional)

**What is it:**
- Real e-commerce dataset with user behavior
- ~476MB, hosted on HuggingFace
- Repository: https://huggingface.co/datasets/NEU-HAI/OPeRA

**Do you need it:**
- ❌ **Not required** for training personas
- ✅ **Optional** for future enhancements
- ✅ **Nice to have** for real user profiling

**How it's downloaded:**
```bash
git clone https://huggingface.co/datasets/NEU-HAI/OPeRA DATA/opera
```

**Why it might fail:**
- Large file (476MB) - may timeout on slow connections
- Git LFS files - Colab sometimes has issues
- **Solution:** The setup script continues without it if it fails

**If you want to skip OPeRA:**
- Comment out `download_opera_dataset()` in setup script
- Or just let it fail/timeout - training will still work!

---

## Troubleshooting

### Issue: "DATA folder not found" after Step 7

**Cause:** Generation failed or Drive sync failed

**Solution:**
```python
# Check if DATA exists locally
!ls -la DATA/

# If empty, regenerate
!python scripts/colab/setup_training_data.py

# Then save to Drive
!cp -r DATA/* /content/drive/MyDrive/darpan_mvp_data/
```

---

### Issue: "personas.json not found"

**Cause:** Persona generation failed

**Solution:**
```python
# Regenerate personas manually
!python scripts/generate_mvp_personas.py

# Verify
!ls -lh DATA/personas.json DATA/twin_bank.json
```

---

### Issue: "SFT directory empty"

**Cause:** Training data generation failed

**Solution:**
```python
# First ensure personas exist
!ls DATA/personas.json

# Then regenerate training data
!python scripts/generate_mvp_training_data.py

# Verify
!ls DATA/sft/ | wc -l  # Should show 18
```

---

### Issue: OPeRA download fails/times out

**This is OK!** OPeRA is optional. Training will work fine without it.

**If you want to retry:**
```python
!git clone https://huggingface.co/datasets/NEU-HAI/OPeRA DATA/opera
```

**To skip OPeRA entirely:**
- Just ignore the warning
- Training data (DATA/sft/) is what matters

---

### Issue: Drive sync is slow

**Cause:** Large files (especially if OPeRA is included)

**Solutions:**
1. **Exclude OPeRA from Drive sync:**
   ```python
   # Only sync essential files
   !cp DATA/personas.json /content/drive/MyDrive/darpan_mvp_data/
   !cp DATA/twin_bank.json /content/drive/MyDrive/darpan_mvp_data/
   !cp -r DATA/sft /content/drive/MyDrive/darpan_mvp_data/
   ```

2. **Compress before syncing:**
   ```python
   !tar -czf DATA_essentials.tar.gz DATA/personas.json DATA/twin_bank.json DATA/sft/
   !cp DATA_essentials.tar.gz /content/drive/MyDrive/
   ```

---

## Local Development

If you want to generate DATA locally (not on Colab):

```bash
# Make sure you're in project root
cd /path/to/darpan-whatif-simulator

# Activate venv
source .venv/bin/activate

# Generate personas
python scripts/generate_mvp_personas.py

# Generate training data
python scripts/generate_mvp_training_data.py

# Optional: Download OPeRA
git clone https://huggingface.co/datasets/NEU-HAI/OPeRA DATA/opera
```

**Then commit to git?**
- ❌ NO! DATA is in .gitignore (too large)
- ✅ Keep DATA local only
- ✅ Use the Colab + Drive workflow for training

---

## Summary

### ✅ Best Practice Workflow

1. **First time on Colab:**
   - Use `notebooks/train_mistral_on_colab_with_data.ipynb`
   - Let Step 7 generate DATA automatically (~5-10 min)
   - DATA saves to Drive automatically

2. **Every time after:**
   - Use same notebook
   - Step 7 loads from Drive instantly (~30 sec)
   - Start training immediately

3. **Never:**
   - Don't commit DATA to git (too large)
   - Don't regenerate if you have it in Drive
   - Don't download adapters until training is done

### 📊 Time Comparison

| Approach | Setup Time | Subsequent Runs |
|----------|-----------|-----------------|
| **Generate every time** | 5-10 min | 5-10 min ❌ |
| **Drive persistence** | 5-10 min | 30 sec ✅ |
| **Git (not possible)** | N/A | N/A (too large) |

**Conclusion:** Drive persistence saves 5-10 minutes per session!

---

## Quick Reference

### Essential Files for Training
```
Required (must have):
├── DATA/personas.json         15KB
├── DATA/twin_bank.json       9.6KB
└── DATA/sft/*.jsonl           11MB  (18 files)

Optional (nice to have):
└── DATA/opera/               476MB  (for future use)
```

### Commands
```bash
# Generate all DATA (run once)
python scripts/colab/setup_training_data.py

# Save to Drive
cp -r DATA/* /content/drive/MyDrive/darpan_mvp_data/

# Load from Drive (future sessions)
cp -r /content/drive/MyDrive/darpan_mvp_data DATA/

# Verify DATA
ls -lh DATA/personas.json DATA/twin_bank.json
ls DATA/sft/ | wc -l  # Should be 18
```

---

**Questions?** Ask Claude Code for help with DATA generation!
