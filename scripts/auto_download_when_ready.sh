#!/bin/bash
###############################################################################
# Auto-Download Models When Training is Complete
#
# This script monitors training progress and automatically downloads
# and organizes models when training is complete.
#
# Usage:
#   ./scripts/auto_download_when_ready.sh
#   ./scripts/auto_download_when_ready.sh --check-interval 60
###############################################################################

set -e

# Configuration
INSTANCE_IP="3.108.237.6"
KEY_FILE="~/darpan-training-new.pem"
CHECK_INTERVAL=30  # seconds
MAX_WAIT_HOURS=3   # maximum time to wait

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --check-interval)
            CHECK_INTERVAL="$2"
            shift 2
            ;;
        --max-wait-hours)
            MAX_WAIT_HOURS="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--check-interval SECONDS] [--max-wait-hours HOURS]"
            echo "  --check-interval SECONDS    How often to check (default: 30)"
            echo "  --max-wait-hours HOURS      Max time to wait (default: 3)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "=========================================================================="
echo "🤖 AUTO-DOWNLOAD MONITOR"
echo "=========================================================================="
echo ""
echo "📋 Configuration:"
echo "   • Check interval: $CHECK_INTERVAL seconds"
echo "   • Max wait time: $MAX_WAIT_HOURS hours"
echo "   • Instance: $INSTANCE_IP"
echo ""

START_TIME=$(date +%s)
MAX_WAIT_SECONDS=$((MAX_WAIT_HOURS * 3600))

# Function to check training progress
check_progress() {
    PROGRESS=$(ssh -i "$KEY_FILE" ubuntu@$INSTANCE_IP "cd ~/mvp_v1.0 && ls -la artifacts/llm_adapters/ | wc -l" 2>/dev/null || echo "0")
    PROGRESS=$((PROGRESS - 2))  # Subtract 2 for . and ..
    echo $PROGRESS
}

# Function to get GPU status
get_gpu_status() {
    ssh -i "$KEY_FILE" ubuntu@$INSTANCE_IP "nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits" 2>/dev/null || echo "0,0,0"
}

# Function to get recent logs
get_recent_logs() {
    ssh -i "$KEY_FILE" ubuntu@$INSTANCE_IP "cd ~/mvp_v1.0 && tmux capture-pane -t training -p | tail -3" 2>/dev/null || echo "No logs available"
}

echo "🔍 Starting monitoring loop..."
echo "Press Ctrl+C to stop monitoring"
echo ""

while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    
    # Check if we've exceeded max wait time
    if [ $ELAPSED -gt $MAX_WAIT_SECONDS ]; then
        echo -e "${YELLOW}⏰ Maximum wait time exceeded ($MAX_WAIT_HOURS hours)${NC}"
        echo "Stopping monitoring. You can check manually later."
        break
    fi
    
    # Clear screen and show status
    clear
    echo "=========================================================================="
    echo "🤖 AUTO-DOWNLOAD MONITOR - $(date)"
    echo "=========================================================================="
    
    # Check training progress
    PROGRESS=$(check_progress)
    GPU_STATUS=$(get_gpu_status)
    
    echo "📊 Training Status:"
    echo "   • Progress: $PROGRESS/18 personas"
    echo "   • Completion: $((PROGRESS * 100 / 18))%"
    echo "   • GPU Status: $GPU_STATUS"
    echo "   • Elapsed time: $((ELAPSED / 60)) minutes"
    echo ""
    
    # Check if training is complete
    if [ "$PROGRESS" -ge 18 ]; then
        echo -e "${GREEN}🎉 Training is COMPLETE!${NC}"
        echo ""
        echo "📥 Starting automatic download and organization..."
        
        # Run the download script
        if ./scripts/download_and_organize_models.sh --version "auto_$(date +%Y%m%d_%H%M%S)"; then
            echo ""
            echo -e "${GREEN}✅ Models downloaded and organized successfully!${NC}"
            echo ""
            echo "🚀 Ready to interact with your digital twins!"
            echo "   ./trained_models/latest/start_interaction.sh"
            echo ""
            echo "📋 Or manually:"
            echo "   cp trained_models/latest/configs/interaction_config.yaml CONFIGS/serve/llm.yaml"
            echo "   python interact_cli.py"
        else
            echo -e "${RED}❌ Download failed. Please check manually.${NC}"
        fi
        
        break
    else
        # Show recent activity
        echo "📋 Recent Activity:"
        get_recent_logs | sed 's/^/   /'
        echo ""
        
        # Estimate remaining time
        if [ "$PROGRESS" -gt 0 ]; then
            TIME_PER_PERSONA=$((ELAPSED / PROGRESS))
            REMAINING_PERSONAS=$((18 - PROGRESS))
            ESTIMATED_REMAINING=$((REMAINING_PERSONAS * TIME_PER_PERSONA))
            echo "⏱️  Estimated time remaining: $((ESTIMATED_REMAINING / 60)) minutes"
        else
            echo "⏱️  Training starting..."
        fi
        
        echo ""
        echo "Next check in $CHECK_INTERVAL seconds..."
        echo "Press Ctrl+C to stop monitoring"
        
        sleep $CHECK_INTERVAL
    fi
done

echo ""
echo "=========================================================================="
echo "👋 Monitoring complete!"
echo "=========================================================================="
