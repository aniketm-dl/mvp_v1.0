# 🚀 Darpan Labs - Quick Reference Card

**Train 18 LLM personas on AWS in ~90 minutes for ~$0.50**

---

## ⚡ One Command (Complete Workflow)

```bash
make workflow
```

**That's it!** This does everything: Launch → Setup → Train → Download → Chat

---

## 📋 Step-by-Step (If You Prefer)

```bash
# 1. Launch AWS GPU instance
make launch
# → Get IP address

# 2. SSH into instance  
ssh -i ~/darpan-training.pem ubuntu@<IP>

# 3. Setup (on EC2)
make setup-instance
# → Takes ~10 min

# 4. Train (on EC2)
make train
# → Takes ~90 min, costs ~$0.50

# 5. Download (local)
make download
# → Downloads 18 adapters

# 6. Chat (local)
make chat
# → Talk to personas
```

---

## 🎯 Essential Commands

```bash
# Check status
./darpan.py status

# See all commands
make help

# Quick start guide
make quickstart

# List personas
make personas-list

# Start API server
make serve

# Run tests
make test

# Check costs
make cost-status

# List S3 files
make s3-list
```

---

## 📊 Status Check

```bash
./darpan.py status
```

Shows:
- ✅ Launch: Complete/Pending
- ✅ Setup: Complete/Pending  
- ✅ Train: Complete/Pending
- ✅ Download: Complete/Pending
- Instance ID, S3 bucket, adapter count

---

## 💰 Cost Tracking

| Action | Cost | Time |
|--------|------|------|
| Launch instance | $0 | 2 min |
| Setup | $0.06 | 10 min |
| Train (18 personas) | $0.50 | 90 min |
| **Total** | **~$0.55** | **~2 hours** |

**Instance:** g5.xlarge spot @ ~$0.35/hr

---

## 🔐 Credentials Location

```
~/.aws/credentials           ⚠️  AWS keys (NEVER share!)
~/.aws/config               ✅ Region settings
~/darpan-training.pem       ⚠️  SSH key (NEVER share!)
~/.aws_training_env         ✅ S3 bucket, safe to share
```

**Check:** [docs/CREDENTIALS_QUICK_REF.md](docs/CREDENTIALS_QUICK_REF.md)

---

## 🐛 Quick Troubleshooting

**"AWS credentials not found"**
```bash
aws configure
```

**"Permission denied (publickey)"**
```bash
chmod 400 ~/darpan-training.pem
```

**"CUDA out of memory"**
- Use g5.xlarge instead of g4dn.xlarge

**"Training failed"**
```bash
# On EC2:
nvidia-smi
tail -f artifacts/training.log
```

---

## 📚 Full Documentation

- **Main guide:** [README.md](README.md)
- **Usage guide:** [USAGE_GUIDE.md](USAGE_GUIDE.md) ← Complete instructions
- **AWS setup:** [docs/AWS_SETUP.md](docs/AWS_SETUP.md)
- **Training:** [docs/TRAINING.md](docs/TRAINING.md)
- **Credentials:** [docs/CREDENTIALS_GUIDE.md](docs/CREDENTIALS_GUIDE.md)
- **API:** [docs/API.md](docs/API.md)

---

## 🎉 What You Get

After training:
- ✅ 18 trained persona adapters
- ✅ Each ~20MB (LoRA)
- ✅ Ready for production
- ✅ Interactive chat interface
- ✅ FastAPI server
- ✅ Complete API

**Use cases:**
- "What if" simulations
- User behavior prediction
- A/B test forecasting
- Persona-based recommendations

---

## 🚀 Getting Started

**Never used this before?**
1. Read: [README.md](README.md)
2. Check: `make quickstart`
3. Run: `make workflow`

**Used it before?**
```bash
./darpan.py status  # Where am I?
make help           # What can I do?
```

---

**Quick support:** Check [USAGE_GUIDE.md](USAGE_GUIDE.md) for complete instructions
**Cost:** ~$0.50 per training run
**Time:** ~2 hours (mostly automated)
