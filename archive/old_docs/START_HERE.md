# 🚀 Start Here - Your Complete AWS Training Setup

##  Quick Path 

### Phase 1: Local Setup (10 minutes)

```bash
# 1. Install AWS CLI
brew install awscli  # macOS
# or: pip install awscli

# 2. Configure credentials
aws configure
# Enter your Access Key ID and Secret Key

# 3. Clone repo
cd ~
git clone https://github.com/aniketm-dl/mvp_v1.0.git
cd mvp_v1.0

# 4. Create S3 bucket
export BUCKET_NAME="darpan-training-$(date +%s)"
aws s3 mb s3://$BUCKET_NAME
echo "export TRAINING_S3_BUCKET=$BUCKET_NAME" >> ~/.bashrc
```

✅ **Local setup complete!**

---

### Phase 2: Launch Instance (5 minutes)

```bash
# Interactive launcher (easiest)
./scripts/aws/launch_training_instance.sh

# Follow prompts:
# - Region: us-east-1
# - GPU: g5.xlarge (recommended)
# - Pricing: Spot instance
# - Key: Create new

# You'll get: ssh -i ~/darpan-training.pem ubuntu@<IP>
```

✅ **Instance running!**

---

### Phase 3: Setup Instance (10 minutes)

```bash
# SSH into instance
ssh -i ~/darpan-training.pem ubuntu@<IP>

# Run setup (one command)
bash <(curl -s https://raw.githubusercontent.com/aniketm-dl/mvp_v1.0/main/scripts/aws/setup_training_instance.sh)

# It will prompt for:
# 1. GitHub username & PAT
# 2. HuggingFace token
# 3. S3 bucket name

# Wait ~10 minutes for setup
```

✅ **Instance configured!**

---

### Phase 4: Train (1.5 hours)

```bash
# On EC2 instance
cd ~/mvp_v1.0
source venv/bin/activate

# Start training with auto-shutdown
python scripts/aws/train_production.py --auto-shutdown

# Or use background session
tmux new -s training
python scripts/aws/train_production.py --auto-shutdown
# Press Ctrl+B then D to detach
```

✅ **Training started!** Instance will auto-shutdown when done.

---

### Phase 5: Download (5 minutes)

```bash
# Back on your local machine
cd ~/mvp_v1.0

# Download trained models
aws s3 sync s3://$TRAINING_S3_BUCKET/trained_adapters/ \
  artifacts/llm_adapters/

# Verify
ls artifacts/llm_adapters/
# Should show 18 directories
```

✅ **Models downloaded! Ready to use locally.**

---

## 💰 Total Cost: ~$0.50

- g5.xlarge spot instance: $0.35/hour
- Training time: ~1.5 hours
- Storage (S3): ~$0.01/month
- **Total: $0.53**

Compare to:
- Colab Pro: $9.99/month
- **Savings: 95%!**

---

## 📚 Detailed Guides

### New to AWS?
👉 **[AWS Account Setup](AWS_ACCOUNT_SETUP.md)** - Step-by-step AWS configuration

### Want Complete Guide?
👉 **[AWS Training Guide](AWS_TRAINING_GUIDE.md)** - Full 50-page manual with troubleshooting

### Need Fast Overview?
👉 **[Quick Start](AWS_QUICK_START.md)** - 5-minute condensed version

### Want to Understand Features?
👉 **[Production Features](PRODUCTION_FEATURES.md)** - Scalability & production readiness

---

## ✨ What's Production-Ready Now?

### 1. **Scalable to N Personas**
- Not hardcoded to 18
- Works with 1 or 1000 personas
- Just edit `DATA/personas.json`

### 2. **Configuration-Driven**
- Edit `CONFIGS/aws/training_config.yaml`
- No code changes needed
- Different configs for dev/prod

### 3. **Error Recovery**
- Auto-retry on failures (3 attempts)
- Resume from last completed
- Detailed error logs

### 4. **Cost Management**
- Real-time cost tracking
- Budget alerts
- Auto-shutdown to save money

### 5. **Parallel Training**
- Multi-GPU support
- Train 4 personas simultaneously
- 4x faster for large batches

### 6. **Comprehensive Monitoring**
- Progress tracking
- Performance metrics
- S3 sync status
- JSON reports

---

## 🎯 Your Next Steps

### Step 1: AWS Setup (if not done)
```bash
# Follow this guide
open DOCS/AWS_ACCOUNT_SETUP.md
```

**Key tasks:**
- [ ] AWS CLI installed & configured
- [ ] S3 bucket created
- [ ] SSH key pair created
- [ ] HuggingFace token obtained

### Step 2: Launch & Train
```bash
# Launch instance
./scripts/aws/launch_training_instance.sh

# Setup instance
# (See Phase 3 above)

# Start training
python scripts/aws/train_production.py --auto-shutdown
```

### Step 3: Download & Test
```bash
# Download models
aws s3 sync s3://$TRAINING_S3_BUCKET/trained_adapters/ \
  artifacts/llm_adapters/

# Test locally
cd ~/mvp_v1.0
python interact_cli.py
```

---

## 🔥 Production Features

### Configuration Example

Edit `CONFIGS/aws/training_config.yaml`:

```yaml
# Train with different model
training:
  base_model: "mistralai/Mistral-7B-Instruct-v0.3"
  epochs: 2  # More epochs
  lora:
    rank: 16  # Larger rank

# Enable parallel training
parallelization:
  enabled: true
  num_workers: 4

# Auto-retry failed personas
error_handling:
  max_retries: 3
  fail_fast: false

# Budget alert
cost:
  budget_alert_usd: 10
```

### Usage Examples

```bash
# Train all personas
python scripts/aws/train_production.py

# Train specific personas
python scripts/aws/train_production.py \
  --twins persona1 persona2 persona3

# Parallel training (multi-GPU)
python scripts/aws/train_production.py --parallel

# Custom config
python scripts/aws/train_production.py \
  --config my_config.yaml

# Dry run (preview)
python scripts/aws/train_production.py --dry-run

# With auto-shutdown
python scripts/aws/train_production.py --auto-shutdown
```

---

## 🆘 Common Issues

### "AWS CLI not found"
```bash
brew install awscli
aws configure
```

### "Access Denied"
```bash
# Make sure you created IAM user with EC2 & S3 permissions
# See: AWS_ACCOUNT_SETUP.md Step 2
```

### "GPU quota exceeded"
```bash
# Use spot instances (no quota needed)
# Or request quota increase (takes 15 min - 24 hours)
# See: AWS_ACCOUNT_SETUP.md Step 5
```

### "Training fails on instance"
```bash
# Check GPU
nvidia-smi

# Check logs
tail -f ~/mvp_v1.0/artifacts/training.log

# See full troubleshooting: AWS_TRAINING_GUIDE.md
```

---

## 📊 Cost Tracking

### Check Current Costs
```bash
# AWS Billing Dashboard
open https://console.aws.amazon.com/billing/

# Or via CLI
aws ce get-cost-and-usage \
  --time-period Start=2025-10-01,End=2025-10-11 \
  --granularity DAILY \
  --metrics BlendedCost
```

### Set Budget Alert
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name training-cost-alert \
  --metric-name EstimatedCharges \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold
```

---

## 🎓 Learning Path

### Beginner
1. Follow **Quick Path** above
2. Read **AWS Account Setup**
3. Launch one training run
4. Download and test models

### Intermediate
1. Customize `training_config.yaml`
2. Train specific personas only
3. Try parallel training
4. Set up monitoring

### Advanced
1. Multi-GPU training on p3.8xlarge
2. Custom base models
3. Distributed training across instances
4. CI/CD integration

---

## 📦 What's Included

### Scripts Created
- ✅ `scripts/aws/launch_training_instance.sh` - Interactive launcher
- ✅ `scripts/aws/setup_training_instance.sh` - Automated setup
- ✅ `scripts/aws/train_production.py` - Production orchestrator
- ✅ `scripts/aws/train_with_s3_sync.py` - Simple version (still works)

### Configs Created
- ✅ `CONFIGS/aws/training_config.yaml` - Full configuration

### Docs Created
- ✅ `DOCS/AWS_ACCOUNT_SETUP.md` - AWS setup guide
- ✅ `DOCS/AWS_TRAINING_GUIDE.md` - Complete training guide
- ✅ `DOCS/AWS_QUICK_START.md` - Quick reference
- ✅ `DOCS/PRODUCTION_FEATURES.md` - Feature documentation
- ✅ `DOCS/START_HERE.md` - This file!

---

## ✅ Pre-Flight Checklist

Before starting training:

- [ ] AWS account created
- [ ] AWS CLI installed (`aws --version`)
- [ ] AWS credentials configured (`aws sts get-caller-identity`)
- [ ] S3 bucket created (`aws s3 ls`)
- [ ] SSH key created (`ls ~/.ssh/darpan-training.pem`)
- [ ] HuggingFace token obtained
- [ ] Repo cloned locally (`ls ~/mvp_v1.0`)

**All checked?** You're ready! Run:
```bash
./scripts/aws/launch_training_instance.sh
```

---

## 🎉 Success Criteria

After training completes:

✅ **Training report saved:**
```bash
cat artifacts/training_report.json
# Should show 18/18 successful
```

✅ **Models in S3:**
```bash
aws s3 ls s3://$TRAINING_S3_BUCKET/trained_adapters/
# Should show 18 directories
```

✅ **Models downloaded locally:**
```bash
ls artifacts/llm_adapters/
# Should show 18 directories with adapter_model.safetensors
```

✅ **Test works:**
```bash
python interact_cli.py
# Should load models and respond
```

---

## 🚀 Ready to Start?

**Choose your path:**

### 🏃 Fast Track (You have AWS setup already)
```bash
./scripts/aws/launch_training_instance.sh
```

### 📚 Detailed Setup (New to AWS)
```bash
open DOCS/AWS_ACCOUNT_SETUP.md
```

### 🤔 Just Browsing?
```bash
open DOCS/PRODUCTION_FEATURES.md
```

---

## 💬 Need Help?

- Check troubleshooting sections in guides
- Review error logs: `artifacts/training.log`
- Open GitHub issue with error details
- Check AWS CloudWatch logs

**Good luck with your training! 🎯**

---

**Last Updated:** 2025-10-10
