from __future__ import annotations

import numpy as np
import pytest

from src.evaluation.correlation import CorrelationMetrics
from src.evaluation.ks_test import KSSimilarityTest


class TestCorrelationMetrics:
    """Test correlation metrics computation."""

    def test_spearman_perfect_correlation(self):
        """Test Spearman correlation with perfect positive correlation."""
        metrics = CorrelationMetrics(min_samples=5)

        predicted = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        actual = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        corr, p_value = metrics.compute_spearman(predicted, actual)

        assert corr == pytest.approx(1.0, abs=0.01)
        assert p_value < 0.05

    def test_pearson_perfect_correlation(self):
        """Test Pearson correlation with perfect linear correlation."""
        metrics = CorrelationMetrics(min_samples=5)

        predicted = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        actual = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        corr, p_value = metrics.compute_pearson(predicted, actual)

        assert corr == pytest.approx(1.0, abs=0.01)
        assert p_value < 0.05

    def test_compute_all_metrics(self):
        """Test computing all metrics at once."""
        metrics = CorrelationMetrics(min_samples=5)

        predicted = np.array([3.8, 4.1, 2.9, 3.5, 4.2])
        actual = np.array([4.0, 4.0, 3.0, 3.0, 4.0])

        results = metrics.compute_all_metrics(predicted, actual)

        assert "spearman" in results
        assert "pearson" in results
        assert "error_metrics" in results
        assert "interpretation" in results

        assert isinstance(results["spearman"]["correlation"], float)
        assert isinstance(results["error_metrics"]["mae"], float)
        assert isinstance(results["error_metrics"]["rmse"], float)

    def test_too_few_samples(self):
        """Test handling of too few samples."""
        metrics = CorrelationMetrics(min_samples=10)

        predicted = np.array([3.8, 4.1, 2.9])
        actual = np.array([4.0, 4.0, 3.0])

        corr, p_value = metrics.compute_spearman(predicted, actual)

        assert corr == 0.0
        assert p_value == 1.0

    def test_batch_correlations(self):
        """Test batch correlation computation."""
        metrics = CorrelationMetrics(min_samples=5)

        predictions = [
            np.array([3.8, 4.1, 2.9, 3.5, 4.2]),
            np.array([2.9, 3.1, 3.8, 4.1, 3.5]),
        ]
        actuals = [
            np.array([4.0, 4.0, 3.0, 3.0, 4.0]),
            np.array([3.0, 3.0, 4.0, 4.0, 3.0]),
        ]
        labels = ["persona_1", "persona_2"]

        results = metrics.batch_correlations(predictions, actuals, labels)

        assert "individual_results" in results
        assert "aggregate" in results
        assert len(results["individual_results"]) == 2
        assert "mean_spearman" in results["aggregate"]

    def test_confidence_interval(self):
        """Test bootstrap confidence interval computation."""
        metrics = CorrelationMetrics(min_samples=10)

        np.random.seed(42)
        predicted = np.random.uniform(1, 5, size=50)
        actual = predicted + np.random.normal(0, 0.5, size=50)

        ci_results = metrics.compute_confidence_interval(
            predicted, actual, confidence=0.95, n_bootstrap=100
        )

        assert "spearman_ci" in ci_results
        assert "pearson_ci" in ci_results
        assert len(ci_results["spearman_ci"]) == 2
        assert ci_results["spearman_ci"][0] < ci_results["spearman_ci"][1]


class TestKSSimilarityTest:
    """Test KS similarity test."""

    def test_identical_distributions(self):
        """Test KS test with identical distributions."""
        ks_test = KSSimilarityTest(significance_level=0.05)

        distribution = np.array([0.1, 0.2, 0.4, 0.2, 0.1])

        similarity = ks_test.compute_ks_similarity(distribution, distribution)

        assert similarity >= 0.99

    def test_different_distributions(self):
        """Test KS test with very different distributions."""
        ks_test = KSSimilarityTest(significance_level=0.05)

        dist1 = np.array([0.8, 0.1, 0.05, 0.03, 0.02])
        dist2 = np.array([0.02, 0.03, 0.05, 0.1, 0.8])

        similarity = ks_test.compute_ks_similarity(dist1, dist2)

        assert similarity < 0.5

    def test_full_distribution_test(self):
        """Test full distribution test with interpretation."""
        ks_test = KSSimilarityTest(significance_level=0.05)

        predicted = np.array([0.1, 0.2, 0.4, 0.2, 0.1])
        actual = np.array([0.12, 0.18, 0.42, 0.18, 0.1])

        results = ks_test.test_distributions(predicted, actual)

        assert "ks_statistic" in results
        assert "p_value" in results
        assert "similarity" in results
        assert "interpretation" in results
        assert "passes_threshold" in results

        assert results["similarity"] >= 0.8

    def test_batch_test(self):
        """Test batch KS testing."""
        ks_test = KSSimilarityTest(significance_level=0.05)

        predictions = [
            np.array([0.1, 0.2, 0.4, 0.2, 0.1]),
            np.array([0.15, 0.25, 0.35, 0.15, 0.1]),
        ]
        actuals = [
            np.array([0.12, 0.18, 0.42, 0.18, 0.1]),
            np.array([0.14, 0.26, 0.36, 0.14, 0.1]),
        ]
        labels = ["persona_1", "persona_2"]

        results = ks_test.batch_test(predictions, actuals, labels)

        assert "individual_results" in results
        assert "aggregate" in results
        assert len(results["individual_results"]) == 2
        assert "mean_similarity" in results["aggregate"]
        assert "pass_rate" in results["aggregate"]

    def test_compare_to_baseline(self):
        """Test comparison to baseline distribution."""
        ks_test = KSSimilarityTest(significance_level=0.05)

        predicted = np.array([0.1, 0.2, 0.4, 0.2, 0.1])
        actual = np.array([0.12, 0.18, 0.42, 0.18, 0.1])
        baseline = np.array([0.2, 0.2, 0.2, 0.2, 0.2])  # Uniform

        results = ks_test.compare_to_baseline(predicted, actual, baseline)

        assert "model" in results
        assert "baseline" in results
        assert "improvement" in results

        assert results["improvement"]["better_than_baseline"]
        assert results["improvement"]["absolute"] > 0
