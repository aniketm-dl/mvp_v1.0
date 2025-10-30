"""
Create demographic and flight bands for airline passengers.
Phase 1.1: Band creation for cohort grouping.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

import pandas as pd
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def create_age_bands(df: pd.DataFrame, age_bands_config: List[Dict]) -> pd.DataFrame:
    """
    Create age bands from age column.

    Args:
        df: DataFrame with 'age' column
        age_bands_config: List of band definitions from config

    Returns:
        DataFrame with 'age_band' column added
    """
    logger.info("Creating age bands...")

    def assign_age_band(age: int) -> str:
        for band in age_bands_config:
            if band["min"] <= age <= band["max"]:
                return band["label"]
        return "unknown"

    df["age_band"] = df["age"].apply(assign_age_band)

    # Log distribution
    band_counts = df["age_band"].value_counts().to_dict()
    logger.info(f"  Age band distribution: {band_counts}")

    return df


def create_distance_bands(df: pd.DataFrame, distance_bands_config: List[Dict]) -> pd.DataFrame:
    """
    Create distance bands from flight_distance column.

    Args:
        df: DataFrame with 'flight_distance' column
        distance_bands_config: List of band definitions from config

    Returns:
        DataFrame with 'distance_band' column added
    """
    logger.info("Creating distance bands...")

    def assign_distance_band(distance: float) -> str:
        for band in distance_bands_config:
            if band["min"] <= distance <= band["max"]:
                return band["label"]
        return "unknown"

    df["distance_band"] = df["flight_distance"].apply(assign_distance_band)

    # Log distribution
    band_counts = df["distance_band"].value_counts().to_dict()
    logger.info(f"  Distance band distribution: {band_counts}")

    return df


def create_delay_bands(df: pd.DataFrame, delay_bands_config: List[Dict]) -> pd.DataFrame:
    """
    Create delay bands from arrival_delay_minutes column.

    Args:
        df: DataFrame with 'arrival_delay_minutes' column
        delay_bands_config: List of band definitions from config

    Returns:
        DataFrame with 'delay_band' column added
    """
    logger.info("Creating delay bands...")

    def assign_delay_band(delay: float) -> str:
        for band in delay_bands_config:
            if band["min"] <= delay <= band["max"]:
                return band["label"]
        return "unknown"

    df["delay_band"] = df["arrival_delay_minutes"].apply(assign_delay_band)

    # Log distribution
    band_counts = df["delay_band"].value_counts().to_dict()
    logger.info(f"  Delay band distribution: {band_counts}")

    return df


def add_all_bands(
    df: pd.DataFrame,
    config: dict
) -> pd.DataFrame:
    """
    Add all demographic and flight bands to DataFrame.

    Args:
        df: Input DataFrame
        config: Configuration dictionary

    Returns:
        DataFrame with all bands added
    """
    logger.info("=" * 80)
    logger.info("CREATING BANDS")
    logger.info("=" * 80)

    df = df.copy()

    # Add bands
    df = create_age_bands(df, config["age_bands"])
    df = create_distance_bands(df, config["distance_bands"])
    df = create_delay_bands(df, config["delay_bands"])

    logger.info("=" * 80)
    logger.info("✅ BANDS CREATED")
    logger.info("=" * 80)

    return df


def main():
    """CLI entry point for band creation."""
    from pathlib import Path

    # Paths
    project_root = Path(__file__).parent.parent.parent
    config_path = project_root / "CONFIGS" / "airline" / "twin_config.yaml"
    data_path = project_root / "DATA" / "airline" / "demo_airline.parquet"
    output_path = project_root / "DATA" / "airline" / "clean_with_bands.parquet"

    # Load config
    logger.info(f"Loading config from: {config_path}")
    config = load_config(config_path)

    # Load data
    logger.info(f"Loading data from: {data_path}")
    df = pd.read_parquet(data_path)
    logger.info(f"Loaded {len(df)} samples")

    # Add bands
    df_with_bands = add_all_bands(df, config)

    # Save
    logger.info(f"Saving to: {output_path}")
    df_with_bands.to_parquet(output_path, compression="snappy", index=False)

    logger.info(f"\n✅ Complete! Output: {output_path}")
    logger.info(f"   Total samples: {len(df_with_bands)}")
    logger.info(f"   New columns: age_band, distance_band, delay_band")


if __name__ == "__main__":
    main()
