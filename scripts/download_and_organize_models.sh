#!/bin/bash
###############################################################################
# Download and Organize Trained Models with Versioning
#
# This script downloads trained models from AWS and organizes them in a
# versioned folder system for easy tracking and interaction.
#
# Usage:
#   ./scripts/download_and_organize_models.sh
#   ./scripts/download_and_organize_models.sh --version v1.0
#   ./scripts/download_and_organize_models.sh --force-download
###############################################################################

set -e

# Configuration
INSTANCE_IP="3.108.237.6"
KEY_FILE="~/darpan-training-new.pem"
S3_BUCKET="darpan-training-aniketniranjanmishra"
LOCAL_BASE_DIR="trained_models"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
VERSION=""
FORCE_DOWNLOAD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --version)
            VERSION="$2"
            shift 2
            ;;
        --force-download)
            FORCE_DOWNLOAD=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--version VERSION] [--force-download]"
            echo "  --version VERSION    Set version tag (default: auto-generated)"
            echo "  --force-download     Force download even if models exist locally"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "=========================================================================="
echo "📥 DOWNLOAD AND ORGANIZE TRAINED MODELS"
echo "=========================================================================="
echo ""

# Generate version if not provided
if [ -z "$VERSION" ]; then
    VERSION="v$(date +%Y%m%d_%H%M%S)"
fi

echo "📋 Configuration:"
echo "   • Version: $VERSION"
echo "   • Instance: $INSTANCE_IP"
echo "   • S3 Bucket: $S3_BUCKET"
echo "   • Local Directory: $LOCAL_BASE_DIR/$VERSION"
echo ""

# Create versioned directory structure
VERSION_DIR="$LOCAL_BASE_DIR/$VERSION"
ADAPTERS_DIR="$VERSION_DIR/adapters"
METADATA_DIR="$VERSION_DIR/metadata"
CONFIGS_DIR="$VERSION_DIR/configs"

echo "📁 Creating directory structure..."
mkdir -p "$ADAPTERS_DIR"
mkdir -p "$METADATA_DIR"
mkdir -p "$CONFIGS_DIR"

# Check if models exist locally and training is complete
echo "🔍 Checking training status..."
PROGRESS=$(ssh -i "$KEY_FILE" ubuntu@$INSTANCE_IP "cd ~/mvp_v1.0 && ls -la artifacts/llm_adapters/ | wc -l")
PROGRESS=$((PROGRESS - 2))  # Subtract 2 for . and ..

echo "   • Training progress: $PROGRESS/18 personas"

if [ "$PROGRESS" -lt 18 ] && [ "$FORCE_DOWNLOAD" = false ]; then
    echo -e "${YELLOW}⚠️  Training not complete yet ($PROGRESS/18 personas)${NC}"
    echo "   Use --force-download to download partial results"
    exit 1
fi

# Create S3 bucket if it doesn't exist
echo ""
echo "☁️  Setting up S3 bucket..."
aws s3 mb "s3://$S3_BUCKET" 2>/dev/null || echo "   Bucket already exists"

# Download models from instance to S3
echo ""
echo "📤 Syncing models from instance to S3..."
ssh -i "$KEY_FILE" ubuntu@$INSTANCE_IP "cd ~/mvp_v1.0 && aws s3 sync artifacts/llm_adapters/ s3://$S3_BUCKET/trained_adapters/"

# Download models from S3 to local versioned directory
echo ""
echo "📥 Downloading models to local versioned directory..."
aws s3 sync "s3://$S3_BUCKET/trained_adapters/" "$ADAPTERS_DIR/"

# Download additional metadata and configs
echo ""
echo "📋 Downloading metadata and configurations..."

# Copy personas configuration
cp "DATA/personas.json" "$METADATA_DIR/"

# Copy training configuration
cp "CONFIGS/aws/training_config.yaml" "$CONFIGS_DIR/"

# Copy SFT data info
echo "📊 SFT Data Information:" > "$METADATA_DIR/sft_data_info.txt"
echo "Generated: $(date)" >> "$METADATA_DIR/sft_data_info.txt"
echo "Total examples: $(find DATA/sft -name "*.jsonl" -exec wc -l {} + | tail -1 | awk '{print $1}')" >> "$METADATA_DIR/sft_data_info.txt"
echo "Personas: $(ls DATA/sft/*.jsonl | wc -l)" >> "$METADATA_DIR/sft_data_info.txt"

# Create model inventory
echo ""
echo "📝 Creating model inventory..."
cat > "$METADATA_DIR/model_inventory.json" << EOF
{
  "version": "$VERSION",
  "download_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "training_completion": "$PROGRESS/18",
  "base_model": "mistralai/Mistral-7B-Instruct-v0.2",
  "versioning_strategy": "Development sprint versioning - preserve all versions",
  "purpose": "Organized model storage for iterative development and improvement",
  "training_config": {
    "epochs": 1,
    "lora_rank": 8,
    "lora_alpha": 16,
    "learning_rate": 2e-4
  },
  "personas": [
EOF

# List all trained personas
PERSONA_COUNT=0
for persona_dir in "$ADAPTERS_DIR"/*; do
    if [ -d "$persona_dir" ] && [ -f "$persona_dir/adapter_model.safetensors" ]; then
        PERSONA_NAME=$(basename "$persona_dir")
        if [ "$PERSONA_COUNT" -gt 0 ]; then
            echo "," >> "$METADATA_DIR/model_inventory.json"
        fi
        echo "    \"$PERSONA_NAME\"" >> "$METADATA_DIR/model_inventory.json"
        PERSONA_COUNT=$((PERSONA_COUNT + 1))
    fi
done

cat >> "$METADATA_DIR/model_inventory.json" << EOF
  ],
  "total_personas": $PERSONA_COUNT,
  "adapter_sizes": {
EOF

# Get adapter sizes
FIRST_SIZE=true
for persona_dir in "$ADAPTERS_DIR"/*; do
    if [ -d "$persona_dir" ] && [ -f "$persona_dir/adapter_model.safetensors" ]; then
        PERSONA_NAME=$(basename "$persona_dir")
        SIZE_MB=$(du -sm "$persona_dir" | cut -f1)
        
        if [ "$FIRST_SIZE" = true ]; then
            FIRST_SIZE=false
        else
            echo "," >> "$METADATA_DIR/model_inventory.json"
        fi
        echo "    \"$PERSONA_NAME\": ${SIZE_MB}" >> "$METADATA_DIR/model_inventory.json"
    fi
done

cat >> "$METADATA_DIR/model_inventory.json" << EOF
  }
}
EOF

# Create interaction configuration
echo ""
echo "⚙️  Creating interaction configuration..."
cat > "$CONFIGS_DIR/interaction_config.yaml" << EOF
# Interaction Configuration for Version $VERSION
# Generated: $(date)

llm:
  use_stub: false  # Use real trained models
  base_model: "mistralai/Mistral-7B-Instruct-v0.2"
  adapter_dir: "$(pwd)/$ADAPTERS_DIR"
  temperature: 0.7
  top_p: 0.9
  max_new_tokens: 200
  seed: 42

personas:
  config_file: "$(pwd)/$METADATA_DIR/personas.json"
  total_count: $PERSONA_COUNT
  version: "$VERSION"

interaction:
  welcome_message: "Welcome to Darpan Labs Digital Twin Simulator v$VERSION"
  max_history: 10
  auto_save_chats: true
EOF

# Create symlink to latest version
echo ""
echo "🔗 Creating symlink to latest version..."
rm -f "$LOCAL_BASE_DIR/latest"
ln -sf "$VERSION" "$LOCAL_BASE_DIR/latest"

# Create quick start script
echo ""
echo "📝 Creating quick start script..."
cat > "$VERSION_DIR/start_interaction.sh" << 'EOF'
#!/bin/bash
# Quick start script for interacting with trained personas

echo "🎭 Starting Darpan Labs Digital Twin Interaction"
echo "Version: $(basename $(dirname $0))"
echo ""

# Check if we're in the right directory
if [ ! -f "interact_cli.py" ]; then
    echo "❌ Please run this script from the project root directory"
    echo "   cd /path/to/mvp_v1.0"
    echo "   ./trained_models/latest/start_interaction.sh"
    exit 1
fi

# Update config to use this version
echo "⚙️  Updating configuration..."
cp "$(dirname $0)/configs/interaction_config.yaml" CONFIGS/serve/llm.yaml

# Start interaction
echo "🚀 Starting interaction..."
python interact_cli.py
EOF

chmod +x "$VERSION_DIR/start_interaction.sh"

# Create README for this version
echo ""
echo "📖 Creating version documentation..."
cat > "$VERSION_DIR/README.md" << EOF
# Trained Models Version $VERSION

## Overview
This directory contains the trained persona models downloaded on $(date).

## Versioning Strategy
This version is part of our development sprint versioning system. Each version represents a complete training run and is preserved to:
- Track improvements across development sprints
- Maintain stable versions while experimenting with new approaches
- Enable performance comparison between different training iterations
- Never lose working models during development

**Important**: This version should never be modified. Create new versions for improvements.

## Contents
- \`adapters/\` - Trained LoRA adapters for each persona
- \`metadata/\` - Training metadata and model inventory
- \`configs/\` - Configuration files for interaction
- \`start_interaction.sh\` - Quick start script

## Training Details
- **Completion**: $PROGRESS/18 personas
- **Base Model**: mistralai/Mistral-7B-Instruct-v0.2
- **Training Method**: LoRA fine-tuning
- **Total Personas**: $PERSONA_COUNT

## Quick Start
\`\`\`bash
# From project root
./trained_models/$VERSION/start_interaction.sh
\`\`\`

## Manual Setup
\`\`\`bash
# Copy interaction config
cp trained_models/$VERSION/configs/interaction_config.yaml CONFIGS/serve/llm.yaml

# Start interaction
python interact_cli.py
\`\`\`

## Model Inventory
See \`metadata/model_inventory.json\` for detailed information about each trained persona.

## File Sizes
$(du -sh adapters/* | sort -hr | head -10)
EOF

# Summary
echo ""
echo "=========================================================================="
echo "✅ DOWNLOAD AND ORGANIZATION COMPLETE!"
echo "=========================================================================="
echo ""
echo -e "${GREEN}📁 Models organized in: $VERSION_DIR${NC}"
echo -e "${GREEN}🔗 Latest symlink: $LOCAL_BASE_DIR/latest${NC}"
echo ""
echo "📊 Summary:"
echo "   • Personas trained: $PERSONA_COUNT/18"
echo "   • Total size: $(du -sh "$VERSION_DIR" | cut -f1)"
echo "   • Adapters: $ADAPTERS_DIR"
echo "   • Metadata: $METADATA_DIR"
echo "   • Configs: $CONFIGS_DIR"
echo ""
echo "🚀 Quick Start:"
echo "   ./trained_models/$VERSION/start_interaction.sh"
echo ""
echo "📋 Available versions:"
ls -la "$LOCAL_BASE_DIR" | grep "^d" | awk '{print "   • " $9}'
echo ""
echo -e "${BLUE}💡 Tip: Use the start_interaction.sh script for easy setup!${NC}"
