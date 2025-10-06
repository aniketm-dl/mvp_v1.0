# Phase J — Train twins from OPeRA

## Prepare SFT from OPeRA
1) Place your file at DATA/opera/opera_events.parquet (or .csv).
2) Edit CONFIGS/opera/fields.yaml to match your columns and routing rules.
3) Convert:
   python scripts/opera/prepare_sft_from_opera.py --cfg CONFIGS/opera/fields.yaml

## Train
- One twin:
  python scripts/train_llm_persona_sft.py --twin_id k3
- All twins listed in DATA/personas.json:
  python scripts/train_all_twins.py

## Inspect training status
- File: DATA/train_runs.json
- API: GET /admin/train/status  (header: X-Admin-Token: changeme)

## Use the adapters
- Flip CONFIGS/serve/llm.yaml → llm.use_stub: false
- Reload adapter per twin:
  curl -H "X-Admin-Token: changeme" -X POST http://127.0.0.1:8000/admin/twin/k3/reload
- Interact via Twin Lab (/twin/chat, /twin/decide) and run /simulate with explain modes.
