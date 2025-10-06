from __future__ import annotations
import json, argparse, yaml, subprocess, sys
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fields_cfg", default="CONFIGS/opera/fields.yaml")
    ap.add_argument("--training_cfg", default="CONFIGS/opera/training.yaml")
    args = ap.parse_args()

    # Just delegate to the existing converter which reads fields.yaml.
    # Personas are routed by assignment rules in fields.yaml.
    subprocess.check_call([sys.executable, "scripts/opera/prepare_sft_from_opera.py", "--cfg", args.fields_cfg])
    print("SFT generation step completed (per fields.yaml routing).")

if __name__ == "__main__":
    main()
