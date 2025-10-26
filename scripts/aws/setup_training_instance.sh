#!/bin/bash
###############################################################################
# AWS Instance Bootstrap for OPeRA-SSR
#
# This script prepares a fresh Ubuntu GPU instance to run the OPeRA-SSR pipeline:
#   1. Installs system packages (Python, git, AWS CLI)
#   2. Clones the repository
#   3. Creates a virtual environment and installs project dependencies
#   4. Performs a quick CUDA sanity check
#   5. Prints the commands required to run the end-to-end training pipeline
#
# Usage:
#   chmod +x scripts/aws/setup_training_instance.sh
#   ./scripts/aws/setup_training_instance.sh
###############################################################################

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

REPO_URL="https://github.com/aniketm-dl/mvp_v1.0.git"
REPO_DIR="$HOME/mvp_v1.0"
PYTHON_BIN="python3.10"

echo -e "${CYAN}=========================================================================="
echo "🚀 Darpan Labs – AWS Instance Bootstrap"
echo -e "==========================================================================${NC}"

echo -e "${CYAN}1. Updating system packages...${NC}"
sudo apt-get update -y
sudo apt-get upgrade -y

echo -e "${CYAN}2. Installing system dependencies...${NC}"
sudo apt-get install -y \
    $PYTHON_BIN \
    ${PYTHON_BIN}-venv \
    ${PYTHON_BIN}-dev \
    python3-pip \
    git git-lfs \
    unzip \
    curl \
    tmux \
    htop

# Install AWS CLI v2 if missing
if ! command -v aws >/dev/null 2>&1; then
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip >/dev/null
    sudo ./aws/install
    rm -rf aws awscliv2.zip
fi

# Ensure python3 points to desired interpreter
sudo update-alternatives --install /usr/bin/python3 python3 $(command -v $PYTHON_BIN) 1

python3 --version
pip3 --version

echo -e "${CYAN}3. Cloning repository...${NC}"
if [ -d "$REPO_DIR" ]; then
    echo -e "${YELLOW}Repository already exists at $REPO_DIR – pulling latest changes.${NC}"
    git -C "$REPO_DIR" pull --rebase
else
    git clone "$REPO_URL" "$REPO_DIR"
fi

cd "$REPO_DIR"

echo -e "${CYAN}4. Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip

echo -e "${CYAN}5. Installing project dependencies...${NC}"
pip install -e .

echo -e "${CYAN}6. Checking CUDA availability...${NC}"
python - <<'PY'
import torch

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU name: {torch.cuda.get_device_name(0)}")
else:
    print("⚠️  CUDA not available. Training will run on CPU only.")
PY

echo -e "${GREEN}\n✅ Instance setup complete!${NC}"
echo
echo "Next steps (run inside the virtual environment):"
echo "  1. export OPENAI_API_KEY=sk-..."
echo "  2. export HF_TOKEN=hf_...  # optional but recommended"
echo "  3. bash scripts/aws/train_complete_pipeline.sh --use-llm-elicitations --llm-max-samples 500 --auto-shutdown"
echo
echo "Individual steps (if you prefer manual control):"
echo "  python scripts/01_download_opera.py"
echo "  python scripts/02_preprocess_opera.py"
echo "  python scripts/03_discover_personas.py --use-llm-summary"
echo "  python scripts/04_train_ssr.py --use-references --training-pairs DATA/OPeRA/processed/ssr_training_pairs_llm.jsonl"
echo "  python scripts/07_evaluate.py"
echo
echo -e "${CYAN}Happy modeling!${NC}"
