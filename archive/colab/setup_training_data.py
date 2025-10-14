#!/usr/bin/env python3
"""
Set up all training data on Google Colab.
Downloads OPeRA dataset and generates all persona training data.

This script is designed to run on Colab where DATA folder doesn't exist.
"""

from __future__ import annotations
import sys
from pathlib import Path
import subprocess
import json

def check_data_exists() -> bool:
    """Check if DATA folder already exists with required files.    """
    data_dir = Path("DATA")

    if not data_dir.exists():
        return False

    # Check for required files
    required_files = [
        "personas.json",
        "twin_bank.json",
        "sft"  # directory
    ]

    for req in required_files:
        if not (data_dir / req).exists():
            return False

    # Check SFT has files
    sft_dir = data_dir / "sft"
    if sft_dir.is_dir():
        sft_files = list(sft_dir.glob("*.jsonl"))
        if len(sft_files) < 18:  # Should have 18 persona files
            return False

    return True

def download_opera_dataset():
    """Download OPeRA dataset from HuggingFace."""
    print("\n📥 Downloading OPeRA dataset from HuggingFace...")
    print("   (This is a large dataset ~476MB, may take 5-10 minutes)")

    data_dir = Path("DATA")
    data_dir.mkdir(exist_ok=True)

    opera_dir = data_dir / "opera"

    if opera_dir.exists() and (opera_dir / ".git").exists():
        print("   ✅ OPeRA dataset already downloaded")
        return

    try:
        # Clone the dataset from HuggingFace
        cmd = [
            "git", "clone",
            "https://huggingface.co/datasets/NEU-HAI/OPeRA",
            str(opera_dir)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode == 0:
            print("   ✅ OPeRA dataset downloaded successfully")
        else:
            print(f"   ⚠️  Warning: OPeRA download had issues: {result.stderr}")
            print("   Continuing without OPeRA (optional for training)")

    except subprocess.TimeoutExpired:
        print("   ⚠️  Warning: OPeRA download timed out (too large)")
        print("   Continuing without OPeRA (optional for training)")
    except Exception as e:
        print(f"   ⚠️  Warning: Could not download OPeRA: {e}")
        print("   Continuing without OPeRA (optional for training)")

def generate_personas():
    """Generate personas.json and twin_bank.json."""
    print("\n🎯 Generating personas and twin bank...")

    # Run the persona generation script
    try:
        result = subprocess.run(
            [sys.executable, "scripts/generate_mvp_personas.py"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        print("   ✅ Personas generated successfully")
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error generating personas: {e.stderr}")
        raise

def generate_training_data():
    """Generate SFT training data for all personas."""
    print("\n📚 Generating training data for all 18 personas...")
    print("   (Creating 150 examples per persona = 2,700 total)")

    # Run the training data generation script
    try:
        result = subprocess.run(
            [sys.executable, "scripts/generate_mvp_training_data.py"],
            capture_output=True,
            text=True,
            check=True,
            timeout=120
        )
        print(result.stdout)
        print("   ✅ Training data generated successfully")
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error generating training data: {e.stderr}")
        raise
    except subprocess.TimeoutExpired:
        print("   ⚠️  Training data generation timed out")
        raise

def verify_data():
    """Verify all data was created correctly."""
    print("\n✅ Verifying generated data...")

    data_dir = Path("DATA")
    errors = []

    # Check personas.json
    personas_file = data_dir / "personas.json"
    if personas_file.exists():
        personas = json.loads(personas_file.read_text())
        if len(personas.get("personas", [])) == 18:
            print(f"   ✅ personas.json: {len(personas['personas'])} personas")
        else:
            errors.append(f"personas.json has {len(personas.get('personas', []))} personas, expected 18")
    else:
        errors.append("personas.json not found")

    # Check twin_bank.json
    twin_bank_file = data_dir / "twin_bank.json"
    if twin_bank_file.exists():
        twin_bank = json.loads(twin_bank_file.read_text())
        if len(twin_bank.get("twins", [])) == 18:
            print(f"   ✅ twin_bank.json: {len(twin_bank['twins'])} twins")
        else:
            errors.append(f"twin_bank.json has {len(twin_bank.get('twins', []))} twins, expected 18")
    else:
        errors.append("twin_bank.json not found")

    # Check SFT training data
    sft_dir = data_dir / "sft"
    if sft_dir.exists():
        sft_files = list(sft_dir.glob("*.jsonl"))
        if len(sft_files) == 18:
            # Count total examples
            total_examples = 0
            for f in sft_files:
                lines = f.read_text().strip().split('\n')
                total_examples += len(lines)
            print(f"   ✅ SFT training data: {len(sft_files)} files, {total_examples:,} examples")
        else:
            errors.append(f"SFT has {len(sft_files)} files, expected 18")
    else:
        errors.append("SFT directory not found")

    # Check OPeRA (optional)
    opera_dir = data_dir / "opera"
    if opera_dir.exists():
        print(f"   ✅ OPeRA dataset: present")
    else:
        print(f"   ⚠️  OPeRA dataset: not present (optional)")

    # Calculate total size
    total_size_mb = sum(f.stat().st_size for f in data_dir.rglob('*') if f.is_file()) / (1024 * 1024)
    print(f"   📦 Total DATA size: {total_size_mb:.1f}MB")

    if errors:
        print("\n❌ Verification errors:")
        for err in errors:
            print(f"   • {err}")
        return False

    print("\n🎉 All data generated and verified successfully!")
    return True

def main():
    """Main setup workflow."""
    print("=" * 70)
    print("🚀 DARPAN LABS - TRAINING DATA SETUP FOR GOOGLE COLAB")
    print("=" * 70)

    # Check if data already exists
    if check_data_exists():
        print("\n✅ DATA folder already exists with required files!")
        print("   Skipping data generation.")
        print("\n💡 If you want to regenerate, delete the DATA folder and run again.")
        verify_data()
        return

    print("\n📋 Setup Plan:")
    print("   1. Download OPeRA dataset from HuggingFace (~476MB, optional)")
    print("   2. Generate personas.json and twin_bank.json")
    print("   3. Generate training data for 18 personas (2,700 examples)")
    print("   4. Verify all data")
    print("\n⏱️  Estimated time: 5-10 minutes")
    print("\nPress Ctrl+C to cancel, or continuing in 3 seconds...")

    try:
        import time
        time.sleep(3)
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        return

    try:
        # Step 1: Download OPeRA (optional, may fail/timeout)
        download_opera_dataset()

        # Step 2: Generate personas
        generate_personas()

        # Step 3: Generate training data
        generate_training_data()

        # Step 4: Verify
        success = verify_data()

        if success:
            print("\n" + "=" * 70)
            print("✨ SETUP COMPLETE!")
            print("=" * 70)
            print("\n📁 DATA folder is ready for training!")
            print("\n⏭️  Next steps:")
            print("   1. Save DATA to Google Drive: cp -r DATA /content/drive/MyDrive/")
            print("   2. Start training: python scripts/train_all_adapters.py")
            print("\n💡 DATA will persist in Google Drive for future sessions")
        else:
            print("\n❌ Setup completed with errors - please review above")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
