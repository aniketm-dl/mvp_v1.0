#!/usr/bin/env python3
from __future__ import annotations

"""
Download OPeRA dataset from Hugging Face and prepare for SSR training.

OPeRA Dataset: wang-ziyi/OPeRA
- User data: Demographics, personality (OCEAN scores)
- Action data: User interactions (clicks, searches, purchases)
- Session data: Temporal session logs
"""

import json
from pathlib import Path

import pandas as pd
from datasets import load_dataset
from rich.console import Console
from rich.table import Table

console = Console()


def main():
    console.print("\n[bold cyan]📥 Downloading OPeRA Dataset from Hugging Face[/bold cyan]")
    console.print("   Dataset: [bold]wang-ziyi/OPeRA[/bold]")
    console.print("   This may take a few minutes...\n")

    # Create output directories
    raw_dir = Path("DATA/OPeRA/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Download user data (contains survey/personality info)
    console.print("1️⃣  Loading filtered_user data...")
    user_ds = load_dataset("wang-ziyi/OPeRA", "filtered_user", split="train")
    user_df = user_ds.to_pandas()
    console.print(f"   ✅ Loaded {len(user_df)} users")

    # Download action data (contains actual shopping behavior)
    console.print("2️⃣  Loading filtered_action data...")
    action_ds = load_dataset("wang-ziyi/OPeRA", "filtered_action", split="train")
    action_df = action_ds.to_pandas()
    console.print(f"   ✅ Loaded {len(action_df)} actions")

    # Download session data
    console.print("3️⃣  Loading filtered_session data...")
    session_ds = load_dataset("wang-ziyi/OPeRA", "filtered_session", split="train")
    session_df = session_ds.to_pandas()
    console.print(f"   ✅ Loaded {len(session_df)} sessions\n")

    # Save raw data
    console.print("[bold cyan]💾 Saving raw data files...[/bold cyan]")

    # Save user data as parquet (will be used as survey data)
    user_df.to_parquet(raw_dir / "opera_users.parquet", index=False)
    console.print(f"   ✅ Saved: {raw_dir}/opera_users.parquet")

    # Save actions and sessions as parquet
    action_df.to_parquet(raw_dir / "opera_actions.parquet", index=False)
    console.print(f"   ✅ Saved: {raw_dir}/opera_actions.parquet")

    session_df.to_parquet(raw_dir / "opera_sessions.parquet", index=False)
    console.print(f"   ✅ Saved: {raw_dir}/opera_sessions.parquet")

    # Create aligned sessions JSONL (combining session + actions)
    console.print("\n[bold cyan]🔧 Creating aligned session logs...[/bold cyan]")
    sessions_jsonl = []

    for _, session in session_df.iterrows():
        session_id = session.get("session_id", session.get("id", f"sess_{_}"))
        user_id = session.get("user_id", "unknown")
        timestamp = session.get("timestamp", session.get("start_time", "2024-01-01T00:00:00"))

        # Get actions for this session
        session_actions = action_df[action_df["session_id"] == session_id] if "session_id" in action_df.columns else []

        actions_list = []
        for idx, action_row in (session_actions.iterrows() if len(session_actions) > 0 else []):
            actions_list.append({
                "t": idx,
                "action": action_row.get("action_type", action_row.get("action", "click")),
                "action_label": 0,  # Will be mapped later
                "observation": action_row.get("observation", action_row.get("page_content", "Product page")),
                "context": {
                    "product_id": action_row.get("product_id", ""),
                    "price": action_row.get("price"),
                    "category": action_row.get("category", ""),
                }
            })

        # Only include sessions with at least 3 actions
        if len(actions_list) >= 3:
            sessions_jsonl.append({
                "user_id": str(user_id),
                "session_id": str(session_id),
                "timestamp": str(timestamp),
                "actions": actions_list
            })

    # Save sessions JSONL
    with open(raw_dir / "sample_sessions.jsonl", "w") as f:
        for session in sessions_jsonl:
            f.write(json.dumps(session) + "\n")

    console.print(f"   ✅ Saved: {raw_dir}/sample_sessions.jsonl ({len(sessions_jsonl)} sessions)")

    # Create placeholder files for rationales and outcomes
    console.print("\n[bold cyan]📝 Creating placeholder rationales and outcomes...[/bold cyan]")

    # Rationales (will be populated from action data if available)
    rationales = []
    for session in sessions_jsonl[:1000]:  # Limit for demo
        rationales.append({
            "session_id": session["session_id"],
            "rationale": "User selected based on price and features."  # Placeholder
        })

    with open(raw_dir / "opera_rationales.jsonl", "w") as f:
        for rat in rationales:
            f.write(json.dumps(rat) + "\n")
    console.print(f"   ✅ Saved: {raw_dir}/opera_rationales.jsonl")

    # Outcomes (final purchase decisions)
    outcomes = []
    for session in sessions_jsonl[:1000]:
        if session["actions"]:
            final_action = session["actions"][-1]
            outcomes.append({
                "session_id": session["session_id"],
                "outcome": {
                    "choice": final_action["context"].get("product_id", "unknown"),
                    "product_id": final_action["context"].get("product_id", "unknown"),
                    "satisfaction": 4,  # Placeholder: 1-5 Likert scale
                    "purchased": True
                }
            })

    with open(raw_dir / "opera_outcomes.jsonl", "w") as f:
        for outcome in outcomes:
            f.write(json.dumps(outcome) + "\n")
    console.print(f"   ✅ Saved: {raw_dir}/opera_outcomes.jsonl")

    console.print()

    # Display statistics table
    table = Table(title="OPeRA Dataset Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", justify="right", style="green")

    table.add_row("Users", f"{len(user_df):,}")
    table.add_row("Sessions", f"{len(session_df):,}")
    table.add_row("Actions", f"{len(action_df):,}")
    table.add_row("Aligned Sessions", f"{len(sessions_jsonl):,}")
    table.add_row("Actions per User", f"{len(action_df) / len(user_df):.1f}")
    table.add_row("Sessions per User", f"{len(session_df) / len(user_df):.1f}")

    console.print(table)
    console.print()

    # Show column information
    console.print("[bold cyan]👤 User Data Columns:[/bold cyan]")
    for i, col in enumerate(user_df.columns[:15], 1):  # Show first 15
        sample = user_df[col].iloc[0] if len(user_df) > 0 else "N/A"
        console.print(f"   {i:2d}. {col:20s} (e.g., {sample})")
    if len(user_df.columns) > 15:
        console.print(f"   ... and {len(user_df.columns) - 15} more columns")

    console.print("\n[bold green]✅ Download complete![/bold green]")
    console.print(f"[bold]📁 Data saved to: {raw_dir.absolute()}[/bold]\n")

if __name__ == "__main__":
    main()
