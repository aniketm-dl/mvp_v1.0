#!/bin/bash
#
# Migrate Darpan Labs codebase to new structure
#
# This script:
# 1. Archives old documentation and status files
# 2. Creates new docs directory with essential guides
# 3. Replaces README with consolidated version
# 4. Sets up CLI and environment
#

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║         DARPAN LABS - MIGRATION TO NEW STRUCTURE                           ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Confirm before proceeding
read -p "This will archive old files and restructure the project. Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Migration cancelled"
    exit 1
fi

echo "🔄 Starting migration..."
echo ""

# ============================================================================
# Step 1: Create archive directories
# ============================================================================
echo "📁 Creating archive directories..."
mkdir -p archive/old_docs
mkdir -p archive/migration_files
mkdir -p archive/old_scripts
echo "   ✅ Created archive/"

# ============================================================================
# Step 2: Archive status and summary files
# ============================================================================
echo ""
echo "📦 Archiving status and summary files..."

files_to_archive=(
    "MVP_STATUS.md"
    "MIGRATION_TO_MISTRAL.md"
    "MISTRAL_SETUP_COMPLETE.md"
    "DATA_SOLUTION_SUMMARY.md"
    "PERSONAS_SUMMARY.md"
    "COLAB_CHECKLIST.md"
    "TWIN_INTERACTION_GUIDE.md"
    "CONTRIBUTING.md"
    "CHANGELOG.md"
)

for file in "${files_to_archive[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" archive/migration_files/
        echo "   ✅ Archived: $file"
    fi
done

# ============================================================================
# Step 3: Archive redundant documentation
# ============================================================================
echo ""
echo "📚 Archiving redundant documentation..."

docs_to_archive=(
    "DOCS/COLAB_QUICKSTART.md"
    "DOCS/COLAB_WORKFLOW.md"
    "DOCS/QUICKSTART_MVP.md"
    "DOCS/SETUP_COMPLETE.md"
    "DOCS/RUNBOOK_PHASE_G.md"
    "DOCS/PHASE_J_RUNBOOK.md"
    "DOCS/PLAYGROUND.md"
    "DOCS/TWIN_LAB.md"
    "DOCS/NON_TECH_SUMMARY.md"
    "DOCS/PERSONA_TRAINING.md"
    "DOCS/OPERA_TO_SFT.md"
    "DOCS/SFT_DATA.md"
    "DOCS/DATA_GENERATION_GUIDE.md"
    "DOCS/DEPLOY.md"
    "DOCS/MODEL_BENCHMARK_COMPARISON.md"
    "DOCS/MISTRAL_QUICKSTART.md"
    "DOCS/AWS_QUICK_START.md"
)

for doc in "${docs_to_archive[@]}"; do
    if [ -f "$doc" ]; then
        mv "$doc" archive/old_docs/
        echo "   ✅ Archived: $doc"
    fi
done

# Keep START_HERE.md temporarily for reference
if [ -f "DOCS/START_HERE.md" ]; then
    cp "DOCS/START_HERE.md" archive/old_docs/
    echo "   ✅ Copied: DOCS/START_HERE.md (for reference)"
fi

# ============================================================================
# Step 4: Create new docs directory
# ============================================================================
echo ""
echo "📖 Creating new documentation structure..."

mkdir -p docs

# Copy essential AWS docs
if [ -f "DOCS/AWS_ACCOUNT_SETUP.md" ]; then
    cp "DOCS/AWS_ACCOUNT_SETUP.md" docs/AWS_SETUP.md
    echo "   ✅ Created: docs/AWS_SETUP.md"
fi

if [ -f "DOCS/AWS_TRAINING_GUIDE.md" ]; then
    cp "DOCS/AWS_TRAINING_GUIDE.md" docs/TRAINING.md
    echo "   ✅ Created: docs/TRAINING.md"
fi

# Copy API documentation
if [ -f "API/SCHEMAS.md" ]; then
    cp "API/SCHEMAS.md" docs/API.md
    echo "   ✅ Created: docs/API.md"
fi

# Copy production features
if [ -f "DOCS/PRODUCTION_FEATURES.md" ]; then
    cp "DOCS/PRODUCTION_FEATURES.md" docs/ARCHITECTURE.md
    echo "   ✅ Created: docs/ARCHITECTURE.md"
fi

# ============================================================================
# Step 5: Replace README
# ============================================================================
echo ""
echo "📝 Updating README..."

if [ -f "README.md" ]; then
    mv README.md archive/README.old.md
    echo "   ✅ Archived: README.md → archive/README.old.md"
fi

if [ -f "README.NEW.md" ]; then
    mv README.NEW.md README.md
    echo "   ✅ New README.md installed"

    # Also copy to docs/
    cp README.md docs/README.md
    echo "   ✅ Copied to docs/README.md"
else
    echo "   ⚠️  README.NEW.md not found, keeping old README"
fi

# ============================================================================
# Step 6: Setup CLI
# ============================================================================
echo ""
echo "🔧 Setting up CLI..."

if [ -f "darpan.py" ]; then
    chmod +x darpan.py
    echo "   ✅ Made darpan.py executable"

    # Create symlink for convenience
    if [ ! -f "darpan" ]; then
        ln -s darpan.py darpan
        echo "   ✅ Created symlink: darpan → darpan.py"
    fi
else
    echo "   ⚠️  darpan.py not found"
fi

# ============================================================================
# Step 7: Create .env.example
# ============================================================================
echo ""
echo "⚙️  Creating .env.example..."

cat > .env.example << 'EOF'
# Darpan Labs - Environment Configuration

# AWS Configuration
AWS_REGION=us-east-1
TRAINING_S3_BUCKET=darpan-training-YOUR_NAME

# HuggingFace
HF_TOKEN=your_huggingface_token_here

# Training Configuration
BASE_MODEL=mistralai/Mistral-7B-Instruct-v0.2
TRAINING_EPOCHS=1
LORA_RANK=8
LEARNING_RATE=2e-4

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
ADMIN_TOKEN=changeme

# Monitoring (optional)
SENTRY_DSN=
WANDB_API_KEY=
EOF

echo "   ✅ Created .env.example"

# ============================================================================
# Step 8: Create .gitignore additions
# ============================================================================
echo ""
echo "📝 Updating .gitignore..."

cat >> .gitignore << 'EOF'

# Darpan workflow state
.darpan_workflow_state.json

# Environment
.env

# AWS credentials (safety)
*.pem
credentials.json
EOF

echo "   ✅ Updated .gitignore"

# ============================================================================
# Step 9: Clean up
# ============================================================================
echo ""
echo "🧹 Cleaning up..."

make clean 2>/dev/null || true
echo "   ✅ Cleaned build artifacts"

# ============================================================================
# Step 10: Create migration summary
# ============================================================================
echo ""
echo "📊 Creating migration log..."

cat > archive/MIGRATION_LOG.txt << EOF
Darpan Labs - Migration Log
============================

Date: $(date)
Migration script: migrate_to_new_structure.sh

Files Archived:
---------------
$(ls -1 archive/migration_files/)

Docs Archived:
--------------
$(ls -1 archive/old_docs/)

New Structure:
--------------
docs/
├── README.md
├── AWS_SETUP.md
├── TRAINING.md
├── API.md
└── ARCHITECTURE.md

New Files:
----------
- darpan.py (Unified CLI)
- Makefile (Enhanced)
- src/datasets/ (Dataset abstraction)
- .env.example
- REFACTORING_SUMMARY.md

Notes:
------
- Old README saved as: archive/README.old.md
- All status/summary files in: archive/migration_files/
- Old docs in: archive/old_docs/
- Opera scripts unchanged (backward compatible)

To rollback:
------------
$ mv archive/README.old.md README.md
$ cp -r archive/old_docs/* DOCS/
$ git checkout HEAD -- Makefile
$ rm darpan.py src/datasets/*.py

EOF

echo "   ✅ Created: archive/MIGRATION_LOG.txt"

# ============================================================================
# Done!
# ============================================================================
echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                         MIGRATION COMPLETE! 🎉                             ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ Summary:"
echo "   • Archived old files → archive/"
echo "   • Created new docs/ directory with 5 essential guides"
echo "   • Installed new README.md"
echo "   • Setup unified CLI (darpan.py)"
echo "   • Created .env.example template"
echo ""
echo "📚 Next Steps:"
echo "   1. Review: cat README.md"
echo "   2. Quick start: make quickstart"
echo "   3. See all commands: make help"
echo "   4. Check status: ./darpan.py status"
echo ""
echo "🔄 To see what changed:"
echo "   • Read: REFACTORING_SUMMARY.md"
echo "   • View log: archive/MIGRATION_LOG.txt"
echo ""
echo "📦 Archived files are safe in:"
echo "   • archive/migration_files/ (status files)"
echo "   • archive/old_docs/ (old documentation)"
echo "   • archive/README.old.md (original README)"
echo ""
echo "🚀 Try the new workflow:"
echo "   make workflow"
echo ""
