# 🚀 Start Here - Refactored Darpan Labs

**Welcome to the refactored Darpan Labs Digital Twin Simulator!**

Everything you need is now in **one place** with **one command**.

---

## Quick Links

📘 **[HANDOVER.md](HANDOVER.md)** - Complete handover document (read this first!)  
📋 **[REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)** - Detailed changes  
📖 **[README.NEW.md](README.NEW.md)** - New consolidated README  
🔧 **Migration:** `./migrate_to_new_structure.sh`

---

## 30-Second Overview

**Before:** 24 docs, 15+ commands, manual tracking
**After:** 1 README, 1 command, automated workflow

**Complete workflow:**
```bash
make workflow    # Launch → Setup → Train → Download → Chat
```

**Cost:** ~$0.50 per training run (90 minutes on AWS)

---

## What's New?

### 1. **Unified CLI** (`./darpan.py`)
Single command for entire lifecycle:
```bash
./darpan.py workflow    # Complete automation
./darpan.py status      # Check progress
./darpan.py chat        # Talk to personas
```

### 2. **Enhanced Makefile**
Self-documenting with 50+ commands:
```bash
make help         # Show all commands
make quickstart   # Quick start guide
make workflow     # Complete automation
```

### 3. **Dataset Abstraction**
Easy to add new datasets:
```python
from src.datasets import DatasetFactory
dataset = DatasetFactory.create("opera")  # or "amazon", "shopify"
```

### 4. **Consolidated Docs**
24 files → 4 essential guides:
- `docs/README.md` - Main guide
- `docs/AWS_SETUP.md` - AWS setup
- `docs/TRAINING.md` - Training details
- `docs/API.md` - API docs

---

## Try It Now

### Check Status
```bash
./darpan.py status
```

### See All Commands
```bash
make help
make quickstart
```

### List Personas
```bash
make personas-list
```

### Test Locally
```bash
make interact    # Chat with personas (if adapters exist)
make serve       # Start API server
make test        # Run tests
```

---

## Next Steps

### 1. Review (10 minutes)
```bash
# Read handover document
cat HANDOVER.md

# Read refactoring summary
cat REFACTORING_SUMMARY.md

# Read new README
cat README.NEW.md
```

### 2. Test (5 minutes)
```bash
# Test CLI
./darpan.py --help
./darpan.py status

# Test Makefile
make help
make quickstart
make personas-list
```

### 3. Migrate (2 minutes)
```bash
# When ready, run migration
./migrate_to_new_structure.sh

# This will:
# - Archive old files → archive/
# - Install new README
# - Create docs/ directory
# - Setup CLI
```

### 4. Deploy (Optional)
```bash
# Run complete workflow (requires AWS)
make workflow

# Or step-by-step
make launch
make setup-instance  # On EC2
make train           # On EC2
make download        # Local
make chat            # Local
```

---

## File Guide

| File | Purpose |
|------|---------|
| `HANDOVER.md` | **→ Read this first!** Complete handover |
| `REFACTORING_SUMMARY.md` | Detailed changes and design decisions |
| `README.NEW.md` | New consolidated README (ready to install) |
| `darpan.py` | Unified CLI for workflow automation |
| `Makefile` | Enhanced with 50+ commands |
| `migrate_to_new_structure.sh` | Automated migration script |
| `src/datasets/` | Dataset abstraction layer |

---

## Decision Tree

**Are you a new user?**
→ Read [README.NEW.md](README.NEW.md)
→ Run `make quickstart`

**Are you reviewing the refactoring?**
→ Read [HANDOVER.md](HANDOVER.md)
→ Test commands locally
→ Provide feedback

**Are you ready to migrate?**
→ Run `./migrate_to_new_structure.sh`
→ Test `make workflow`

**Are you contributing code?**
→ Read [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)
→ Check dataset abstraction layer
→ Follow existing patterns

---

## Key Benefits

### For New Users
✅ Read ONE README (vs 24 docs)  
✅ Run ONE command (`make workflow`)  
✅ Clear progress indicators  
✅ Helpful error messages  

### For Developers
✅ All commands in Makefile (`make help`)  
✅ Dataset abstraction (easy to extend)  
✅ Self-documenting code  
✅ Backward compatible  

### For Production
✅ Automated workflow  
✅ Error recovery and retry  
✅ Cost tracking and alerts  
✅ S3 backup and sync  

---

## FAQ

**Q: Will this break existing code?**  
A: No. All existing scripts work. New workflow is additive.

**Q: Can I rollback?**  
A: Yes. Old files are in `archive/`, easy to restore.

**Q: How much does training cost?**  
A: ~$0.50 per run (g5.xlarge spot for 90 min).

**Q: How do I add a new dataset?**  
A: Implement `BaseDataset` in `src/datasets/`.

**Q: Where are the Opera scripts?**  
A: Still in `scripts/opera/`, unchanged and working.

---

## Support

📧 **Questions?** Review [HANDOVER.md](HANDOVER.md)  
🐛 **Issues?** Check [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)  
💡 **Ideas?** Extend dataset abstraction or Makefile  

---

## Summary

**You now have:**
- ✅ Automated workflow (one command does everything)
- ✅ Unified CLI with state tracking
- ✅ Self-documenting Makefile (50+ commands)
- ✅ Dataset abstraction (extensible)
- ✅ Consolidated documentation (4 guides)
- ✅ Production-ready features
- ✅ Backward compatibility

**Get started:**
```bash
make quickstart
./darpan.py status
```

**Ready to go! 🚀**

---

**Last Updated:** 2025-10-11  
**Status:** ✅ Complete and ready for use
