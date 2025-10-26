from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from src.ssr.evaluation_utils import LIKERT_VALUES
from src.ssr.llm_elicitation import persona_vec_to_demographics


def load_flr_responses(path: Path) -> List[Dict[str, object]]:
    """Load FLR baseline responses from JSONL."""
    records: List[Dict[str, object]] = []
    with path.open("r") as fh:
        for line in fh:
            if not line.strip():
                continue
            record = json.loads(line)
            rating = record.get("flr_rating")
            if rating is None:
                continue
            records.append(
                {
                    "stimulus_text": record.get("stimulus_text"),
                    "flr_rating": int(rating),
                    "demographics": record.get("demographics"),
                    "persona_vec": record.get("persona_vec"),
                }
            )
    return records


def aggregate_flr_predictions(records: List[Dict[str, object]]) -> Dict[str, object]:
    """Aggregate FLR ratings into Likert pmfs."""
    grouped: Dict[str, List[int]] = defaultdict(list)
    subgroup_metadata: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for record in records:
        stimulus = record.get("stimulus_text")
        if stimulus is None:
            continue
        rating = int(record["flr_rating"])
        grouped[stimulus].append(rating)
        subgroup_metadata[stimulus].append(
            {
                "flr_rating": rating,
                "demographics": record.get("demographics"),
                "persona_vec": record.get("persona_vec"),
                "expected_rating": float(rating),
            }
        )

    predictions: List[Dict[str, object]] = []
    for stimulus, ratings in grouped.items():
        counts = np.bincount(np.array(ratings, dtype=int), minlength=6)[1:6]
        total = counts.sum()
        if total == 0:
            continue
        pmf = counts / total
        mean = float(np.dot(pmf, LIKERT_VALUES))
        variance = float(np.dot(pmf, (LIKERT_VALUES - mean) ** 2))
        predictions.append(
            {
                "stimulus_text": stimulus,
                "pred_mean": mean,
                "pred_distribution": pmf,
                "pred_mode": int(np.argmax(pmf) + 1),
                "pred_std": float(np.sqrt(max(variance, 0.0))),
                "num_samples": int(total),
                "responses": subgroup_metadata[stimulus],
            }
        )

    metadata = {
        "source": "flr",
        "num_responses": len(records),
    }
    return {"predictions": predictions, "metadata": metadata}


def compute_overall_pmf(predictions: List[Dict[str, object]]) -> np.ndarray:
    """Weight average concept pmfs across responses."""
    total_weight = sum(item.get("num_samples", 0) for item in predictions)
    if total_weight == 0:
        return np.zeros(5, dtype=float)
    accumulator = np.zeros(5, dtype=float)
    for item in predictions:
        weight = item.get("num_samples", 0)
        if weight <= 0:
            continue
        accumulator += np.array(item["pred_distribution"], dtype=float) * weight
    return accumulator / total_weight


def ensure_human_demographics(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure demographic columns exist by deriving from persona vectors when needed."""
    if "demographics" in df.columns:
        demo_series = df["demographics"].fillna({})
    else:
        demo_series = pd.Series([{}] * len(df))

    derived_rows = []
    for idx, record in df.iterrows():
        demo = demo_series.iloc[idx] if isinstance(demo_series.iloc[idx], dict) else {}
        if not demo and record.get("persona_vec") is not None:
            try:
                demo = persona_vec_to_demographics(record["persona_vec"])
            except Exception:  # pragma: no cover - defensive
                demo = {}
        derived_rows.append(demo)

    derived_df = pd.DataFrame(derived_rows)
    for column in ["age_bracket", "gender", "income_bracket"]:
        if column in derived_df.columns:
            df[column] = derived_df[column]
        else:
            df[column] = None
    return df


def compute_human_group_stats(df: pd.DataFrame, field: str) -> Dict[object, Dict[str, float]]:
    """Compute mean Likert score per demographic field for human data."""
    stats: Dict[object, Dict[str, float]] = {}
    valid_df = df.dropna(subset=[field])
    if valid_df.empty:
        return stats
    for value, group in valid_df.groupby(field):
        scores = group["likert_score"].to_numpy(dtype=float)
        stats[value] = {
            "mean": float(scores.mean()) if len(scores) else None,
            "count": int(len(scores)),
        }
    return stats


def compute_subgroup_metrics(
    scenario_label: str,
    predictions: List[Dict[str, object]],
    human_df: pd.DataFrame,
) -> pd.DataFrame:
    """Compare predicted vs human subgroup means across common demographic fields."""
    group_fields = ["age_bracket", "gender", "income_bracket"]

    predicted_values: Dict[str, Dict[object, List[float]]] = {
        field: defaultdict(list) for field in group_fields
    }
    predicted_counts: Dict[str, Dict[object, int]] = {
        field: defaultdict(int) for field in group_fields
    }

    for concept in predictions:
        for response in concept.get("responses", []):
            demo = response.get("demographics") or {}
            if not demo and response.get("persona_vec") is not None:
                try:
                    demo = persona_vec_to_demographics(response["persona_vec"])
                except Exception:  # pragma: no cover - defensive
                    demo = {}
            if not demo:
                continue
            expected = response.get("expected_rating")
            if expected is None and response.get("flr_rating") is not None:
                expected = float(response["flr_rating"])
            if expected is None:
                continue
            for field in group_fields:
                value = demo.get(field)
                if value is None:
                    continue
                predicted_values[field][value].append(float(expected))
                predicted_counts[field][value] += 1

    human_stats_by_field = {field: compute_human_group_stats(human_df, field) for field in group_fields}

    rows = []
    for field in group_fields:
        values = set(predicted_values[field].keys()) | set(human_stats_by_field[field].keys())
        for value in sorted(values):
            preds = predicted_values[field].get(value, [])
            pred_mean = float(np.mean(preds)) if preds else None
            pred_count = predicted_counts[field].get(value, 0)
            human_info = human_stats_by_field[field].get(value, {})
            human_mean = human_info.get("mean")
            human_count = human_info.get("count", 0)
            diff: Optional[float] = None
            if pred_mean is not None and human_mean is not None:
                diff = float(pred_mean - human_mean)
            rows.append(
                {
                    "scenario": scenario_label,
                    "group_type": field,
                    "group_value": value,
                    "predicted_mean": pred_mean,
                    "human_mean": human_mean,
                    "delta": diff,
                    "predicted_count": int(pred_count),
                    "human_count": int(human_count),
                }
            )

    return pd.DataFrame(rows)
