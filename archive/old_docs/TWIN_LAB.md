# Twin Lab (inspect, train, run, interact)

## Inspect
- GET /twin/bank — list twins, adapter availability.
- GET /twin/{id}/inspect — persona details + llm config.
- CLI: python scripts/lab.py bank | inspect --twin k3

## Interact
- Chat: POST /twin/chat  (stub reply until adapters exist)
- Decide: POST /twin/decide (reasons via runtime; ranking still via heads)
- CLI: python scripts/lab.py chat --twin k3 --prompt "What do you value?"

## Train SFT per twin
1) Create SFT JSONL per twin under DATA/sft/<twin>.jsonl (see DOCS/SFT_DATA.md)
   Or generate synthetic:
   python scripts/prepare_llm_sft_data.py
2) Train LoRA adapter:
   python scripts/train_llm_persona_sft.py --twin_id k3
   Output: artifacts/llm_adapters/k3/*
3) Reload adapter in API:
   curl -H "X-Admin-Token: changeme" -X POST http://127.0.0.1:8000/admin/twin/k3/reload
4) Flip runtime to real model:
   CONFIGS/serve/llm.yaml -> llm.use_stub: false
   Restart API.

## Evaluate
python scripts/eval_llm_persona_sft.py --twin_id k3

## Determinism
- Generation uses temperature 0 and top_p 1.
- Seed fixed in llm.yaml and training config.
