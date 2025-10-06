from __future__ import annotations
from pathlib import Path
import argparse, yaml
from transformers import AutoTokenizer, AutoModelForCausalLM, set_seed
from peft import PeftModel

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--twin_id", required=True)
    ap.add_argument("--cfg", default="CONFIGS/train/llm_persona.yaml")
    args = ap.parse_args()
    cfg = yaml.safe_load(Path(args.cfg).read_text())["train"]
    base = cfg["base_model"]
    set_seed(int(cfg["seed"]))
    twin_dir = Path(cfg["adapter_dir"]) / args.twin_id

    tok = AutoTokenizer.from_pretrained(base)
    base_m = AutoModelForCausalLM.from_pretrained(base)
    m = PeftModel.from_pretrained(base_m, twin_dir)
    m.eval()

    prompt = "User: What do you value when shopping for sunscreen?\nAssistant:"
    x = tok(prompt, return_tensors="pt")
    out = m.generate(**x, do_sample=False, temperature=0.0, top_p=1.0, max_new_tokens=48)
    print(tok.decode(out[0], skip_special_tokens=True))

if __name__ == "__main__":
    main()
