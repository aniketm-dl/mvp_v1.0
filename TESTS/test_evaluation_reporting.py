from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.evaluation.reporting import (
    aggregate_flr_predictions,
    compute_overall_pmf,
    compute_subgroup_metrics,
    ensure_human_demographics,
    load_flr_responses,
)


def test_load_and_aggregate_flr(tmp_path: Path):
    path = tmp_path / "flr.jsonl"
    records = [
        {
            "stimulus_text": "Offer A",
            "flr_rating": 5,
            "demographics": {"age_bracket": 2},
        },
        {
            "stimulus_text": "Offer A",
            "flr_rating": 4,
            "persona_vec": [0.1] * 12,
        },
        {"stimulus_text": "Offer B", "flr_rating": 2},
        {"stimulus_text": "Offer C"},
    ]
    with path.open("w") as fh:
        for record in records:
            fh.write(json.dumps(record) + "\n")

    loaded = load_flr_responses(path)
    assert len(loaded) == 3
    assert {item["stimulus_text"] for item in loaded} == {"Offer A", "Offer B"}

    aggregated = aggregate_flr_predictions(loaded)
    predictions = aggregated["predictions"]
    assert aggregated["metadata"]["num_responses"] == 3
    assert len(predictions) == 2

    offer_a = next(item for item in predictions if item["stimulus_text"] == "Offer A")
    np.testing.assert_allclose(
        offer_a["pred_distribution"],
        np.array([0.0, 0.0, 0.0, 0.5, 0.5]),
    )


def test_compute_overall_pmf_and_subgroups():
    predictions = [
        {
            "stimulus_text": "Offer A",
            "pred_distribution": np.array([0.1, 0.2, 0.3, 0.2, 0.2]),
            "num_samples": 10,
            "responses": [
                {"expected_rating": 4.0, "demographics": {"age_bracket": 2}},
                {"expected_rating": 3.0, "persona_vec": [0.1] * 12},
            ],
        },
        {
            "stimulus_text": "Offer B",
            "pred_distribution": np.array([0.0, 0.1, 0.2, 0.3, 0.4]),
            "num_samples": 5,
            "responses": [
                {"expected_rating": 4.5, "demographics": {"income_bracket": 3}},
            ],
        },
    ]

    pmf = compute_overall_pmf(predictions)
    np.testing.assert_allclose(pmf.sum(), 1.0)

    human_df = pd.DataFrame(
        {
            "stimulus_text": ["Offer A", "Offer A", "Offer B"],
            "likert_score": [4, 3, 5],
            "persona_vec": [[0.1] * 12, [0.2] * 12, [0.3] * 12],
        }
    )
    human_df = ensure_human_demographics(human_df)
    subgroup_df = compute_subgroup_metrics("anchor", predictions, human_df)
    assert {"group_type", "group_value", "scenario"} <= set(subgroup_df.columns)
    assert (subgroup_df["scenario"] == "anchor").all()
