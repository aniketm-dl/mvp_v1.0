from __future__ import annotations

import numpy as np

from src.ssr.anchor_mapper import SSRAnchorMapper


class DummyEmbedder:
    """Minimal embedder that returns fixed 2D vectors for known tokens."""

    def __init__(self, table):
        self.table = table

    def encode_texts(self, texts, normalize=True, **kwargs):
        if isinstance(texts, str):
            texts = [texts]
        embeddings = []
        for text in texts:
            vec = np.array(self.table[text], dtype=np.float32)
            if normalize:
                norm = np.linalg.norm(vec)
                if norm == 0:
                    embeddings.append(vec)
                else:
                    embeddings.append(vec / norm)
            else:
                embeddings.append(vec)
        return np.vstack(embeddings)


def test_anchor_mapper_average_and_temperature():
    # Define simple 2D vectors so cosine similarities are easy to reason about.
    table = {
        "resp": [1.0, 0.0],
        "set1_a1": [1.0, 0.0],
        "set1_a2": [0.5, 0.0],
        "set1_a3": [0.0, 0.0],
        "set1_a4": [-0.5, 0.0],
        "set1_a5": [-1.0, 0.0],
        "set2_a1": [0.0, 1.0],
        "set2_a2": [0.0, 0.5],
        "set2_a3": [0.0, 0.0],
        "set2_a4": [0.5, 0.5],
        "set2_a5": [1.0, 1.0],
    }

    anchor_sets = {
        "set1": ["set1_a1", "set1_a2", "set1_a3", "set1_a4", "set1_a5"],
        "set2": ["set2_a1", "set2_a2", "set2_a3", "set2_a4", "set2_a5"],
    }

    mapper = SSRAnchorMapper(
        embedder=DummyEmbedder(table),
        anchor_sets=anchor_sets,
        temperature=1.0,
        epsilon=1e-6,
    )

    result = mapper.compute_pmf("resp")
    pmf = result["pmf"]
    per_set_pmfs = result["per_set_pmfs"]

    # Each per-set pmf should be a valid distribution (sum to 1 and positive).
    for name, pmf_set in per_set_pmfs.items():
        assert np.isclose(pmf_set.sum(), 1.0)
        assert np.all(pmf_set > 0), f"pmf for {name} should be strictly positive"

    # Averaged pmf must equal the arithmetic mean of the set-level pmfs.
    manual_average = np.vstack(list(per_set_pmfs.values())).mean(axis=0)
    assert np.allclose(pmf, manual_average)
    assert np.isclose(result["expected_rating"], np.dot(pmf, np.arange(1, 6)))

    # Temperature < 1 should sharpen the distribution; use 0.5 so exponent=2
    sharp_mapper = SSRAnchorMapper(
        embedder=DummyEmbedder(table),
        anchor_sets=anchor_sets,
        temperature=0.5,
        epsilon=1e-6,
    )
    sharp = sharp_mapper.compute_pmf("resp")

    assert sharp["pmf"].argmax() == pmf.argmax()
    assert sharp["pmf"][pmf.argmax()] > pmf[pmf.argmax()]
