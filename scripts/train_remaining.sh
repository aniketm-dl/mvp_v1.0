#!/bin/bash
source .venv/bin/activate
for twin in convenience_seeker eco_conscious trendsetter budget_optimizer social_validator gift_buyer bulk_buyer comparison_shopper mobile_shopper subscription_enthusiast brand_switcher experiential_buyer minimalist local_supporter; do
  echo "Training $twin..."
  python scripts/train_llm_persona_sft.py --twin_id $twin --base_model gpt2 --epochs 1
  echo "✅ Completed $twin"
done
echo "🎉 All remaining twins trained!"
