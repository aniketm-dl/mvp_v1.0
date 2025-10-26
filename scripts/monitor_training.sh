#!/bin/bash
###############################################################################
# Monitor Training Progress and Download Models
#
# This script monitors the training progress on AWS and downloads
# the trained models when complete.
#
# Usage:
#   ./scripts/monitor_training.sh
###############################################################################

set -e

# Configuration
INSTANCE_IP="3.108.237.6"
KEY_FILE="~/darpan-training-new.pem"
S3_BUCKET="darpan-training-aniketniranjanmishra"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================================================="
echo "📊 MONITORING TRAINING PROGRESS"
echo "=========================================================================="
echo ""

# Function to check training status
check_training_status() {
    echo "🔍 Checking training status..."
    
    # Get training progress
    PROGRESS=$(ssh -i "$KEY_FILE" ubuntu@$INSTANCE_IP "cd ~/mvp_v1.0 && ls -la artifacts/llm_adapters/ | wc -l")
    PROGRESS=$((PROGRESS - 2))  # Subtract 2 for . and ..
    
    # Get GPU status
    GPU_STATUS=$(ssh -i "$KEY_FILE" ubuntu@$INSTANCE_IP "nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits")
    
    echo "   • Personas trained: $PROGRESS/18"
    echo "   • GPU status: $GPU_STATUS"
    
    # Check if training is complete
    if [ "$PROGRESS" -ge 18 ]; then
        echo -e "${GREEN}✅ Training complete!${NC}"
        return 0
    else
        echo -e "${YELLOW}⏳ Training in progress...${NC}"
        return 1
    fi
}

# Function to download models
download_models() {
    echo ""
    echo "=========================================================================="
    echo "📥 DOWNLOADING TRAINED MODELS"
    echo "=========================================================================="
    
    # Create S3 bucket if it doesn't exist
    echo "Creating S3 bucket..."
    aws s3 mb "s3://$S3_BUCKET" 2>/dev/null || echo "Bucket already exists"
    
    # Sync models from instance to S3
    echo "Syncing models to S3..."
    ssh -i "$KEY_FILE" ubuntu@$INSTANCE_IP "cd ~/mvp_v1.0 && aws s3 sync artifacts/llm_adapters/ s3://$S3_BUCKET/trained_adapters/"
    
    # Download to local machine
    echo "Downloading models locally..."
    aws s3 sync "s3://$S3_BUCKET/trained_adapters/" artifacts/llm_adapters/
    
    echo -e "${GREEN}✅ Models downloaded successfully!${NC}"
    echo "   • Local path: artifacts/llm_adapters/"
    echo "   • S3 path: s3://$S3_BUCKET/trained_adapters/"
}

# Function to show training logs
show_logs() {
    echo ""
    echo "=========================================================================="
    echo "📋 RECENT TRAINING LOGS"
    echo "=========================================================================="
    
    ssh -i "$KEY_FILE" ubuntu@$INSTANCE_IP "cd ~/mvp_v1.0 && tmux capture-pane -t training -p | tail -10"
}

# Main monitoring loop
echo "Starting monitoring loop..."
echo "Press Ctrl+C to stop monitoring"
echo ""

while true; do
    clear
    echo "=========================================================================="
    echo "📊 TRAINING MONITOR - $(date)"
    echo "=========================================================================="
    
    if check_training_status; then
        echo ""
        echo "🎉 Training is complete!"
        download_models
        break
    fi
    
    show_logs
    
    echo ""
    echo "Next check in 30 seconds..."
    sleep 30
done

echo ""
echo "=========================================================================="
echo "✨ MONITORING COMPLETE"
echo "=========================================================================="
echo ""
echo "Next steps:"
echo "  1. Test interaction with trained personas"
echo "  2. Terminate AWS instance to avoid charges"
echo ""
echo "To test personas:"
echo "  python interact_cli.py"
echo ""
echo "To terminate instance:"
echo "  aws ec2 terminate-instances --instance-ids <instance-id> --region ap-south-1"
echo ""
