# 🚀 How to Use the Refactored Darpan Labs System

**Complete guide for training LLM personas on AWS and using them locally.**

---

## Quick Start (First Time Setup)

### 1. Prerequisites Check

```bash
# Check if you have everything
make quickstart

# Or manually check:
aws --version              # AWS CLI installed?
aws sts get-caller-identity  # AWS configured?
ls ~/darpan-training.pem   # SSH key exists?
```

**Don't have AWS set up?** → See [docs/AWS_SETUP.md](docs/AWS_SETUP.md)

---

## 🎯 Complete Workflow (One Command)

### Option 1: Fully Automated

```bash
# Run everything: Launch → Setup → Train → Download → Chat
make workflow
```

**What this does:**
1. Launches AWS g5.xlarge spot instance (~$0.35/hr)
2. Prompts you to SSH and run setup
3. Prompts you to run training
4. Downloads trained models from S3
5. Starts interactive chat with personas

**Time:** ~2 hours (mostly automated)
**Cost:** ~$0.50 total

---

### Option 2: Step-by-Step (Recommended for First Time)

#### Step 1: Launch AWS Instance

```bash
make launch
```

**Output:**
```
Instance launched: i-1234567890abcdef0
Public IP: 54.123.45.67
SSH command: ssh -i ~/darpan-training.pem ubuntu@54.123.45.67
```

**Save the IP address!**

---

#### Step 2: Setup Instance

```bash
# SSH into the instance
ssh -i ~/darpan-training.pem ubuntu@54.123.45.67
```

**On the EC2 instance:**
```bash
cd ~/mvp_v1.0
make setup-instance
```

**What this does:**
- Installs NVIDIA drivers + CUDA (~5 min)
- Installs Python dependencies (~3 min)
- Downloads Opera dataset (~2 min)
- Prepares training data
- Authenticates with HuggingFace

**You'll be prompted for:**
- HuggingFace token (get from https://huggingface.co/settings/tokens)

**Time:** ~10 minutes

---

#### Step 3: Train Models

**Still on EC2 instance:**

```bash
cd ~/mvp_v1.0
make train
```

**This will:**
- Train all 18 persona adapters
- Save each to S3 automatically
- Auto-shutdown instance when done

**Time:** ~90 minutes
**Cost:** ~$0.50

**Monitor progress (in another terminal):**
```bash
ssh -i ~/darpan-training.pem ubuntu@<IP>
watch -n 10 'ls artifacts/llm_adapters/*/adapter_model.safetensors | wc -l'
# Should show 0-18 as training progresses
```

---

#### Step 4: Download Models

**Back on your local machine:**

```bash
make download
```

**What this does:**
- Downloads all 18 adapters from S3 (~400MB)
- Verifies integrity
- Stores in `artifacts/llm_adapters/`

**Time:** ~5 minutes

---

#### Step 5: Chat with Personas

```bash
make chat
```

**What you'll see:**
```
🎯 DARPAN LABS - 18 DIGITAL TWIN PERSONAS

1. The Bargain Hunter (bargain_hunter)
2. The Premium Loyalist (premium_loyalist)
...

Choose a persona to chat with:
Your choice: 1

💬 CHATTING WITH: The Bargain Hunter
Type your questions below...

You: What do you think about this laptop priced at $1200?
Bargain Hunter: That seems expensive. I'd look for sales or refurbished options...
```

**Commands:**
- Type number (1-18) to select persona
- Type message to chat
- Type `back` to switch persona
- Type `quit` to exit

---

## 🔄 Common Use Cases

### Train Specific Personas Only

```bash
# Train just 3 personas (for testing)
./darpan.py train --twins bargain_hunter premium_buyer deal_hunter
```

### Resume Interrupted Training

```bash
# Training automatically skips completed personas
make train

# It will continue from where it left off
```

### Download Specific Models

```bash
# Download just one persona
aws s3 sync s3://YOUR_BUCKET/trained_adapters/bargain_hunter/ \
  artifacts/llm_adapters/bargain_hunter/
```

### Train Locally (If You Have GPU)

```bash
# Train all personas on your local GPU
make train-local-all

# Train one persona
make train-local-one TWIN=bargain_hunter
```

**Requirements:**
- 16GB+ GPU (NVIDIA)
- CUDA installed
- 100GB+ disk space

**Time:** 3-4 hours on consumer GPU

---

## 💻 Local Development

### Start API Server

```bash
# Development mode (auto-reload)
make serve

# Production mode (4 workers)
make serve-prod
```

**Access:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### Test Endpoints

```bash
# Check health
curl http://localhost:8000/health

# List personas
curl http://localhost:8000/twin/personas

# Simulate scenario
curl -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d @API/examples/requests.json
```

### Run Tests

```bash
# Quick tests
make test

# All quality checks
make all-checks

# Specific test
make test-specific FILE=test_health.py
```

### Evaluate Models

```bash
# Check persona separation quality
make gate

# Generate reports
make report-confusion
make report-deltas
```

---

## 📊 Monitor & Manage

### Check Workflow Status

```bash
./darpan.py status
```

**Output:**
```
📊 WORKFLOW STATUS

✅ Launch: Complete
✅ Setup: Complete
✅ Train: Complete
✅ Download: Complete

Instance ID: i-1234567890abcdef0
S3 Bucket: s3://darpan-training-1760105520/
Adapters: 18/18
```

### Check AWS Costs

```bash
make cost-status
```

**Output:**
```
📊 Checking AWS costs...
Current month: $0.53
```

### List S3 Contents

```bash
make s3-list
```

**Output:**
```
📦 Listing s3://darpan-training-1760105520/

trained_adapters/bargain_hunter/
trained_adapters/premium_buyer/
...
```

### Upload Local Models to S3

```bash
make s3-upload
```

---

## 🎨 Advanced Usage

### Use Different Base Model

Edit `CONFIGS/aws/training_config.yaml`:
```yaml
training:
  base_model: "mistralai/Mistral-7B-Instruct-v0.3"  # or v0.2
  epochs: 1
```

Then train as usual.

### Parallel Training (Multi-GPU)

If you have p3.8xlarge (4 GPUs):

```bash
./darpan.py train --parallel
```

**Time:** 4x faster (~25 minutes)
**Cost:** $1.00/hr (but only for 25 min = $0.42)

### Custom Training Data

```bash
# Prepare your own training data
make prep-sft-data

# Or from Opera dataset
make prep-opera-sft

# Train with custom data
python scripts/train_llm_persona_sft.py \
  --twin_id custom_persona \
  --data_path DATA/sft/custom_persona.jsonl
```

### Add New Dataset

```python
# src/datasets/my_dataset.py
from src.datasets import BaseDataset

class MyDataset(BaseDataset):
    def download(self):
        # Download logic
        pass

    def prepare_personas(self):
        # Extract personas
        pass

    def prepare_training_data(self, persona_id, output_path):
        # Generate training data
        pass

# Register
from src.datasets import DatasetFactory
DatasetFactory.register("my_dataset", MyDataset)

# Use
dataset = DatasetFactory.create("my_dataset")
```

---

## 🐛 Troubleshooting

### "AWS credentials not found"

```bash
aws configure
# Enter your Access Key ID and Secret Access Key
```

### "Permission denied (publickey)"

```bash
# Fix SSH key permissions
chmod 400 ~/darpan-training.pem

# Try again
ssh -i ~/darpan-training.pem ubuntu@<IP>
```

### "CUDA out of memory"

Use larger GPU:
```bash
# Edit launch script to use g5.xlarge instead of g4dn.xlarge
# Or use p3.2xlarge (16GB V100)
```

### "S3 bucket not found"

```bash
# Check bucket name
cat ~/.aws_training_env

# Create if missing
aws s3 mb s3://darpan-training-$(whoami)
export TRAINING_S3_BUCKET=darpan-training-$(whoami)
```

### "Training failed"

```bash
# Check logs on EC2 instance
tail -f artifacts/training.log

# Check GPU
nvidia-smi

# Verify CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

### "Models not working locally"

```bash
# Verify adapters downloaded
ls artifacts/llm_adapters/*/adapter_model.safetensors | wc -l
# Should show 18

# Check file sizes
du -sh artifacts/llm_adapters/*/
# Each should be 15-35 MB
```

---

## 📚 All Available Commands

### Workflow Commands

```bash
make workflow          # Complete automated workflow
make workflow-status   # Check progress
make launch            # Launch AWS instance
make setup-instance    # Setup environment (on EC2)
make train             # Train models (on EC2)
make download          # Download trained models
make chat              # Interactive chat
```

### Development Commands

```bash
make setup             # Install dependencies
make serve             # Start API server
make serve-prod        # Production server
make interact          # CLI chat interface
make test              # Run tests
make gate              # Quality gates
make all-checks        # All tests + gates
```

### Dataset Commands

```bash
make dataset-opera     # Download Opera dataset
make dataset-info      # Show dataset stats
make personas-discover # Discover personas
make personas-list     # List all personas
make prep-sft-data     # Prepare training data
```

### AWS Management

```bash
make cost-status       # Check AWS costs
make cost-alert        # Set budget alert
make s3-list           # List S3 contents
make s3-upload         # Upload models to S3
make s3-download       # Download from S3
```

### Utilities

```bash
make help              # Show all commands
make quickstart        # Quick start guide
make clean             # Clean build artifacts
make fmt               # Format code
make lint              # Run linters
```

---

## 💡 Pro Tips

### 1. Use tmux on EC2

```bash
# Start persistent session
tmux new -s training

# Run training
make train

# Detach: Ctrl+B then D
# Training continues even if you disconnect!

# Reattach later
tmux attach -t training
```

### 2. Monitor Training Progress

```bash
# Create monitoring script
cat > monitor.sh << 'EOF'
#!/bin/bash
while true; do
  clear
  echo "=== Training Progress ==="
  ls artifacts/llm_adapters/*/adapter_model.safetensors 2>/dev/null | wc -l
  echo "/18 personas complete"
  echo ""
  nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv
  sleep 30
done
EOF
chmod +x monitor.sh
./monitor.sh
```

### 3. Save Instance Info

```bash
# After launch, save to file
echo "INSTANCE_IP=54.123.45.67" >> ~/.aws_training_env
echo "INSTANCE_ID=i-1234567890abcdef0" >> ~/.aws_training_env
source ~/.aws_training_env

# Use in scripts
ssh -i ~/darpan-training.pem ubuntu@$INSTANCE_IP
```

### 4. Backup Everything

```bash
# Backup trained models
make s3-upload

# Backup training data
aws s3 sync DATA/ s3://$TRAINING_S3_BUCKET/darpan_training_data/

# Download everything locally
make download
aws s3 sync s3://$TRAINING_S3_BUCKET/darpan_training_data/ DATA/
```

---

## 🎯 Next Steps After Training

### 1. Test Locally

```bash
make chat
make serve
make test
make gate
```

### 2. Deploy to Production

```bash
# Docker deployment
make docker-build
make docker-run

# Or direct deployment
make serve-prod
```

### 3. Integrate with Application

```python
import requests

# Call API
response = requests.post("http://localhost:8000/simulate", json={
    "user_id": "u123",
    "scenarios": [
        {"variant_id": "base"},
        {"variant_id": "discount", "context_overrides": {"price_mean": 90}}
    ],
    "explain": "blend"
})

predictions = response.json()
```

See [docs/API.md](docs/API.md) for full API reference.

---

## 📞 Get Help

- **Documentation:** [docs/](docs/)
- **Credentials:** [docs/CREDENTIALS_GUIDE.md](docs/CREDENTIALS_GUIDE.md)
- **Training:** [docs/TRAINING.md](docs/TRAINING.md)
- **API:** [docs/API.md](docs/API.md)

---

## ✅ Summary

**To use the system:**

1. **First time:**
   ```bash
   make workflow
   ```

2. **Train again:**
   ```bash
   make launch
   # SSH to instance
   make setup-instance
   make train
   # Back to local
   make download
   ```

3. **Use models:**
   ```bash
   make chat       # Interactive
   make serve      # API server
   ```

4. **Monitor:**
   ```bash
   ./darpan.py status
   make cost-status
   make s3-list
   ```

**That's it!** 🚀

---

**Last Updated:** 2025-10-11
**Cost:** ~$0.50 per training run
**Time:** ~2 hours total
**Output:** 18 production-ready LLM persona adapters
