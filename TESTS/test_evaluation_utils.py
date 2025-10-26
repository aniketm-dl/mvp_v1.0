from __future__ import annotations

import json
from pathlib import Path
from typing import List

import numpy as np

from src.ssr.evaluation_utils import (
    aggregate_anchor_predictions,
    load_synthetic_responses,
)


def test_load_synthetic_responses(tmp_path: Path):
    file_path = tmp_path / "responses.jsonl"
    records = [
        {
            "stimulus_text": "Offer A",
            "llm_response": "I love this product.",
            "persona_vec": [0.1] * 12,
            "likert_score": 5,
            "generation_params": {"temperature": 0.5},
        },
        {
            "stimulus_text": "Offer B",
            "llm_response": "Not for me.",
        },
        {
            "stimulus_text": "Offer C",
            "no_response": True,
        },
    ]
    with file_path.open("w") as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")

    loaded = load_synthetic_responses(file_path)
    assert len(loaded) == 2
    assert {item["stimulus_text"] for item in loaded} == {"Offer A", "Offer B"}


class DummyAnchorMapper:
    def __init__(self, sequences: List[List[float]]):
        self.sequences = [np.array(seq, dtype=float) for seq in sequences]
        self.calls = 0

    def compute_pmf(self, *_args, **_kwargs):
        pmf = self.sequences[self.calls % len(self.sequences)]
        self.calls += 1
        return {
            "pmf": pmf,
            "expected_rating": float(np.dot(pmf, np.arange(1, 6))),
            "per_set_pmfs": {"setA": pmf},
        }

    def get_metadata(self):
        return {"anchor_version": "test", "anchor_hash": "abc123"}


def test_aggregate_anchor_predictions():
    responses = [
        {"stimulus_text": "Offer A", "llm_response": "Great!"},
        {"stimulus_text": "Offer A", "llm_response": "Looks decent."},
        {"stimulus_text": "Offer B", "llm_response": "No thanks."},
    ]

    mapper = DummyAnchorMapper(
        [
            [0.1, 0.2, 0.3, 0.2, 0.2],
            [0.2, 0.2, 0.2, 0.2, 0.2],
            [0.05, 0.1, 0.15, 0.3, 0.4],
        ]
    )

    aggregated = aggregate_anchor_predictions(
        responses,
        mapper,  # type: ignore[arg-type]
        temperature=1.0,
        epsilon=1e-6,
    )

    preds = aggregated["predictions"]
    meta = aggregated["metadata"]

    assert meta["anchor_version"] == "test"
    assert meta["anchor_hash"] == "abc123"

    assert len(preds) == 2

    offer_a = next(item for item in preds if item["stimulus_text"] == "Offer A")
    np.testing.assert_allclose(
        offer_a["pred_distribution"],
        np.array([0.15, 0.2, 0.25, 0.2, 0.2]),
    )
    assert offer_a["num_samples"] == 2
    assert len(offer_a["responses"]) == 2

    offer_b = next(item for item in preds if item["stimulus_text"] == "Offer B")
    assert offer_b["num_samples"] == 1
    assert offer_b["pred_mode"] in {4, 5}
    assert all("expected_rating" in resp for resp in offer_b["responses"])
