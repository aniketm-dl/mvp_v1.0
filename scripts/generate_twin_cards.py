#!/usr/bin/env python3
"""
Generate twin cards from airline passenger data.
Phase 2: Sample diverse passengers and create rich persona cards.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.airline.twin_card import TwinCard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_cohort_priors(cohort_priors_path: Path) -> dict:
    """
    Load cohort priors from JSONL file.

    Args:
        cohort_priors_path: Path to cohort_priors.jsonl

    Returns:
        Dictionary mapping cohort_key -> cohort_prior
    """
    priors_map = {}

    with open(cohort_priors_path, "r") as f:
        for line in f:
            prior = json.loads(line.strip())
            priors_map[prior["cohort_key"]] = prior

    logger.info(f"Loaded {len(priors_map)} cohort priors")
    return priors_map


def sample_diverse_passengers(df: pd.DataFrame, n_samples: int = 12) -> pd.DataFrame:
    """
    Sample diverse passengers from dataset using stratification.

    Args:
        df: DataFrame with all passengers
        n_samples: Number of twin cards to generate

    Returns:
        DataFrame with sampled passengers
    """
    logger.info(f"Sampling {n_samples} diverse passengers...")

    # Strategy: Stratify by satisfaction, class, and travel type
    # This ensures we get a diverse mix

    # Filter to train set only
    if "split_id" in df.columns:
        df_train = df[df["split_id"] == "train"].copy()
        logger.info(f"  Using train set: {len(df_train)} passengers")
    else:
        df_train = df.copy()

    # Add satisfaction_label if not present (derive from y column)
    if "satisfaction_label" not in df_train.columns and "y" in df_train.columns:
        df_train["satisfaction_label"] = df_train["y"].apply(
            lambda x: "satisfied" if x == 1 else "dissatisfied"
        )

    # Stratification columns
    df_train["strata"] = (
        df_train["satisfaction_label"].astype(str) + "_" +
        df_train["flight_class"].astype(str) + "_" +
        df_train["type_of_travel"].astype(str)
    )

    # Sample from each stratum
    strata_counts = df_train["strata"].value_counts()
    logger.info(f"  Found {len(strata_counts)} unique strata")

    # Calculate samples per stratum
    samples_per_stratum = max(1, n_samples // len(strata_counts))

    sampled_dfs = []
    for stratum in strata_counts.index:
        stratum_df = df_train[df_train["strata"] == stratum]

        # Sample
        n_to_sample = min(samples_per_stratum, len(stratum_df))
        sampled = stratum_df.sample(n=n_to_sample, random_state=42)
        sampled_dfs.append(sampled)

    # Combine
    sampled_df = pd.concat(sampled_dfs, ignore_index=True)

    # If we have too many, trim
    if len(sampled_df) > n_samples:
        sampled_df = sampled_df.sample(n=n_samples, random_state=42)

    # If we have too few, add random samples
    if len(sampled_df) < n_samples:
        remaining = n_samples - len(sampled_df)
        # Sample from passengers not already selected
        not_selected = df_train[~df_train["row_id"].isin(sampled_df["row_id"])]
        additional = not_selected.sample(n=min(remaining, len(not_selected)), random_state=42)
        sampled_df = pd.concat([sampled_df, additional], ignore_index=True)

    logger.info(f"  Sampled {len(sampled_df)} passengers")

    # Log diversity
    logger.info("\n📊 Sample diversity:")
    logger.info(f"  Satisfaction: {sampled_df['satisfaction_label'].value_counts().to_dict()}")
    logger.info(f"  Class: {sampled_df['flight_class'].value_counts().to_dict()}")
    logger.info(f"  Travel type: {sampled_df['type_of_travel'].value_counts().to_dict()}")
    logger.info(f"  Gender: {sampled_df['gender'].value_counts().to_dict()}")

    return sampled_df


def generate_twin_cards(
    df_sampled: pd.DataFrame,
    cohort_priors_map: dict,
    output_dir: Path
) -> list[TwinCard]:
    """
    Generate twin cards from sampled passengers.

    Args:
        df_sampled: DataFrame with sampled passengers
        cohort_priors_map: Map of cohort_key -> prior
        output_dir: Directory to save twin card JSON files

    Returns:
        List of generated TwinCard objects
    """
    logger.info("=" * 80)
    logger.info("GENERATING TWIN CARDS")
    logger.info("=" * 80)

    output_dir.mkdir(parents=True, exist_ok=True)

    twin_cards = []

    for idx, (_, row) in enumerate(df_sampled.iterrows(), start=1):
        twin_id = f"twin_{idx:03d}"

        logger.info(f"Creating {twin_id}...")

        # Create twin card
        twin_card = TwinCard.from_passenger_row(
            row=row,
            twin_id=twin_id,
            cohort_priors_map=cohort_priors_map
        )

        # Save to file
        output_path = output_dir / f"{twin_id}.json"
        twin_card.save(output_path)

        logger.info(f"  Label: {twin_card.label}")
        logger.info(f"  Cohort: {twin_card.cohort_key}")
        logger.info(f"  Tags: {', '.join(twin_card.psychographics) if twin_card.psychographics else 'none'}")
        logger.info(f"  Saved: {output_path.name}")

        twin_cards.append(twin_card)

    logger.info("=" * 80)
    logger.info(f"✅ Generated {len(twin_cards)} twin cards")
    logger.info("=" * 80)

    return twin_cards


def main():
    """Main entry point."""
    # Paths
    project_root = Path(__file__).parent.parent
    data_path = project_root / "DATA" / "airline" / "clean_with_tags.parquet"
    cohort_priors_path = project_root / "DATA" / "airline" / "cohorts" / "cohort_priors.jsonl"
    output_dir = project_root / "DATA" / "airline" / "twins"

    # Load data
    logger.info(f"Loading data from: {data_path}")
    df = pd.read_parquet(data_path)
    logger.info(f"Loaded {len(df)} passengers")

    # Load cohort priors
    logger.info(f"Loading cohort priors from: {cohort_priors_path}")
    cohort_priors_map = load_cohort_priors(cohort_priors_path)

    # Sample diverse passengers
    df_sampled = sample_diverse_passengers(df, n_samples=12)

    # Generate twin cards
    twin_cards = generate_twin_cards(df_sampled, cohort_priors_map, output_dir)

    logger.info(f"\n✅ Complete! {len(twin_cards)} twin cards saved to: {output_dir}")

    # List all generated twins
    logger.info("\n📋 Generated twins:")
    for twin in twin_cards:
        logger.info(f"  {twin.id}: {twin.label}")


if __name__ == "__main__":
    main()
