# 🎭 Trained Models Management System

This document explains how to download, organize, and interact with your trained persona models using the versioned system.

## 📁 Directory Structure

```
trained_models/
├── latest -> v20241016_143000/          # Symlink to latest version
├── v20241016_143000/                    # Versioned model directory
│   ├── adapters/                        # Trained LoRA adapters
│   │   ├── bargain_hunter/
│   │   ├── premium_loyalist/
│   │   └── ... (18 personas)
│   ├── metadata/                        # Training metadata
│   │   ├── model_inventory.json         # Complete model inventory
│   │   ├── personas.json               # Persona definitions
│   │   └── sft_data_info.txt           # SFT data information
│   ├── configs/                         # Configuration files
│   │   └── interaction_config.yaml     # Ready-to-use config
│   ├── start_interaction.sh            # Quick start script
│   └── README.md                       # Version documentation
└── v20241016_150000/                    # Another version (example)
```

## 🚀 Quick Start

### 1. **Automatic Download (Recommended)**
```bash
# Monitor training and auto-download when complete
./scripts/auto_download_when_ready.sh
```

### 2. **Manual Download**
```bash
# Download and organize models with versioning
./scripts/download_and_organize_models.sh

# Or with custom version name
./scripts/download_and_organize_models.sh --version v1.0
```

### 3. **Start Interacting**
```bash
# Use the quick start script (easiest)
./trained_models/latest/start_interaction.sh

# Or use the versioned interaction script
python scripts/versioned_interact.py
```

## 📋 Available Commands

### **Download and Organization**
```bash
# Auto-download when training is complete
./scripts/auto_download_when_ready.sh

# Manual download with versioning
./scripts/download_and_organize_models.sh [--version VERSION] [--force-download]

# Check training status
./check_training_status.sh
```

### **Version Management**
```bash
# List all available versions
python scripts/versioned_interact.py --list-versions

# Show version information
python scripts/versioned_interact.py --version v1.0 --info

# List personas for a version
python scripts/versioned_interact.py --version v1.0 --list-personas
```

### **Interaction**
```bash
# Interactive persona selection (uses latest version)
python scripts/versioned_interact.py

# Use specific version
python scripts/versioned_interact.py --version v1.0

# Chat with specific persona
python scripts/versioned_interact.py --persona bargain_hunter

# Use original interaction script
python interact_cli.py
```

## 🎯 What Gets Downloaded

### **Essential Files for Interaction:**
- ✅ **LoRA Adapters**: `adapter_model.safetensors` (the actual trained models)
- ✅ **Adapter Configs**: `adapter_config.json` (model configuration)
- ✅ **Tokenizers**: Tokenizer files for text processing
- ✅ **Persona Definitions**: Complete persona information
- ✅ **Interaction Configs**: Ready-to-use configuration files

### **Metadata and Tracking:**
- 📊 **Model Inventory**: Complete list of trained personas
- 📈 **Training Info**: Training parameters and completion status
- 📝 **SFT Data Info**: Information about training data used
- 🔧 **Configuration Files**: All necessary configs for interaction

## 🔧 Configuration Management

The system automatically manages configurations:

1. **Backs up** your current config to `CONFIGS/serve/llm.yaml.backup`
2. **Updates** the config to use the downloaded models
3. **Sets** `use_stub: false` to use real trained models
4. **Configures** the correct adapter directory path

## 📊 Version Information

Each version includes:
- **Download timestamp**
- **Training completion status** (e.g., "18/18 personas")
- **Base model information**
- **Training configuration** (epochs, LoRA settings, etc.)
- **Model sizes** for each persona
- **Complete persona inventory**

## 🎭 The 18 Personas

1. **bargain_hunter** - Always looking for deals
2. **premium_loyalist** - Pays extra for quality
3. **impulse_buyer** - Buys on emotion
4. **research_oriented** - Compares everything
5. **convenience_seeker** - Wants things fast and easy
6. **eco_conscious** - Cares about sustainability
7. **trendsetter** - Wants the latest and greatest
8. **budget_optimizer** - Maximizes value
9. **social_validator** - Cares what others think
10. **gift_buyer** - Shops for others
11. **bulk_buyer** - Buys in large quantities
12. **comparison_shopper** - Always comparing options
13. **mobile_shopper** - Shops on phone
14. **subscription_enthusiast** - Loves recurring services
15. **brand_switcher** - Tries different brands
16. **experiential_buyer** - Values experiences
17. **minimalist** - Wants simple, essential items
18. **local_supporter** - Prefers local businesses

## 🔄 Workflow Example

```bash
# 1. Monitor training (optional)
./scripts/auto_download_when_ready.sh

# 2. When training is complete, models are automatically downloaded
#    to trained_models/v20241016_143000/

# 3. Start interacting
./trained_models/latest/start_interaction.sh

# 4. Select a persona (e.g., "1" for The Bargain Hunter)

# 5. Start chatting!
# You: What laptop should I buy?
# The Bargain Hunter: I'd recommend waiting for a sale! Most laptops...
```

## 🛠️ Troubleshooting

### **No Models Found**
```bash
# Check if training is complete
./check_training_status.sh

# Force download partial results
./scripts/download_and_organize_models.sh --force-download
```

### **Configuration Issues**
```bash
# Restore backup config
cp CONFIGS/serve/llm.yaml.backup CONFIGS/serve/llm.yaml

# Or manually set up for a version
cp trained_models/v1.0/configs/interaction_config.yaml CONFIGS/serve/llm.yaml
```

### **Version Not Found**
```bash
# List available versions
python scripts/versioned_interact.py --list-versions

# Use latest version
python scripts/versioned_interact.py
```

## 💡 Tips

1. **Use the auto-download script** - It monitors training and downloads automatically
2. **Check version info** - Each version includes detailed metadata
3. **Keep multiple versions** - You can compare different training runs
4. **Use quick start scripts** - They handle all configuration automatically
5. **Backup your configs** - The system automatically backs up before changes

## 📞 Support

If you encounter issues:
1. Check the version README: `trained_models/latest/README.md`
2. Verify model inventory: `trained_models/latest/metadata/model_inventory.json`
3. Check training logs on AWS instance
4. Ensure you're running from the project root directory

---

**Happy chatting with your digital twins! 🎭✨**
