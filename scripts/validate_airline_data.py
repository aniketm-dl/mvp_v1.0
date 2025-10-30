#!/usr/bin/env python3
"""
Validate airline dataset and generate basic statistics.
Phase 0: Data validation for LLM-based digital twin simulator.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def validate_data(data_path: Path) -> dict:
    """
    Validate airline dataset and return statistics.

    Args:
        data_path: Path to demo_airline.parquet

    Returns:
        Dictionary with validation results and statistics
    """
    print("=" * 80)
    print("AIRLINE DATA VALIDATION")
    print("=" * 80)

    # Load data
    print(f"\n📂 Loading data from: {data_path}")
    df = pd.read_parquet(data_path)

    # Basic stats
    stats = {
        "total_samples": len(df),
        "total_columns": len(df.columns),
        "columns": list(df.columns),
    }

    print(f"✓ Loaded {stats['total_samples']} samples with {stats['total_columns']} columns")

    # Check for split
    if "split_id" in df.columns:
        split_counts = df["split_id"].value_counts().to_dict()
        stats["split_counts"] = split_counts
        print(f"\n📊 Split distribution:")
        for split, count in split_counts.items():
            print(f"  {split}: {count} samples ({count/len(df)*100:.1f}%)")

    # Check satisfaction labels
    if "satisfaction_label" in df.columns:
        label_counts = df["satisfaction_label"].value_counts().to_dict()
        stats["satisfaction_distribution"] = label_counts
        print(f"\n😊 Satisfaction distribution:")
        for label, count in label_counts.items():
            print(f"  {label}: {count} ({count/len(df)*100:.1f}%)")

    # Check demographics
    demographics = ["gender", "customer_type", "age", "type_of_travel", "flight_class"]
    print(f"\n👤 Demographics:")
    stats["demographics"] = {}

    for col in demographics:
        if col not in df.columns:
            print(f"  ⚠️  {col}: MISSING")
            continue

        if col == "age":
            age_stats = {
                "min": int(df[col].min()),
                "max": int(df[col].max()),
                "mean": float(df[col].mean()),
                "median": float(df[col].median())
            }
            stats["demographics"][col] = age_stats
            print(f"  {col}: {age_stats['min']}-{age_stats['max']} (mean: {age_stats['mean']:.1f})")
        else:
            value_counts = df[col].value_counts().to_dict()
            stats["demographics"][col] = value_counts
            print(f"  {col}: {', '.join([f'{k}={v}' for k, v in list(value_counts.items())[:3]])}")

    # Check service ratings (1-5 scale)
    service_cols = [
        "inflight_wifi_service",
        "departure_arrival_time_convenient",
        "ease_of_online_booking",
        "gate_location",
        "food_and_drink",
        "online_boarding",
        "seat_comfort",
        "inflight_entertainment",
        "on_board_service",
        "leg_room_service",
        "baggage_handling",
        "checkin_service",
        "inflight_service",
        "cleanliness"
    ]

    print(f"\n⭐ Service Ratings (14 items, 1-5 scale):")
    stats["service_ratings"] = {}

    available_ratings = [col for col in service_cols if col in df.columns]
    print(f"  Found {len(available_ratings)}/{len(service_cols)} rating columns")

    for col in available_ratings:
        mean_rating = df[col].mean()
        std_rating = df[col].std()
        stats["service_ratings"][col] = {
            "mean": float(mean_rating),
            "std": float(std_rating)
        }

    # Show top and bottom rated services
    if available_ratings:
        rating_means = {col: df[col].mean() for col in available_ratings}
        sorted_ratings = sorted(rating_means.items(), key=lambda x: x[1], reverse=True)

        print(f"\n  Top 3 rated services:")
        for col, mean_val in sorted_ratings[:3]:
            print(f"    {col}: {mean_val:.2f}")

        print(f"\n  Bottom 3 rated services:")
        for col, mean_val in sorted_ratings[-3:]:
            print(f"    {col}: {mean_val:.2f}")

    # Check flight details
    print(f"\n✈️  Flight Details:")
    flight_cols = ["flight_distance", "departure_delay_minutes", "arrival_delay_minutes"]
    stats["flight_details"] = {}

    for col in flight_cols:
        if col in df.columns:
            col_stats = {
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "mean": float(df[col].mean()),
                "median": float(df[col].median())
            }
            stats["flight_details"][col] = col_stats
            print(f"  {col}: min={col_stats['min']:.0f}, max={col_stats['max']:.0f}, mean={col_stats['mean']:.1f}")

    # Check for missing values
    print(f"\n🔍 Missing Values:")
    missing = df.isnull().sum()
    missing_cols = missing[missing > 0]

    if len(missing_cols) > 0:
        stats["missing_values"] = missing_cols.to_dict()
        for col, count in missing_cols.items():
            print(f"  {col}: {count} ({count/len(df)*100:.1f}%)")
    else:
        print("  ✓ No missing values!")
        stats["missing_values"] = {}

    print("\n" + "=" * 80)
    print("✅ VALIDATION COMPLETE")
    print("=" * 80)

    return stats


def main():
    """Main entry point."""
    # Path to dataset
    data_path = Path(__file__).parent.parent / "DATA" / "airline" / "demo_airline.parquet"

    if not data_path.exists():
        print(f"❌ Error: Dataset not found at {data_path}")
        return 1

    # Validate and get stats
    stats = validate_data(data_path)

    # Save stats to JSON
    stats_path = data_path.parent / "validation_stats.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"\n💾 Statistics saved to: {stats_path}")

    return 0


if __name__ == "__main__":
    exit(main())
