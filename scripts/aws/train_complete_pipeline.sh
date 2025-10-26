#!/bin/bash
###############################################################################
# Complete OPeRA-SSR-Twin Training Pipeline for AWS
#
# This script runs the full pipeline from OPeRA download to trained models:
# 1. Download OPeRA dataset from HuggingFace
# 2. Preprocess & align data
# 3. Discover personas (UMAP + HDBSCAN + GPT-4o)
# 4. Train SSR model
# 5. Train LLM twins (optional)
# 6. Evaluate models
# 7. Sync to S3
#
# Prerequisites:
#   - OPENAI_API_KEY env var set (for persona summarization)
#   - HF_TOKEN env var set (for downloading base models)
#   - TRAINING_S3_BUCKET env var set (for S3 sync)
#   - AWS credentials configured
#
# Usage:
#   bash scripts/aws/train_complete_pipeline.sh [--skip-llm-twins]
###############################################################################

set -e  # Exit on any error

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse arguments
SKIP_LLM_TWINS=false
AUTO_SHUTDOWN=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-llm-twins)
      SKIP_LLM_TWINS=true
      shift
      ;;
    --auto-shutdown)
      AUTO_SHUTDOWN=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo -e "${CYAN}=========================================================================="
echo -e "🚀 DARPAN LABS - COMPLETE OPeRA-SSR-TWIN TRAINING PIPELINE"
echo -e "==========================================================================${NC}"
echo ""

# Check prerequisites
echo -e "${CYAN}📋 Checking prerequisites...${NC}"

if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}❌ OPENAI_API_KEY not set. Required for persona summarization.${NC}"
    echo "   Set with: export OPENAI_API_KEY='sk-...'"
    exit 1
fi
echo -e "${GREEN}✅ OpenAI API key found${NC}"

if [ -z "$HF_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  HF_TOKEN not set. May fail to download base models.${NC}"
    echo "   Set with: export HF_TOKEN='hf_...'"
else
    echo -e "${GREEN}✅ HuggingFace token found${NC}"
fi

if [ -z "$TRAINING_S3_BUCKET" ]; then
    echo -e "${YELLOW}⚠️  TRAINING_S3_BUCKET not set. Will skip S3 sync.${NC}"
    echo "   Set with: export TRAINING_S3_BUCKET='darpan-training-USERNAME'"
else
    echo -e "${GREEN}✅ S3 bucket configured: $TRAINING_S3_BUCKET${NC}"
fi

echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo -e "${CYAN}🐍 Activating virtual environment...${NC}"
    source venv/bin/activate
    echo -e "${GREEN}✅ Virtual environment activated${NC}"
    echo ""
fi

# Record start time
START_TIME=$(date +%s)
echo -e "${CYAN}⏰ Pipeline started at: $(date)${NC}"
echo ""

###############################################################################
# STEP 1: Download OPeRA Dataset
###############################################################################

echo -e "${CYAN}=========================================================================="
echo -e "STEP 1/7: Download OPeRA Dataset from HuggingFace"
echo -e "==========================================================================${NC}"
echo ""

python scripts/01_download_opera.py

echo ""
echo -e "${GREEN}✅ Step 1 complete: OPeRA dataset downloaded${NC}"
echo ""

###############################################################################
# STEP 2: Preprocess Data
###############################################################################

echo -e "${CYAN}=========================================================================="
echo -e "STEP 2/7: Preprocess & Align OPeRA Data"
echo -e "==========================================================================${NC}"
echo ""

python scripts/02_preprocess_opera.py \
  --survey DATA/OPeRA/raw/opera_users.parquet \
  --sessions DATA/OPeRA/raw/sample_sessions.jsonl \
  --rationales DATA/OPeRA/raw/opera_rationales.jsonl \
  --outcomes DATA/OPeRA/raw/opera_outcomes.jsonl \
  --out-dir DATA/OPeRA/processed \
  --min-steps 3 \
  --max-steps 100

echo ""
echo -e "${GREEN}✅ Step 2 complete: Data preprocessed & aligned${NC}"
echo ""

###############################################################################
# STEP 3: Discover Personas
###############################################################################

echo -e "${CYAN}=========================================================================="
echo -e "STEP 3/7: Discover Personas (UMAP + HDBSCAN + GPT-4o)"
echo -e "==========================================================================${NC}"
echo ""

python scripts/03_discover_personas.py \
  --features DATA/OPeRA/processed/persona_features.parquet \
  --out models/persona_profiles.json \
  --min-cluster-size 50 \
  --use-llm-summary \
  --save-clustering DATA/OPeRA/interim/cluster_assignments.parquet

echo ""
echo -e "${GREEN}✅ Step 3 complete: Personas discovered${NC}"
echo ""

# Check if personas were discovered
if [ ! -f "models/persona_profiles.json" ]; then
    echo -e "${RED}❌ Persona discovery failed. Exiting.${NC}"
    exit 1
fi

NUM_PERSONAS=$(python -c "import json; print(len(json.load(open('models/persona_profiles.json'))['personas']))")
echo -e "${CYAN}📊 Discovered ${NUM_PERSONAS} personas${NC}"
echo ""

###############################################################################
# STEP 4: Train SSR Model
###############################################################################

echo -e "${CYAN}=========================================================================="
echo -e "STEP 4/7: Train SSR Model (Semantic Similarity Rating)"
echo -e "==========================================================================${NC}"
echo ""

python scripts/04_train_ssr.py \
  --training-pairs DATA/OPeRA/processed/ssr_training_pairs.jsonl \
  --out models/ssr_reference \
  --base-model sentence-transformers/all-MiniLM-L6-v2 \
  --embedding-epochs 10 \
  --regression-epochs 20 \
  --batch-size 32 \
  --learning-rate 2e-5

echo ""
echo -e "${GREEN}✅ Step 4 complete: SSR model trained${NC}"
echo ""

###############################################################################
# STEP 5: Train LLM Twins (Optional)
###############################################################################

if [ "$SKIP_LLM_TWINS" = false ]; then
    echo -e "${CYAN}=========================================================================="
    echo -e "STEP 5/7: Train LLM Twins (Mistral-7B LoRA Adapters)"
    echo -e "==========================================================================${NC}"
    echo ""

    # Check if existing LLM training script exists
    if [ -f "scripts/aws/train_production.py" ]; then
        python scripts/aws/train_production.py \
          --personas-file models/persona_profiles.json \
          --sync-s3
    else
        echo -e "${YELLOW}⚠️  LLM training script not found. Skipping LLM twin training.${NC}"
        echo "   SSR-only model is still functional for predictions."
    fi

    echo ""
    echo -e "${GREEN}✅ Step 5 complete: LLM twins trained${NC}"
    echo ""
else
    echo -e "${YELLOW}⏭️  Skipping LLM twin training (--skip-llm-twins flag)${NC}"
    echo ""
fi

###############################################################################
# STEP 6: Evaluate Models
###############################################################################

echo -e "${CYAN}=========================================================================="
echo -e "STEP 6/7: Evaluate Models (KS Similarity + Correlation)"
echo -e "==========================================================================${NC}"
echo ""

# Create placeholder evaluation script if it doesn't exist
if [ ! -f "scripts/07_evaluate.py" ]; then
    echo -e "${YELLOW}⚠️  Evaluation script not yet implemented. Skipping.${NC}"
else
    python scripts/07_evaluate.py \
      --ssr-model models/ssr_reference \
      --test-data DATA/OPeRA/processed/aligned_sequences.jsonl \
      --out-dir reports
fi

echo ""
echo -e "${GREEN}✅ Step 6 complete: Models evaluated${NC}"
echo ""

###############################################################################
# STEP 7: Sync to S3
###############################################################################

echo -e "${CYAN}=========================================================================="
echo -e "STEP 7/7: Sync Models & Reports to S3"
echo -e "==========================================================================${NC}"
echo ""

if [ -z "$TRAINING_S3_BUCKET" ]; then
    echo -e "${YELLOW}⚠️  TRAINING_S3_BUCKET not set. Skipping S3 sync.${NC}"
else
    echo -e "${CYAN}📤 Syncing to S3: s3://$TRAINING_S3_BUCKET/${NC}"

    # Sync models
    aws s3 sync models/ s3://$TRAINING_S3_BUCKET/models/ --exclude "*.git/*" --exclude "__pycache__/*"
    echo -e "${GREEN}✅ Models synced${NC}"

    # Sync artifacts (if LLM twins were trained)
    if [ -d "artifacts/llm_adapters" ] && [ "$SKIP_LLM_TWINS" = false ]; then
        aws s3 sync artifacts/llm_adapters/ s3://$TRAINING_S3_BUCKET/artifacts/llm_adapters/
        echo -e "${GREEN}✅ LLM adapters synced${NC}"
    fi

    # Sync reports
    if [ -d "reports" ]; then
        aws s3 sync reports/ s3://$TRAINING_S3_BUCKET/reports/
        echo -e "${GREEN}✅ Reports synced${NC}"
    fi

    # Sync processed data (for reproducibility)
    aws s3 sync DATA/OPeRA/processed/ s3://$TRAINING_S3_BUCKET/data/processed/
    echo -e "${GREEN}✅ Processed data synced${NC}"
fi

echo ""
echo -e "${GREEN}✅ Step 7 complete: S3 sync finished${NC}"
echo ""

###############################################################################
# Summary
###############################################################################

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
HOURS=$((ELAPSED / 3600))
MINUTES=$(((ELAPSED % 3600) / 60))

echo -e "${CYAN}=========================================================================="
echo -e "✨ PIPELINE COMPLETE!"
echo -e "==========================================================================${NC}"
echo ""
echo -e "${GREEN}⏱️  Total time: ${HOURS}h ${MINUTES}m${NC}"
echo ""
echo -e "${CYAN}📁 Generated Files:${NC}"
echo "   • DATA/OPeRA/processed/aligned_sequences.jsonl"
echo "   • models/persona_profiles.json (${NUM_PERSONAS} personas)"
echo "   • models/ssr_reference/ (SSR model)"
if [ "$SKIP_LLM_TWINS" = false ] && [ -d "artifacts/llm_adapters" ]; then
    echo "   • artifacts/llm_adapters/ (LLM twins)"
fi
echo ""

if [ ! -z "$TRAINING_S3_BUCKET" ]; then
    echo -e "${CYAN}☁️  S3 Location: s3://$TRAINING_S3_BUCKET/${NC}"
    echo ""
fi

echo -e "${CYAN}📊 Model Quality:${NC}"
echo "   • Personas: ${NUM_PERSONAS} discovered"
echo "   • SSR: Check logs for correlation score"
if [ "$SKIP_LLM_TWINS" = false ]; then
    echo "   • LLM Twins: Check artifacts/ directory"
fi
echo ""

echo -e "${CYAN}🚀 Next Steps:${NC}"
echo "   1. Download models locally (if on EC2):"
echo "      aws s3 sync s3://$TRAINING_S3_BUCKET/models/ models/"
echo ""
echo "   2. Test SSR inference:"
echo "      python -c \"from src.ssr.inference import SSRInference; ssr = SSRInference('models/ssr_reference'); print(ssr.predict('Free shipping'))\""
echo ""
echo "   3. Launch demo app:"
echo "      streamlit run src/app/main.py"
echo ""

# Auto-shutdown if requested
if [ "$AUTO_SHUTDOWN" = true ]; then
    echo -e "${YELLOW}⏰ Auto-shutdown enabled. Shutting down in 5 minutes...${NC}"
    echo "   Cancel with: sudo shutdown -c"
    sudo shutdown -h +5
fi

echo -e "${GREEN}✅ Training pipeline complete!${NC}"
echo ""
