#!/bin/bash
#
# Complete Pipeline: Phase 1-3 on AWS
# Runs OPeRA parsing, encoder training, and persona discovery
#
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
AWS_REGION="${AWS_REGION:-ap-south-1}"
INSTANCE_TYPE="${INSTANCE_TYPE:-g5.xlarge}"
MAX_SPOT_PRICE="${MAX_SPOT_PRICE:-0.50}"
KEY_NAME="darpan-training"
KEY_PATH="$HOME/darpan-training.pem"
S3_BUCKET="${TRAINING_S3_BUCKET:-darpan-training-aniketniranjanmishra}"

# Script paths
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="$PROJECT_ROOT/logs/phase_1_3_$TIMESTAMP"
mkdir -p "$LOG_DIR"

echo -e "${BLUE}=========================================================================="
echo "🚀 PHASE 1-3 COMPLETE PIPELINE - AWS EXECUTION"
echo "==========================================================================${NC}"
echo "Region: $AWS_REGION | Instance: $INSTANCE_TYPE | Bucket: $S3_BUCKET"
echo "Log Directory: $LOG_DIR"
echo ""

# Step 0: Pre-flight checks
echo -e "${YELLOW}[STEP 0] Pre-flight checks${NC}"
echo "Checking AWS credentials..."
aws sts get-caller-identity > /dev/null || {
    echo -e "${RED}❌ AWS credentials not configured${NC}"
    exit 1
}
echo -e "${GREEN}✓ AWS credentials valid${NC}"

echo "Checking S3 bucket..."
aws s3 ls "s3://$S3_BUCKET/" > /dev/null || {
    echo -e "${RED}❌ S3 bucket not accessible: $S3_BUCKET${NC}"
    exit 1
}
echo -e "${GREEN}✓ S3 bucket accessible${NC}"

# Verify key exists or create
if [ ! -f "$KEY_PATH" ]; then
    echo "Creating SSH key pair..."
    aws ec2 create-key-pair \
        --key-name "$KEY_NAME" \
        --region "$AWS_REGION" \
        --query 'KeyMaterial' \
        --output text > "$KEY_PATH" 2>/dev/null || {
        echo "Key pair exists in AWS, using with different name..."
        KEY_NAME="darpan-training-$(date +%s)"
        aws ec2 create-key-pair \
            --key-name "$KEY_NAME" \
            --region "$AWS_REGION" \
            --query 'KeyMaterial' \
            --output text > "$KEY_PATH"
    }
    chmod 400 "$KEY_PATH"
fi
echo -e "${GREEN}✓ SSH Key: $KEY_PATH${NC}"
echo ""

# Step 1: Launch AWS instance
echo -e "${YELLOW}[STEP 1] Launching AWS GPU instance${NC}"

# Get latest Ubuntu Deep Learning AMI
AMI_ID=$(aws ec2 describe-images \
    --region "$AWS_REGION" \
    --owners 099720109477 \
    --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" "Name=state,Values=available" \
    --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
    --output text)
echo "AMI: $AMI_ID"

# Get or create security group
SG_NAME="darpan-training-sg"
SG_ID=$(aws ec2 describe-security-groups --region "$AWS_REGION" --filters "Name=group-name,Values=$SG_NAME" --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || echo "")
if [ -z "$SG_ID" ] || [ "$SG_ID" == "None" ]; then
    SG_ID=$(aws ec2 create-security-group --region "$AWS_REGION" --group-name "$SG_NAME" --description "Darpan training" --query 'GroupId' --output text)
    aws ec2 authorize-security-group-ingress --region "$AWS_REGION" --group-id "$SG_ID" --protocol tcp --port 22 --cidr 0.0.0.0/0 2>/dev/null || true
fi
echo "Security Group: $SG_ID"

# Launch spot instance
LAUNCH_SPEC=$(cat <<EOF
{
  "ImageId": "$AMI_ID",
  "InstanceType": "$INSTANCE_TYPE",
  "KeyName": "$KEY_NAME",
  "SecurityGroupIds": ["$SG_ID"],
  "BlockDeviceMappings": [{"DeviceName": "/dev/sda1","Ebs": {"VolumeSize": 150,"VolumeType": "gp3"}}],
  "TagSpecifications": [{"ResourceType": "instance","Tags": [{"Key": "Name","Value": "darpan-phase-1-3"}]}],
  "UserData": "$(echo '#!/bin/bash
set -e
apt-get update
apt-get install -y git python3-pip python3-venv awscli
' | base64 -w 0)"
}
EOF
)

SPOT_REQUEST=$(aws ec2 request-spot-instances \
    --region "$AWS_REGION" \
    --spot-price "$MAX_SPOT_PRICE" \
    --instance-count 1 \
    --type "one-time" \
    --launch-specification "$LAUNCH_SPEC")

SPOT_REQUEST_ID=$(echo "$SPOT_REQUEST" | python3 -c "import sys,json; print(json.load(sys.stdin)['SpotInstanceRequests'][0]['SpotInstanceRequestId'])")
echo "Spot Request: $SPOT_REQUEST_ID"
echo "Waiting for fulfillment..."

# Wait for spot request
for i in {1..60}; do
    STATUS=$(aws ec2 describe-spot-instance-requests --region "$AWS_REGION" --spot-instance-request-ids "$SPOT_REQUEST_ID" --query 'SpotInstanceRequests[0].Status.Code' --output text)
    if [ "$STATUS" == "fulfilled" ]; then
        break
    elif [ "$STATUS" == "price-too-low" ] || [ "$STATUS" == "capacity-not-available" ]; then
        echo -e "${RED}❌ Spot request failed: $STATUS${NC}"
        exit 1
    fi
    echo "Status: $STATUS (attempt $i/60)"
    sleep 5
done

INSTANCE_ID=$(aws ec2 describe-spot-instance-requests --region "$AWS_REGION" --spot-instance-request-ids "$SPOT_REQUEST_ID" --query 'SpotInstanceRequests[0].InstanceId' --output text)
echo -e "${GREEN}✓ Instance launched: $INSTANCE_ID${NC}"

# Wait for running
echo "Waiting for instance to start..."
aws ec2 wait instance-running --region "$AWS_REGION" --instance-ids "$INSTANCE_ID"

PUBLIC_IP=$(aws ec2 describe-instances --region "$AWS_REGION" --instance-ids "$INSTANCE_ID" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)
echo -e "${GREEN}✓ Instance running: $PUBLIC_IP${NC}"
echo ""

# Save instance info
cat > "$LOG_DIR/instance_info.txt" << EOF
INSTANCE_ID=$INSTANCE_ID
PUBLIC_IP=$PUBLIC_IP
AWS_REGION=$AWS_REGION
KEY_PATH=$KEY_PATH
TIMESTAMP=$TIMESTAMP
EOF

# Wait for SSH to be ready
echo "Waiting for SSH to be ready..."
for i in {1..30}; do
    if ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=5 "ubuntu@$PUBLIC_IP" "echo 'SSH ready'" 2>/dev/null; then
        break
    fi
    echo "Attempt $i/30..."
    sleep 10
done
echo -e "${GREEN}✓ SSH ready${NC}"
echo ""

# Step 2: Setup environment on instance
echo -e "${YELLOW}[STEP 2] Setting up environment on AWS instance${NC}"

ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "ubuntu@$PUBLIC_IP" << 'ENDSSH'
set -e

# Clone repository
echo "Cloning repository..."
git clone https://github.com/aniketm-dl/mvp_v1.0.git
cd mvp_v1.0
git checkout refactor/aws-workflow-automation

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -e .

# Install additional dependencies for Phase 3
pip install hdbscan umap-learn scikit-learn leidenalg python-igraph pytorch-lightning

# Verify installations
echo "Verifying installations..."
python3 -c "import torch; print('PyTorch:', torch.__version__)"
python3 -c "import hdbscan; print('HDBSCAN: OK')"
python3 -c "import pytorch_lightning; print('PyTorch Lightning: OK')"

echo "Environment setup complete"
ENDSSH

echo -e "${GREEN}✓ Environment setup complete${NC}"
echo ""

# Step 3: Phase 1 - Parse OPeRA Data
echo -e "${YELLOW}[STEP 3] PHASE 1: Parse OPeRA Data${NC}"

ssh -i "$KEY_PATH" "ubuntu@$PUBLIC_IP" << 'ENDSSH'
set -e
cd mvp_v1.0
source venv/bin/activate

echo "Phase 1: Downloading and parsing OPeRA dataset..."

# Download OPeRA raw data (if script exists)
if [ -f "scripts/download_opera_dataset.py" ]; then
    echo "Downloading OPeRA dataset..."
    python3 scripts/download_opera_dataset.py
fi

# Parse OPeRA data
echo "Parsing OPeRA data..."
python3 scripts/parse_opera.py \
    --in DATA/OPeRA/raw \
    --out DATA/OPeRA/processed \
    --config CONFIGS/opera.yaml

echo "✓ Phase 1 complete"
ls -lh DATA/OPeRA/processed/
ENDSSH

echo -e "${GREEN}✓ Phase 1 complete: OPeRA data parsed${NC}"
echo ""

# Step 4: Phase 2 - Train Behavioral Encoder
echo -e "${YELLOW}[STEP 4] PHASE 2: Train Behavioral Encoder${NC}"

ssh -i "$KEY_PATH" "ubuntu@$PUBLIC_IP" << 'ENDSSH'
set -e
cd mvp_v1.0
source venv/bin/activate

echo "Phase 2: Training behavioral encoder..."

python3 scripts/train/encoder_train.py \
    --data DATA/OPeRA/processed \
    --config CONFIGS/encoder.yaml \
    --out artifacts/encoder

echo "✓ Phase 2 complete"
ls -lh artifacts/encoder/
ENDSSH

echo -e "${GREEN}✓ Phase 2 complete: Encoder trained${NC}"
echo ""

# Step 5: Phase 3E.1 - Generate Session Embeddings
echo -e "${YELLOW}[STEP 5] PHASE 3E.1: Generate Session Embeddings${NC}"

ssh -i "$KEY_PATH" "ubuntu@$PUBLIC_IP" << 'ENDSSH'
set -e
cd mvp_v1.0
source venv/bin/activate

echo "Phase 3E.1: Generating session embeddings from encoder..."

# Run inference to generate embeddings
python3 << 'PYTHON'
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import torch
import pandas as pd
import pytorch_lightning as pl
from src.data.opera.dataset import OPeRADataModule
from scripts.train.encoder_train import EncoderLightningModule

# Load trained encoder
checkpoint_path = "artifacts/encoder/best.ckpt"
model = EncoderLightningModule.load_from_checkpoint(checkpoint_path)
model.eval()
model.to("cuda" if torch.cuda.is_available() else "cpu")

# Load data
dm = OPeRADataModule("DATA/OPeRA/processed", batch_size=128, num_workers=4)
dm.setup()

# Generate embeddings
embeddings = []
session_ids = []

with torch.no_grad():
    for batch_idx, batch in enumerate(dm.val_dataloader()):
        batch = {k: v.to(model.device) if torch.is_tensor(v) else v for k, v in batch.items()}
        outputs = model(batch)
        embeddings.append(outputs["fused"].cpu().numpy())
        if "session_id" in batch:
            session_ids.extend(batch["session_id"])
        else:
            session_ids.extend([f"session_{batch_idx}_{i}" for i in range(len(outputs["fused"]))])

        if batch_idx % 100 == 0:
            print(f"Processed {batch_idx} batches...")

import numpy as np
embeddings = np.vstack(embeddings)

# Save
Path("artifacts/encoder").mkdir(parents=True, exist_ok=True)
df = pd.DataFrame(embeddings, columns=[f"emb_{i}" for i in range(embeddings.shape[1])])
df["session_id"] = session_ids
df.to_parquet("artifacts/encoder/session_embeddings.parquet", index=False)

print(f"✓ Generated {len(df)} session embeddings")
print(f"  Shape: {embeddings.shape}")
print(f"  Saved to: artifacts/encoder/session_embeddings.parquet")
PYTHON

echo "✓ Phase 3E.1 complete"
ls -lh artifacts/encoder/session_embeddings.parquet
ENDSSH

echo -e "${GREEN}✓ Phase 3E.1 complete: Session embeddings generated${NC}"
echo ""

# Step 6: Phase 3E.2 & 3E.3 - Discover Personas
echo -e "${YELLOW}[STEP 6] PHASE 3E.2 & 3E.3: Cluster Sessions & Discover Personas${NC}"

ssh -i "$KEY_PATH" "ubuntu@$PUBLIC_IP" << 'ENDSSH'
set -e
cd mvp_v1.0
source venv/bin/activate

echo "Phase 3E.2 & 3E.3: Running persona discovery pipeline..."

# Update config to point to session embeddings
sed -i 's|step_embeddings_path:.*|step_embeddings_path: artifacts/encoder/session_embeddings.parquet|' CONFIGS/discovery.yaml

# Run discovery pipeline
python3 scripts/run_dynamic_discovery.py

echo "✓ Phase 3E.2 & 3E.3 complete"
echo ""
echo "Discovered personas:"
cat DATA/personas_discovered/registry.json
echo ""
echo "Discovery report:"
cat artifacts/discovery/report.md
ENDSSH

echo -e "${GREEN}✓ Phase 3E.2 & 3E.3 complete: Personas discovered${NC}"
echo ""

# Step 7: Upload artifacts to S3
echo -e "${YELLOW}[STEP 7] Uploading artifacts to S3${NC}"

ssh -i "$KEY_PATH" "ubuntu@$PUBLIC_IP" << ENDSSH
set -e
cd mvp_v1.0

echo "Uploading artifacts to S3..."

# Upload encoder
aws s3 sync artifacts/encoder/ s3://$S3_BUCKET/phase_1_3/$TIMESTAMP/encoder/

# Upload discovered personas
aws s3 sync DATA/personas_discovered/ s3://$S3_BUCKET/phase_1_3/$TIMESTAMP/personas_discovered/

# Upload discovery artifacts
aws s3 sync artifacts/discovery/ s3://$S3_BUCKET/phase_1_3/$TIMESTAMP/discovery/

# Upload processed data
aws s3 sync DATA/OPeRA/processed/ s3://$S3_BUCKET/phase_1_3/$TIMESTAMP/opera_processed/ \
    --exclude "*.parquet" --include "*.json"

echo "✓ Artifacts uploaded to S3"
ENDSSH

echo -e "${GREEN}✓ Artifacts uploaded to S3${NC}"
echo ""

# Step 8: Download artifacts locally
echo -e "${YELLOW}[STEP 8] Downloading artifacts to local machine${NC}"

mkdir -p "$PROJECT_ROOT/artifacts/encoder"
mkdir -p "$PROJECT_ROOT/DATA/personas_discovered"
mkdir -p "$PROJECT_ROOT/artifacts/discovery"

echo "Downloading encoder..."
aws s3 sync "s3://$S3_BUCKET/phase_1_3/$TIMESTAMP/encoder/" "$PROJECT_ROOT/artifacts/encoder/"

echo "Downloading discovered personas..."
aws s3 sync "s3://$S3_BUCKET/phase_1_3/$TIMESTAMP/personas_discovered/" "$PROJECT_ROOT/DATA/personas_discovered/"

echo "Downloading discovery artifacts..."
aws s3 sync "s3://$S3_BUCKET/phase_1_3/$TIMESTAMP/discovery/" "$PROJECT_ROOT/artifacts/discovery/"

echo -e "${GREEN}✓ Artifacts downloaded locally${NC}"
echo ""

# Step 9: Cleanup
echo -e "${YELLOW}[STEP 9] Cleaning up${NC}"

read -p "Terminate EC2 instance? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Terminating instance $INSTANCE_ID..."
    aws ec2 terminate-instances --region "$AWS_REGION" --instance-ids "$INSTANCE_ID"
    echo -e "${GREEN}✓ Instance terminated${NC}"
else
    echo "Instance $INSTANCE_ID left running"
    echo "To terminate later: aws ec2 terminate-instances --region $AWS_REGION --instance-ids $INSTANCE_ID"
fi

echo ""
echo -e "${BLUE}=========================================================================="
echo "✅ PHASE 1-3 PIPELINE COMPLETE"
echo "==========================================================================${NC}"
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
echo "S3 Location: s3://$S3_BUCKET/phase_1_3/$TIMESTAMP/"
echo ""
echo "Next Steps:"
echo "  1. Review discovery report: cat artifacts/discovery/report.md"
echo "  2. Validate personas: ls -la DATA/personas_discovered/"
echo "  3. Ready for Phase 4 (SFT dataset generation)"
echo ""
echo "Logs saved to: $LOG_DIR"
echo -e "${BLUE}==========================================================================${NC}"
