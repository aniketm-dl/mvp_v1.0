#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def resplit_airline_data(
    input_path: str,
    output_path: str,
    test_size: float = 0.2,
    seed: int = 42
) -> None:
    """
    Resplit airline data to exact 80-20 train/test split.

    Args:
        input_path: Path to existing parquet file
        output_path: Path for output parquet file
        test_size: Fraction for test set (default 0.2 for 80-20 split)
        seed: Random seed for reproducibility
    """
    logger.info("=" * 80)
    logger.info("AIRLINE DATA RESPLITTING")
    logger.info("=" * 80)

    # Load existing data
    logger.info(f"Loading data from {input_path}")
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} rows")

    # Remove old split_id if exists
    if "split_id" in df.columns:
        df = df.drop(columns=["split_id"])
        logger.info("Removed old split_id column")

    # Verify we have target column
    if "y" not in df.columns:
        raise ValueError("Target column 'y' not found in dataset")

    # Drop rows with missing target
    initial_rows = len(df)
    df = df.dropna(subset=["y"])
    rows_dropped = initial_rows - len(df)

    if rows_dropped > 0:
        logger.warning(f"Dropped {rows_dropped} rows with missing target")

    logger.info(f"Dataset size: {len(df)} rows")
    logger.info(f"Target distribution: {df['y'].value_counts().to_dict()}")

    # Stratified split
    logger.info(f"Performing stratified split (test_size={test_size}, seed={seed})")

    try:
        train_idx, test_idx = train_test_split(
            df.index,
            test_size=test_size,
            stratify=df["y"],
            random_state=seed
        )

        df["split_id"] = "train"
        df.loc[test_idx, "split_id"] = "test"
        df["split_id"] = df["split_id"].astype("category")

        # Verify split ratios
        train_df = df[df["split_id"] == "train"]
        test_df = df[df["split_id"] == "test"]

        train_ratio = train_df["y"].mean()
        test_ratio = test_df["y"].mean()
        ratio_diff = abs(train_ratio - test_ratio)

        logger.info("=" * 80)
        logger.info("SPLIT COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Train: {len(train_df)} rows ({len(train_df)/len(df)*100:.1f}%)")
        logger.info(f"  y=1: {(train_df['y']==1).sum()} ({train_ratio*100:.1f}%)")
        logger.info(f"  y=0: {(train_df['y']==0).sum()} ({(1-train_ratio)*100:.1f}%)")
        logger.info(f"Test:  {len(test_df)} rows ({len(test_df)/len(df)*100:.1f}%)")
        logger.info(f"  y=1: {(test_df['y']==1).sum()} ({test_ratio*100:.1f}%)")
        logger.info(f"  y=0: {(test_df['y']==0).sum()} ({(1-test_ratio)*100:.1f}%)")
        logger.info(f"Label ratio difference: {ratio_diff:.3f}")

        if ratio_diff > 0.01:
            logger.warning(f"Label ratio difference ({ratio_diff:.3f}) exceeds 1%")

    except ValueError as e:
        logger.error(f"Stratified split failed: {e}")
        raise

    # Save output
    logger.info(f"Saving to {output_path}")
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)

    df.to_parquet(output_path, compression="snappy", index=False)

    file_size = output_path_obj.stat().st_size / (1024 * 1024)
    logger.info(f"Saved {len(df)} rows ({file_size:.2f} MB)")
    logger.info("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Resplit airline data to exact 80-20 train/test split"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="DATA/airline/demo_airline.parquet",
        help="Path to input parquet file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="DATA/airline/demo_airline.parquet",
        help="Path to output parquet file",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Test set proportion (default 0.2 for 80-20 split)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for split",
    )

    args = parser.parse_args()

    resplit_airline_data(
        input_path=args.input,
        output_path=args.output,
        test_size=args.test_size,
        seed=args.seed
    )


if __name__ == "__main__":
    main()
