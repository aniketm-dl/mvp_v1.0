#!/bin/bash
#
# Complete Pipeline: Phase 1-3 on Local Machine
# Runs OPeRA parsing, encoder training, and persona discovery
#
# Requirements:
# - GPU with 16GB+ VRAM (NVIDIA)
# - 100GB+ free disk space
# - Python 3.10+
#
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="$PROJECT_ROOT/logs/phase_1_3_local_$TIMESTAMP"
mkdir -p "$LOG_DIR"

echo -e "${BLUE}=========================================================================="
echo "🚀 PHASE 1-3 COMPLETE PIPELINE - LOCAL EXECUTION"
echo "==========================================================================${NC}"
echo "Project Root: $PROJECT_ROOT"
echo "Log Directory: $LOG_DIR"
echo ""

# Step 0: Pre-flight checks
echo -e "${YELLOW}[STEP 0] Pre-flight checks${NC}"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Check for GPU
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ NVIDIA GPU detected${NC}"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    echo -e "${YELLOW}⚠  No NVIDIA GPU detected - training will be slow${NC}"
fi

# Check disk space
FREE_SPACE=$(df -h "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
echo "Free disk space: $FREE_SPACE"

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip > "$LOG_DIR/pip_install.log" 2>&1
pip install -e . >> "$LOG_DIR/pip_install.log" 2>&1
pip install hdbscan umap-learn scikit-learn leidenalg python-igraph pytorch-lightning >> "$LOG_DIR/pip_install.log" 2>&1

# Verify installations
python3 -c "import torch; print('PyTorch:', torch.__version__)"
python3 -c "import hdbscan; print('HDBSCAN: OK')"
python3 -c "import pytorch_lightning; print('PyTorch Lightning: OK')"

echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 1: Phase 1 - Parse OPeRA Data
echo -e "${YELLOW}[STEP 1] PHASE 1: Parse OPeRA Data${NC}"
echo "Start time: $(date)"

# Download OPeRA raw data (if script exists)
if [ -f "scripts/download_opera_dataset.py" ]; then
    echo "Downloading OPeRA dataset..."
    python3 scripts/download_opera_dataset.py 2>&1 | tee "$LOG_DIR/phase1_download.log"
fi

# Parse OPeRA data
echo "Parsing OPeRA data..."
python3 scripts/parse_opera.py \
    --in DATA/OPeRA/raw \
    --out DATA/OPeRA/processed \
    --config CONFIGS/opera.yaml \
    2>&1 | tee "$LOG_DIR/phase1_parse.log"

echo -e "${GREEN}✓ Phase 1 complete: OPeRA data parsed${NC}"
echo "Output: DATA/OPeRA/processed/"
ls -lh DATA/OPeRA/processed/
echo ""

# Step 2: Phase 2 - Train Behavioral Encoder
echo -e "${YELLOW}[STEP 2] PHASE 2: Train Behavioral Encoder${NC}"
echo "Start time: $(date)"
echo "This may take 1-2 hours depending on GPU..."

python3 scripts/train/encoder_train.py \
    --data DATA/OPeRA/processed \
    --config CONFIGS/encoder.yaml \
    --out artifacts/encoder \
    2>&1 | tee "$LOG_DIR/phase2_encoder.log"

echo -e "${GREEN}✓ Phase 2 complete: Encoder trained${NC}"
echo "Output: artifacts/encoder/"
ls -lh artifacts/encoder/
echo ""

# Step 3: Phase 3E.1 - Generate Session Embeddings
echo -e "${YELLOW}[STEP 3] PHASE 3E.1: Generate Session Embeddings${NC}"
echo "Start time: $(date)"

python3 << 'PYTHON' 2>&1 | tee "$LOG_DIR/phase3e1_embeddings.log"
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import torch
import pandas as pd
import pytorch_lightning as pl
import numpy as np

print("Loading trained encoder...")
from src.data.opera.dataset import OPeRADataModule
from scripts.train.encoder_train import EncoderLightningModule

# Load trained encoder
checkpoint_path = "artifacts/encoder/best.ckpt"
if not Path(checkpoint_path).exists():
    checkpoint_path = "artifacts/encoder/checkpoints/last.ckpt"

model = EncoderLightningModule.load_from_checkpoint(checkpoint_path)
model.eval()

device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
print(f"Model loaded on {device}")

# Load data
dm = OPeRADataModule("DATA/OPeRA/processed", batch_size=128, num_workers=4)
dm.setup()

# Generate embeddings
embeddings = []
session_ids = []
rationales = []

print("Generating embeddings...")
with torch.no_grad():
    for batch_idx, batch in enumerate(dm.val_dataloader()):
        batch_device = {k: v.to(device) if torch.is_tensor(v) else v for k, v in batch.items()}
        outputs = model(batch_device)

        embeddings.append(outputs["fused"].cpu().numpy())

        if "session_id" in batch:
            session_ids.extend(batch["session_id"])
        else:
            session_ids.extend([f"session_{batch_idx}_{i}" for i in range(len(outputs["fused"]))])

        # Extract rationales if available
        if "rationale" in batch:
            rationales.extend([str(r) for r in batch["rationale"]])

        if (batch_idx + 1) % 100 == 0:
            print(f"Processed {batch_idx + 1} batches...")

embeddings = np.vstack(embeddings)

# Create DataFrame
df = pd.DataFrame(embeddings, columns=[f"emb_{i}" for i in range(embeddings.shape[1])])
df["session_id"] = session_ids
if rationales:
    df["rationales_agg"] = rationales

# Save
Path("artifacts/encoder").mkdir(parents=True, exist_ok=True)
df.to_parquet("artifacts/encoder/session_embeddings.parquet", index=False)

print(f"✓ Generated {len(df)} session embeddings")
print(f"  Shape: {embeddings.shape}")
print(f"  Saved to: artifacts/encoder/session_embeddings.parquet")
PYTHON

echo -e "${GREEN}✓ Phase 3E.1 complete: Session embeddings generated${NC}"
echo "Output: artifacts/encoder/session_embeddings.parquet"
ls -lh artifacts/encoder/session_embeddings.parquet
echo ""

# Step 4: Phase 3E.2 & 3E.3 - Discover Personas
echo -e "${YELLOW}[STEP 4] PHASE 3E.2 & 3E.3: Cluster Sessions & Discover Personas${NC}"
echo "Start time: $(date)"

# Update config to point to session embeddings
if [ -f "CONFIGS/discovery.yaml" ]; then
    # Backup original
    cp CONFIGS/discovery.yaml CONFIGS/discovery.yaml.bak

    # Update embeddings path
    sed -i.tmp 's|step_embeddings_path:.*|step_embeddings_path: artifacts/encoder/session_embeddings.parquet|' CONFIGS/discovery.yaml
    rm -f CONFIGS/discovery.yaml.tmp

    echo "Updated discovery config"
fi

# Run discovery pipeline
python3 scripts/run_dynamic_discovery.py 2>&1 | tee "$LOG_DIR/phase3e23_discovery.log"

echo -e "${GREEN}✓ Phase 3E.2 & 3E.3 complete: Personas discovered${NC}"
echo ""

# Display results
if [ -f "DATA/personas_discovered/registry.json" ]; then
    echo "Discovered personas:"
    cat DATA/personas_discovered/registry.json
    echo ""
fi

if [ -f "artifacts/discovery/report.md" ]; then
    echo "Discovery report:"
    cat artifacts/discovery/report.md
    echo ""
fi

echo ""
echo -e "${BLUE}=========================================================================="
echo "✅ PHASE 1-3 PIPELINE COMPLETE"
echo "==========================================================================${NC}"
echo "End time: $(date)"
echo ""
echo "Summary:"
echo "  ✓ Phase 1: OPeRA data parsed"
echo "  ✓ Phase 2: Behavioral encoder trained"
echo "  ✓ Phase 3E.1: Session embeddings generated"
echo "  ✓ Phase 3E.2: Sessions clustered"
echo "  ✓ Phase 3E.3: Personas discovered"
echo ""
echo "Outputs:"
echo "  - Encoder checkpoint: artifacts/encoder/best.ckpt"
echo "  - Session embeddings: artifacts/encoder/session_embeddings.parquet"
echo "  - Discovered personas: DATA/personas_discovered/"
echo "  - Discovery report: artifacts/discovery/report.md"
echo ""
echo "Next Steps:"
echo "  1. Review discovery report: cat artifacts/discovery/report.md"
echo "  2. Validate personas: ls -la DATA/personas_discovered/"
echo "  3. Check quality metrics in report"
echo "  4. Ready for Phase 4 (SFT dataset generation)"
echo ""
echo "Logs saved to: $LOG_DIR"
echo -e "${BLUE}==========================================================================${NC}"

# Restore original config
if [ -f "CONFIGS/discovery.yaml.bak" ]; then
    echo ""
    read -p "Restore original discovery.yaml? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mv CONFIGS/discovery.yaml.bak CONFIGS/discovery.yaml
        echo "Original config restored"
    fi
fi
