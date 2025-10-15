# Retraining Workflow After Code Changes

This guide explains exactly what to do when you modify model files or training code and need to retrain your models.

## 📋 Table of Contents
1. [Quick Reference](#quick-reference)
2. [Detailed Step-by-Step](#detailed-step-by-step)
3. [Option A: Push to GitHub (Recommended)](#option-a-push-to-github-recommended)
4. [Option B: Direct Sync to EC2 (Faster for Testing)](#option-b-direct-sync-to-ec2-faster-for-testing)
5. [Troubleshooting](#troubleshooting)

---

## Quick Reference

### When You Change Code Locally

```bash
# OPTION A: Via GitHub (clean, recommended)
git add .
git commit -m "Update training logic"
git push
make launch          # EC2 will pull latest from GitHub
# SSH to EC2
make train

# OPTION B: Direct sync (faster for testing)
make launch
make sync-code       # Sync local changes directly to EC2
# SSH to EC2
make train
```

---

## Detailed Step-by-Step

### Scenario: You Changed Training Code Locally

Let's say you modified:
- `src/models/encoder.py` - Changed feature extraction
- `scripts/train_llm_persona_sft.py` - Modified training hyperparameters
- `CONFIGS/train/lora.yaml` - Updated LoRA config

**You need to retrain because:**
- Model architecture changed → Old adapters incompatible
- Training process changed → Need to regenerate with new logic
- Config changed → Results will differ

---

## Option A: Push to GitHub (Recommended)

This is the **cleanest approach** for production changes.

### Step 1: Commit and Push Your Changes

```bash
# 1. Check what you changed
git status

# 2. Review your changes
git diff

# 3. Stage your changes
git add src/models/encoder.py
git add scripts/train_llm_persona_sft.py
git add CONFIGS/train/lora.yaml

# 4. Commit with descriptive message
git commit -m "feat: Update encoder architecture and training config

- Modified feature extraction in encoder.py
- Updated LoRA hyperparameters
- Changed training batch size to 4"

# 5. Push to your branch
git push
```

### Step 2: Launch EC2 Instance

```bash
make launch
```

This will:
- Launch g5.xlarge GPU instance
- Show instance ID and IP address

### Step 3: SSH and Update Code on EC2

```bash
# SSH into your instance (IP from previous step)
ssh -i ~/darpan-training.pem ubuntu@<INSTANCE_IP>

# Navigate to repo
cd ~/mvp_v1.0

# Pull latest changes from GitHub
git pull origin refactor/aws-workflow-automation

# Verify changes are there
git log -1
```

### Step 4: Run Training

```bash
# Activate environment
source venv/bin/activate

# Start training with auto-shutdown
./darpan.py train --auto-shutdown

# Or use tmux for persistent session
tmux new -s training
./darpan.py train --auto-shutdown
# Press Ctrl+B then D to detach
```

### Step 5: Download Trained Models

```bash
# Back on your local machine
make download

# Or manually
aws s3 sync s3://your-bucket/trained_adapters/ artifacts/llm_adapters/
```

### Step 6: Test Locally

```bash
# Start API server
make serve

# Chat with retrained personas
make chat

# Run tests to verify
make test
make gate
```

---

## Option B: Direct Sync to EC2 (Faster for Testing)

This is **faster for rapid iteration** but doesn't update GitHub.

### Step 1: Add Sync Command to Makefile

First, let's add a `sync-code` command to your Makefile:

```makefile
sync-code: ## Sync local code changes to EC2 instance
	@echo "📤 Syncing local code to EC2..."
	@read -p "Enter EC2 instance IP: " EC2_IP; \
	rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' \
	  --exclude '.git' --exclude 'artifacts' --exclude 'DATA' \
	  ./ ubuntu@$$EC2_IP:~/mvp_v1.0/
	@echo "✅ Code synced to EC2"
```

### Step 2: Launch Instance

```bash
make launch
```

### Step 3: Sync Local Changes Directly

```bash
# Sync your local changes to EC2
make sync-code
# Enter EC2 IP when prompted

# Or use rsync directly
rsync -avz --exclude 'venv' --exclude '__pycache__' \
  -e "ssh -i ~/darpan-training.pem" \
  ./ ubuntu@<INSTANCE_IP>:~/mvp_v1.0/
```

### Step 4: SSH and Train

```bash
ssh -i ~/darpan-training.pem ubuntu@<INSTANCE_IP>

cd ~/mvp_v1.0
source venv/bin/activate
./darpan.py train --auto-shutdown
```

### Step 5: Commit Later

After testing, commit your changes:

```bash
git add .
git commit -m "feat: Tested and working - updated training logic"
git push
```

---

## 🎯 Which Steps to Start From?

### If You Changed ONLY Training Code/Models:

**Skip these:**
- ❌ `make dataset-opera` - No need to re-download data
- ❌ `make prep-sft-data` - Unless data prep logic changed
- ❌ `make setup-instance` - Instance setup unchanged

**Required steps:**
1. ✅ Push code or sync to EC2
2. ✅ `make train` - **Retrain all models**
3. ✅ `make download` - Download new models
4. ✅ `make test` - Verify changes work
5. ✅ `make gate` - Check separation metrics

### If You Changed Data Preparation:

**Required steps:**
1. ✅ `make prep-sft-data` - Regenerate training data
2. ✅ Upload to S3: `aws s3 sync DATA/ s3://bucket/darpan_training_data/`
3. ✅ `make train` - Train with new data
4. ✅ `make download` - Download models
5. ✅ `make gate` - Verify quality

### If You Changed Dataset Source (Opera → New Dataset):

**Required steps:**
1. ✅ Implement new dataset in `src/datasets/`
2. ✅ `make dataset-<new>` - Download new dataset
3. ✅ `make prep-sft-data` - Generate training data
4. ✅ `make train` - Train models
5. ✅ `make download` - Download models
6. ✅ `make all-checks` - Full verification

---

## 🔄 Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ 1. LOCAL: Make code changes                                 │
│    • Edit src/models/encoder.py                             │
│    • Edit scripts/train_llm_persona_sft.py                  │
│    • Edit CONFIGS/train/lora.yaml                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. SYNC: Get changes to EC2                                 │
│    • OPTION A: git push → EC2 git pull                      │
│    • OPTION B: rsync local → EC2                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. EC2: Launch instance                                     │
│    • make launch                                            │
│    • Note instance IP                                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. EC2: Retrain models                                      │
│    • ssh to instance                                        │
│    • cd ~/mvp_v1.0                                          │
│    • source venv/bin/activate                               │
│    • ./darpan.py train --auto-shutdown                      │
│    • Models auto-save to S3                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. LOCAL: Download and test                                 │
│    • make download                                          │
│    • make serve                                             │
│    • make chat                                              │
│    • make test && make gate                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Troubleshooting

### Problem: EC2 doesn't have my latest changes

**Solution:**
```bash
# On EC2, verify what code is running
cd ~/mvp_v1.0
git log -1          # Check latest commit
git status          # Check for uncommitted changes

# If outdated, pull latest
git pull origin refactor/aws-workflow-automation

# Or re-sync from local
# (from local machine)
make sync-code
```

### Problem: Training fails with "Model architecture mismatch"

**Cause:** You changed model architecture but kept old adapters

**Solution:**
```bash
# On EC2, clean old models
rm -rf artifacts/llm_adapters/*

# Retrain from scratch
./darpan.py train
```

### Problem: Changes work on EC2 but not locally

**Cause:** Local artifacts are stale

**Solution:**
```bash
# Download fresh models from S3
make clean-models    # Remove old models
make download        # Download new ones

# Or manually
rm -rf artifacts/llm_adapters/
aws s3 sync s3://bucket/trained_adapters/ artifacts/llm_adapters/
```

### Problem: Training is slow/expensive

**Solution 1: Train subset first**
```bash
# Train just 3 personas for testing
./darpan.py train --twins bargain_hunter premium_buyer deal_hunter
```

**Solution 2: Use cheaper instance**
```bash
# Edit scripts/aws/launch_training_instance.sh
# Change: INSTANCE_TYPE="g4dn.xlarge"  # $0.15/hr (was g5.xlarge)
```

**Solution 3: Test locally first (if you have GPU)**
```bash
make train-local-one TWIN=k0
```

---

## 📝 Best Practices

### 1. Always Test Small First
```bash
# Don't retrain all 18 personas immediately
# Test with 1-3 first
./darpan.py train --twins k0 k1 k2
```

### 2. Use Git Branches for Experiments
```bash
# Create experiment branch
git checkout -b experiment/new-encoder

# Make changes, test on EC2
# If it works, merge to main
# If not, just delete branch
```

### 3. Document Your Changes
```bash
# Good commit message
git commit -m "feat: Reduce encoder dimensions from 15 to 12

- Removed redundant demographic features
- Updated mixture.py to handle 12-D vectors
- Retrained all models - quality gates pass"
```

### 4. Keep S3 Backups
```bash
# Before major changes, backup current models
aws s3 cp s3://bucket/trained_adapters/ \
  s3://bucket/trained_adapters_backup_2025-10-15/ --recursive
```

### 5. Monitor Costs
```bash
# Check costs regularly
make cost-status

# Set budget alerts
make cost-alert
```

---

## 🎯 Quick Decision Tree

**Q: What did I change?**

- **Changed training hyperparameters only** (batch size, learning rate, epochs)
  → Start from: **Step 2 (Sync)** → Train → Download

- **Changed model architecture** (encoder, features, embeddings)
  → Start from: **Step 2 (Sync)** → Clean old models → Train → Download → **Test thoroughly**

- **Changed data preparation logic**
  → Start from: **Step 1 (Prep data)** → Train → Download

- **Changed dataset source** (Opera → New dataset)
  → Start from: **Step 0 (Implement dataset)** → Download data → Prep → Train → Download

- **Changed API/inference code only** (no training changes)
  → **No retraining needed!** Just deploy new API code

---

## 💡 Pro Tips

1. **Use tmux on EC2** - Training takes hours, don't lose progress on disconnect
   ```bash
   tmux new -s training
   ./darpan.py train --auto-shutdown
   # Ctrl+B then D to detach
   ```

2. **Enable auto-shutdown** - Save money when training completes
   ```bash
   ./darpan.py train --auto-shutdown
   ```

3. **Monitor training remotely** - Check S3 for intermediate checkpoints
   ```bash
   watch -n 300 aws s3 ls s3://bucket/trained_adapters/
   ```

4. **Parallel training** - If you have multi-GPU instance
   ```bash
   make train-parallel
   ```

5. **Keep logs** - Save training output for debugging
   ```bash
   ./darpan.py train 2>&1 | tee training_$(date +%Y%m%d_%H%M%S).log
   ```

---

## 🔗 Related Documentation

- [USAGE_GUIDE.md](../USAGE_GUIDE.md) - Complete usage instructions
- [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) - Command cheat sheet
- [AWS_SETUP.md](AWS_SETUP.md) - AWS configuration details
- [TRAINING.md](TRAINING.md) - Training deep dive

---

**Need help?** Check `make help` for all available commands.
