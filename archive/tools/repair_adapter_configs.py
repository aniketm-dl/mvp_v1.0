from pathlib import Path
import json, argparse

DEF = {
  "peft_type": "LORA",
  "task_type": "CAUSAL_LM",
  "r": 8,
  "lora_alpha": 16,
  "lora_dropout": 0.05,
  "bias": "none",
  "inference_mode": False,
  "target_modules": ["c_attn","c_fc","c_proj"]
}

def repair_dir(d: Path, base_model: str):
    cfg_path = d / "adapter_config.json"
    if not cfg_path.exists():
        print("missing", cfg_path)
        return
    try:
        cfg = json.loads(cfg_path.read_text())
    except Exception:
        cfg = {}
    if "peft_type" not in cfg:
        cfg = {**DEF, "base_model_name_or_path": base_model}
        cfg_path.write_text(json.dumps(cfg, indent=2))
        print("repaired", cfg_path)
    else:
        cfg.setdefault("base_model_name_or_path", base_model)
        cfg_path.write_text(json.dumps(cfg, indent=2))
        print("ok", cfg_path)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="gpt2")
    ap.add_argument("--root", default="artifacts/llm_adapters")
    a = ap.parse_args()
    root = Path(a.root)
    for d in sorted(root.glob("p*/")):
        repair_dir(d, a.base)

if __name__ == "__main__":
    main()
