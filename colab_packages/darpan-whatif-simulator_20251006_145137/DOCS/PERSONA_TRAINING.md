# Persona training from OPeRA (end-to-end)

Goal: produce LoRA adapters for all target personas, switch runtime to real LLM, reload adapters, and verify chats.

## 0) Prepare OPeRA data
- Put file at DATA/opera/opera_events.parquet (or .csv).
- Edit CONFIGS/opera/fields.yaml to match columns and routing rules.

## 1) Choose target set
- Option A (default): use existing DATA/personas.json
- Option B: discover personas from OPeRA clusters by psychographic tags:
  python scripts/opera/discover_personas_from_opera.py --augment --min_rows 200 --max_personas 24

## 2) Generate SFT per persona
make opera-sft   # runs converter using fields.yaml

## 3) Train all adapters
make train-all   # trains each persona using CONFIGS/train/llm_persona.yaml

## 4) Flip runtime and reload
- CONFIGS/opera/training.yaml controls: set_use_stub_false and reload_all_adapters
- Run:
  python scripts/pipeline/train_and_load_all_twins.py

## 5) Verify
- GET /admin/adapters (header X-Admin-Token) shows available/loaded status.
- Chat with a few twins:
  python scripts/lab.py chat --twin <id> --prompt "What do you value?"
