# Darpan Labs - Digital Twin Simulator

**Production-ready LLM-powered personas for e-commerce "what-if" simulations**

Train 18+ unique shopper personas on AWS GPU in 90 minutes for ~$0.50. Ask "what if we change the price?" and get persona-specific predictions with explanations.

---

## 🚀 Quick Start (5 Steps)

### Complete Automated Workflow

```bash
# One command to rule them all
make workflow
```

This will:
1. **Launch** AWS GPU instance (g5.xlarge spot)
2. **Setup** environment (CUDA, Python, dependencies)
3. **Train** all persona adapters (1.5 hours)
4. **Download** trained models from S3
5. **Chat** with your trained personas interactively

### Step-by-Step Workflow

```bash
# 1. Launch AWS instance
make launch

# 2. SSH into instance and run setup
ssh -i ~/darpan-training.pem ubuntu@<INSTANCE_IP>
make setup-instance

# 3. Train models (on EC2 instance)
make train

# 4. Download models (on local machine)
make download

# 5. Chat with personas
make chat
```

### Cost

- **Instance**: g5.xlarge spot @ $0.35/hr
- **Training time**: ~1.5 hours
- **Total cost**: ~$0.50

---

## 📋 Prerequisites

### Local Machine

```bash
# Install AWS CLI
brew install awscli  # macOS
# or: pip install awscli

# Configure AWS credentials
aws configure
# Enter Access Key ID, Secret Key, region (us-east-1)

# Create S3 bucket for models
aws s3 mb s3://darpan-training-$(whoami)
export TRAINING_S3_BUCKET=darpan-training-$(whoami)

# Clone repo
git clone https://github.com/aniketm-dl/mvp_v1.0.git
cd mvp_v1.0

# Install dependencies
make setup
```

### AWS Account

1. Sign up at [aws.amazon.com](https://aws.amazon.com)
2. Create IAM user with EC2 + S3 permissions
3. Generate Access Key (save credentials)
4. Request GPU quota if needed (see [docs/AWS_SETUP.md](docs/AWS_SETUP.md))

### HuggingFace Token

1. Go to https://huggingface.co/settings/tokens
2. Create token with "Read" access
3. Keep it handy (needed during setup)

---

## 💻 Usage

### Workflow Commands

```bash
# Full automated workflow
make workflow                    # Complete: Launch → Setup → Train → Download → Chat
make workflow-status             # Check progress

# Individual steps
make launch                      # Launch AWS GPU instance
make setup-instance              # Setup instance (run on EC2)
make train                       # Train all personas (on EC2)
make train-subset                # Train specific personas
make train-parallel              # Multi-GPU parallel training
make download                    # Download trained models from S3
make chat                        # Interactive chat with personas
```

### Development Commands

```bash
# Local API server
make serve                       # Start FastAPI server (http://localhost:8000)
make interact                    # CLI chat interface

# Testing & Quality
make test                        # Run all tests
make gate                        # Check persona separation quality
make all-checks                  # Full test suite

# Code quality
make fmt                         # Format code
make lint                        # Run linters
make clean                       # Clean build artifacts
```

### Dataset & Personas

```bash
# Dataset management
make dataset-opera               # Download Opera dataset
make dataset-info                # Show dataset statistics
make personas-discover           # Discover personas from Opera data
make personas-list               # List all available personas

# Training data preparation
make prep-sft-data               # Prepare SFT training data
make prep-opera-sft              # Prepare from Opera dataset
```

### AWS & Cost Management

```bash
# Cost tracking
make cost-status                 # Check current AWS costs
make cost-alert                  # Set budget alert ($5 default)

# S3 management
make s3-list                     # List S3 contents
make s3-upload                   # Upload models to S3
make s3-download                 # Download from S3 (alias: make download)
```

### Help

```bash
make help                        # Show all available commands
make quickstart                  # Show quick start guide
```

---

## 🏗️ Architecture

### Key Components

```
mvp_v1.0/
├── darpan.py                    # Unified CLI (NEW!)
├── Makefile                     # All commands in one place (UPDATED!)
│
├── src/
│   ├── api/                     # FastAPI endpoints
│   ├── models/                  # Mixture model, encoders, policy heads
│   ├── reasoning/               # LLM twins, guard, cache
│   ├── datasets/                # Dataset abstraction (NEW!)
│   │   ├── base.py             # Base dataset interface
│   │   ├── opera.py            # Opera dataset implementation
│   │   └── factory.py          # Dataset factory (extensible)
│   └── features/                # Feature extraction
│
├── scripts/
│   ├── aws/                     # AWS training automation
│   │   ├── launch_training_instance.sh
│   │   ├── setup_training_instance.sh
│   │   ├── train_production.py
│   │   └── train_with_s3_sync.py
│   ├── opera/                   # Opera dataset scripts
│   └── train_*.py               # Training scripts
│
├── DATA/
│   ├── personas.json            # Persona definitions
│   ├── sft/                     # Training data (JSONL)
│   └── opera/                   # Opera dataset files
│
├── CONFIGS/
│   ├── aws/                     # AWS training config
│   ├── serve/                   # API serving config
│   └── defaults.yaml            # Default settings
│
└── docs/                        # Documentation
    ├── README.md                # This file
    ├── AWS_SETUP.md             # AWS account setup
    ├── TRAINING.md              # Training guide
    └── API.md                   # API documentation
```

### Dataset Abstraction Layer (NEW!)

Support for multiple datasets with unified interface:

```python
from src.datasets import DatasetFactory

# Load Opera dataset
dataset = DatasetFactory.create("opera")

# Download raw data
dataset.download()

# Discover personas
personas = dataset.prepare_personas()

# Generate training data for specific persona
dataset.prepare_training_data("premium_buyer", Path("DATA/sft/premium_buyer.jsonl"))

# Get dataset stats
stats = dataset.get_stats()
```

**Future datasets**: Easy to add Amazon, Shopify, etc. by implementing `BaseDataset`.

---

## 🎯 What This Does

### Problem

You want to answer questions like:
- "What if we raised prices 10%?"
- "What if we offered free shipping?"
- "What if we changed the ad copy?"

### Solution

Train LLM-powered "twin" personas that mimic real user segments:
- **Bargain Hunter**: Prioritizes lowest price
- **Premium Buyer**: Values quality over price
- **Deal Hunter**: Loves promotions
- **+ 15 more personas** from Opera dataset

### Example

```python
# API Request
POST /simulate
{
  "user_id": "u123",
  "scenarios": [
    {"variant_id": "base"},
    {"variant_id": "10pct_off", "context_overrides": {"price_mean": 90}},
    {"variant_id": "free_ship", "context_overrides": {"delivery_eta_days": 1}}
  ],
  "explain": "blend"
}

# Response
{
  "base": {
    "top_product": "laptop",
    "probability": 0.65,
    "reason": "Good specs at reasonable price"
  },
  "10pct_off": {
    "top_product": "laptop",
    "probability": 0.82,    # +17% lift!
    "reason": "Great deal with discount",
    "delta_vs_base": +0.17
  },
  "free_ship": {
    "top_product": "laptop",
    "probability": 0.71,    # +6% lift
    "reason": "Fast delivery is appealing",
    "delta_vs_base": +0.06
  }
}
```

---

## 🔧 Configuration

### Training Configuration

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

# Parallelization (multi-GPU)
parallelization:
  enabled: false
  num_workers: 4

# Error handling
error_handling:
  max_retries: 3
  fail_fast: false

# Cost management
cost:
  auto_shutdown: true
  budget_alert_usd: 5.0
```

### API Configuration

Edit `CONFIGS/serve/api.yaml`:

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  workers: 4

models:
  base_model: "mistralai/Mistral-7B-Instruct-v0.2"
  adapter_dir: "artifacts/llm_adapters"
  use_cache: true

features:
  use_policy_heads: true  # Fast path
  explain_mode: "blend"   # or "per_twin" or "none"
```

---

## 📊 Quality Gates

We ensure personas are well-separated and stable:

```bash
make gate
```

Checks:
- **Silhouette Score** ≥ 0.35 (cluster separation)
- **Jensen-Shannon Divergence** ≥ 0.10 (probability distribution difference)
- **Adjusted Rand Index** ≥ 0.80 (clustering stability)

If gates fail, personas are too similar. Retrain with more diverse data.

---

## 🧪 Testing

```bash
# Quick tests
make test                        # Run all tests (2-3 min)

# Specific tests
make test-specific FILE=test_health.py
make gate                        # Separation metrics
make guard                       # Reason validation

# Full test suite
make all-checks                  # Everything (5-10 min)
```

---

## 🚢 Production Deployment

### Docker

```bash
# Build image
make docker-build

# Run container
make docker-run

# Access API at http://localhost:8000
```

### Manual Deployment

```bash
# On production server
git clone https://github.com/aniketm-dl/mvp_v1.0.git
cd mvp_v1.0

# Download trained models
export TRAINING_S3_BUCKET=your-bucket
make download

# Start production server
make serve-prod

# Or use systemd, supervisor, etc.
```

---

## 📚 Documentation

- **[AWS Setup Guide](docs/AWS_SETUP.md)** - Complete AWS account setup
- **[Training Guide](docs/TRAINING.md)** - Detailed training instructions
- **[API Documentation](docs/API.md)** - API endpoints and examples
- **[Architecture](docs/ARCHITECTURE.md)** - System design and components

---

## 🤝 Contributing

We welcome contributions! Areas to improve:

1. **New datasets**: Implement `BaseDataset` for Amazon, Shopify, etc.
2. **Better personas**: Improve persona discovery algorithms
3. **Faster training**: Optimize LoRA configuration
4. **Web UI**: Build interactive dashboard
5. **Model evaluation**: Better separation metrics

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📝 License

MIT License - see [LICENSE](LICENSE)

---

## 🆘 Troubleshooting

### "CUDA out of memory"

```bash
# Use smaller batch size or larger GPU
# Edit scripts/train_llm_persona_sft.py:
# per_device_train_batch_size=1
# gradient_accumulation_steps=8

# Or use g5.xlarge instead of g4dn.xlarge
```

### "AWS credentials not found"

```bash
aws configure
# Enter your Access Key ID and Secret Access Key
```

### "S3 sync failed"

```bash
# Check bucket permissions
aws s3 ls s3://your-bucket/

# Manually sync
aws s3 sync artifacts/llm_adapters/ s3://your-bucket/trained_adapters/
```

### "Training is slow"

```bash
# Check GPU usage (should be 80-100%)
nvidia-smi

# Verify CUDA is available
python -c "import torch; print(torch.cuda.is_available())"

# Use faster GPU: g5.xlarge instead of g4dn.xlarge
```

### "Spot instance terminated"

Spot instances can be reclaimed. Solutions:
- Set higher max spot price
- Use on-demand instances (more expensive)
- Enable auto-resume from S3 backups

---

## 🎓 What's Next?

After successful training:

1. **Test locally**: `make chat`
2. **Deploy API**: `make serve`
3. **Integrate with app**: See [API docs](docs/API.md)
4. **Monitor performance**: `make metrics`
5. **Iterate on personas**: Refine based on feedback

---

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/aniketm-dl/mvp_v1.0/issues)
- **Email**: support@darpanlabs.com

---

**Built with ❤️ by Darpan Labs**

*Making AI personas accessible, affordable, and production-ready.*
