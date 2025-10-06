from __future__ import annotations
from pathlib import Path
import argparse, json, torch
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments, DataCollatorForLanguageModeling
from transformers.pytorch_utils import Conv1D
from peft import LoraConfig, get_peft_model, TaskType

def ensure_text(ex):
    if ex.get("text"): return ex
    # Combine input and output for SFT format
    inp = ex.get("input", "")
    out = ex.get("output", "")
    if inp and out:
        ex["text"] = inp + out
    else:
        parts=[ex.get(k,"") for k in ("input","output","prompt","rationale")]
        ex["text"]=" ".join(p for p in parts if isinstance(p,str) and p.strip())
    return ex

def find_targets(model):
    # GPT-2 style layers
    gpt2_want=("c_attn","c_fc","c_proj")
    # Llama/Mistral style layers
    llama_want=("q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj")

    allow=(torch.nn.Linear, Conv1D, torch.nn.Conv1d)
    names=set()

    # Try to find any matching layers
    for n,m in model.named_modules():
        if isinstance(m,allow):
            layer_name = n.split(".")[-1]
            if layer_name in gpt2_want or layer_name in llama_want:
                names.add(layer_name)

    # Return found layers or sensible defaults
    if names:
        return sorted(names)

    # Default to GPT-2 or Llama based on model type
    model_name = model.config.model_type if hasattr(model, 'config') else ""
    if "llama" in model_name.lower() or "mistral" in model_name.lower():
        return ["q_proj", "v_proj"]  # Minimal but effective
    return ["c_attn","c_fc","c_proj"]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--twin_id",required=True)
    ap.add_argument("--data",default=None)
    ap.add_argument("--base_model",default="gpt2")
    ap.add_argument("--max_length",type=int,default=512)
    ap.add_argument("--epochs",type=int,default=1)
    ap.add_argument("--lr",type=float,default=2e-4)
    a=ap.parse_args()

    data=a.data or f"DATA/sft/{a.twin_id}.jsonl"
    if not Path(data).exists(): print("[skip] no SFT",data); return

    ds=load_dataset("json",data_files=data,split="train")
    if "text" not in ds.column_names: ds=ds.map(ensure_text)

    tok=AutoTokenizer.from_pretrained(a.base_model, use_fast=True)
    tok.pad_token = tok.pad_token or tok.eos_token

    def tokf(b):
        enc = tok(b["text"], truncation=True, max_length=a.max_length, padding="max_length")
        enc["labels"] = enc["input_ids"]
        return enc

    ds_tok = ds.map(tokf, batched=True, remove_columns=ds.column_names)

    model = AutoModelForCausalLM.from_pretrained(a.base_model)
    model.resize_token_embeddings(len(tok))
    targets = find_targets(model)
    lora=LoraConfig(task_type=TaskType.CAUSAL_LM, r=8, lora_alpha=16, lora_dropout=0.05,
                    target_modules=targets, bias="none")
    model = get_peft_model(model, lora)

    out = Path(f"artifacts/llm_adapters/{a.twin_id}")
    out.mkdir(parents=True, exist_ok=True)

    args = TrainingArguments(output_dir=str(out), learning_rate=a.lr, num_train_epochs=a.epochs,
                             per_device_train_batch_size=2, logging_steps=50, save_strategy="no", report_to=[])
    collator = DataCollatorForLanguageModeling(tokenizer=tok, mlm=False)

    Trainer(model=model, args=args, train_dataset=ds_tok, data_collator=collator).train()
    model.save_pretrained(out)      # this writes a proper adapter_config.json (with peft_type)
    tok.save_pretrained(out)
    print("Saved adapter for", a.twin_id, "->", out)
if __name__=="__main__": main()
