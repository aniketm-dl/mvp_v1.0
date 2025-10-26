#!/usr/bin/env python3
"""
Versioned Persona Interaction Script

This script allows you to interact with trained personas from any version
of the trained models, with proper configuration management.

Usage:
    python scripts/versioned_interact.py
    python scripts/versioned_interact.py --version v1.0
    python scripts/versioned_interact.py --list-versions
    python scripts/versioned_interact.py --persona bargain_hunter
"""

from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def list_available_versions() -> List[str]:
    """List all available model versions."""
    trained_models_dir = Path("trained_models")
    if not trained_models_dir.exists():
        return []
    
    versions = []
    for item in trained_models_dir.iterdir():
        if item.is_dir() and item.name != "latest":
            versions.append(item.name)
    
    return sorted(versions, reverse=True)  # Newest first

def get_version_info(version: str) -> Dict[str, Any]:
    """Get information about a specific version."""
    version_dir = Path("trained_models") / version
    metadata_file = version_dir / "metadata" / "model_inventory.json"
    
    if not metadata_file.exists():
        return {}
    
    with open(metadata_file, 'r') as f:
        return json.load(f)

def list_available_personas(version: str) -> List[str]:
    """List available personas for a version."""
    version_dir = Path("trained_models") / version
    adapters_dir = version_dir / "adapters"
    
    if not adapters_dir.exists():
        return []
    
    personas = []
    for persona_dir in adapters_dir.iterdir():
        if persona_dir.is_dir() and (persona_dir / "adapter_model.safetensors").exists():
            personas.append(persona_dir.name)
    
    return sorted(personas)

def setup_interaction_config(version: str) -> bool:
    """Set up the interaction configuration for a specific version."""
    version_dir = Path("trained_models") / version
    config_file = version_dir / "configs" / "interaction_config.yaml"
    
    if not config_file.exists():
        print(f"❌ Configuration file not found for version {version}")
        return False
    
    # Backup current config
    current_config = Path("CONFIGS/serve/llm.yaml")
    if current_config.exists():
        backup_config = Path("CONFIGS/serve/llm.yaml.backup")
        shutil.copy2(current_config, backup_config)
        print(f"📋 Backed up current config to {backup_config}")
    
    # Copy version config
    shutil.copy2(config_file, current_config)
    print(f"✅ Updated configuration for version {version}")
    return True

def load_personas_for_version(version: str) -> List[Dict[str, Any]]:
    """Load personas for a specific version."""
    version_dir = Path("trained_models") / version
    personas_file = version_dir / "metadata" / "personas.json"
    
    if not personas_file.exists():
        # Fallback to main personas file
        personas_file = Path("DATA/personas.json")
    
    if not personas_file.exists():
        return []
    
    with open(personas_file, 'r') as f:
        data = json.load(f)
    return data.get('personas', [])

def print_version_info(version: str):
    """Print information about a version."""
    info = get_version_info(version)
    if not info:
        print(f"❌ No information available for version {version}")
        return
    
    print(f"\n📊 Version Information: {version}")
    print("=" * 60)
    print(f"📅 Download Date: {info.get('download_date', 'Unknown')}")
    print(f"🎯 Training Completion: {info.get('training_completion', 'Unknown')}")
    print(f"🤖 Base Model: {info.get('base_model', 'Unknown')}")
    print(f"👥 Total Personas: {info.get('total_personas', 0)}")
    
    if 'training_config' in info:
        config = info['training_config']
        print(f"⚙️  Training Config:")
        print(f"   • Epochs: {config.get('epochs', 'Unknown')}")
        print(f"   • LoRA Rank: {config.get('lora_rank', 'Unknown')}")
        print(f"   • Learning Rate: {config.get('learning_rate', 'Unknown')}")

def print_personas_for_version(version: str):
    """Print available personas for a version."""
    personas = load_personas_for_version(version)
    available_personas = list_available_personas(version)
    
    print(f"\n🎭 Available Personas for {version}")
    print("=" * 60)
    
    for i, persona in enumerate(personas, 1):
        persona_id = persona['id']
        label = persona.get('label', persona_id)
        blurb = persona.get('blurb', '')
        tags = ', '.join(persona.get('psychographic_tags', []))
        
        # Check if this persona is actually trained
        status = "✅ Trained" if persona_id in available_personas else "❌ Not trained"
        
        print(f"\n{i:2d}. {label} {status}")
        print(f"    ID: {persona_id}")
        print(f"    {blurb}")
        print(f"    Tags: {tags}")

def main():
    parser = argparse.ArgumentParser(description="Versioned persona interaction")
    parser.add_argument("--version", type=str, help="Specific version to use")
    parser.add_argument("--list-versions", action="store_true", help="List available versions")
    parser.add_argument("--list-personas", action="store_true", help="List personas for version")
    parser.add_argument("--persona", type=str, help="Specific persona to interact with")
    parser.add_argument("--info", action="store_true", help="Show version information")
    
    args = parser.parse_args()
    
    print("🎭 Versioned Persona Interaction")
    print("=" * 50)
    
    # List versions if requested
    if args.list_versions:
        versions = list_available_versions()
        if versions:
            print("\n📋 Available Versions:")
            for version in versions:
                info = get_version_info(version)
                completion = info.get('training_completion', 'Unknown')
                personas = info.get('total_personas', 0)
                print(f"  • {version}: {completion} ({personas} personas)")
        else:
            print("❌ No trained model versions found")
            print("   Run: ./scripts/download_and_organize_models.sh")
        return
    
    # Determine version to use
    if args.version:
        version = args.version
    else:
        # Use latest version
        latest_link = Path("trained_models/latest")
        if latest_link.exists() and latest_link.is_symlink():
            version = latest_link.readlink().name
        else:
            versions = list_available_versions()
            if not versions:
                print("❌ No trained model versions found")
                print("   Run: ./scripts/download_and_organize_models.sh")
                return
            version = versions[0]  # Use newest
    
    print(f"🎯 Using version: {version}")
    
    # Show version info if requested
    if args.info:
        print_version_info(version)
        return
    
    # List personas if requested
    if args.list_personas:
        print_personas_for_version(version)
        return
    
    # Check if version exists
    version_dir = Path("trained_models") / version
    if not version_dir.exists():
        print(f"❌ Version {version} not found")
        print("Available versions:", list_available_versions())
        return
    
    # Set up configuration
    if not setup_interaction_config(version):
        return
    
    # Import and run the main interaction script
    try:
        from interact_cli import main as interact_main
        print(f"\n🚀 Starting interaction with version {version}...")
        print("=" * 60)
        interact_main()
    except ImportError as e:
        print(f"❌ Could not import interaction script: {e}")
        print("Make sure you're running from the project root directory")
    except Exception as e:
        print(f"❌ Error during interaction: {e}")

if __name__ == "__main__":
    main()
