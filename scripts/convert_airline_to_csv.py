#!/usr/bin/env python3
"""
Convert airline parquet files to CSV for easy inspection.

This script converts all airline-related parquet files to CSV format,
making it easy to open in Excel, Numbers, or any CSV viewer.

Usage:
    python scripts/convert_airline_to_csv.py

Output:
    - DATA/airline/csv/demo_airline.csv
    - DATA/airline/csv/clean_with_bands.csv
    - DATA/airline/csv/clean_with_tags.csv
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def convert_parquet_to_csv(
    parquet_path: Path,
    csv_path: Path,
    include_index: bool = False
) -> None:
    """
    Convert a parquet file to CSV.

    Args:
        parquet_path: Path to input parquet file
        csv_path: Path to output CSV file
        include_index: Whether to include DataFrame index in CSV
    """
    logger.info(f"Converting {parquet_path.name} to CSV...")

    # Read parquet
    df = pd.read_parquet(parquet_path)

    # Log basic info
    logger.info(f"  Rows: {len(df):,}")
    logger.info(f"  Columns: {len(df.columns)}")

    # Create output directory if needed
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV
    df.to_csv(csv_path, index=include_index)

    # Calculate file sizes
    parquet_size = parquet_path.stat().st_size / 1024
    csv_size = csv_path.stat().st_size / 1024

    logger.info(f"  Saved: {csv_path}")
    logger.info(f"  Size: {parquet_size:.1f}KB (parquet) → {csv_size:.1f}KB (csv)")
    logger.info("")


def main():
    """Convert all airline parquet files to CSV."""

    logger.info("=" * 80)
    logger.info("AIRLINE DATA CONVERTER: Parquet → CSV")
    logger.info("=" * 80)
    logger.info("")

    # Define base paths
    data_dir = Path("DATA/airline")
    csv_dir = data_dir / "csv"

    # Files to convert
    files_to_convert = [
        ("demo_airline.parquet", "demo_airline.csv"),
        ("clean_with_bands.parquet", "clean_with_bands.csv"),
        ("clean_with_tags.parquet", "clean_with_tags.csv"),
    ]

    # Convert each file
    for parquet_file, csv_file in files_to_convert:
        parquet_path = data_dir / parquet_file
        csv_path = csv_dir / csv_file

        if not parquet_path.exists():
            logger.warning(f"⚠️  File not found: {parquet_path}")
            continue

        try:
            convert_parquet_to_csv(parquet_path, csv_path)
        except Exception as e:
            logger.error(f"❌ Error converting {parquet_file}: {e}")
            continue

    # Print summary
    logger.info("=" * 80)
    logger.info("CONVERSION COMPLETE")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"CSV files saved to: {csv_dir}")
    logger.info("")
    logger.info("Next steps:")
    logger.info("  1. Open CSV files in Excel, Numbers, or any spreadsheet app")
    logger.info("  2. Use Python/pandas for analysis:")
    logger.info(f"     df = pd.read_csv('{csv_dir}/demo_airline.csv')")
    logger.info("  3. Generate data summary:")
    logger.info("     python scripts/explore_airline_data.py")
    logger.info("")


if __name__ == "__main__":
    main()
