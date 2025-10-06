#!/usr/bin/env python3
"""
Download and extract trained adapters from Google Colab.

Usage:
    python scripts/colab/download_adapters.py --zip path/to/llm_adapters_llama2.zip
"""

import argparse
import zipfile
from pathlib import Path
import shutil

def main():
    parser = argparse.ArgumentParser(description="Extract trained adapters from Colab")
    parser.add_argument(
        "--zip",
        required=True,
        help="Path to the adapter zip file (e.g., llm_adapters_llama2.zip)"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Backup existing adapters before extracting"
    )
    args = parser.parse_args()

    # Get paths
    project_root = Path(__file__).parent.parent.parent
    zip_path = Path(args.zip)
    adapters_dir = project_root / "artifacts" / "llm_adapters"

    # Validate zip file
    if not zip_path.exists():
        print(f"❌ Error: Zip file not found: {zip_path}")
        return 1

    print(f"📦 Extracting adapters from: {zip_path}")
    print(f"📁 Target directory: {adapters_dir}")

    # Backup existing adapters if requested
    if args.backup and adapters_dir.exists():
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = project_root / "artifacts" / f"llm_adapters_backup_{timestamp}"

        print(f"💾 Backing up existing adapters to: {backup_dir}")
        shutil.copytree(adapters_dir, backup_dir)
        print(f"✅ Backup complete")

    # Create artifacts directory if it doesn't exist
    adapters_dir.parent.mkdir(parents=True, exist_ok=True)

    # Extract zip
    print(f"🗜️  Extracting...")
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        # Get list of files
        file_list = zipf.namelist()
        total_files = len(file_list)

        # Extract all files
        for i, file in enumerate(file_list, 1):
            zipf.extract(file, adapters_dir.parent)

            # Progress indicator
            if i % 50 == 0 or i == total_files:
                print(f"   Extracted {i}/{total_files} files...", end='\r')

        print(f"\n✅ Extraction complete!")

    # Verify extracted adapters
    print(f"\n📊 Verifying adapters...")

    if not adapters_dir.exists():
        print(f"❌ Error: Adapters directory not created after extraction")
        return 1

    # Count adapters
    adapter_count = 0
    for adapter_dir in adapters_dir.iterdir():
        if adapter_dir.is_dir():
            adapter_file = adapter_dir / "adapter_model.safetensors"
            if adapter_file.exists():
                size_mb = adapter_file.stat().st_size / (1024 * 1024)
                print(f"   ✅ {adapter_dir.name:<25} ({size_mb:>6.1f} MB)")
                adapter_count += 1

    print(f"\n✅ Found {adapter_count} valid adapters")

    # Update config if needed
    config_path = project_root / "CONFIGS" / "serve" / "llm.yaml"
    if config_path.exists():
        import yaml
        config = yaml.safe_load(config_path.read_text())

        current_stub = config.get("llm", {}).get("use_stub", True)
        current_model = config.get("llm", {}).get("base_model", "")

        print(f"\n⚙️  Current configuration:")
        print(f"   • use_stub: {current_stub}")
        print(f"   • base_model: {current_model}")

        if current_stub:
            print(f"\n💡 Tip: Set 'use_stub: false' in {config_path} to use the new adapters")

        if "llama" not in current_model.lower():
            print(f"⚠️  Warning: Current base_model doesn't match trained adapters (Llama-2)")
            print(f"   Update base_model to 'meta-llama/Llama-2-7b-chat-hf' in {config_path}")

    print(f"\n🚀 Ready to use! Run: python interact_cli.py")
    return 0

if __name__ == "__main__":
    exit(main())
