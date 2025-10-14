#!/usr/bin/env python3
"""
Package codebase for Google Colab upload (cross-platform Python version).
"""

import zipfile
import os
from pathlib import Path
from datetime import datetime

# Files/dirs to exclude
EXCLUDE_PATTERNS = [
    '.git',
    '__pycache__',
    '.pyc',
    'venv',
    '.venv',
    'node_modules',
    'artifacts/llm_adapters',
    '.DS_Store',
    'colab_packages',
    '.egg-info',
    '.ipynb_checkpoints',
    '*.pyc',
]

def should_exclude(file_path: Path) -> bool:
    """Check if file should be excluded."""
    path_str = str(file_path)
    for pattern in EXCLUDE_PATTERNS:
        if pattern in path_str:
            return True
    return False

def get_all_files(root_dir: Path):
    """Get all files to include in package."""
    for item in root_dir.rglob('*'):
        if item.is_file() and not should_exclude(item):
            yield item

def main():
    print("📦 Packaging codebase for Google Colab...")

    # Get project root (two levels up from this script)
    project_root = Path(__file__).parent.parent.parent

    # Create output directory
    output_dir = project_root / "colab_packages"
    output_dir.mkdir(exist_ok=True)

    # Package name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"darpan-whatif-simulator_{timestamp}.zip"
    package_path = output_dir / package_name

    print(f"🗜️  Creating zip file: {package_path}")

    # Create zip
    file_count = 0
    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in get_all_files(project_root):
            # Get relative path
            arcname = file_path.relative_to(project_root)
            zipf.write(file_path, arcname)
            file_count += 1

            # Progress indicator
            if file_count % 100 == 0:
                print(f"   Added {file_count} files...", end='\r')

    # Get size
    size_mb = package_path.stat().st_size / (1024 * 1024)

    print(f"\n✅ Package created successfully!")
    print(f"")
    print(f"📊 Details:")
    print(f"   • File: {package_path}")
    print(f"   • Size: {size_mb:.1f} MB")
    print(f"   • Files: {file_count}")
    print(f"")
    print(f"📤 Next steps:")
    print(f"   1. Upload to Google Drive: https://drive.google.com/")
    print(f"   2. Open Google Colab: https://colab.research.google.com/")
    print(f"   3. Upload notebook: notebooks/train_on_colab.ipynb")
    print(f"   4. Follow notebook instructions")
    print(f"")

    if size_mb > 100:
        print(f"⚠️  Warning: Package is over 100MB. Consider removing large files.")
    else:
        print(f"💡 Package size is good for quick upload!")

if __name__ == "__main__":
    main()
