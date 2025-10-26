from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

LikertStats = Dict[str, object]


def load_human_ratings(path: Path) -> pd.DataFrame:
    """Load human ratings from a JSONL file produced by preprocessing.

    Expected schema per line:
        {
            "stimulus_text": str,
            "likert_score": int,
            ...
        }
    """
    records: List[Dict[str, object]] = []
    with path.open("r") as fh:
        for line in fh:
            if not line.strip():
                continue
            record = json.loads(line)
            # Only keep required fields
            if "likert_score" not in record or record.get("likert_score") is None:
                continue
            cleaned: Dict[str, object] = {
                "stimulus_text": record.get("stimulus_text"),
                "likert_score": int(record.get("likert_score")),
            }

            if "persona_vec" in record and record.get("persona_vec") is not None:
                cleaned["persona_vec"] = record.get("persona_vec")
            if "demographics" in record and record.get("demographics") is not None:
                cleaned["demographics"] = record.get("demographics")
            if "session_id" in record:
                cleaned["session_id"] = record.get("session_id")
            if "user_id" in record:
                cleaned["user_id"] = record.get("user_id")

            records.append(cleaned)
    df = pd.DataFrame(records)
    # Drop rows with missing fields
    df = df.dropna(subset=["stimulus_text", "likert_score"])  # type: ignore[arg-type]
    df["likert_score"] = df["likert_score"].astype(int)
    return df


def compute_human_distributions(df: pd.DataFrame) -> Dict[str, LikertStats]:
    """Aggregate human Likert distributions per stimulus/concept."""
    stats: Dict[str, LikertStats] = {}
    for stimulus, group in df.groupby("stimulus_text"):
        counts = (
            group["likert_score"].value_counts().reindex([1, 2, 3, 4, 5], fill_value=0).to_numpy()
        )
        n = counts.sum()
        if n == 0:
            continue
        pmf = counts / n
        mean = float(np.dot(pmf, np.arange(1, 6)))
        stats[stimulus] = {
            "counts": counts.astype(int),
            "pmf": pmf,
            "mean": mean,
            "n": int(n),
        }
    return stats


def bootstrap_test_retest(
    df: pd.DataFrame,
    *,
    num_bootstrap: int = 200,
    random_state: Optional[int] = 42,
) -> Tuple[float, List[float]]:
    """Estimate human test–retest ceiling via half-sample bootstrapping."""
    rng = np.random.default_rng(random_state)
    grouped = df.groupby("stimulus_text")["likert_score"].apply(list)
    correlations: List[float] = []

    for _ in range(num_bootstrap):
        means_a: Dict[str, float] = {}
        means_b: Dict[str, float] = {}
        for stimulus, scores in grouped.items():
            scores_array = np.array(scores, dtype=float)
            n = len(scores_array)
            if n < 2:
                continue
            perm = rng.permutation(n)
            split = n // 2
            split_a = scores_array[perm[:split]]
            split_b = scores_array[perm[split:]]
            if len(split_a) == 0 or len(split_b) == 0:
                continue
            means_a[stimulus] = float(split_a.mean())
            means_b[stimulus] = float(split_b.mean())

        common = sorted(set(means_a) & set(means_b))
        if len(common) < 2:
            continue
        vec_a = np.array([means_a[s] for s in common])
        vec_b = np.array([means_b[s] for s in common])
        corr_matrix = np.corrcoef(vec_a, vec_b)
        corr = corr_matrix[0, 1]
        if np.isnan(corr):
            continue
        correlations.append(float(corr))

    if not correlations:
        return 0.0, []

    return float(np.mean(correlations)), correlations


def convert_human_stats_to_dataframe(stats: Dict[str, LikertStats]) -> pd.DataFrame:
    """Represent aggregated stats as DataFrame for easy joining."""
    rows = []
    for stimulus, values in stats.items():
        rows.append(
            {
                "stimulus_text": stimulus,
                "human_mean": values["mean"],
                "human_counts": values["counts"],
                "human_pmf": values["pmf"],
                "human_n": values["n"],
            }
        )
    df = pd.DataFrame(rows)
    return df
