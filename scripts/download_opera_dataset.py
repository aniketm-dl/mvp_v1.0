#!/usr/bin/env python3
"""
Download OPeRA dataset from Hugging Face and prepare for twin discovery.
"""

from datasets import load_dataset
import pandas as pd
from pathlib import Path

def main():
    print("📥 Downloading OPeRA dataset from Hugging Face...")
    print("   Dataset: wang-ziyi/OPeRA")
    print("   This may take a few minutes...\n")

    # Download user data (contains survey/personality info)
    print("1️⃣ Loading filtered_user data...")
    user_ds = load_dataset("wang-ziyi/OPeRA", "filtered_user", split="train")
    user_df = user_ds.to_pandas()
    print(f"   ✅ Loaded {len(user_df)} users")

    # Download action data (contains actual shopping behavior)
    print("2️⃣ Loading filtered_action data...")
    action_ds = load_dataset("wang-ziyi/OPeRA", "filtered_action", split="train")
    action_df = action_ds.to_pandas()
    print(f"   ✅ Loaded {len(action_df)} actions")

    # Download session data
    print("3️⃣ Loading filtered_session data...")
    session_ds = load_dataset("wang-ziyi/OPeRA", "filtered_session", split="train")
    session_df = session_ds.to_pandas()
    print(f"   ✅ Loaded {len(session_df)} sessions\n")

    # Save to local parquet files for processing
    out_dir = Path("DATA/opera/processed")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("💾 Saving to local files...")
    user_df.to_parquet(out_dir / "users.parquet", index=False)
    action_df.to_parquet(out_dir / "actions.parquet", index=False)
    session_df.to_parquet(out_dir / "sessions.parquet", index=False)

    print(f"   ✅ Saved to {out_dir}/\n")

    # Show summary
    print("📊 Dataset Summary:")
    print(f"   Users: {len(user_df)}")
    print(f"   Sessions: {len(session_df)}")
    print(f"   Actions: {len(action_df)}")
    print(f"   Actions per user: {len(action_df) / len(user_df):.1f}")
    print(f"   Sessions per user: {len(session_df) / len(user_df):.1f}\n")

    # Show user columns
    print("👤 User data columns:")
    for col in user_df.columns:
        print(f"   - {col}")

    print("\n✅ Download complete!")
    print(f"📁 Data saved to: {out_dir.absolute()}")

if __name__ == "__main__":
    main()
