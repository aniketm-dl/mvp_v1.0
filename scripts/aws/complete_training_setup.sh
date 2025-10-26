#!/bin/bash
###############################################################################
# Complete Training Setup Script for EC2
#
# This script sets up and runs the complete training pipeline on EC2.
# Run this ON THE EC2 INSTANCE after SSHing in.
#
# Usage (on EC2):
#   bash complete_training_setup.sh
###############################################################################

set -e

echo "========================================================================"
echo "🚀 Complete Persona Training Setup"
echo "========================================================================"
echo ""

# Update system
echo "Step 1: Updating system..."
sudo apt-get update -qq

# Install Python and dependencies
echo "Step 2: Installing Python dependencies..."
sudo apt-get install -y python3-pip python3-venv git

# Create working directory
WORK_DIR="$HOME/persona_training"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

echo "Step 3: Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Install required packages
echo "Step 4: Installing PyTorch and transformers..."
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers==4.36.2
pip install peft==0.7.1
pip install datasets==2.16.1
pip install accelerate==0.25.0
pip install bitsandbytes==0.41.3
pip install sentencepiece==0.1.99
pip install protobuf==3.20.3
pip install tqdm rich

# Download training data and personas
echo "Step 5: Downloading training data from S3..."
mkdir -p DATA/sft
aws s3 sync s3://darpan-training-1760183626/darpan_training_data/sft/ DATA/sft/ --quiet
aws s3 cp s3://darpan-training-1760183626/darpan_training_data/personas.json DATA/personas.json

echo "Step 6: Creating training script..."
cat > train_all_personas.py << 'PYTHON_SCRIPT'
#!/usr/bin/env python3
"""
Train all 18 personas with LoRA fine-tuning
"""
import os
import json
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_dataset
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BASE_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
OUTPUT_DIR = "trained_models"
DATA_DIR = "DATA/sft"

# LoRA Configuration
lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM
)

# Training Arguments
training_args = TrainingArguments(
    output_dir="./temp_output",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
    save_steps=100,
    save_total_limit=2,
    warmup_steps=100,
    optim="paged_adamw_8bit",
)

def train_persona(persona_id: str, data_file: str):
    """Train a single persona"""
    logger.info(f"\n{'='*80}")
    logger.info(f"Training persona: {persona_id}")
    logger.info(f"{'='*80}\n")
    
    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.float16,
        device_map="auto",
        load_in_8bit=True
    )
    
    # Apply LoRA
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    # Load dataset
    dataset = load_dataset('json', data_files=data_file, split='train')
    
    # Tokenize
    def tokenize_function(examples):
        return tokenizer(
            examples['text'],
            truncation=True,
            max_length=512,
            padding='max_length'
        )
    
    tokenized_dataset = dataset.map(tokenize_function, batched=True, remove_columns=dataset.column_names)
    
    # Data collator
    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    
    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=data_collator,
    )
    
    # Train
    trainer.train()
    
    # Save
    output_path = Path(OUTPUT_DIR) / persona_id
    output_path.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_path)
    tokenizer.save_pretrained(output_path)
    
    logger.info(f"✓ Saved model to {output_path}")
    
    # Clear memory
    del model
    del trainer
    torch.cuda.empty_cache()

def main():
    # Load personas
    with open('DATA/personas.json', 'r') as f:
        personas_data = json.load(f)
    personas = personas_data['personas']
    
    logger.info(f"Found {len(personas)} personas to train")
    
    # Train each persona
    for i, persona in enumerate(personas, 1):
        persona_id = persona['id']
        data_file = f"{DATA_DIR}/{persona_id}.jsonl"
        
        if not Path(data_file).exists():
            logger.warning(f"Skipping {persona_id} - no data file")
            continue
        
        logger.info(f"\n[{i}/{len(personas)}] Starting {persona_id}...")
        
        try:
            train_persona(persona_id, data_file)
            logger.info(f"✓ Completed {persona_id}")
        except Exception as e:
            logger.error(f"✗ Failed {persona_id}: {e}")
            continue
    
    logger.info("\n" + "="*80)
    logger.info("🎉 All personas trained!")
    logger.info(f"Models saved in: {OUTPUT_DIR}")
    logger.info("="*80)

if __name__ == '__main__':
    main()
PYTHON_SCRIPT

chmod +x train_all_personas.py

echo "Step 7: Starting training..."
python3 train_all_personas.py 2>&1 | tee training.log

echo "Step 8: Creating download package..."
tar -czf trained_models_$(date +%Y%m%d_%H%M%S).tar.gz trained_models/

echo ""
echo "========================================================================"
echo "✓ Training Complete!"
echo "========================================================================"
echo ""
echo "Trained models location: $WORK_DIR/trained_models/"
echo "Archive: trained_models_*.tar.gz"
echo ""
echo "To download:"
echo "  scp -i ~/your-key.pem ubuntu@INSTANCE_IP:$WORK_DIR/trained_models_*.tar.gz ."
echo ""
echo "⚠️  DO NOT TERMINATE THIS INSTANCE YET!"
echo "    First download the models, then manually terminate from AWS console"
echo "========================================================================"

