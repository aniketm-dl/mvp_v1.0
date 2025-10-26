from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import numpy as np

from src.ssr.anchor_mapper import SSRAnchorMapper

LIKERT_VALUES = np.arange(1, 6, dtype=float)


def load_synthetic_responses(path: Path) -> List[Dict[str, object]]:
    """Load persona-conditioned LLM responses for SSR anchor mapping."""
    responses: List[Dict[str, object]] = []
    with path.open("r") as fh:
        for line in fh:
            if not line.strip():
                continue
            record = json.loads(line)
            if "stimulus_text" not in record or "llm_response" not in record:
                continue
            responses.append(
                {
                    "stimulus_text": record["stimulus_text"],
                    "llm_response": record["llm_response"],
                    "persona_vec": record.get("persona_vec"),
                    "demographics": record.get("demographics"),
                    "likert_score": record.get("likert_score"),
                    "generation_params": record.get("generation_params"),
                    "llm_sample_index": record.get("llm_sample_index"),
                }
            )
    return responses


def aggregate_anchor_predictions(
    responses: List[Dict[str, object]],
    anchor_mapper: SSRAnchorMapper,
    *,
    temperature: float = 1.0,
    epsilon: float = 1e-6,
) -> Dict[str, object]:
    """Aggregate Likert pmfs from anchor mapping across responses."""
    grouped_pmfs: Dict[str, List[np.ndarray]] = defaultdict(list)
    grouped_metadata: Dict[str, List[Dict[str, object]]] = defaultdict(list)

    for record in responses:
        mapping = anchor_mapper.compute_pmf(
            record["llm_response"],
            temperature=temperature,
            epsilon=epsilon,
        )
        expected_rating = mapping["expected_rating"]
        grouped_pmfs[record["stimulus_text"]].append(mapping["pmf"])
        grouped_metadata[record["stimulus_text"]].append(
            {
                "response": record["llm_response"],
                "likert_score": record.get("likert_score"),
                "persona_vec": record.get("persona_vec"),
                "demographics": record.get("demographics"),
                "generation_params": record.get("generation_params"),
                "llm_sample_index": record.get("llm_sample_index"),
                "expected_rating": expected_rating,
                "per_set_pmfs": {
                    name: pmf.tolist() for name, pmf in mapping["per_set_pmfs"].items()
                },
            }
        )

    predictions: List[Dict[str, object]] = []
    for stimulus_text, pmfs in grouped_pmfs.items():
        pmf_matrix = np.vstack(pmfs)
        averaged = pmf_matrix.mean(axis=0)
        mean = float(np.dot(averaged, LIKERT_VALUES))
        variance = float(np.dot(averaged, (LIKERT_VALUES - mean) ** 2))
        std = float(np.sqrt(max(variance, 0.0)))
        predictions.append(
            {
                "stimulus_text": stimulus_text,
                "pred_mean": mean,
                "pred_distribution": averaged,
                "pred_mode": int(np.argmax(averaged) + 1),
                "pred_std": std,
                "num_samples": len(pmfs),
                "responses": grouped_metadata[stimulus_text],
            }
        )

    metadata = anchor_mapper.get_metadata()
    return {
        "predictions": predictions,
        "metadata": metadata,
    }
