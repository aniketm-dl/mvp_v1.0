from __future__ import annotations
import argparse
from pathlib import Path
import yaml
import pandas as pd
import numpy as np


def aggregate_to_sessions(
    steps_df: pd.DataFrame,
    method: str,
    min_steps: int,
    keep_rationales: bool,
    keep_facts: bool
) -> pd.DataFrame:
    """Aggregate step-level embeddings to session-level."""

    # Group by session
    grouped = steps_df.groupby('session_id')

    results = []
    for session_id, group in grouped:
        if len(group) < min_steps:
            continue

        # Extract embedding columns
        emb_cols = [c for c in group.columns if c.startswith('emb_')]
        embeddings = group[emb_cols].values

        # Aggregate embeddings
        if method == 'mean':
            session_emb = np.mean(embeddings, axis=0)
        elif method == 'last':
            session_emb = embeddings[-1]
        elif method == 'max':
            session_emb = np.max(embeddings, axis=0)
        else:
            session_emb = np.mean(embeddings, axis=0)

        # Build session record
        record = {
            'session_id': session_id,
            'user_id': group['user_id'].iloc[0] if 'user_id' in group.columns else None,
            'split': group['split'].iloc[0] if 'split' in group.columns else 'train',
            'n_steps': len(group)
        }

        # Add aggregated embedding
        for i, val in enumerate(session_emb):
            record[f'emb_{i}'] = val

        # Aggregate text for labeling
        if keep_rationales and 'rationale' in group.columns:
            record['rationales_agg'] = ' '.join(group['rationale'].dropna().astype(str))

        if keep_facts and 'facts' in group.columns:
            record['facts_agg'] = ' '.join(group['facts'].dropna().astype(str))

        # Copy demographics if present
        for col in ['age_group', 'gender', 'location_type', 'persona_id']:
            if col in group.columns:
                record[col] = group[col].iloc[0]

        results.append(record)

    return pd.DataFrame(results)


def main():
    parser = argparse.ArgumentParser(description="Aggregate step embeddings to sessions")
    parser.add_argument('--steps', type=Path, required=True, help="Step embeddings parquet")
    parser.add_argument('--out', type=Path, required=True, help="Output session embeddings")
    parser.add_argument('--config', type=Path, default=Path('CONFIGS/discovery.yaml'))
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    agg_config = config['aggregation']

    print(f"Loading step embeddings from {args.steps}")
    df = pd.read_parquet(args.steps)
    print(f"  Loaded {len(df)} steps")

    print(f"Aggregating to sessions (method={agg_config['method']})")
    sessions = aggregate_to_sessions(
        df,
        method=agg_config['method'],
        min_steps=agg_config['min_steps_per_session'],
        keep_rationales=agg_config['keep_rationales'],
        keep_facts=agg_config['keep_facts']
    )

    print(f"  Aggregated to {len(sessions)} sessions")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    sessions.to_parquet(args.out, index=False)
    print(f"Saved to {args.out}")


if __name__ == '__main__':
    main()
