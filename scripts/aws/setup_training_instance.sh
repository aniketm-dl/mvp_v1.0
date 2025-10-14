#!/bin/bash
###############################################################################
# AWS GPU Instance Setup for Darpan Labs Digital Twin Training
#
# This script sets up a fresh AWS EC2 GPU instance with everything needed
# to train all 18 Mistral-7B persona adapters.
#
# Instance Requirements:
#   - GPU: g4dn.xlarge (T4, 16GB) or g5.xlarge (A10G, 24GB)
#   - OS: Ubuntu 22.04 LTS (Deep Learning AMI recommended)
#   - Storage: 100GB EBS gp3
#
# Usage:
#   chmod +x scripts/aws/setup_training_instance.sh
#   ./scripts/aws/setup_training_instance.sh
###############################################################################

set -e  # Exit on any error

echo "=========================================================================="
echo "🚀 DARPAN LABS - AWS GPU TRAINING INSTANCE SETUP"
echo "=========================================================================="

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on AWS EC2
if ! curl -s http://169.254.169.254/latest/meta-data/instance-type &>/dev/null; then
    echo -e "${YELLOW}⚠️  Warning: Not running on AWS EC2${NC}"
    echo "This script is designed for AWS EC2 instances."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Get instance info
if curl -s http://169.254.169.254/latest/meta-data/instance-type &>/dev/null; then
    INSTANCE_TYPE=$(curl -s http://169.254.169.254/latest/meta-data/instance-type)
    INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
    REGION=$(curl -s http://169.254.169.254/latest/meta-data/placement/region)

    echo -e "${GREEN}✅ Instance Details:${NC}"
    echo "   • Instance ID: $INSTANCE_ID"
    echo "   • Instance Type: $INSTANCE_TYPE"
    echo "   • Region: $REGION"
    echo
fi

# Step 1: Update system packages
echo "=========================================================================="
echo "📦 Step 1: Updating system packages..."
echo "=========================================================================="
sudo apt-get update -y
sudo apt-get upgrade -y

# Step 2: Install NVIDIA drivers and CUDA (if not already installed)
echo ""
echo "=========================================================================="
echo "🎮 Step 2: Checking GPU and CUDA installation..."
echo "=========================================================================="

if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✅ NVIDIA drivers already installed${NC}"
    nvidia-smi
else
    echo -e "${YELLOW}⚠️  Installing NVIDIA drivers...${NC}"

    # Install NVIDIA drivers
    sudo apt-get install -y ubuntu-drivers-common
    sudo ubuntu-drivers autoinstall

    # Install CUDA toolkit
    wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
    sudo dpkg -i cuda-keyring_1.0-1_all.deb
    sudo apt-get update
    sudo apt-get -y install cuda-toolkit-12-4

    echo -e "${GREEN}✅ NVIDIA drivers and CUDA installed${NC}"
    echo -e "${YELLOW}⚠️  Please reboot the instance and run this script again${NC}"
    echo "   Command: sudo reboot"
    exit 0
fi

# Step 3: Install Python 3.10+ and pip
echo ""
echo "=========================================================================="
echo "🐍 Step 3: Installing Python and dependencies..."
echo "=========================================================================="

sudo apt-get install -y \
    python3.10 \
    python3-pip \
    python3.10-venv \
    git \
    git-lfs \
    htop \
    tmux \
    vim \
    curl \
    wget

# Set Python 3.10 as default
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

python3 --version
pip3 --version

echo -e "${GREEN}✅ Python installed${NC}"

# Step 4: Install AWS CLI (for S3 sync)
echo ""
echo "=========================================================================="
echo "☁️  Step 4: Installing AWS CLI..."
echo "=========================================================================="

if ! command -v aws &> /dev/null; then
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
    rm -rf aws awscliv2.zip
    echo -e "${GREEN}✅ AWS CLI installed${NC}"
else
    echo -e "${GREEN}✅ AWS CLI already installed${NC}"
fi

aws --version

# Step 5: Configure AWS credentials (interactive)
echo ""
echo "=========================================================================="
echo "🔑 Step 5: AWS Credentials Setup"
echo "=========================================================================="
echo "We need AWS credentials for S3 access (to save trained models)."
echo ""
echo "Options:"
echo "  1. Use IAM role (if instance has one) - RECOMMENDED"
echo "  2. Configure manually with access keys"
echo ""

if aws sts get-caller-identity &>/dev/null; then
    echo -e "${GREEN}✅ AWS credentials already configured via IAM role${NC}"
else
    echo -e "${YELLOW}⚠️  No IAM role detected${NC}"
    read -p "Enter AWS Access Key ID (or press Enter to skip): " AWS_ACCESS_KEY
    if [ ! -z "$AWS_ACCESS_KEY" ]; then
        read -p "Enter AWS Secret Access Key: " AWS_SECRET_KEY
        read -p "Enter default region (e.g., us-east-1): " AWS_REGION

        aws configure set aws_access_key_id "$AWS_ACCESS_KEY"
        aws configure set aws_secret_access_key "$AWS_SECRET_KEY"
        aws configure set default.region "$AWS_REGION"

        echo -e "${GREEN}✅ AWS credentials configured${NC}"
    else
        echo -e "${YELLOW}⚠️  Skipping AWS configuration - you won't be able to use S3${NC}"
    fi
fi

# Step 6: Clone the repository
echo ""
echo "=========================================================================="
echo "📥 Step 6: Cloning mvp_v1.0 repository..."
echo "=========================================================================="

# Check if repo already exists
if [ -d "$HOME/mvp_v1.0" ]; then
    echo -e "${YELLOW}⚠️  Repository already exists at $HOME/mvp_v1.0${NC}"
    read -p "Delete and re-clone? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$HOME/mvp_v1.0"
    else
        cd "$HOME/mvp_v1.0"
        git pull
        echo -e "${GREEN}✅ Repository updated${NC}"
    fi
fi

if [ ! -d "$HOME/mvp_v1.0" ]; then
    echo "Enter your GitHub credentials:"
    read -p "GitHub username: " GITHUB_USER
    read -sp "GitHub Personal Access Token (PAT): " GITHUB_TOKEN
    echo

    git clone "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/aniketm-dl/mvp_v1.0.git" "$HOME/mvp_v1.0"
    echo -e "${GREEN}✅ Repository cloned${NC}"
fi

cd "$HOME/mvp_v1.0"
pwd

# Step 7: Install Python dependencies
echo ""
echo "=========================================================================="
echo "📚 Step 7: Installing Python dependencies..."
echo "=========================================================================="

# Create virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install PyTorch with CUDA support
echo "Installing PyTorch with CUDA 12.1..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install other dependencies
pip install \
    transformers>=4.42.0 \
    peft>=0.10.0 \
    accelerate>=0.30.0 \
    datasets>=2.20.0 \
    bitsandbytes \
    sentencepiece \
    protobuf \
    huggingface-hub

# Install project in editable mode
pip install -e .

echo -e "${GREEN}✅ Python dependencies installed${NC}"

# Step 8: Verify GPU availability in PyTorch
echo ""
echo "=========================================================================="
echo "🧪 Step 8: Verifying GPU access in PyTorch..."
echo "=========================================================================="

python3 << EOF
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"GPU count: {torch.cuda.device_count()}")
    print(f"GPU name: {torch.cuda.get_device_name(0)}")
    print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
else:
    print("❌ CUDA not available - training will be very slow!")
    exit(1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ GPU verification passed${NC}"
else
    echo -e "${RED}❌ GPU verification failed${NC}"
    exit 1
fi

# Step 9: HuggingFace authentication
echo ""
echo "=========================================================================="
echo "🤗 Step 9: HuggingFace Authentication"
echo "=========================================================================="
echo "You need a HuggingFace token to download Mistral-7B."
echo "Get your token from: https://huggingface.co/settings/tokens"
echo ""
read -sp "Enter your HuggingFace token: " HF_TOKEN
echo

if [ ! -z "$HF_TOKEN" ]; then
    # Login to HuggingFace
    echo "$HF_TOKEN" | huggingface-cli login --token "$HF_TOKEN"

    # Also set as environment variable
    echo "export HF_TOKEN=$HF_TOKEN" >> ~/.bashrc
    export HF_TOKEN="$HF_TOKEN"

    echo -e "${GREEN}✅ HuggingFace authentication configured${NC}"
else
    echo -e "${YELLOW}⚠️  No token provided - you may not be able to download models${NC}"
fi

# Step 10: Setup training data
echo ""
echo "=========================================================================="
echo "📁 Step 10: Setting up training data..."
echo "=========================================================================="

# Check if DATA exists in S3
read -p "Enter S3 bucket name for data storage (or press Enter to skip): " S3_BUCKET

if [ ! -z "$S3_BUCKET" ]; then
    echo "Checking S3 bucket: s3://${S3_BUCKET}/darpan_training_data/"

    if aws s3 ls "s3://${S3_BUCKET}/darpan_training_data/" &>/dev/null; then
        echo -e "${GREEN}✅ Found existing data in S3, downloading...${NC}"
        aws s3 sync "s3://${S3_BUCKET}/darpan_training_data/" DATA/
        echo -e "${GREEN}✅ Data synced from S3${NC}"
    else
        echo -e "${YELLOW}⚠️  No data found in S3, will generate fresh data${NC}"
    fi

    # Save S3 bucket name for later use
    echo "export TRAINING_S3_BUCKET=$S3_BUCKET" >> ~/.bashrc
    export TRAINING_S3_BUCKET="$S3_BUCKET"
fi

# Generate data if it doesn't exist
if [ ! -d "DATA" ] || [ ! -f "DATA/personas.json" ]; then
    echo "Generating training data..."
    python3 scripts/colab/setup_training_data.py

    # Upload to S3 if bucket is configured
    if [ ! -z "$S3_BUCKET" ]; then
        echo "Uploading generated data to S3..."
        aws s3 sync DATA/ "s3://${S3_BUCKET}/darpan_training_data/"
        echo -e "${GREEN}✅ Data uploaded to S3${NC}"
    fi
fi

# Step 11: Create helper scripts
echo ""
echo "=========================================================================="
echo "📝 Step 11: Creating helper scripts..."
echo "=========================================================================="

# Create training wrapper script
cat > ~/start_training.sh << 'SCRIPT'
#!/bin/bash
cd ~/mvp_v1.0
source venv/bin/activate
python scripts/aws/train_with_s3_sync.py "$@"
SCRIPT

chmod +x ~/start_training.sh

# Create shutdown script
cat > ~/shutdown_after_training.sh << 'SCRIPT'
#!/bin/bash
echo "Training complete. Shutting down in 5 minutes..."
echo "Cancel with: sudo shutdown -c"
sudo shutdown -h +5
SCRIPT

chmod +x ~/shutdown_after_training.sh

echo -e "${GREEN}✅ Helper scripts created${NC}"
echo "   • ~/start_training.sh - Start training with auto-save to S3"
echo "   • ~/shutdown_after_training.sh - Auto-shutdown after training"

# Step 12: Setup complete
echo ""
echo "=========================================================================="
echo "✨ SETUP COMPLETE!"
echo "=========================================================================="
echo ""
echo -e "${GREEN}🎉 Your AWS instance is ready for training!${NC}"
echo ""
echo "Quick Start:"
echo "  1. Start training all 18 personas:"
echo "     cd ~/mvp_v1.0"
echo "     source venv/bin/activate"
echo "     python scripts/aws/train_with_s3_sync.py"
echo ""
echo "  2. Or use tmux for persistent sessions:"
echo "     tmux new -s training"
echo "     ~/start_training.sh"
echo "     # Press Ctrl+B then D to detach"
echo ""
echo "  3. Auto-shutdown after training (saves money!):"
echo "     python scripts/aws/train_with_s3_sync.py --auto-shutdown"
echo ""
echo "Instance Info:"
echo "  • Location: ~/mvp_v1.0"
echo "  • Python env: ~/mvp_v1.0/venv"
if [ ! -z "$S3_BUCKET" ]; then
echo "  • S3 backup: s3://${S3_BUCKET}/darpan_training_data/"
fi
echo ""
echo "💡 Tips:"
echo "  • Use 'htop' to monitor CPU/RAM"
echo "  • Use 'nvidia-smi' to monitor GPU"
echo "  • Training takes ~1.5-3.5 hours depending on GPU type"
echo "  • Trained models will be in: artifacts/llm_adapters/"
echo ""
echo "⚠️  Don't forget to terminate the instance when done to avoid charges!"
echo ""
