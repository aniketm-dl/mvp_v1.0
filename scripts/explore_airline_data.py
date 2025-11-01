#!/usr/bin/env python3
"""
Comprehensive exploration of airline dataset.

Generates a detailed data summary report including:
- Dataset overview (shape, columns, dtypes)
- Missing value analysis
- Categorical distribution
- Numerical statistics
- Service ratings distribution
- Correlation analysis
- Satisfaction breakdown

Usage:
    python scripts/explore_airline_data.py --file demo_airline.parquet
    python scripts/explore_airline_data.py --file csv/demo_airline.csv
    python scripts/explore_airline_data.py --all
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Optional

import pandas as pd
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_data(file_path: Path) -> pd.DataFrame:
    """Load data from parquet or CSV."""
    logger.info(f"Loading data from {file_path}...")

    if file_path.suffix == ".parquet":
        df = pd.read_parquet(file_path)
    elif file_path.suffix == ".csv":
        df = pd.read_csv(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")

    logger.info(f"Loaded {len(df):,} rows, {len(df.columns)} columns")
    return df


def print_section(title: str) -> None:
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80 + "\n")


def explore_overview(df: pd.DataFrame) -> None:
    """Print dataset overview."""
    print_section("DATASET OVERVIEW")

    print(f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"Memory Usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
    print("\nColumns:")

    # Group columns by type
    from collections import defaultdict
    dtype_groups = defaultdict(list)
    for col, dtype in df.dtypes.items():
        dtype_groups[str(dtype)].append(col)

    for dtype, cols in dtype_groups.items():
        print(f"  {dtype}: {len(cols)} columns")
        print(f"    {', '.join(cols[:5])}" +
              (f" ... (+{len(cols)-5} more)" if len(cols) > 5 else ""))


def explore_missing(df: pd.DataFrame) -> None:
    """Analyze missing values."""
    print_section("MISSING VALUE ANALYSIS")

    missing = df.isnull().sum()
    missing_pct = (missing / len(df)) * 100

    missing_df = pd.DataFrame({
        'Missing': missing,
        'Percent': missing_pct
    })
    missing_df = missing_df[missing_df['Missing'] > 0].sort_values('Missing', ascending=False)

    if len(missing_df) == 0:
        print("✅ No missing values found!")
    else:
        print(f"⚠️  {len(missing_df)} columns with missing values:\n")
        print(missing_df.to_string())


def explore_categorical(df: pd.DataFrame) -> None:
    """Explore categorical columns."""
    print_section("CATEGORICAL DISTRIBUTIONS")

    # Identify categorical columns
    cat_cols = df.select_dtypes(include=['object', 'category']).columns

    for col in cat_cols:
        if col in ['row_id', 'split_id']:
            continue

        print(f"\n{col}:")
        value_counts = df[col].value_counts()

        for val, count in value_counts.items():
            pct = (count / len(df)) * 100
            print(f"  {val:30s} {count:6,} ({pct:5.1f}%)")


def explore_numerical(df: pd.DataFrame) -> None:
    """Explore numerical columns."""
    print_section("NUMERICAL STATISTICS")

    # Identify numerical columns (exclude service ratings for now)
    num_cols = ['age', 'flight_distance', 'departure_delay_minutes', 'arrival_delay_minutes']
    num_cols = [c for c in num_cols if c in df.columns]

    if num_cols:
        stats = df[num_cols].describe().T
        stats['missing'] = df[num_cols].isnull().sum()

        print(stats.to_string())


def explore_service_ratings(df: pd.DataFrame) -> None:
    """Explore service rating distributions."""
    print_section("SERVICE RATINGS (1-5 Scale)")

    # Load service items from schema
    schema_path = Path("DATA/airline/airline_schema.json")
    if schema_path.exists():
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        service_items = schema.get("service_items", [])
    else:
        # Fallback list
        service_items = [
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

    service_items = [s for s in service_items if s in df.columns]

    if not service_items:
        print("⚠️  No service rating columns found")
        return

    print(f"{'Service Item':<40} {'Mean':<8} {'Median':<8} {'Missing':<10}")
    print("-" * 70)

    for item in service_items:
        mean_val = df[item].mean()
        median_val = df[item].median()
        missing = df[item].isnull().sum()

        # Format item name nicely
        display_name = item.replace('_', ' ').title()

        print(f"{display_name:<40} {mean_val:>7.2f} {median_val:>7.0f} {missing:>9,}")


def explore_satisfaction(df: pd.DataFrame) -> None:
    """Analyze satisfaction distribution."""
    print_section("SATISFACTION BREAKDOWN")

    if 'satisfaction_label' in df.columns:
        print("\nBy Label:")
        sat_counts = df['satisfaction_label'].value_counts()
        for label, count in sat_counts.items():
            pct = (count / len(df)) * 100
            print(f"  {label:30s} {count:6,} ({pct:5.1f}%)")

    if 'y' in df.columns:
        print("\nBy Numeric Target (y):")
        y_counts = df['y'].value_counts().sort_index()
        for val, count in y_counts.items():
            pct = (count / len(df)) * 100
            label = "Satisfied" if val == 1 else "Neutral/Dissatisfied"
            print(f"  {label:30s} {count:6,} ({pct:5.1f}%)")


def explore_correlations(df: pd.DataFrame) -> None:
    """Show key correlations with satisfaction."""
    print_section("CORRELATIONS WITH SATISFACTION")

    if 'y' not in df.columns:
        print("⚠️  Target variable 'y' not found")
        return

    # Get numerical columns
    num_cols = df.select_dtypes(include=['int8', 'int16', 'int32', 'int64', 'float64']).columns
    num_cols = [c for c in num_cols if c not in ['row_id', 'y']]

    if not num_cols:
        print("⚠️  No numerical columns found")
        return

    # Calculate correlations
    corrs = df[num_cols + ['y']].corr()['y'].drop('y').sort_values(ascending=False)

    print(f"{'Feature':<40} {'Correlation':<15}")
    print("-" * 55)

    for feature, corr in corrs.items():
        # Format feature name nicely
        display_name = feature.replace('_', ' ').title()
        print(f"{display_name:<40} {corr:>+.3f}")


def explore_psychographic_tags(df: pd.DataFrame) -> None:
    """Explore psychographic tags if available."""
    print_section("PSYCHOGRAPHIC TAGS")

    # Check for tag columns
    tag_cols = [c for c in df.columns if c.endswith('_tag')]

    if not tag_cols:
        print("⚠️  No psychographic tag columns found")
        print("    (These are added by airline_processing.py)")
        return

    for tag in tag_cols:
        print(f"\n{tag}:")
        value_counts = df[tag].value_counts()

        for val, count in value_counts.items():
            pct = (count / len(df)) * 100
            print(f"  {str(val):10s} {count:6,} ({pct:5.1f}%)")


def explore_bucketed_features(df: pd.DataFrame) -> None:
    """Explore bucketed features if available."""
    print_section("BUCKETED FEATURES")

    bucket_cols = [c for c in df.columns if c.endswith('_bucket')]

    if not bucket_cols:
        print("⚠️  No bucket columns found")
        print("    (These are added by airline_processing.py)")
        return

    for bucket in bucket_cols:
        print(f"\n{bucket}:")
        value_counts = df[bucket].value_counts().sort_index()

        for val, count in value_counts.items():
            pct = (count / len(df)) * 100
            print(f"  {val:20s} {count:6,} ({pct:5.1f}%)")


def explore_all(df: pd.DataFrame, file_name: str) -> None:
    """Run all exploration functions."""

    print("\n" + "█" * 80)
    print(f"  AIRLINE DATASET EXPLORATION: {file_name}")
    print("█" * 80)

    explore_overview(df)
    explore_missing(df)
    explore_categorical(df)
    explore_numerical(df)
    explore_service_ratings(df)
    explore_satisfaction(df)
    explore_correlations(df)
    explore_psychographic_tags(df)
    explore_bucketed_features(df)

    print("\n" + "█" * 80)
    print("  EXPLORATION COMPLETE")
    print("█" * 80 + "\n")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Explore airline dataset and generate summary report"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Path to parquet or CSV file (relative to DATA/airline/)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Explore all available files",
    )

    args = parser.parse_args()

    data_dir = Path("DATA/airline")

    if args.all:
        # Explore all available files
        files = [
            "demo_airline.parquet",
            "clean_with_bands.parquet",
            "clean_with_tags.parquet",
        ]

        for file_name in files:
            file_path = data_dir / file_name
            if file_path.exists():
                df = load_data(file_path)
                explore_all(df, file_name)
            else:
                logger.warning(f"⚠️  File not found: {file_path}")

    elif args.file:
        file_path = data_dir / args.file
        if not file_path.exists():
            logger.error(f"❌ File not found: {file_path}")
            return

        df = load_data(file_path)
        explore_all(df, args.file)

    else:
        # Default: explore demo file
        file_path = data_dir / "demo_airline.parquet"
        if not file_path.exists():
            logger.error(f"❌ File not found: {file_path}")
            logger.info("Usage: python scripts/explore_airline_data.py --file <filename>")
            return

        df = load_data(file_path)
        explore_all(df, "demo_airline.parquet")


if __name__ == "__main__":
    main()
