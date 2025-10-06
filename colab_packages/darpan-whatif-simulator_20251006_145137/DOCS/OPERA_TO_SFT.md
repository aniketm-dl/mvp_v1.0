# OPeRA → SFT data

1) Put your OPeRA export at DATA/opera/opera_events.parquet (or .csv).
2) Adjust CONFIGS/opera/fields.yaml to match column names and routing rules.
3) Run:
   python scripts/opera/prepare_sft_from_opera.py --cfg CONFIGS/opera/fields.yaml
4) Outputs per-twin JSONL at DATA/sft/<twin>.jsonl ready for LoRA SFT.
