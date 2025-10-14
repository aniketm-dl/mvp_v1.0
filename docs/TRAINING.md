# Training Guide

Complete guide for training LLM persona adapters on AWS.

## Overview

Train 18 persona adapters on AWS GPU in ~90 minutes for ~$0.50.

**Workflow:** Launch → Setup → Train → Download → Chat

## Quick Start

```bash
# Complete automation
make workflow
```

## Step-by-Step

### 1. Launch Instance

```bash
make launch
# Or manually:
./scripts/aws/launch_training_instance.sh
```

**What it does:**
- Launches g5.xlarge spot instance (~$0.35/hr)
- Creates security group
- Configures storage (100GB)
- Returns SSH command

**Output:**
```
Instance launched: i-1234567890abcdef0
SSH: ssh -i ~/darpan-training.pem ubuntu@54.123.45.67
```

### 2. Setup Instance

SSH into instance:
```bash
ssh -i ~/darpan-training.pem ubuntu@<INSTANCE_IP>
```

Run setup:
```bash
cd ~/mvp_v1.0
make setup-instance
```

**What it does:**
- Installs NVIDIA drivers + CUDA
- Installs Python 3.10 + dependencies
- Clones GitHub repo
- Downloads Opera dataset
- Authenticates with HuggingFace
- Prepares training data

**Time:** ~10 minutes

### 3. Train Models

On EC2 instance:
```bash
cd ~/mvp_v1.0
make train
# This runs: ./darpan.py train --auto-shutdown
```

**What it does:**
- Trains 18 LoRA adapters
- Saves to local disk
- Syncs to S3 after each adapter
- Auto-shutdown when complete

**Time:** ~90 minutes
**Cost:** ~$0.50

**Monitor progress:**
```bash
# In another terminal
ssh -i ~/darpan-training.pem ubuntu@<INSTANCE_IP>
watch -n 5 'ls -lh artifacts/llm_adapters/*/adapter_model.safetensors | wc -l'
```

### 4. Download Models

On your local machine:
```bash
make download
# This runs: aws s3 sync s3://BUCKET/trained_adapters/ artifacts/llm_adapters/
```

**What it does:**
- Downloads all adapters from S3
- Verifies integrity
- Shows progress

**Size:** ~400MB total

### 5. Chat with Personas

```bash
make chat
# Or: python interact_cli.py
```

**What it does:**
- Loads all 18 adapters
- Interactive CLI
- Select persona and chat

## Training Configuration

Edit `CONFIGS/aws/training_config.yaml`:

```yaml
training:
  base_model: "mistralai/Mistral-7B-Instruct-v0.2"
  epochs: 1
  max_length: 512
  learning_rate: 2e-4
  lora:
    rank: 8
    alpha: 16
    dropout: 0.1
```

## Training Specific Personas

```bash
# Train only 3 personas
./darpan.py train --twins bargain_hunter premium_buyer deal_hunter

# Or with Makefile
make train-subset
```

## Parallel Training (Multi-GPU)

If you have p3.8xlarge (4 GPUs):

```bash
./darpan.py train --parallel
```

## Cost Breakdown

| Item | Cost |
|------|------|
| g5.xlarge spot (90 min) | $0.53 |
| Storage (100GB for 2 hours) | $0.02 |
| S3 storage (400MB) | $0.01/month |
| Data transfer | $0.00 (free tier) |
| **Total** | **~$0.55** |

## Time Breakdown

| GPU | Time per Twin | Total (18 twins) | Cost |
|-----|---------------|------------------|------|
| g4dn.xlarge (T4) | 10 min | 3 hours | $0.54 |
| g5.xlarge (A10G) | 5 min | 1.5 hours | $0.53 |
| p3.2xlarge (V100) | 3 min | 1 hour | $1.00 |

## Monitoring

### GPU Usage

```bash
# On EC2 instance
watch -n 1 nvidia-smi
```

Should show ~90-100% GPU utilization.

### Training Progress

```bash
# Count completed adapters
ls artifacts/llm_adapters/*/adapter_model.safetensors | wc -l

# Check sizes
du -sh artifacts/llm_adapters/*/
```

### S3 Sync Status

```bash
# List S3 contents
aws s3 ls s3://$TRAINING_S3_BUCKET/trained_adapters/ --recursive
```

### Cost Tracking

```bash
# On local machine
make cost-status
```

## Troubleshooting

### "CUDA out of memory"

**Solution 1:** Use gradient checkpointing
```python
# Edit scripts/train_llm_persona_sft.py
model.gradient_checkpointing_enable()
```

**Solution 2:** Use larger GPU
- Upgrade to g5.xlarge (24GB)
- Or p3.2xlarge (16GB V100)

### "Training very slow"

Check GPU is being used:
```bash
nvidia-smi
# GPU-Util should be 80-100%
```

If 0%, check:
```python
import torch
print(torch.cuda.is_available())  # Should be True
```

### "S3 sync failed"

```bash
# Test S3 access
aws s3 ls s3://$TRAINING_S3_BUCKET/

# Manual sync
aws s3 sync artifacts/llm_adapters/ s3://$TRAINING_S3_BUCKET/trained_adapters/
```

### "Spot instance terminated"

Spot instances can be reclaimed. Solutions:
- Set higher max price
- Use on-demand instances
- Enable auto-resume from S3

### "HuggingFace authentication failed"

```bash
# Re-authenticate
huggingface-cli login
# Enter token
```

## Quality Checks

After training:

```bash
# Run separation metrics
make gate

# Run tests
make test

# Check persona confusion
make report-confusion
```

**Expected:**
- Silhouette score ≥ 0.35
- JSD ≥ 0.10
- All tests pass

## Production Deployment

### Option 1: Download and Deploy Locally

```bash
make download
make serve
```

### Option 2: Docker

```bash
make docker-build
make docker-run
```

### Option 3: Keep on EC2

```bash
# Don't terminate instance
# Run API server
make serve-prod
```

## Next Steps

1. **Test locally:** `make chat`
2. **Run quality gates:** `make gate`
3. **Deploy API:** `make serve`
4. **Integrate:** See [API.md](API.md)

---

**Total time:** ~2 hours (mostly automated)
**Total cost:** ~$0.55
**Output:** 18 trained LoRA adapters ready for production
