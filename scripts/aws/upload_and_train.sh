#!/bin/bash
###############################################################################
# Upload SFT Data and Start Training on AWS EC2 Instance
#
# This script uploads the prepared SFT training data to the running EC2 instance
# and starts training all 18 personas.
#
# Prerequisites:
#   - EC2 instance is running
#   - SSH access configured
#   - Instance has been set up with the setup script
#
# Usage:
#   ./scripts/aws/upload_and_train.sh <instance_ip> <key_file>
#   ./scripts/aws/upload_and_train.sh 54.123.45.67 ~/darpan-training.pem
###############################################################################

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================================================="
echo "🚀 UPLOAD SFT DATA AND START TRAINING"
echo "=========================================================================="
echo ""

# Check arguments
if [ $# -lt 2 ]; then
    echo -e "${RED}❌ Usage: $0 <instance_ip> <key_file>${NC}"
    echo ""
    echo "Example:"
    echo "  $0 54.123.45.67 ~/darpan-training.pem"
    echo ""
    echo "To find your instance IP:"
    echo "  aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,State.Name,PublicIpAddress]' --output table"
    exit 1
fi

INSTANCE_IP=$1
KEY_FILE=$2

# Validate key file
if [ ! -f "$KEY_FILE" ]; then
    echo -e "${RED}❌ Key file not found: $KEY_FILE${NC}"
    exit 1
fi

# Test SSH connection
echo "🔍 Testing SSH connection to $INSTANCE_IP..."
if ! ssh -i "$KEY_FILE" -o ConnectTimeout=10 -o StrictHostKeyChecking=no ubuntu@$INSTANCE_IP "echo 'SSH connection successful'" &>/dev/null; then
    echo -e "${RED}❌ Cannot connect to instance${NC}"
    echo "Please check:"
    echo "  • Instance IP: $INSTANCE_IP"
    echo "  • Key file: $KEY_FILE"
    echo "  • Security group allows SSH (port 22)"
    echo "  • Instance is running"
    exit 1
fi

echo -e "${GREEN}✅ SSH connection successful${NC}"
echo ""

# Step 1: Upload SFT training data
echo "=========================================================================="
echo "📤 Step 1: Uploading SFT training data..."
echo "=========================================================================="

# Create DATA/sft directory on instance
ssh -i "$KEY_FILE" ubuntu@$INSTANCE_IP "mkdir -p ~/mvp_v1.0/DATA/sft"

# Upload all SFT files
echo "Uploading SFT data files..."
scp -i "$KEY_FILE" DATA/sft/*.jsonl ubuntu@$INSTANCE_IP:~/mvp_v1.0/DATA/sft/

echo -e "${GREEN}✅ SFT data uploaded${NC}"
echo ""

# Step 2: Upload personas.json
echo "=========================================================================="
echo "👥 Step 2: Uploading personas configuration..."
echo "=========================================================================="

scp -i "$KEY_FILE" DATA/personas.json ubuntu@$INSTANCE_IP:~/mvp_v1.0/DATA/

echo -e "${GREEN}✅ Personas configuration uploaded${NC}"
echo ""

# Step 3: Upload training configuration
echo "=========================================================================="
echo "⚙️  Step 3: Uploading training configuration..."
echo "=========================================================================="

scp -i "$KEY_FILE" CONFIGS/aws/training_config.yaml ubuntu@$INSTANCE_IP:~/mvp_v1.0/CONFIGS/aws/

echo -e "${GREEN}✅ Training configuration uploaded${NC}"
echo ""

# Step 4: Verify setup on instance
echo "=========================================================================="
echo "🔍 Step 4: Verifying instance setup..."
echo "=========================================================================="

ssh -i "$KEY_FILE" ubuntu@$INSTANCE_IP << 'EOF'
cd ~/mvp_v1.0

echo "Checking Python environment..."
source venv/bin/activate
python --version

echo "Checking GPU availability..."
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU count: {torch.cuda.device_count()}') if torch.cuda.is_available() else None"

echo "Checking SFT data..."
ls -la DATA/sft/ | head -5
echo "Total SFT files: $(ls DATA/sft/*.jsonl | wc -l)"

echo "Checking personas..."
ls -la DATA/personas.json
EOF

echo -e "${GREEN}✅ Instance verification complete${NC}"
echo ""

# Step 5: Start training
echo "=========================================================================="
echo "🎓 Step 5: Starting persona training..."
echo "=========================================================================="

echo "Starting training in tmux session for persistence..."
ssh -i "$KEY_FILE" ubuntu@$INSTANCE_IP << 'EOF'
cd ~/mvp_v1.0
source venv/bin/activate

# Create tmux session for training
tmux new-session -d -s training

# Start training in tmux session
tmux send-keys -t training "cd ~/mvp_v1.0" Enter
tmux send-keys -t training "source venv/bin/activate" Enter
tmux send-keys -t training "python scripts/aws/train_production.py --auto-shutdown" Enter

echo "Training started in tmux session 'training'"
echo "To monitor progress:"
echo "  tmux attach -t training"
echo "  # Press Ctrl+B then D to detach"
EOF

echo -e "${GREEN}✅ Training started in tmux session${NC}"
echo ""

# Step 6: Provide monitoring instructions
echo "=========================================================================="
echo "📊 Step 6: Monitoring Training Progress"
echo "=========================================================================="
echo ""
echo "Training is now running in the background. Here's how to monitor:"
echo ""
echo "1. Connect to instance:"
echo -e "   ${BLUE}ssh -i $KEY_FILE ubuntu@$INSTANCE_IP${NC}"
echo ""
echo "2. Attach to training session:"
echo -e "   ${BLUE}tmux attach -t training${NC}"
echo "   (Press Ctrl+B then D to detach without stopping training)"
echo ""
echo "3. Check training progress:"
echo -e "   ${BLUE}ls -la ~/mvp_v1.0/artifacts/llm_adapters/ | wc -l${NC}"
echo ""
echo "4. Monitor GPU usage:"
echo -e "   ${BLUE}nvidia-smi${NC}"
echo ""
echo "5. Check training logs:"
echo -e "   ${BLUE}tail -f ~/mvp_v1.0/artifacts/training.log${NC}"
echo ""
echo "=========================================================================="
echo "⏱️  Expected Training Time"
echo "=========================================================================="
echo ""
echo "• g4dn.xlarge (T4): ~3.5 hours"
echo "• g5.xlarge (A10G): ~1.5 hours"
echo "• p3.2xlarge (V100): ~1 hour"
echo ""
echo "Training will auto-shutdown the instance when complete."
echo ""
echo "=========================================================================="
echo "💾 Downloading Trained Models"
echo "=========================================================================="
echo ""
echo "After training completes, download models locally:"
echo ""
echo "1. Create S3 bucket (if not exists):"
echo -e "   ${BLUE}aws s3 mb s3://darpan-training-aniketniranjanmishra${NC}"
echo ""
echo "2. Sync models from instance to S3:"
echo -e "   ${BLUE}ssh -i $KEY_FILE ubuntu@$INSTANCE_IP 'aws s3 sync ~/mvp_v1.0/artifacts/llm_adapters/ s3://darpan-training-aniketniranjanmishra/trained_adapters/'${NC}"
echo ""
echo "3. Download to local machine:"
echo -e "   ${BLUE}aws s3 sync s3://darpan-training-aniketniranjanmishra/trained_adapters/ artifacts/llm_adapters/${NC}"
echo ""
echo "=========================================================================="
echo "✨ Training Started Successfully!"
echo "=========================================================================="
echo ""
echo -e "${GREEN}🎉 All 18 personas are now training on AWS!${NC}"
echo ""
echo "Next steps:"
echo "  1. Monitor progress using the commands above"
echo "  2. Wait for training to complete (~1-3.5 hours)"
echo "  3. Download trained models when done"
echo "  4. Test interaction with trained personas"
echo ""
echo -e "${YELLOW}⚠️  Don't forget to terminate the instance when done to avoid charges!${NC}"
echo ""
