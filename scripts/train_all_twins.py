from pathlib import Path
import subprocess, glob

def main():
    sft_files = sorted(glob.glob("DATA/sft/*.jsonl"))
    if not sft_files:
        raise SystemExit("No SFT files found in DATA/sft/")
    twins = [Path(p).stem for p in sft_files]
    print("Twins to train:", twins)

    base_model = "gpt2"  # change if needed

    for tid in twins:
        print(f"[train] {tid}")
        cmd = ["python","scripts/train_llm_persona_sft.py",
               "--twin_id", tid,
               "--base_model", base_model,
               "--epochs","1"]
        subprocess.check_call(cmd)

if __name__ == "__main__":
    main()
