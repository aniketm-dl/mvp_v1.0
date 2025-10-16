from __future__ import annotations
import pytest
import numpy as np
import tempfile
from pathlib import Path
import pickle
import pandas as pd
import yaml

from discovery.build_graph import build_knn_graph
from discovery.quality_gates import (
    gate_silhouette,
    gate_davies_bouldin,
    compute_distinct_n,
    gate_distinct_n,
    run_all_gates
)


class TestGraphConstruction:
    """Test k-NN graph construction."""

    def test_build_graph_basic(self):
        """Test basic graph construction."""
        # Create synthetic embeddings
        np.random.seed(17)
        N = 100
        D = 256
        embeddings = np.random.randn(N, D).astype(np.float32)
        # Normalize
        embeddings = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)

        graph = build_knn_graph(
            embeddings=embeddings,
            k=10,
            metric="cosine",
            min_similarity=0.35,
            approximate=False,
            seed=17
        )

        assert graph["N"] == N
        assert graph["k"] == 10
        assert graph["indices"].shape == (N, 10)
        assert graph["distances"].shape == (N, 10)
        assert graph["similarities"].shape == (N, 10)
        assert graph["adjacency"].shape == (N, N)
        assert graph["distance_matrix"].shape == (N, N)

        # Check symmetry
        assert np.allclose(graph["adjacency"], graph["adjacency"].T)

        # Check diagonal is zero
        assert np.allclose(np.diag(graph["distance_matrix"]), 0.0)

    def test_similarity_threshold(self):
        """Test that similarity threshold filters edges correctly."""
        np.random.seed(17)
        N = 50
        D = 64
        embeddings = np.random.randn(N, D).astype(np.float32)
        embeddings = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)

        # Build with high threshold
        graph = build_knn_graph(
            embeddings=embeddings,
            k=10,
            metric="cosine",
            min_similarity=0.8,  # Very high threshold
            approximate=False,
            seed=17
        )

        # Many edges should be filtered
        n_edges = graph["mask"].sum()
        assert n_edges < N * 10  # Less than k * N edges
        assert n_edges > 0  # But some edges remain


class TestQualityGates:
    """Test quality gate functions."""

    def test_silhouette_gate_pass(self):
        """Test silhouette gate with well-separated clusters."""
        # Create 3 well-separated clusters
        np.random.seed(17)
        cluster_0 = np.random.randn(30, 10) + np.array([5, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        cluster_1 = np.random.randn(30, 10) + np.array([0, 5, 0, 0, 0, 0, 0, 0, 0, 0])
        cluster_2 = np.random.randn(30, 10) + np.array([0, 0, 5, 0, 0, 0, 0, 0, 0, 0])

        embeddings = np.vstack([cluster_0, cluster_1, cluster_2]).astype(np.float32)
        labels = np.array([0] * 30 + [1] * 30 + [2] * 30)

        result = gate_silhouette(
            embeddings=embeddings,
            labels=labels,
            min_score=0.45
        )

        assert result["passed"] is True
        assert result["score"] >= 0.45

    def test_silhouette_gate_fail(self):
        """Test silhouette gate with poorly separated clusters."""
        # Create overlapping clusters
        np.random.seed(17)
        embeddings = np.random.randn(100, 10).astype(np.float32)
        labels = np.random.randint(0, 3, size=100)  # Random labels

        result = gate_silhouette(
            embeddings=embeddings,
            labels=labels,
            min_score=0.45
        )

        # Should fail or have low score
        assert result["score"] < 0.45 or not result["passed"]

    def test_davies_bouldin_gate(self):
        """Test Davies-Bouldin gate."""
        # Well-separated clusters should have low DB index
        np.random.seed(17)
        cluster_0 = np.random.randn(30, 10) + np.array([10, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        cluster_1 = np.random.randn(30, 10) + np.array([0, 10, 0, 0, 0, 0, 0, 0, 0, 0])

        embeddings = np.vstack([cluster_0, cluster_1]).astype(np.float32)
        labels = np.array([0] * 30 + [1] * 30)

        result = gate_davies_bouldin(
            embeddings=embeddings,
            labels=labels,
            max_score=0.8
        )

        assert result["passed"] is True
        assert result["score"] <= 0.8

    def test_distinct_n_computation(self):
        """Test n-gram computation."""
        text = "the quick brown fox jumps over the lazy dog"
        trigrams = compute_distinct_n(text, n=3)

        assert "the quick brown" in trigrams
        assert "quick brown fox" in trigrams
        assert "lazy dog" not in trigrams  # Only 2 words
        assert len(trigrams) == 7  # 9 words - 3 + 1

    def test_distinct_n_gate(self):
        """Test distinct-n gate."""
        # Create mock cluster responses
        cluster_responses = {
            0: [
                "I love cheap products with great deals",
                "always looking for discounts and sales",
                "price is the most important factor"
            ],
            1: [
                "I prefer premium quality brands",
                "willing to pay more for reliability",
                "brand reputation matters most"
            ]
        }

        result = gate_distinct_n(
            cluster_responses=cluster_responses,
            n=3,
            min_margin=0.05
        )

        # Should pass - clusters have distinct language
        assert result["passed"] is True
        assert result["mean_margin"] >= 0.05

    def test_run_all_gates(self):
        """Test running all gates together."""
        # Create synthetic data
        np.random.seed(17)
        cluster_0 = np.random.randn(30, 10) + np.array([5, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        cluster_1 = np.random.randn(30, 10) + np.array([0, 5, 0, 0, 0, 0, 0, 0, 0, 0])

        embeddings = np.vstack([cluster_0, cluster_1]).astype(np.float32)
        labels = np.array([0] * 30 + [1] * 30)

        gate_config = {
            "silhouette": {
                "enabled": True,
                "min_score": 0.3
            },
            "davies_bouldin": {
                "enabled": True,
                "max_score": 1.0
            }
        }

        results = run_all_gates(
            embeddings=embeddings,
            labels=labels,
            gate_config=gate_config
        )

        assert "gates" in results
        assert "silhouette" in results["gates"]
        assert "davies_bouldin" in results["gates"]
        assert results["n_gates"] == 2
        assert results["all_passed"] is True


class TestEmbeddingLoader:
    """Test embedding loader."""

    def test_legacy_mode(self):
        """Test legacy 15-D embedding loading."""
        from services.router.embedding_loader import EmbeddingLoader

        # Use default config
        config_path = Path("CONFIGS/discovery.yaml")

        # Temporarily modify config to use legacy mode
        with open(config_path) as f:
            config = yaml.safe_load(f)

        original_use_encoder = config["router"]["use_encoder_embeddings"]

        try:
            # Force legacy mode
            config["router"]["use_encoder_embeddings"] = False

            with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
                yaml.dump(config, f)
                temp_config_path = Path(f.name)

            loader = EmbeddingLoader(temp_config_path)

            assert loader.use_encoder is False
            assert loader.embedding_dim == 15
            assert len(loader.twins) == 18  # 18 personas

            # Test encoding
            session_data = {"embedding": np.random.rand(15).tolist()}
            emb = loader.encode_session(session_data)

            assert emb.shape == (15,)
            assert np.allclose(np.linalg.norm(emb), 1.0)  # Normalized

        finally:
            # Restore original config
            config["router"]["use_encoder_embeddings"] = original_use_encoder
            temp_config_path.unlink(missing_ok=True)

    def test_get_twin_centers(self):
        """Test retrieving twin centers."""
        from services.router.embedding_loader import EmbeddingLoader

        config_path = Path("CONFIGS/discovery.yaml")
        loader = EmbeddingLoader(config_path)

        centers = loader.get_twin_centers()

        assert isinstance(centers, dict)
        assert len(centers) > 0

        # All centers should be normalized
        for tid, center in centers.items():
            assert np.allclose(np.linalg.norm(center), 1.0, atol=0.01)


class TestMixtureRouter:
    """Test mixture-of-twins router."""

    def test_cosine_similarity(self):
        """Test cosine similarity computation."""
        from services.router.mix_of_twins import MixtureOfTwins

        router = MixtureOfTwins()

        a = np.array([1.0, 0.0, 0.0])
        b = np.array([1.0, 0.0, 0.0])
        sim = router._cosine_similarity(a, b)
        assert np.isclose(sim, 1.0)

        a = np.array([1.0, 0.0, 0.0])
        b = np.array([0.0, 1.0, 0.0])
        sim = router._cosine_similarity(a, b)
        assert np.isclose(sim, 0.0)

    def test_softmax(self):
        """Test softmax with temperature."""
        from services.router.mix_of_twins import MixtureOfTwins

        router = MixtureOfTwins()

        scores = [1.0, 2.0, 3.0]
        probs = router._softmax(scores, temperature=1.0)

        assert len(probs) == 3
        assert np.isclose(sum(probs), 1.0)
        assert probs[2] > probs[1] > probs[0]  # Higher scores → higher probs

    def test_compute_responsibilities(self):
        """Test responsibility computation."""
        from services.router.mix_of_twins import MixtureOfTwins

        router = MixtureOfTwins()

        # Use a random embedding
        np.random.seed(17)
        emb_dim = router.loader.get_embedding_dim()
        session_emb = np.random.randn(emb_dim).astype(np.float32)
        session_emb = session_emb / np.linalg.norm(session_emb)

        responsibilities = router.compute_responsibilities(session_emb)

        assert isinstance(responsibilities, dict)
        assert len(responsibilities) > 0
        assert np.isclose(sum(responsibilities.values()), 1.0)

        # Check sorted by weight
        weights = list(responsibilities.values())
        assert weights == sorted(weights, reverse=True)

    def test_primary_twin(self):
        """Test primary twin selection."""
        from services.router.mix_of_twins import MixtureOfTwins

        router = MixtureOfTwins()

        responsibilities = {
            "twin_a": 0.5,
            "twin_b": 0.3,
            "twin_c": 0.2
        }

        primary = router.primary_twin(responsibilities)

        assert primary["id"] == "twin_a"
        assert primary["weight"] == 0.5

    def test_route_legacy(self):
        """Test routing with legacy embeddings."""
        from services.router.mix_of_twins import MixtureOfTwins

        # Force legacy mode
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            config = {
                "router": {
                    "use_encoder_embeddings": False,
                    "fallback_embeddings_path": "DATA/twin_bank.json",
                    "temperature": 0.5
                },
                "persona": {
                    "personas_path": "DATA/personas.json"
                }
            }
            yaml.dump(config, f)
            temp_config_path = Path(f.name)

        try:
            router = MixtureOfTwins(config_path=temp_config_path)

            session_data = {"embedding": np.random.rand(15).tolist()}
            result = router.route(session_data)

            assert "responsibilities" in result
            assert "primary" in result
            assert result["backend"] == "legacy"
            assert result["embedding_dim"] == 15

        finally:
            temp_config_path.unlink(missing_ok=True)

    def test_determinism(self):
        """Test that routing is deterministic."""
        from services.router.mix_of_twins import MixtureOfTwins

        router = MixtureOfTwins()

        # Same input should give same output
        np.random.seed(17)
        emb = np.random.rand(15).tolist()
        session_data = {"embedding": emb}

        result1 = router.route(session_data)
        result2 = router.route(session_data)

        assert result1["responsibilities"] == result2["responsibilities"]
        assert result1["primary"]["id"] == result2["primary"]["id"]


class TestDeterminism:
    """Test determinism across discovery pipeline."""

    def test_graph_determinism(self):
        """Test that graph construction is deterministic."""
        np.random.seed(17)
        embeddings = np.random.randn(50, 32).astype(np.float32)
        embeddings = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)

        graph1 = build_knn_graph(
            embeddings=embeddings,
            k=5,
            metric="cosine",
            min_similarity=0.3,
            approximate=False,
            seed=17
        )

        graph2 = build_knn_graph(
            embeddings=embeddings,
            k=5,
            metric="cosine",
            min_similarity=0.3,
            approximate=False,
            seed=17
        )

        assert np.array_equal(graph1["indices"], graph2["indices"])
        assert np.array_equal(graph1["distances"], graph2["distances"])


def test_integration_smoke():
    """Smoke test for full pipeline integration."""
    # This test ensures all modules can be imported and basic functionality works

    # Test imports
    from discovery.build_graph import build_knn_graph
    from discovery.quality_gates import run_all_gates
    from services.router.embedding_loader import EmbeddingLoader
    from services.router.mix_of_twins import MixtureOfTwins

    # Test basic functionality
    np.random.seed(17)
    embeddings = np.random.randn(20, 16).astype(np.float32)
    embeddings = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)

    graph = build_knn_graph(
        embeddings=embeddings,
        k=3,
        metric="cosine",
        min_similarity=0.2,
        approximate=False,
        seed=17
    )

    assert graph is not None
    assert "adjacency" in graph

    labels = np.array([0] * 10 + [1] * 10)

    gate_config = {
        "silhouette": {"enabled": True, "min_score": 0.0},
        "davies_bouldin": {"enabled": True, "max_score": 2.0}
    }

    results = run_all_gates(embeddings, labels, gate_config)
    assert results["n_gates"] == 2
