"""
Derive psychographic tags from airline passenger behavior and ratings.
Phase 1.2: Tag passengers with behavioral archetypes.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

import pandas as pd
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def tag_punctuality_sensitive(row: pd.Series) -> bool:
    """
    Tag: Punctuality Sensitive
    Rule: High delay AND low satisfaction OR high time_convenient rating

    Args:
        row: DataFrame row

    Returns:
        True if passenger is punctuality sensitive
    """
    # Check if major delays exist
    has_major_delay = row["delay_band"] in ["moderate", "major"]

    # Check time convenience rating
    time_convenient = row.get("departure_arrival_time_convenient", 0)

    # Satisfied passengers
    is_satisfied = row.get("satisfaction_label", "").lower() == "satisfied"

    # Punctuality sensitive if:
    # 1. Major delay AND dissatisfied
    # 2. High time convenience rating (>= 4)
    return (has_major_delay and not is_satisfied) or (time_convenient >= 4)


def tag_comfort_seeker(row: pd.Series) -> bool:
    """
    Tag: Comfort Seeker
    Rule: High ratings for comfort-related services

    Args:
        row: DataFrame row

    Returns:
        True if passenger is comfort-focused
    """
    comfort_cols = ["seat_comfort", "leg_room_service", "cleanliness"]

    # Check if all comfort columns exist
    if not all(col in row.index for col in comfort_cols):
        return False

    # Get ratings
    ratings = [row[col] for col in comfort_cols if pd.notna(row[col])]

    if not ratings:
        return False

    # Mean rating >= 4.2
    mean_rating = sum(ratings) / len(ratings)
    return mean_rating >= 4.2


def tag_service_reliability(row: pd.Series) -> bool:
    """
    Tag: Service Reliability
    Rule: High ratings for baggage and on-board service

    Args:
        row: DataFrame row

    Returns:
        True if passenger values service reliability
    """
    baggage = row.get("baggage_handling", 0)
    onboard = row.get("on_board_service", 0)

    return baggage >= 4 and onboard >= 4


def tag_digital_first(row: pd.Series) -> bool:
    """
    Tag: Digital First
    Rule: High ratings for digital services (online booking and boarding)

    Args:
        row: DataFrame row

    Returns:
        True if passenger prefers digital channels
    """
    online_booking = row.get("ease_of_online_booking", 0)
    online_boarding = row.get("online_boarding", 0)

    return online_booking >= 4.2 and online_boarding >= 4.2


def tag_value_conscious(row: pd.Series) -> bool:
    """
    Tag: Value Conscious
    Rule: Economy class + Personal travel + moderate rating variance

    Args:
        row: DataFrame row

    Returns:
        True if passenger is value/price conscious
    """
    is_economy = str(row.get("flight_class", "")).lower() in ["eco", "economy", "eco plus"]
    is_personal = "personal" in str(row.get("type_of_travel", "")).lower()

    # Get all service ratings
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

    ratings = [row[col] for col in service_cols if col in row.index and pd.notna(row[col])]

    if not ratings or len(ratings) < 5:
        return is_economy and is_personal

    # Check rating variance (value-conscious passengers have moderate, not extreme variance)
    import numpy as np
    variance = np.var(ratings)

    return is_economy and is_personal and variance <= 0.8


def tag_amenity_lover(row: pd.Series) -> bool:
    """
    Tag: Amenity Lover
    Rule: High ratings for entertainment and food services

    Args:
        row: DataFrame row

    Returns:
        True if passenger values amenities
    """
    entertainment = row.get("inflight_entertainment", 0)
    food_drink = row.get("food_and_drink", 0)

    return entertainment >= 4.2 and food_drink >= 4.2


def tag_business_oriented(row: pd.Series) -> bool:
    """
    Tag: Business Oriented
    Rule: Business travel + high check-in/boarding ratings

    Args:
        row: DataFrame row

    Returns:
        True if passenger has business travel mindset
    """
    is_business = "business" in str(row.get("type_of_travel", "")).lower()
    checkin = row.get("checkin_service", 0)
    boarding = row.get("online_boarding", 0)

    return is_business and checkin >= 4 and boarding >= 4


def derive_psychographic_tags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive all psychographic tags for each passenger.

    Args:
        df: DataFrame with service ratings and demographics

    Returns:
        DataFrame with psychographic tag columns added
    """
    logger.info("=" * 80)
    logger.info("DERIVING PSYCHOGRAPHIC TAGS")
    logger.info("=" * 80)

    df = df.copy()

    # Apply tagging functions
    tag_functions = {
        "punctuality_sensitive": tag_punctuality_sensitive,
        "comfort_seeker": tag_comfort_seeker,
        "service_reliability": tag_service_reliability,
        "digital_first": tag_digital_first,
        "value_conscious": tag_value_conscious,
        "amenity_lover": tag_amenity_lover,
        "business_oriented": tag_business_oriented,
    }

    for tag_name, tag_func in tag_functions.items():
        logger.info(f"Applying tag: {tag_name}")
        df[tag_name] = df.apply(tag_func, axis=1)

        # Log distribution
        count = df[tag_name].sum()
        pct = count / len(df) * 100
        logger.info(f"  {tag_name}: {count} passengers ({pct:.1f}%)")

    # Create a comma-separated list of tags per passenger
    tag_cols = list(tag_functions.keys())
    df["psychographic_tags"] = df.apply(
        lambda row: ",".join([tag for tag in tag_cols if row[tag]]),
        axis=1
    )

    # Log summary
    logger.info("\n📊 Tag Summary:")
    tag_count_dist = df["psychographic_tags"].apply(lambda x: len(x.split(",")) if x else 0)
    logger.info(f"  Mean tags per passenger: {tag_count_dist.mean():.2f}")
    logger.info(f"  Max tags: {tag_count_dist.max()}")
    logger.info(f"  Passengers with no tags: {(tag_count_dist == 0).sum()}")

    logger.info("=" * 80)
    logger.info("✅ TAGS DERIVED")
    logger.info("=" * 80)

    return df


def main():
    """CLI entry point for psychographic tagging."""
    # Paths
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "CONFIGS" / "airline" / "twin_config.yaml"
    data_path = project_root / "DATA" / "airline" / "clean_with_bands.parquet"
    output_path = project_root / "DATA" / "airline" / "clean_with_tags.parquet"

    # Load config
    logger.info(f"Loading config from: {config_path}")
    config = load_config(config_path)

    # Load data
    logger.info(f"Loading data from: {data_path}")
    df = pd.read_parquet(data_path)
    logger.info(f"Loaded {len(df)} samples")

    # Derive tags
    df_with_tags = derive_psychographic_tags(df)

    # Save
    logger.info(f"Saving to: {output_path}")
    df_with_tags.to_parquet(output_path, compression="snappy", index=False)

    logger.info(f"\n✅ Complete! Output: {output_path}")
    logger.info(f"   Total samples: {len(df_with_tags)}")
    logger.info(f"   New columns: 7 tag booleans + psychographic_tags (comma-separated)")


if __name__ == "__main__":
    main()
