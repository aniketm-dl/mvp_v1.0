#!/usr/bin/env python3
"""
Migrate Legacy Personas to V2 Schema

Converts DATA/personas.json (v1 format) to individual persona files under DATA/personas/
following the new persona.schema.json specification.

This is a one-time migration script. After running, the legacy file can be deprecated.

Usage:
    python scripts/personas/migrate_v1_personas.py
    python scripts/personas/migrate_v1_personas.py --dry-run  # Preview without writing
"""

from __future__ import annotations
import json
import sys
from pathlib import Path
from datetime import date
from typing import Dict, List, Any
import argparse


# Mapping from old shopping_values to new enum values
VALUE_MAPPING = {
    "savings": "price",
    "value": "value",
    "best_price": "price",
    "quality": "quality",
    "reliability": "quality",
    "brand_reputation": "brand",
    "excitement": "novelty",
    "novelty": "novelty",
    "instant_gratification": "convenience",
    "information": "quality",
    "validation": "social_proof",
    "confidence": "quality",
    "speed": "speed",
    "ease": "convenience",
    "reliability": "quality",
    "sustainability": "sustainability",
    "ethics": "sustainability",
    "impact": "sustainability",
    "innovation": "novelty",
    "status": "prestige",
    "bulk_savings": "price",
    "efficiency": "convenience",
    "preparedness": "convenience",
    "comprehensive_info": "quality",
    "rational_choice": "quality",
    "mobile_experience": "convenience",
    "simplicity": "convenience",
    "automation": "convenience",
    "consistency": "quality",
    "flexibility": "convenience",
    "current_value": "value",
    "options": "novelty",
    "uniqueness": "novelty",
    "emotion": "novelty",
    "meaning": "prestige",
    "necessity": "price",
    "longevity": "quality",
    "local_impact": "sustainability",
    "authenticity": "brand",
    "community": "social_proof",
    "thoughtfulness": "quality",
    "presentation": "brand",
    "social_proof": "social_proof",
    "popularity": "social_proof",
    "recommendations": "social_proof",
    "affordability": "price",
}


def normalize_shopping_values(old_values: List[str]) -> List[str]:
    """Convert old shopping values to new enum values."""
    new_values = []
    seen = set()

    for val in old_values:
        mapped = VALUE_MAPPING.get(val, val)
        if mapped not in seen:
            new_values.append(mapped)
            seen.add(mapped)

    return new_values


def infer_demographics(persona_id: str, old_data: Dict[str, Any]) -> Dict[str, str]:
    """Infer demographics from persona characteristics."""
    # Default demographics
    demos = {
        "age_range": "25-34",  # Default to specific middle range
        "region": "north_america",  # Default region
        "income_bracket": "middle",  # Default income
    }

    # Infer from persona characteristics
    persona_lower = persona_id.lower()
    tags = old_data.get("psychographic_tags", [])

    # Age inference
    if "young" in persona_lower or "mobile" in persona_lower:
        demos["age_range"] = "18-24"
    elif "senior" in persona_lower or "traditional" in persona_lower:
        demos["age_range"] = "55-64"
    elif "budget" in persona_lower or "comparison" in persona_lower:
        demos["age_range"] = "35-44"  # Slightly older, more established
    else:
        demos["age_range"] = "25-34"  # Default young professional

    # Income inference
    if "premium" in persona_lower or "luxury" in persona_lower:
        demos["income_bracket"] = "high"
    elif "budget" in persona_lower or "bargain" in persona_lower:
        demos["income_bracket"] = "lower_middle"
    elif "affluent" in tags or old_data.get("label", "").lower().find("premium") >= 0:
        demos["income_bracket"] = "upper_middle"

    return demos


def infer_price_sensitivity(persona_id: str, old_data: Dict[str, Any]) -> Dict[str, Any]:
    """Infer price sensitivity from persona characteristics."""
    persona_lower = persona_id.lower()
    constraints = old_data.get("decision_constraints", "").lower()

    if "bargain" in persona_lower or "budget" in persona_lower or "price" in constraints:
        return {
            "level": "very_high",
            "threshold_low_usd": 20.0,
            "threshold_high_usd": 100.0,
        }
    elif "premium" in persona_lower or "luxury" in persona_lower:
        return {
            "level": "very_low",
            "threshold_low_usd": 100.0,
            "threshold_high_usd": 1000.0,
        }
    else:
        return {
            "level": "medium",
            "threshold_low_usd": 50.0,
            "threshold_high_usd": 300.0,
        }


def generate_decision_heuristics(old_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate decision heuristics from old format."""
    constraints = old_data.get("decision_constraints", "")
    typical_behavior = old_data.get("typical_behavior", "")
    shopping_values = old_data.get("shopping_values", [])

    heuristics = []

    # Parse constraints into heuristics
    if "price" in constraints.lower():
        heuristics.append({
            "if": "multiple options with similar quality",
            "then": "choose the lowest price option",
            "because": "price optimization is primary decision factor",
            "priority": 1
        })

    if "brand" in constraints.lower() or "premium" in old_data.get("label", "").lower():
        heuristics.append({
            "if": "brand is well-known and trusted",
            "then": "prefer that brand even at higher price",
            "because": "brand reputation signals quality and reliability",
            "priority": 2
        })

    if "quality" in " ".join(shopping_values):
        heuristics.append({
            "if": "product has high review ratings",
            "then": "prioritize it over lower-rated alternatives",
            "because": "quality validation through social proof is important",
            "priority": 3
        })

    if "speed" in " ".join(shopping_values) or "fast" in typical_behavior.lower():
        heuristics.append({
            "if": "delivery time differs by more than 2 days",
            "then": "choose faster delivery option",
            "because": "time savings are highly valued",
            "priority": 4
        })

    # Add generic heuristics to reach minimum of 5
    while len(heuristics) < 5:
        heuristics.append({
            "if": "options are equivalent on primary values",
            "then": "choose based on next priority value",
            "because": "systematic decision making requires tie-breakers",
            "priority": len(heuristics) + 1
        })

    return heuristics[:10]  # Cap at 10


def generate_evaluation_probes(old_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate evaluation probes covering required categories."""
    persona_name = old_data.get("label", "This persona")
    constraints = old_data.get("decision_constraints", "")

    probes = [
        {
            "category": "price",
            "prompt": "Product A costs $50 and Product B costs $80. Both have similar features. Which do you choose?",
            "expected_behavior": f"{persona_name} should evaluate based on price sensitivity"
        },
        {
            "category": "promo",
            "prompt": "Product X is regular price but Product Y has a '20% off today only' badge. How do you respond?",
            "expected_behavior": f"{persona_name} should react to promotional urgency appropriately"
        },
        {
            "category": "delivery",
            "prompt": "Option 1: Free shipping in 5 days. Option 2: $10 shipping, arrives tomorrow. Which do you prefer?",
            "expected_behavior": f"{persona_name} should balance speed vs cost based on delivery preferences"
        },
        {
            "category": "ad_copy",
            "prompt": "Product description says 'Premium Quality' vs 'Best Value'. Which phrase appeals more?",
            "expected_behavior": f"{persona_name} should respond to copy aligned with shopping values"
        },
        {
            "category": "returns",
            "prompt": "Product A has 30-day returns, Product B has 90-day returns. Does this affect your choice?",
            "expected_behavior": f"{persona_name} should consider return policy based on risk tolerance"
        },
        {
            "category": "risk",
            "prompt": "Would you buy from a new seller with no reviews if price is 30% lower?",
            "expected_behavior": f"{persona_name} should respond based on risk tolerance and price sensitivity"
        },
    ]

    return probes


def migrate_persona(old_persona: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a single persona from v1 to v2 format."""
    persona_id = old_persona["id"]

    # Convert ocean_scores to required format (normalize to -2 to +2 range)
    old_ocean = old_persona.get("ocean_scores", {})
    new_ocean = {
        key: round((val - 0.5) * 4, 1)  # Map 0-1 to -2 to +2
        for key, val in old_ocean.items()
    }

    # Infer risk tolerance and brand loyalty from psychographics
    tags = old_persona.get("psychographic_tags", [])
    risk_tolerance = "high" if "spontaneous" in tags or "risk" in tags else "medium"
    brand_loyalty = "high" if "brand_loyal" in tags or "loyal" in tags else "medium"

    # Build new persona
    new_persona = {
        "persona_id": persona_id,
        "name": old_persona.get("label", persona_id.replace("_", " ").title()),
        "version": "1.0.0",
        "last_updated": date.today().isoformat(),
        "author": "darpan-labs",
        "demographics": infer_demographics(persona_id, old_persona),
        "psychographics": {
            "big_five": new_ocean,
            "risk_tolerance": risk_tolerance,
            "brand_loyalty": brand_loyalty,
        },
        "shopping_values": normalize_shopping_values(old_persona.get("shopping_values", [])),
        "constraints": [
            old_persona.get("decision_constraints", "No specific constraints"),
            old_persona.get("typical_behavior", "Standard shopping behavior"),
        ],
        "style_capsule": {
            "person_view": "first",
            "target_length": "3-6 sentences",
            "include_example": True,
            "tone_notes": old_persona.get("psychographic_tags", ["neutral"])[:5],
            "slang_allowance": "minimal",
            "taboo_topics": [],
        },
        "decision_heuristics": generate_decision_heuristics(old_persona),
        "channel_prefs": ["app", "search", "email"],  # Default channels
        "delivery_prefs": {
            "speed_vs_cost": "balanced",
            "acceptable_delay_days": 5,
        },
        "price_sensitivity": infer_price_sensitivity(persona_id, old_persona),
        "evaluation_probes": generate_evaluation_probes(old_persona),
        "embedding_seed": old_persona.get("cluster_id", 0) * 100 + 17,  # Deterministic seed
        "rag_filters": {
            "include_tags": old_persona.get("psychographic_tags", []),
            "exclude_tags": [],
            "boost_keywords": old_persona.get("shopping_values", []),
        },
        "safety": {
            "forbidden_categories": ["violence", "hate_speech", "explicit_content"],
            "brand_safety_notes": "General brand-safe guidelines apply",
        },
    }

    return new_persona


def main() -> int:
    """Main migration logic."""
    parser = argparse.ArgumentParser(description="Migrate v1 personas to v2 schema")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migration without writing files",
    )
    parser.add_argument(
        "--legacy-file",
        type=Path,
        default=Path("DATA/personas.json"),
        help="Path to legacy personas.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("DATA/personas"),
        help="Output directory for new persona files",
    )

    args = parser.parse_args()

    # Check legacy file exists
    if not args.legacy_file.exists():
        print(f"❌ Legacy file not found: {args.legacy_file}")
        return 1

    # Load legacy personas
    print(f"📖 Reading legacy personas from {args.legacy_file}")
    with open(args.legacy_file) as f:
        legacy_data = json.load(f)

    personas_list = legacy_data.get("personas", [])
    print(f"Found {len(personas_list)} personas to migrate")

    # Migrate each persona
    registry = []
    migrated = 0

    for old_persona in personas_list:
        persona_id = old_persona["id"]
        print(f"\n🔄 Migrating {persona_id}...")

        try:
            new_persona = migrate_persona(old_persona)

            # Add to registry
            registry.append({
                "persona_id": persona_id,
                "name": new_persona["name"],
                "version": new_persona["version"],
                "last_updated": new_persona["last_updated"],
            })

            if not args.dry_run:
                # Write individual persona file
                output_file = args.output_dir / f"{persona_id}.json"
                output_file.parent.mkdir(parents=True, exist_ok=True)

                with open(output_file, "w") as f:
                    json.dump(new_persona, f, indent=2, ensure_ascii=False)

                print(f"  ✅ Wrote {output_file}")
            else:
                print(f"  [DRY RUN] Would write {args.output_dir / f'{persona_id}.json'}")

            migrated += 1

        except Exception as e:
            print(f"  ❌ Failed to migrate {persona_id}: {e}")

    # Write registry
    if not args.dry_run:
        registry_file = args.output_dir / "registry.json"
        with open(registry_file, "w") as f:
            json.dump({"personas": registry, "count": len(registry)}, f, indent=2)
        print(f"\n✅ Wrote registry: {registry_file}")
    else:
        print(f"\n[DRY RUN] Would write registry with {len(registry)} personas")

    # Summary
    print("\n" + "=" * 70)
    print(f"Migration complete: {migrated}/{len(personas_list)} personas")
    if args.dry_run:
        print("DRY RUN - No files were written")
    else:
        print(f"Files written to {args.output_dir}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
