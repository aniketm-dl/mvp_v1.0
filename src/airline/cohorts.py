"""
Compute cohort priors from airline passenger data.
Phase 1.3: Build similarity-based cohorts and compute aggregate statistics.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List

import pandas as pd
import numpy as np
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def build_cohort_key(row: pd.Series, key_fields: List[str]) -> str:
    """
    Build cohort similarity key from row data.

    Args:
        row: DataFrame row
        key_fields: List of fields to include in key

    Returns:
        Cohort key string (e.g., "25-34_Female_Business travel_Business_long")
    """
    key_parts = []
    for field in key_fields:
        value = str(row.get(field, "unknown"))
        # Clean value for key
        value = value.replace(" ", "_").replace("/", "_")
        key_parts.append(value)

    return "_".join(key_parts)


def compute_point_biserial_correlation(
    df: pd.DataFrame,
    continuous_col: str,
    binary_col: str
) -> float:
    """
    Compute point-biserial correlation between continuous and binary variable.

    Args:
        df: DataFrame
        continuous_col: Name of continuous column (e.g., service rating)
        binary_col: Name of binary column (e.g., satisfaction: 0/1)

    Returns:
        Correlation coefficient (-1 to 1)
    """
    if continuous_col not in df.columns or binary_col not in df.columns:
        return 0.0

    # Drop missing values
    valid_data = df[[continuous_col, binary_col]].dropna()

    if len(valid_data) < 5:
        return 0.0

    # Split by binary variable
    group_0 = valid_data[valid_data[binary_col] == 0][continuous_col]
    group_1 = valid_data[valid_data[binary_col] == 1][continuous_col]

    if len(group_0) == 0 or len(group_1) == 0:
        return 0.0

    # Compute means and pooled std
    mean_0 = group_0.mean()
    mean_1 = group_1.mean()

    n = len(valid_data)
    n0 = len(group_0)
    n1 = len(group_1)

    # Pooled standard deviation
    pooled_std = valid_data[continuous_col].std()

    if pooled_std == 0:
        return 0.0

    # Point-biserial correlation formula
    r_pb = ((mean_1 - mean_0) / pooled_std) * np.sqrt((n0 * n1) / (n * n))

    return float(r_pb)


def compute_cohort_priors(
    df: pd.DataFrame,
    cohort_key: str,
    config: dict
) -> Dict:
    """
    Compute priors for a single cohort.

    Args:
        df: DataFrame subset for this cohort
        cohort_key: Cohort key string
        config: Configuration dictionary

    Returns:
        Dictionary with cohort statistics and priors
    """
    n = len(df)

    # Satisfaction rate
    if "y" in df.columns:
        satisfaction_rate = float(df["y"].mean())
    else:
        satisfaction_rate = 0.5

    # Service rating means and stds
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

    rating_means = {}
    rating_stds = {}

    for col in service_cols:
        if col in df.columns:
            rating_means[col] = float(df[col].mean())
            rating_stds[col] = float(df[col].std())

    # Compute drivers (point-biserial correlation with satisfaction)
    drivers = {}
    if "y" in df.columns:
        for col in service_cols:
            if col in df.columns:
                corr = compute_point_biserial_correlation(df, col, "y")
                drivers[col] = corr

    # Sort drivers
    sorted_drivers = sorted(drivers.items(), key=lambda x: x[1], reverse=True)

    # Top positive and negative drivers
    top_positive = [
        {"service": name, "correlation": corr}
        for name, corr in sorted_drivers[:3] if corr > 0
    ]

    top_negative = [
        {"service": name, "correlation": corr}
        for name, corr in sorted_drivers[-3:] if corr < 0
    ]
    top_negative.reverse()  # Most negative first

    # Price sensitivity tier (heuristic based on class and travel type)
    price_sensitivity = "medium"  # default

    if n > 0:
        # Check predominant class and travel type
        if "flight_class" in df.columns:
            mode_class = df["flight_class"].mode()[0] if len(df["flight_class"].mode()) > 0 else ""
            if mode_class.lower() in ["eco", "economy"]:
                price_sensitivity = "high"
            elif mode_class.lower() == "business":
                price_sensitivity = "low"

        if "type_of_travel" in df.columns:
            mode_travel = df["type_of_travel"].mode()[0] if len(df["type_of_travel"].mode()) > 0 else ""
            if "personal" in mode_travel.lower():
                # Personal travel tends to be more price sensitive
                if price_sensitivity == "medium":
                    price_sensitivity = "high"

    # Discount ladder (from config)
    discount_ladders = config.get("discount_ladders", {})

    # Determine dominant psychographic tags for this cohort
    tag_cols = [
        "punctuality_sensitive",
        "comfort_seeker",
        "service_reliability",
        "digital_first",
        "value_conscious",
        "amenity_lover",
        "business_oriented"
    ]

    dominant_tags = []
    for tag in tag_cols:
        if tag in df.columns:
            tag_pct = df[tag].mean()
            if tag_pct >= 0.3:  # At least 30% of cohort has this tag
                dominant_tags.append(tag)

    # Build discount ladder hints based on dominant tags
    ladder_hints = {}
    for offer_type, offer_ladders in discount_ladders.items():
        # Check if any dominant tag has a specific ladder
        for tag in dominant_tags:
            if tag in offer_ladders:
                ladder_hints[offer_type] = offer_ladders[tag]
                break
        # Use default if no match
        if offer_type not in ladder_hints and "default" in offer_ladders:
            ladder_hints[offer_type] = offer_ladders["default"]

    # Build prior object
    prior = {
        "cohort_key": cohort_key,
        "n": n,
        "satisfaction_rate": round(satisfaction_rate, 3),
        "rating_means": {k: round(v, 2) for k, v in rating_means.items()},
        "rating_stds": {k: round(v, 2) for k, v in rating_stds.items()},
        "top_positive_drivers": top_positive,
        "top_negative_drivers": top_negative,
        "price_sensitivity": price_sensitivity,
        "dominant_tags": dominant_tags,
        "discount_ladder_hints": ladder_hints
    }

    return prior


def compute_all_cohort_priors(
    df: pd.DataFrame,
    config: dict
) -> List[Dict]:
    """
    Compute priors for all cohorts in the dataset.

    Args:
        df: DataFrame with all passengers
        config: Configuration dictionary

    Returns:
        List of cohort prior dictionaries
    """
    logger.info("=" * 80)
    logger.info("COMPUTING COHORT PRIORS")
    logger.info("=" * 80)

    key_fields = config["cohort"]["key_fields"]
    min_cohort_size = config["cohort"]["min_cohort_size"]

    # Build cohort key for each passenger
    logger.info(f"Building cohort keys from fields: {key_fields}")
    df["cohort_key"] = df.apply(lambda row: build_cohort_key(row, key_fields), axis=1)

    # Group by cohort
    cohort_groups = df.groupby("cohort_key")
    logger.info(f"Found {len(cohort_groups)} unique cohorts")

    # Compute priors for each cohort
    priors = []

    for cohort_key, cohort_df in cohort_groups:
        cohort_size = len(cohort_df)

        if cohort_size < min_cohort_size:
            logger.debug(f"  Skipping {cohort_key} (n={cohort_size}, too small)")
            continue

        logger.info(f"  Computing priors for {cohort_key} (n={cohort_size})")

        prior = compute_cohort_priors(cohort_df, cohort_key, config)
        priors.append(prior)

    logger.info(f"\n✅ Computed priors for {len(priors)} cohorts (min size: {min_cohort_size})")

    # Log summary stats
    cohort_sizes = [p["n"] for p in priors]
    logger.info(f"  Mean cohort size: {np.mean(cohort_sizes):.1f}")
    logger.info(f"  Median cohort size: {np.median(cohort_sizes):.1f}")
    logger.info(f"  Smallest cohort: {min(cohort_sizes)}")
    logger.info(f"  Largest cohort: {max(cohort_sizes)}")

    logger.info("=" * 80)
    logger.info("✅ COHORT PRIORS COMPLETE")
    logger.info("=" * 80)

    return priors


def main():
    """CLI entry point for cohort prior computation."""
    # Paths
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "CONFIGS" / "airline" / "twin_config.yaml"
    data_path = project_root / "DATA" / "airline" / "clean_with_tags.parquet"
    output_path = project_root / "DATA" / "airline" / "cohorts" / "cohort_priors.jsonl"

    # Load config
    logger.info(f"Loading config from: {config_path}")
    config = load_config(config_path)

    # Load data
    logger.info(f"Loading data from: {data_path}")
    df = pd.read_parquet(data_path)
    logger.info(f"Loaded {len(df)} samples")

    # Compute cohort priors
    priors = compute_all_cohort_priors(df, config)

    # Save as JSONL
    logger.info(f"Saving to: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        for prior in priors:
            f.write(json.dumps(prior) + "\n")

    logger.info(f"\n✅ Complete! Output: {output_path}")
    logger.info(f"   Total cohorts: {len(priors)}")


if __name__ == "__main__":
    main()
