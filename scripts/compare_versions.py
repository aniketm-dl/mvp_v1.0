#!/usr/bin/env python3
"""
Version Comparison Tool

This script compares different versions of trained models to track
improvements across development sprints.

Usage:
    python scripts/compare_versions.py v1.0 v2.0
    python scripts/compare_versions.py --list-versions
    python scripts/compare_versions.py --generate-report
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

def load_version_info(version: str) -> Dict[str, Any]:
    """Load version information from metadata."""
    version_dir = Path("trained_models") / version
    metadata_file = version_dir / "metadata" / "model_inventory.json"
    
    if not metadata_file.exists():
        return {}
    
    with open(metadata_file, 'r') as f:
        return json.load(f)

def list_available_versions() -> List[str]:
    """List all available versions."""
    trained_models_dir = Path("trained_models")
    if not trained_models_dir.exists():
        return []
    
    versions = []
    for item in trained_models_dir.iterdir():
        if item.is_dir() and item.name != "latest" and not item.name.startswith("archive"):
            versions.append(item.name)
    
    return sorted(versions, reverse=True)

def get_version_stats(version: str) -> Dict[str, Any]:
    """Get comprehensive statistics for a version."""
    info = load_version_info(version)
    if not info:
        return {}
    
    version_dir = Path("trained_models") / version
    adapters_dir = version_dir / "adapters"
    
    stats = {
        "version": version,
        "download_date": info.get("download_date", "Unknown"),
        "training_completion": info.get("training_completion", "Unknown"),
        "total_personas": info.get("total_personas", 0),
        "base_model": info.get("base_model", "Unknown"),
        "training_config": info.get("training_config", {}),
        "adapter_sizes": info.get("adapter_sizes", {}),
        "total_size_mb": 0,
        "personas": info.get("personas", []),
        "directory_size": 0
    }
    
    # Calculate total size
    if adapters_dir.exists():
        total_size = 0
        for persona_dir in adapters_dir.iterdir():
            if persona_dir.is_dir():
                size = sum(f.stat().st_size for f in persona_dir.rglob('*') if f.is_file())
                total_size += size
        stats["total_size_mb"] = total_size / (1024 * 1024)
        stats["directory_size"] = total_size / (1024 * 1024)
    
    return stats

def compare_versions(version1: str, version2: str) -> Dict[str, Any]:
    """Compare two versions and return differences."""
    stats1 = get_version_stats(version1)
    stats2 = get_version_stats(version2)
    
    if not stats1 or not stats2:
        return {"error": "One or both versions not found"}
    
    comparison = {
        "version1": stats1,
        "version2": stats2,
        "differences": {}
    }
    
    # Compare key metrics
    metrics = [
        "total_personas",
        "total_size_mb",
        "directory_size"
    ]
    
    for metric in metrics:
        val1 = stats1.get(metric, 0)
        val2 = stats2.get(metric, 0)
        
        if val1 != val2:
            diff = val2 - val1
            comparison["differences"][metric] = {
                "v1": val1,
                "v2": val2,
                "difference": diff,
                "change_percent": (diff / val1 * 100) if val1 != 0 else 0
            }
    
    # Compare personas
    personas1 = set(stats1.get("personas", []))
    personas2 = set(stats2.get("personas", []))
    
    if personas1 != personas2:
        comparison["differences"]["personas"] = {
            "added": list(personas2 - personas1),
            "removed": list(personas1 - personas2),
            "common": list(personas1 & personas2)
        }
    
    # Compare training configs
    config1 = stats1.get("training_config", {})
    config2 = stats2.get("training_config", {})
    
    config_diffs = {}
    for key in set(config1.keys()) | set(config2.keys()):
        if config1.get(key) != config2.get(key):
            config_diffs[key] = {
                "v1": config1.get(key),
                "v2": config2.get(key)
            }
    
    if config_diffs:
        comparison["differences"]["training_config"] = config_diffs
    
    return comparison

def print_version_comparison(comparison: Dict[str, Any]):
    """Print a formatted version comparison."""
    if "error" in comparison:
        print(f"❌ {comparison['error']}")
        return
    
    v1_stats = comparison["version1"]
    v2_stats = comparison["version2"]
    differences = comparison["differences"]
    
    print("=" * 80)
    print("📊 VERSION COMPARISON")
    print("=" * 80)
    print()
    
    print(f"🔄 Comparing: {v1_stats['version']} → {v2_stats['version']}")
    print()
    
    # Basic info
    print("📋 Basic Information:")
    print(f"   Version 1: {v1_stats['version']} ({v1_stats['download_date']})")
    print(f"   Version 2: {v2_stats['version']} ({v2_stats['download_date']})")
    print(f"   Training: {v1_stats['training_completion']} → {v2_stats['training_completion']}")
    print()
    
    # Differences
    if not differences:
        print("✅ No differences found")
        return
    
    print("🔍 Differences:")
    
    # Model metrics
    for metric, diff in differences.items():
        if metric in ["total_personas", "total_size_mb", "directory_size"]:
            change = diff["change_percent"]
            change_str = f"({change:+.1f}%)" if change != 0 else "(no change)"
            print(f"   • {metric}: {diff['v1']} → {diff['v2']} {change_str}")
    
    # Personas
    if "personas" in differences:
        persona_diff = differences["personas"]
        if persona_diff["added"]:
            print(f"   • Added personas: {', '.join(persona_diff['added'])}")
        if persona_diff["removed"]:
            print(f"   • Removed personas: {', '.join(persona_diff['removed'])}")
    
    # Training config
    if "training_config" in differences:
        print("   • Training configuration changes:")
        for key, diff in differences["training_config"].items():
            print(f"     - {key}: {diff['v1']} → {diff['v2']}")
    
    print()

def generate_version_report() -> Dict[str, Any]:
    """Generate a comprehensive report of all versions."""
    versions = list_available_versions()
    
    if not versions:
        return {"error": "No versions found"}
    
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_versions": len(versions),
        "versions": []
    }
    
    for version in versions:
        stats = get_version_stats(version)
        if stats:
            report["versions"].append(stats)
    
    # Sort by download date
    report["versions"].sort(key=lambda x: x.get("download_date", ""), reverse=True)
    
    return report

def print_version_report(report: Dict[str, Any]):
    """Print a formatted version report."""
    if "error" in report:
        print(f"❌ {report['error']}")
        return
    
    print("=" * 80)
    print("📊 VERSION REPORT")
    print("=" * 80)
    print(f"Generated: {report['generated_at']}")
    print(f"Total Versions: {report['total_versions']}")
    print()
    
    for i, version in enumerate(report["versions"], 1):
        print(f"{i:2d}. {version['version']}")
        print(f"    📅 Date: {version['download_date']}")
        print(f"    🎯 Completion: {version['training_completion']}")
        print(f"    👥 Personas: {version['total_personas']}")
        print(f"    💾 Size: {version['total_size_mb']:.1f} MB")
        print(f"    🤖 Base Model: {version['base_model']}")
        
        # Training config summary
        config = version.get("training_config", {})
        if config:
            print(f"    ⚙️  Config: {config.get('epochs', '?')} epochs, "
                  f"LoRA rank {config.get('lora_rank', '?')}, "
                  f"LR {config.get('learning_rate', '?')}")
        print()

def main():
    parser = argparse.ArgumentParser(description="Compare trained model versions")
    parser.add_argument("version1", nargs="?", help="First version to compare")
    parser.add_argument("version2", nargs="?", help="Second version to compare")
    parser.add_argument("--list-versions", action="store_true", help="List all versions")
    parser.add_argument("--generate-report", action="store_true", help="Generate version report")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    args = parser.parse_args()
    
    if args.list_versions:
        versions = list_available_versions()
        if versions:
            print("📋 Available Versions:")
            for version in versions:
                print(f"  • {version}")
        else:
            print("❌ No versions found")
        return
    
    if args.generate_report:
        report = generate_version_report()
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print_version_report(report)
        return
    
    if not args.version1 or not args.version2:
        print("❌ Please provide two versions to compare")
        print("Usage: python scripts/compare_versions.py v1.0 v2.0")
        return
    
    comparison = compare_versions(args.version1, args.version2)
    
    if args.json:
        print(json.dumps(comparison, indent=2))
    else:
        print_version_comparison(comparison)

if __name__ == "__main__":
    main()
