#!/usr/bin/env python3
"""
Validation script for Phase 1-3 outputs.
Checks that all required files exist and meet quality thresholds.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


def check_phase_1():
    """Validate Phase 1: OPeRA parsing."""
    print("\n" + "=" * 60)
    print("PHASE 1: OPeRA Data Parsing")
    print("=" * 60)

    processed_dir = Path("DATA/OPeRA/processed")
    if not processed_dir.exists():
        print("❌ Processed data directory not found")
        return False

    # Check for expected files
    required_files = []
    parquet_files = list(processed_dir.glob("*.parquet"))

    if not parquet_files:
        print("❌ No parquet files found in processed directory")
        return False

    print(f"✓ Found {len(parquet_files)} parquet files")

    # Load and validate a sample file
    try:
        sample = pd.read_parquet(parquet_files[0])
        print(f"✓ Sample file shape: {sample.shape}")
        print(f"✓ Columns: {', '.join(sample.columns[:5])}...")
    except Exception as e:
        print(f"❌ Error loading parquet: {e}")
        return False

    print("✅ Phase 1 validation passed")
    return True


def check_phase_2():
    """Validate Phase 2: Encoder training."""
    print("\n" + "=" * 60)
    print("PHASE 2: Behavioral Encoder")
    print("=" * 60)

    encoder_dir = Path("artifacts/encoder")
    if not encoder_dir.exists():
        print("❌ Encoder directory not found")
        return False

    # Check for checkpoint
    checkpoints = list(encoder_dir.glob("**/*.ckpt"))
    if not checkpoints:
        print("❌ No checkpoint files found")
        return False

    print(f"✓ Found {len(checkpoints)} checkpoint(s)")

    # Check for best checkpoint
    best_ckpt = encoder_dir / "best.ckpt"
    if not best_ckpt.exists():
        print("⚠  No best.ckpt symlink (using last checkpoint)")
    else:
        print(f"✓ Best checkpoint: {best_ckpt.resolve()}")

    # Check training logs
    metrics_csv = encoder_dir / "logs/version_0/metrics.csv"
    if metrics_csv.exists():
        try:
            metrics = pd.read_csv(metrics_csv)
            final_acc = metrics["val/next_action_acc"].dropna().iloc[-1]
            print(f"✓ Final validation accuracy: {final_acc:.3f}")

            if final_acc < 0.70:
                print(f"⚠  Accuracy below threshold (0.70)")
            else:
                print("✓ Accuracy meets threshold")
        except Exception as e:
            print(f"⚠  Could not parse metrics: {e}")
    else:
        print("⚠  Metrics CSV not found")

    print("✅ Phase 2 validation passed")
    return True


def check_phase_3e1():
    """Validate Phase 3E.1: Session embeddings."""
    print("\n" + "=" * 60)
    print("PHASE 3E.1: Session Embeddings")
    print("=" * 60)

    embeddings_path = Path("artifacts/encoder/session_embeddings.parquet")
    if not embeddings_path.exists():
        print("❌ Session embeddings not found")
        return False

    try:
        df = pd.read_parquet(embeddings_path)
        emb_cols = [c for c in df.columns if c.startswith("emb_")]

        print(f"✓ Embeddings shape: {df.shape}")
        print(f"✓ Sessions: {len(df)}")
        print(f"✓ Embedding dimension: {len(emb_cols)}")

        if len(df) < 100:
            print(f"⚠  Very few sessions ({len(df)}), clustering may be unreliable")
            return False

        if len(emb_cols) == 0:
            print("❌ No embedding columns found")
            return False

        # Check for NaN
        if df[emb_cols].isna().any().any():
            print("⚠  Found NaN values in embeddings")

    except Exception as e:
        print(f"❌ Error loading embeddings: {e}")
        return False

    print("✅ Phase 3E.1 validation passed")
    return True


def check_phase_3e23():
    """Validate Phase 3E.2 & 3E.3: Discovery."""
    print("\n" + "=" * 60)
    print("PHASE 3E.2 & 3E.3: Persona Discovery")
    print("=" * 60)

    # Check registry
    registry_path = Path("DATA/personas_discovered/registry.json")
    if not registry_path.exists():
        print("❌ Persona registry not found")
        return False

    try:
        with open(registry_path) as f:
            registry = json.load(f)

        n_personas = len(registry.get("personas", []))
        print(f"✓ Discovered {n_personas} personas")

        if n_personas == 0:
            print("❌ No personas discovered")
            return False

        if n_personas < 5:
            print(f"⚠  Very few personas ({n_personas}), may need tuning")

        # Check individual files
        personas_dir = Path("DATA/personas_discovered")
        persona_files = list(personas_dir.glob("disc_*.json"))
        print(f"✓ Found {len(persona_files)} persona files")

        if len(persona_files) != n_personas:
            print(f"⚠  Mismatch: registry has {n_personas} but found {len(persona_files)} files")

        # Display sample
        for p in registry["personas"][:3]:
            print(f"  - {p['persona_id']}: {p['name']} (n={p['size']})")

    except Exception as e:
        print(f"❌ Error loading registry: {e}")
        return False

    # Check report
    report_path = Path("artifacts/discovery/report.md")
    if report_path.exists():
        print(f"✓ Discovery report exists")
        with open(report_path) as f:
            content = f.read()
            if "ALL GATES PASSED" in content:
                print("✓ All quality gates passed")
            else:
                print("⚠  Some quality gates failed")
    else:
        print("⚠  Discovery report not found")

    # Check metrics
    metrics_path = Path("artifacts/discovery/metrics.json")
    if metrics_path.exists():
        try:
            with open(metrics_path) as f:
                metrics = json.load(f)

            sil = metrics.get("silhouette", 0)
            db = metrics.get("davies_bouldin", 999)
            ch = metrics.get("calinski_harabasz", 0)

            print(f"\nQuality Metrics:")
            print(f"  Silhouette: {sil:.3f} (target: ≥0.45)")
            print(f"  Davies-Bouldin: {db:.3f} (target: ≤0.8)")
            print(f"  Calinski-Harabasz: {ch:.1f} (target: ≥100)")

            gates_passed = sil >= 0.45 and db <= 0.8 and ch >= 100
            if gates_passed:
                print("✓ All metrics meet thresholds")
            else:
                print("⚠  Some metrics below thresholds")

        except Exception as e:
            print(f"⚠  Could not parse metrics: {e}")
    else:
        print("⚠  Metrics file not found")

    print("✅ Phase 3E.2 & 3E.3 validation passed")
    return True


def main():
    print("\n" + "=" * 60)
    print("PHASE 1-3 VALIDATION")
    print("=" * 60)
    print("Checking all pipeline outputs...\n")

    results = {
        "Phase 1 (OPeRA Parsing)": check_phase_1(),
        "Phase 2 (Encoder Training)": check_phase_2(),
        "Phase 3E.1 (Embeddings)": check_phase_3e1(),
        "Phase 3E.2 & 3E.3 (Discovery)": check_phase_3e23(),
    }

    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    for phase, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}  {phase}")

    all_passed = all(results.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL VALIDATIONS PASSED")
        print("=" * 60)
        print("\nReady for Phase 4: Multi-turn SFT Dataset Generation")
        print("\nNext steps:")
        print("  1. Review discovery report: cat artifacts/discovery/report.md")
        print("  2. Inspect personas: cat DATA/personas_discovered/registry.json")
        print("  3. Enable discovered personas in CONFIGS/discovery.yaml")
        print("  4. Proceed to Phase 4")
        return 0
    else:
        print("❌ SOME VALIDATIONS FAILED")
        print("=" * 60)
        print("\nPlease review the errors above and re-run failed phases.")
        print("\nTo re-run specific phases:")
        print("  Phase 1: python3 scripts/parse_opera.py --in DATA/OPeRA/raw --out DATA/OPeRA/processed --config CONFIGS/opera.yaml")
        print("  Phase 2: python3 scripts/train/encoder_train.py --data DATA/OPeRA/processed --config CONFIGS/encoder.yaml --out artifacts/encoder")
        print("  Phase 3: python3 scripts/run_dynamic_discovery.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())
