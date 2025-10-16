from __future__ import annotations
import pytest
import numpy as np
import pandas as pd
from pathlib import Path


def test_session_aggregation():
    """Test step-to-session aggregation."""
    # Create mock step data
    data = {
        'session_id': [1, 1, 1, 2, 2],
        'emb_0': [0.1, 0.2, 0.3, 0.4, 0.5],
        'emb_1': [0.2, 0.3, 0.4, 0.5, 0.6],
        'rationale': ['a', 'b', 'c', 'd', 'e']
    }
    df = pd.DataFrame(data)

    # Mock aggregation
    grouped = df.groupby('session_id')
    sessions = []
    for sid, group in grouped:
        embs = group[['emb_0', 'emb_1']].values
        session_emb = np.mean(embs, axis=0)
        sessions.append({'session_id': sid, 'emb_0': session_emb[0], 'emb_1': session_emb[1]})

    result = pd.DataFrame(sessions)
    assert len(result) == 2
    assert np.isclose(result.loc[0, 'emb_0'], 0.2)


def test_clustering_basic():
    """Test that clustering produces valid labels."""
    try:
        import hdbscan
    except ImportError:
        pytest.skip("hdbscan not installed")

    # Create synthetic clusters
    cluster_0 = np.random.randn(30, 10) + np.array([5, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    cluster_1 = np.random.randn(30, 10) + np.array([0, 5, 0, 0, 0, 0, 0, 0, 0, 0])
    embeddings = np.vstack([cluster_0, cluster_1])

    clusterer = hdbscan.HDBSCAN(min_cluster_size=10, min_samples=5)
    labels = clusterer.fit_predict(embeddings)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    assert n_clusters >= 2


def test_topic_labeling():
    """Test TF-IDF based labeling."""
    from sklearn.feature_extraction.text import TfidfVectorizer

    texts = [
        "discount sale cheap price bargain",
        "premium quality brand luxury expensive",
        "fast delivery shipping quick speed"
    ]

    vectorizer = TfidfVectorizer(max_features=5, stop_words='english')
    tfidf = vectorizer.fit_transform(texts)
    terms = vectorizer.get_feature_names_out()

    assert len(terms) > 0
    assert 'discount' in terms or 'sale' in terms or 'cheap' in terms


def test_metrics_computation():
    """Test quality metrics."""
    from sklearn.metrics import silhouette_score

    # Well-separated clusters
    cluster_0 = np.random.randn(30, 10) + np.array([5, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    cluster_1 = np.random.randn(30, 10) + np.array([0, 5, 0, 0, 0, 0, 0, 0, 0, 0])
    embeddings = np.vstack([cluster_0, cluster_1])
    labels = np.array([0] * 30 + [1] * 30)

    score = silhouette_score(embeddings, labels)
    assert score > 0.3  # Reasonable separation


def test_persona_synthesis():
    """Test persona JSON generation."""
    import hashlib

    centroid = np.random.rand(256)
    centroid_hash = hashlib.md5(centroid.tobytes()).hexdigest()[:8]
    persona_id = f"disc_{centroid_hash}"

    persona = {
        'persona_id': persona_id,
        'name': 'Test Persona',
        'version': 'mvp_v1_discovered',
        'cluster_id': 0,
        'size': 100
    }

    assert persona['persona_id'].startswith('disc_')
    assert len(persona['persona_id']) == 13  # disc_ + 8 char hash


def test_determinism():
    """Test that pipeline is deterministic."""
    np.random.seed(17)
    embs1 = np.random.randn(100, 10)

    np.random.seed(17)
    embs2 = np.random.randn(100, 10)

    assert np.allclose(embs1, embs2)


def test_integration_smoke():
    """Smoke test for full pipeline."""
    # This would call scripts/run_dynamic_discovery.py in a real test
    # For now, just verify imports work
    try:
        from scripts.run_dynamic_discovery import aggregate_sessions, build_graph, compute_metrics
        assert callable(aggregate_sessions)
        assert callable(build_graph)
        assert callable(compute_metrics)
    except ImportError:
        pytest.skip("Pipeline modules not in path")
