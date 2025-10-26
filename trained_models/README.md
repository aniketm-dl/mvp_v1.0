# 🎭 Trained Models Versioning System

## 📋 Overview

This directory contains versioned trained persona models organized for development sprints and iterative improvements. Each version represents a complete training run with all 18 digital twin personas, allowing us to track progress, compare performance, and preserve working models across development cycles.

## 🎯 Versioning Strategy

### **Why Versioning?**
- **🔄 Development Sprints**: Track improvements across multiple training iterations
- **🛡️ Model Preservation**: Never lose working models during new experiments
- **📊 Performance Comparison**: Compare different training approaches and configurations
- **🔒 Stability**: Maintain stable versions for production while experimenting with new ones
- **📈 Progress Tracking**: Visualize improvements over time

### **Version Naming Convention**
```
v{YYYYMMDD}_{HHMMSS}     # Timestamp-based (automatic)
v{sprint_number}         # Sprint-based (manual)
v{experiment_name}       # Experiment-based (manual)
```

**Examples:**
- `v20241016_143000` - Auto-generated timestamp version
- `v1.0` - First stable release
- `v2.0` - Second major iteration
- `v2.1_lora_improved` - Experiment with improved LoRA settings

## 📁 Directory Structure

```
trained_models/
├── README.md                           # This file
├── latest -> v20241016_143000/         # Symlink to current version
├── v20241016_143000/                   # Version 1 (timestamp-based)
│   ├── adapters/                       # Trained LoRA adapters
│   │   ├── bargain_hunter/
│   │   │   ├── adapter_model.safetensors
│   │   │   ├── adapter_config.json
│   │   │   └── tokenizer files...
│   │   ├── premium_loyalist/
│   │   └── ... (16 more personas)
│   ├── metadata/                       # Training metadata
│   │   ├── model_inventory.json        # Complete model inventory
│   │   ├── personas.json              # Persona definitions
│   │   ├── training_log.json          # Training logs and metrics
│   │   └── sft_data_info.txt          # SFT data information
│   ├── configs/                        # Configuration files
│   │   ├── interaction_config.yaml    # Ready-to-use config
│   │   └── training_config.yaml       # Training configuration used
│   ├── start_interaction.sh           # Quick start script
│   └── README.md                      # Version-specific documentation
├── v20241020_091500/                   # Version 2 (example)
│   └── ... (same structure)
└── v2.0_lora_improved/                 # Version 3 (experiment)
    └── ... (same structure)
```

## 🔄 Development Workflow

### **Sprint 1: Initial Training**
```bash
# Train initial models
./scripts/download_and_organize_models.sh --version v1.0

# Result: trained_models/v1.0/ with all 18 personas
```

### **Sprint 2: Model Improvements**
```bash
# Experiment with different training parameters
# (modify CONFIGS/aws/training_config.yaml)
# Train new models
./scripts/download_and_organize_models.sh --version v2.0

# Result: trained_models/v2.0/ (v1.0 remains untouched)
```

### **Sprint 3: A/B Testing**
```bash
# Test different approaches
./scripts/download_and_organize_models.sh --version v2.1_lora_improved
./scripts/download_and_organize_models.sh --version v2.2_more_data

# Compare performance between versions
python scripts/compare_versions.py v2.0 v2.1_lora_improved
```

### **Sprint 4: Production Release**
```bash
# Promote best version to production
ln -sf v2.1_lora_improved latest

# v1.0, v2.0, v2.2_more_data remain preserved
```

## 🛡️ Model Preservation Rules

### **Never Delete Older Versions**
- ✅ **Keep all versions** - Each represents valuable work
- ✅ **Archive instead of delete** - Move to `archive/` if needed
- ✅ **Document changes** - Each version has its own README
- ✅ **Maintain compatibility** - Ensure old versions still work

### **Version Lifecycle**
1. **Active Development** - Current sprint version
2. **Stable Release** - Tested and validated version
3. **Archived** - Moved to `archive/` but preserved
4. **Never Deleted** - Historical record maintained

## 📊 Version Comparison

### **What to Track Across Versions:**
- **Training Metrics**: Loss, accuracy, convergence time
- **Model Performance**: Response quality, persona consistency
- **Resource Usage**: Training time, GPU memory, cost
- **Data Changes**: SFT data improvements, new examples
- **Configuration Changes**: LoRA settings, learning rates, etc.

### **Comparison Tools:**
```bash
# Compare two versions
python scripts/compare_versions.py v1.0 v2.0

# Show version differences
python scripts/versioned_interact.py --compare v1.0 v2.0

# Generate performance report
python scripts/generate_version_report.py
```

## 🎯 Best Practices

### **Creating New Versions**
1. **Document Changes**: Update version README with what changed
2. **Test Thoroughly**: Validate all 18 personas work correctly
3. **Update Metadata**: Ensure model_inventory.json is complete
4. **Backup Configs**: Save training configuration used
5. **Performance Testing**: Compare against previous versions

### **Version Management**
1. **Use Descriptive Names**: `v2.1_lora_improved` vs `v20241020_091500`
2. **Update Symlinks**: Point `latest` to current stable version
3. **Document Decisions**: Why this version is better
4. **Maintain Compatibility**: Ensure interaction scripts work
5. **Archive Old Versions**: Move to `archive/` when no longer active

### **Quality Gates**
- ✅ All 18 personas trained successfully
- ✅ Model files are complete and valid
- ✅ Interaction system works correctly
- ✅ Performance meets or exceeds previous version
- ✅ Documentation is updated

## 🔧 Management Commands

### **Version Operations**
```bash
# List all versions
python scripts/versioned_interact.py --list-versions

# Show version information
python scripts/versioned_interact.py --version v1.0 --info

# Compare versions
python scripts/compare_versions.py v1.0 v2.0

# Archive old version
mv trained_models/v1.0 trained_models/archive/v1.0

# Update latest symlink
ln -sf v2.1_lora_improved latest
```

### **Interaction with Versions**
```bash
# Use specific version
python scripts/versioned_interact.py --version v1.0

# Use latest version
python scripts/versioned_interact.py

# Quick start with latest
./trained_models/latest/start_interaction.sh
```

## 📈 Sprint Planning

### **Sprint 1: Foundation** ✅
- **Goal**: Establish baseline with all 18 personas
- **Version**: `v1.0`
- **Focus**: Complete training pipeline, basic interaction

### **Sprint 2: Quality Improvement** 🔄
- **Goal**: Improve response quality and persona consistency
- **Version**: `v2.0`
- **Focus**: Better SFT data, improved training parameters

### **Sprint 3: Performance Optimization** 📋
- **Goal**: Faster training, better resource utilization
- **Version**: `v3.0`
- **Focus**: LoRA optimization, training efficiency

### **Sprint 4: Advanced Features** 📋
- **Goal**: Multi-turn conversations, context awareness
- **Version**: `v4.0`
- **Focus**: Advanced training techniques, larger context

## 🎭 Persona Evolution Tracking

### **Version 1.0**: Basic Personas
- 18 personas with fundamental characteristics
- Basic shopping advice and preferences
- Simple conversation patterns

### **Version 2.0**: Enhanced Personas
- Improved response quality
- Better persona consistency
- More nuanced shopping advice

### **Version 3.0**: Advanced Personas
- Multi-turn conversation capability
- Context awareness
- More sophisticated decision-making

## 📋 Version Checklist

When creating a new version, ensure:

- [ ] All 18 personas trained successfully
- [ ] Model files are complete and valid
- [ ] Metadata is accurate and complete
- [ ] Configuration files are ready
- [ ] Interaction system works
- [ ] Performance is documented
- [ ] README is updated
- [ ] Previous versions are preserved
- [ ] Symlinks are updated correctly

## 🚀 Getting Started

### **For New Team Members:**
1. Read this README to understand versioning strategy
2. Check `latest/README.md` for current version details
3. Use `./trained_models/latest/start_interaction.sh` to start
4. Review version history in `metadata/` directories

### **For Developers:**
1. Always create new versions for experiments
2. Never modify existing versions
3. Document all changes in version README
4. Test thoroughly before promoting to `latest`
5. Preserve all previous versions

---

## 📞 Support

- **Version Issues**: Check individual version README files
- **Training Problems**: Review training logs in `metadata/`
- **Interaction Issues**: Verify configuration files
- **Performance Questions**: Compare with previous versions

**Remember: Every version represents valuable work. Preserve, don't delete! 🛡️**
