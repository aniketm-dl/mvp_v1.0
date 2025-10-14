#!/usr/bin/env python3
"""
AWS Training Script with S3 Sync and Auto-Shutdown

This script orchestrates training all 18 persona adapters on AWS with:
- Automatic S3 backup of trained adapters
- Progress tracking and resume capability
- Optional auto-shutdown to save costs
- Real-time cost estimation

Usage:
    python scripts/aws/train_with_s3_sync.py
    python scripts/aws/train_with_s3_sync.py --auto-shutdown
    python scripts/aws/train_with_s3_sync.py --s3-bucket my-bucket --twins bargain_hunter premium_buyer
"""

from __future__ import annotations
import argparse
import json
import subprocess
import time
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

def get_s3_bucket() -> str | None:
    """Get S3 bucket from environment or config."""
    # Try environment variable first
    bucket = os.environ.get('TRAINING_S3_BUCKET')
    if bucket:
        return bucket

    # Try to read from saved config
    config_file = Path.home() / '.darpan_aws_config.json'
    if config_file.exists():
        config = json.loads(config_file.read_text())
        return config.get('s3_bucket')

    return None

def save_s3_bucket(bucket: str):
    """Save S3 bucket to config for future use."""
    config_file = Path.home() / '.darpan_aws_config.json'
    config = {}
    if config_file.exists():
        config = json.loads(config_file.read_text())

    config['s3_bucket'] = bucket
    config_file.write_text(json.dumps(config, indent=2))

def sync_to_s3(local_path: Path, s3_bucket: str, s3_prefix: str):
    """Sync local files to S3."""
    if not s3_bucket:
        return

    s3_path = f"s3://{s3_bucket}/{s3_prefix}"
    print(f"\n📤 Syncing to S3: {s3_path}")

    try:
        cmd = [
            "aws", "s3", "sync",
            str(local_path),
            s3_path,
            "--exclude", "*.pyc",
            "--exclude", "__pycache__/*"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            print(f"✅ Synced to S3 successfully")
        else:
            print(f"⚠️  S3 sync warning: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("⚠️  S3 sync timed out - continuing anyway")
    except Exception as e:
        print(f"⚠️  S3 sync error: {e}")

def sync_from_s3(s3_bucket: str, s3_prefix: str, local_path: Path):
    """Sync files from S3 to local."""
    if not s3_bucket:
        return False

    s3_path = f"s3://{s3_bucket}/{s3_prefix}"
    print(f"\n📥 Checking S3 for existing data: {s3_path}")

    try:
        # Check if S3 path exists
        check_cmd = ["aws", "s3", "ls", s3_path]
        result = subprocess.run(check_cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            print(f"   No existing data in S3")
            return False

        # Sync from S3
        local_path.mkdir(parents=True, exist_ok=True)
        sync_cmd = [
            "aws", "s3", "sync",
            s3_path,
            str(local_path)
        ]
        result = subprocess.run(sync_cmd, capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            print(f"✅ Synced from S3 successfully")
            return True
        else:
            print(f"⚠️  S3 sync failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"⚠️  S3 sync error: {e}")
        return False

def load_personas() -> List[Dict[str, Any]]:
    """Load personas from DATA/personas.json."""
    personas_file = Path("DATA/personas.json")
    if not personas_file.exists():
        raise FileNotFoundError(f"{personas_file} not found! Run setup_training_data.py first.")

    data = json.loads(personas_file.read_text())
    return data["personas"]

def get_instance_info() -> Dict[str, str]:
    """Get AWS instance metadata."""
    info = {}
    try:
        info['instance_type'] = subprocess.check_output(
            ["curl", "-s", "http://169.254.169.254/latest/meta-data/instance-type"],
            timeout=2
        ).decode().strip()

        info['instance_id'] = subprocess.check_output(
            ["curl", "-s", "http://169.254.169.254/latest/meta-data/instance-id"],
            timeout=2
        ).decode().strip()

        info['region'] = subprocess.check_output(
            ["curl", "-s", "http://169.254.169.254/latest/meta-data/placement/region"],
            timeout=2
        ).decode().strip()
    except:
        info['instance_type'] = 'unknown'
        info['instance_id'] = 'unknown'
        info['region'] = 'unknown'

    return info

def estimate_cost(instance_type: str, hours: float) -> float:
    """Estimate training cost based on instance type."""
    # Spot pricing (approximate)
    spot_prices = {
        'g4dn.xlarge': 0.18,
        'g4dn.2xlarge': 0.25,
        'g5.xlarge': 0.35,
        'g5.2xlarge': 0.50,
        'p3.2xlarge': 1.00,
    }

    price_per_hour = spot_prices.get(instance_type, 0.50)
    return price_per_hour * hours

def train_twin(twin_id: str, base_model: str = "mistralai/Mistral-7B-Instruct-v0.2",
               epochs: int = 1, s3_bucket: str | None = None) -> bool:
    """Train a single twin adapter."""

    # Check if already trained
    adapter_file = Path(f"artifacts/llm_adapters/{twin_id}/adapter_model.safetensors")
    if adapter_file.exists():
        size_mb = adapter_file.stat().st_size / (1024 * 1024)
        print(f"   ✅ Already trained ({size_mb:.1f}MB) - skipping")
        return True

    # Check if training data exists
    data_file = Path(f"DATA/sft/{twin_id}.jsonl")
    if not data_file.exists():
        print(f"   ⚠️  No training data found for {twin_id}")
        return False

    # Run training script
    cmd = [
        sys.executable,
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
            check=True
        )

        # Verify adapter was created
        if adapter_file.exists():
            size_mb = adapter_file.stat().st_size / (1024 * 1024)
            print(f"   ✅ Adapter saved ({size_mb:.1f}MB)")

            # Sync to S3 immediately
            if s3_bucket:
                sync_to_s3(
                    Path(f"artifacts/llm_adapters/{twin_id}"),
                    s3_bucket,
                    f"trained_adapters/{twin_id}"
                )

            return True
        else:
            print(f"   ⚠️  Training completed but adapter file not found")
            return False

    except subprocess.CalledProcessError as e:
        print(f"   ❌ Training failed")
        return False

def main():
    parser = argparse.ArgumentParser(description="Train persona adapters on AWS with S3 sync")
    parser.add_argument("--s3-bucket", type=str, help="S3 bucket for storing trained models")
    parser.add_argument("--twins", nargs="+", help="Specific twin IDs to train (default: all)")
    parser.add_argument("--base-model", default="mistralai/Mistral-7B-Instruct-v0.2",
                        help="Base model to use")
    parser.add_argument("--epochs", type=int, default=1, help="Number of training epochs")
    parser.add_argument("--auto-shutdown", action="store_true",
                        help="Automatically shutdown instance after training")
    parser.add_argument("--no-s3", action="store_true", help="Disable S3 sync")
    args = parser.parse_args()

    print("=" * 80)
    print("🚀 DARPAN LABS - AWS GPU TRAINING WITH S3 SYNC")
    print("=" * 80)

    # Get instance info
    instance_info = get_instance_info()
    print(f"\n📊 Instance Info:")
    print(f"   • Type: {instance_info['instance_type']}")
    print(f"   • ID: {instance_info['instance_id']}")
    print(f"   • Region: {instance_info['region']}")

    # Setup S3 bucket
    s3_bucket = None
    if not args.no_s3:
        s3_bucket = args.s3_bucket or get_s3_bucket()

        if not s3_bucket:
            print("\n⚠️  No S3 bucket configured.")
            bucket_input = input("Enter S3 bucket name (or press Enter to skip): ").strip()
            if bucket_input:
                s3_bucket = bucket_input
                save_s3_bucket(s3_bucket)

        if s3_bucket:
            print(f"\n☁️  S3 Bucket: s3://{s3_bucket}/")
            print(f"   Trained adapters will be backed up to S3 automatically")

            # Try to sync existing adapters from S3
            print("\n📥 Checking S3 for previously trained adapters...")
            sync_from_s3(s3_bucket, "trained_adapters/", Path("artifacts/llm_adapters"))
        else:
            print("\n⚠️  S3 sync disabled - trained models will only be stored locally")

    # Load personas
    personas = load_personas()
    print(f"\n📚 Found {len(personas)} personas")

    # Filter twins if specified
    if args.twins:
        personas = [p for p in personas if p["id"] in args.twins]
        print(f"   Training only: {', '.join(p['id'] for p in personas)}")

    # Training configuration
    print(f"\n⚙️  Training Configuration:")
    print(f"   • Base model: {args.base_model}")
    print(f"   • Epochs: {args.epochs}")
    print(f"   • LoRA rank: 8")
    print(f"   • Learning rate: 2e-4")
    print(f"   • Max length: 512")

    # Cost estimation
    est_time_hours = len(personas) * 0.1  # ~6 min per twin average
    if instance_info['instance_type'] in ['g5.xlarge', 'g5.2xlarge']:
        est_time_hours *= 0.5  # G5 is ~2x faster
    elif instance_info['instance_type'].startswith('p3'):
        est_time_hours *= 0.3  # P3 is ~3x faster

    est_cost = estimate_cost(instance_info['instance_type'], est_time_hours)

    print(f"\n💰 Cost Estimation:")
    print(f"   • Estimated time: {est_time_hours:.1f} hours")
    print(f"   • Estimated cost: ${est_cost:.2f}")

    print(f"\n⏱️  Starting training in 3 seconds...")
    time.sleep(3)

    # Train each twin
    start_time = time.time()
    success_count = 0
    failed_twins = []

    for i, persona in enumerate(personas, 1):
        twin_id = persona["id"]
        label = persona["label"]

        print(f"\n{'='*80}")
        print(f"[{i}/{len(personas)}] Training {label}")
        print(f"{'='*80}")
        print(f"Twin ID: {twin_id}")

        twin_start = time.time()
        success = train_twin(twin_id, args.base_model, args.epochs, s3_bucket)
        twin_time = time.time() - twin_start

        if success:
            success_count += 1
            print(f"✅ Completed in {twin_time:.1f}s")
        else:
            failed_twins.append(twin_id)
            print(f"❌ Failed after {twin_time:.1f}s")

    # Training complete
    total_time = time.time() - start_time
    actual_cost = estimate_cost(instance_info['instance_type'], total_time / 3600)

    print("\n" + "=" * 80)
    print("🎉 TRAINING COMPLETE!")
    print("=" * 80)

    print(f"\n📊 Results:")
    print(f"   • Total personas: {len(personas)}")
    print(f"   • Successfully trained: {success_count}")
    print(f"   • Failed: {len(failed_twins)}")
    print(f"   • Total time: {total_time/60:.1f} minutes ({total_time/3600:.2f} hours)")
    print(f"   • Avg time per twin: {total_time/len(personas):.1f}s")
    print(f"   • Actual cost: ${actual_cost:.2f}")

    if failed_twins:
        print(f"\n⚠️  Failed twins: {', '.join(failed_twins)}")

    # Final S3 sync
    if s3_bucket:
        print(f"\n📤 Final sync to S3...")
        sync_to_s3(Path("artifacts/llm_adapters"), s3_bucket, "trained_adapters/")

        # Also sync training data for future use
        sync_to_s3(Path("DATA"), s3_bucket, "darpan_training_data/")

        print(f"\n✅ All trained models backed up to:")
        print(f"   s3://{s3_bucket}/trained_adapters/")

    # Check total adapter size
    adapter_dir = Path("artifacts/llm_adapters")
    if adapter_dir.exists():
        total_size = sum(
            f.stat().st_size
            for f in adapter_dir.rglob("adapter_model.safetensors")
        ) / (1024 * 1024)
        print(f"\n💾 Total adapter storage: {total_size:.1f}MB")

    # Save training report
    report = {
        "timestamp": datetime.now().isoformat(),
        "instance_type": instance_info['instance_type'],
        "instance_id": instance_info['instance_id'],
        "region": instance_info['region'],
        "base_model": args.base_model,
        "total_personas": len(personas),
        "successful": success_count,
        "failed": len(failed_twins),
        "failed_twins": failed_twins,
        "total_time_seconds": total_time,
        "cost_estimate_usd": actual_cost,
        "s3_bucket": s3_bucket
    }

    report_file = Path("artifacts/training_report.json")
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(report, indent=2))
    print(f"\n📄 Training report saved to: {report_file}")

    if s3_bucket:
        sync_to_s3(report_file, s3_bucket, "training_reports/latest.json")

    print(f"\n⏭️  Next steps:")
    print(f"   1. Download adapters locally:")
    print(f"      aws s3 sync s3://{s3_bucket}/trained_adapters/ artifacts/llm_adapters/")
    print(f"   2. Test locally: python interact_cli.py")
    print(f"   3. Run full tests: make test && make gate")

    if success_count == len(personas):
        print(f"\n✨ All {len(personas)} twins trained successfully!")
    else:
        print(f"\n⚠️  {len(failed_twins)} twins failed - review errors above")

    # Auto-shutdown if requested
    if args.auto_shutdown:
        print(f"\n⏰ Auto-shutdown enabled - shutting down in 5 minutes...")
        print(f"   Cancel with: sudo shutdown -c")
        subprocess.run(["sudo", "shutdown", "-h", "+5"])

    return 0 if success_count == len(personas) else 1

if __name__ == "__main__":
    sys.exit(main())
