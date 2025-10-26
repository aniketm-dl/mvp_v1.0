from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.evaluation.human_metrics import (
    bootstrap_test_retest,
    compute_human_distributions,
    convert_human_stats_to_dataframe,
    load_human_ratings,
)


def test_load_human_ratings(tmp_path: Path):
    file_path = tmp_path / "human.jsonl"
    records = [
        {
            "stimulus_text": "Offer A",
            "likert_score": 5,
            "persona_vec": [0.1] * 12,
            "demographics": {"age_bracket": 2},
        },
        {"stimulus_text": "Offer A", "likert_score": 4},
        {"stimulus_text": "Offer B", "likert_score": 2},
        {"stimulus_text": "Offer C"},  # missing score -> ignored
    ]
    with file_path.open("w") as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")

    df = load_human_ratings(file_path)
    assert len(df) == 3
    assert sorted(df["stimulus_text"].unique()) == ["Offer A", "Offer B"]
    assert df["likert_score"].tolist() == [5, 4, 2]
    assert "persona_vec" in df.columns
    first = df.iloc[0]
    assert isinstance(first["persona_vec"], list)
    assert first["demographics"] == {"age_bracket": 2}


def test_compute_human_distributions():
    df = pd.DataFrame(
        {
            "stimulus_text": ["Offer A"] * 4 + ["Offer B"] * 3,
            "likert_score": [5, 4, 4, 3, 1, 2, 2],
        }
    )

    stats = compute_human_distributions(df)
    assert set(stats.keys()) == {"Offer A", "Offer B"}

    offer_a = stats["Offer A"]
    assert offer_a["counts"].tolist() == [0, 0, 1, 2, 1]
    np.testing.assert_allclose(offer_a["pmf"], np.array([0, 0, 0.25, 0.5, 0.25]))
    assert np.isclose(offer_a["mean"], 4.0)

    offer_b = stats["Offer B"]
    assert offer_b["counts"].tolist() == [1, 2, 0, 0, 0]
    np.testing.assert_allclose(offer_b["pmf"], np.array([1 / 3, 2 / 3, 0, 0, 0]))


def test_bootstrap_test_retest_consistency():
    df = pd.DataFrame(
        {
            "stimulus_text": ["Offer A"] * 10 + ["Offer B"] * 10,
            "likert_score": [5] * 5 + [4] * 5 + [2] * 5 + [3] * 5,
        }
    )

    ceiling, samples = bootstrap_test_retest(df, num_bootstrap=50, random_state=0)
    assert 0.0 <= ceiling <= 1.0
    assert len(samples) > 0


def test_convert_stats_dataframe_roundtrip():
    df = pd.DataFrame(
        {
            "stimulus_text": ["Offer A"] * 3,
            "likert_score": [5, 4, 4],
        }
    )
    stats = compute_human_distributions(df)
    stats_df = convert_human_stats_to_dataframe(stats)

    assert list(stats_df.columns) == [
        "stimulus_text",
        "human_mean",
        "human_counts",
        "human_pmf",
        "human_n",
    ]
    assert stats_df.loc[0, "human_n"] == 3
