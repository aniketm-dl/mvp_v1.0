#!/bin/bash
# Package codebase for Google Colab upload
# This creates a clean zip without unnecessary files

set -e

echo "📦 Packaging codebase for Google Colab..."

# Navigate to project root
cd "$(dirname "$0")/../.."

# Create output directory
OUTPUT_DIR="colab_packages"
mkdir -p "$OUTPUT_DIR"

# Package name with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE_NAME="darpan-whatif-simulator_${TIMESTAMP}.zip"

echo "🗜️  Creating zip file: $OUTPUT_DIR/$PACKAGE_NAME"

# Create zip excluding unnecessary files
zip -r "$OUTPUT_DIR/$PACKAGE_NAME" . \
  -x "*.git*" \
  -x "*__pycache__*" \
  -x "*.pyc" \
  -x "*venv/*" \
  -x "*.venv/*" \
  -x "*node_modules/*" \
  -x "artifacts/llm_adapters/*" \
  -x "*.DS_Store" \
  -x "colab_packages/*" \
  -x "*.egg-info/*" \
  -x "*.ipynb_checkpoints/*" \
  -q

# Get size
SIZE=$(du -h "$OUTPUT_DIR/$PACKAGE_NAME" | cut -f1)

echo "✅ Package created successfully!"
echo ""
echo "📊 Details:"
echo "   • File: $OUTPUT_DIR/$PACKAGE_NAME"
echo "   • Size: $SIZE"
echo ""
echo "📤 Next steps:"
echo "   1. Upload to Google Drive: https://drive.google.com/"
echo "   2. Open Google Colab: https://colab.research.google.com/"
echo "   3. Upload notebook: notebooks/train_on_colab.ipynb"
echo "   4. Follow notebook instructions"
echo ""
echo "💡 Tip: Keep the package under 100MB for faster upload"
