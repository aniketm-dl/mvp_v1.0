#!/usr/bin/env python3
"""
Train LLM adapters for all 18 MVP personas.
Wrapper script that trains each twin sequentially.
"""

from __future__ import annotations
import json
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any

def load_personas() -> List[Dict[str, Any]]:
    """Load personas from DATA/personas.json."""
    personas_file = Path("DATA/personas.json")
    if not personas_file.exists():
        raise FileNotFoundError(f"{personas_file} not found!")

    data = json.loads(personas_file.read_text())
    return data["personas"]

def train_twin(twin_id: str, base_model: str = "gpt2", epochs: int = 1) -> bool:
    """Train a single twin adapter."""

    # Check if training data exists
    data_file = Path(f"DATA/sft/{twin_id}.jsonl")
    if not data_file.exists():
        print(f"   ⚠️  No training data found for {twin_id}")
        return False

    # Run training script
    cmd = [
        "python3",
        "scripts/train_llm_persona_sft.py",
        "--twin_id", twin_id,
        "--base_model", base_model,
        "--epochs", str(epochs),
        "--max_length", "512",
        "--lr", "2e-4"
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Training failed: {e.stderr}")
        return False

def main():
    """Train adapters for all personas."""

    print("🎯 Training LLM Adapters for All 18 Personas...\n")

    # Load personas
    personas = load_personas()
    print(f"📚 Found {len(personas)} personas to train\n")

    # Training parameters
    base_model = "mistralai/Mistral-7B-Instruct-v0.2"
    epochs = 1

    print(f"⚙️  Training Configuration:")
    print(f"   • Base model: {base_model}")
    print(f"   • Epochs: {epochs}")
    print(f"   • LoRA rank: 8")
    print(f"   • Learning rate: 2e-4")
    print(f"   • Max length: 512")
    print(f"\n⚠️  Note: Training Mistral-7B requires significant memory (16GB+ GPU recommended)\n")

    # Train each twin
    start_time = time.time()
    success_count = 0
    failed_twins = []

    for i, persona in enumerate(personas, 1):
        twin_id = persona["id"]
        label = persona["label"]

        print(f"[{i}/{len(personas)}] Training {label}...")
        print(f"   Twin ID: {twin_id}")

        twin_start = time.time()

        success = train_twin(twin_id, base_model, epochs)

        twin_time = time.time() - twin_start

        if success:
            # Check adapter was created
            adapter_file = Path(f"artifacts/llm_adapters/{twin_id}/adapter_model.safetensors")
            if adapter_file.exists():
                size_mb = adapter_file.stat().st_size / (1024 * 1024)
                print(f"   ✅ Adapter saved ({size_mb:.1f}MB) in {twin_time:.1f}s\n")
                success_count += 1
            else:
                print(f"   ⚠️  Training completed but adapter file not found\n")
                failed_twins.append(twin_id)
        else:
            print(f"   ❌ Training failed\n")
            failed_twins.append(twin_id)

    # Summary
    total_time = time.time() - start_time

    print("=" * 60)
    print(f"\n🎉 Training Complete!\n")
    print(f"📊 Results:")
    print(f"   • Total personas: {len(personas)}")
    print(f"   • Successfully trained: {success_count}")
    print(f"   • Failed: {len(failed_twins)}")
    print(f"   • Total time: {total_time/60:.1f} minutes")
    print(f"   • Avg time per twin: {total_time/len(personas):.1f}s")

    if failed_twins:
        print(f"\n⚠️  Failed twins: {', '.join(failed_twins)}")

    # Check total adapter size
    adapter_dir = Path("artifacts/llm_adapters")
    if adapter_dir.exists():
        total_size = sum(
            f.stat().st_size
            for f in adapter_dir.rglob("adapter_model.safetensors")
        ) / (1024 * 1024)
        print(f"\n💾 Total adapter storage: {total_size:.1f}MB")

    print(f"\n⏭️  Next steps:")
    print(f"   1. Update policy heads: python scripts/distill_policies.py")
    print(f"   2. Test separation: python scripts/eval_separation.py")
    print(f"   3. Run full tests: make test && make gate")

    if success_count == len(personas):
        print(f"\n✨ All {len(personas)} twins trained successfully!")
    else:
        print(f"\n⚠️  {len(failed_twins)} twins failed - review errors above")

if __name__ == "__main__":
    main()
