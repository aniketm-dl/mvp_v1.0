# 🎯 Final Clean Structure

**Minimal, production-ready codebase for AWS training workflow.**

## Root Directory (Minimal)

```
mvp_v1.0/
├── README.md                    # Main guide
├── Makefile                     # All commands
├── darpan.py                    # Unified CLI
├── interact_cli.py              # Chat interface
├── pyproject.toml               # Dependencies
├── Dockerfile                   # Docker build
├── compose.yaml                 # Docker compose
│
├── docs/                        # 4 essential guides
│   ├── README.md
│   ├── AWS_SETUP.md
│   ├── TRAINING.md
│   └── API.md
│
├── src/                         # Core application
│   ├── api/                    # FastAPI endpoints
│   ├── datasets/               # Dataset abstraction (NEW)
│   ├── features/               # Feature extraction
│   ├── models/                 # ML models
│   ├── reasoning/              # LLM twins, guards
│   ├── metrics/                # Evaluation
│   └── profiles/               # User profiles
│
├── scripts/                     # Essential scripts only
│   ├── aws/                    # AWS automation
│   ├── opera/                  # Opera dataset
│   ├── reports/                # Analytics
│   ├── train_*.py              # Training scripts
│   ├── eval_*.py               # Evaluation
│   ├── prepare_*.py            # Data prep
│   └── distill_*.py            # Policy distillation
│
├── CONFIGS/                     # Configuration
│   ├── aws/                    # AWS training config
│   ├── serve/                  # API serving config
│   ├── opera/                  # Opera dataset config
│   ├── train/                  # Training configs
│   └── tests/                  # Test configs
│
├── DATA/                        # Data files
│   ├── personas.json           # Persona definitions
│   ├── sft/                    # Training data
│   └── opera/                  # Opera dataset
│
├── API/                         # API documentation
│   ├── SCHEMAS.md              # API schemas
│   ├── examples/               # Example requests
│   └── collections/            # Postman collections
│
├── SPECS/                       # Technical specs
│   └── WHAT_IF_SIMULATOR_SPEC.md
│
├── PROMPTS/                     # LLM prompts
│   └── reason_template.txt
│
├── TESTS/                       # All tests
│
└── archive/                     # Archived files
    ├── handover_docs/          # Handover/summary docs
    ├── migration_files/        # Old status files
    ├── old_docs/               # Redundant docs
    ├── colab_notebooks/        # Colab-specific
    ├── examples/               # Old examples
    ├── ui/                     # Web UI (future)
    └── [various scripts]       # Non-essential scripts
```

## What Was Removed/Archived

### ✅ Archived (Safe)
- **6 handover documents** → `archive/handover_docs/`
- **Colab notebooks** → `archive/colab_notebooks/` (3 files)
- **UI directory** → `archive/ui/` (focusing on CLI/API)
- **Examples directory** → `archive/examples/`
- **Colab scripts** → `archive/colab/`
- **Pipeline scripts** → `archive/pipeline/`
- **Utility scripts** → `archive/` (lab.py, cli.py, etc.)
- **Migration script** → `archive/migrate_to_new_structure.sh`

### 🗑️ Deleted
- `available:` - Empty file

## Essential Files Kept

### Workflow (6 files)
- `README.md` - Main guide
- `Makefile` - All commands
- `darpan.py` - Unified CLI
- `interact_cli.py` - Chat interface
- `Dockerfile` - Docker build
- `compose.yaml` - Docker compose

### Documentation (4 files in docs/)
- `README.md` - Copy of main
- `AWS_SETUP.md` - AWS setup
- `TRAINING.md` - Training guide
- `API.md` - API reference

### Configuration (1 file + directories)
- `pyproject.toml` - Python dependencies
- `CONFIGS/` - All config files

### Scripts (16 essential files)
AWS automation:
- `scripts/aws/*.sh` - Launch, setup scripts
- `scripts/aws/train_*.py` - Training orchestration

Training:
- `scripts/train_*.py` - Model training
- `scripts/eval_*.py` - Evaluation
- `scripts/prepare_*.py` - Data preparation
- `scripts/distill_*.py` - Policy distillation

Dataset:
- `scripts/opera/*.py` - Opera dataset scripts
- `scripts/download_opera_dataset.py`

Utilities:
- `scripts/reports/*.py` - Analytics
- `scripts/export_openapi.py`
- `scripts/build_copy_catalog.py`

## Directories Summary

| Directory | Files | Purpose | Status |
|-----------|-------|---------|--------|
| `docs/` | 4 | Documentation | ✅ Essential |
| `src/` | ~50 | Core application | ✅ Essential |
| `scripts/` | 16 | Training scripts | ✅ Essential |
| `CONFIGS/` | ~15 | Configuration | ✅ Essential |
| `DATA/` | Variable | Training data | ✅ Essential |
| `API/` | 3 | API docs | ✅ Essential |
| `SPECS/` | 1 | Specifications | ✅ Essential |
| `PROMPTS/` | 1 | LLM prompts | ✅ Essential |
| `TESTS/` | ~20 | Tests | ✅ Essential |
| `archive/` | ~50 | Old files | 📦 Archived |

## File Count Summary

**Before cleanup:**
- Root: ~20 files
- Docs: 24 files
- Scripts: ~40 files

**After cleanup:**
- Root: 6 files ✅
- Docs: 4 files ✅
- Scripts: 16 files ✅

**Reduction:** ~75% fewer files

## Quick Commands

```bash
# See everything
make help

# Complete workflow
make workflow

# Check status
./darpan.py status

# Interact
make chat
```

## What's NOT Needed for AWS Workflow

❌ Colab notebooks (archived)
❌ Web UI (archived for future)
❌ Examples directory (have interact_cli.py)
❌ Lab/CLI tools (have darpan.py)
❌ Pipeline scripts (can rebuild if needed)
❌ Multiple handover docs (archived)

## What IS Essential

✅ AWS scripts (automation)
✅ Opera scripts (dataset)
✅ Training scripts (model training)
✅ Core application (src/)
✅ Tests (quality)
✅ Configs (settings)
✅ Documentation (4 files)

## Rollback

All archived files are safe:
```bash
# View archived
ls -R archive/

# Restore if needed
cp -r archive/ui .
cp -r archive/colab_notebooks notebooks
# etc.
```

---

**Status:** ✅ Minimal, clean, production-ready
**Files:** Only essential for AWS training workflow
**Archived:** ~50 files safely stored
**Ready:** To train, deploy, and hand over

