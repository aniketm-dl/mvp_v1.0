from __future__ import annotations

import logging
from typing import Dict, List, Tuple

import numpy as np
from scipy.stats import ks_2samp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KSSimilarityTest:
    """
    Kolmogorov-Smirnov (KS) similarity test for comparing distributions.

    Used to validate SSR predictions against actual human behavior distributions.
    """

    def __init__(self, significance_level: float = 0.05):
        """
        Initialize KS test.

        Args:
            significance_level: P-value threshold for statistical significance
        """
        self.significance_level = significance_level

    def compute_ks_statistic(
        self,
        predicted: np.ndarray,
        actual: np.ndarray,
    ) -> Tuple[float, float]:
        """
        Compute KS statistic between predicted and actual distributions.

        Args:
            predicted: Predicted distribution (e.g., Likert probabilities)
            actual: Actual distribution (e.g., observed human ratings)

        Returns:
            (ks_statistic, p_value)
        """
        # Convert probability distributions to samples if needed
        if len(predicted) <= 10:  # Assume it's a probability distribution
            predicted_samples = self._distribution_to_samples(predicted)
        else:
            predicted_samples = predicted

        if len(actual) <= 10:
            actual_samples = self._distribution_to_samples(actual)
        else:
            actual_samples = actual

        # Perform KS test
        statistic, p_value = ks_2samp(predicted_samples, actual_samples)

        return float(statistic), float(p_value)

    def compute_ks_similarity(
        self,
        predicted: np.ndarray,
        actual: np.ndarray,
    ) -> float:
        """
        Compute KS similarity score (1 - KS statistic).

        Higher is better. Target: ≥ 0.80

        Args:
            predicted: Predicted distribution
            actual: Actual distribution

        Returns:
            Similarity score in [0, 1]
        """
        ks_stat, _ = self.compute_ks_statistic(predicted, actual)
        similarity = 1.0 - ks_stat
        return float(similarity)

    def test_distributions(
        self,
        predicted: np.ndarray,
        actual: np.ndarray,
    ) -> Dict[str, any]:
        """
        Full KS test with interpretation.

        Args:
            predicted: Predicted distribution
            actual: Actual distribution

        Returns:
            Dict with statistic, p_value, similarity, significant, interpretation
        """
        ks_stat, p_value = self.compute_ks_statistic(predicted, actual)
        similarity = 1.0 - ks_stat

        # Determine if distributions are significantly different
        is_significant = p_value < self.significance_level

        # Interpretation
        if similarity >= 0.80:
            interpretation = "EXCELLENT: Distributions are very similar"
        elif similarity >= 0.70:
            interpretation = "GOOD: Distributions are similar"
        elif similarity >= 0.60:
            interpretation = "ACCEPTABLE: Distributions are moderately similar"
        else:
            interpretation = "POOR: Distributions differ substantially"

        return {
            "ks_statistic": ks_stat,
            "p_value": p_value,
            "similarity": similarity,
            "significant_difference": is_significant,
            "interpretation": interpretation,
            "passes_threshold": similarity >= 0.80,
        }

    def batch_test(
        self,
        predictions: List[np.ndarray],
        actuals: List[np.ndarray],
        labels: List[str],
    ) -> Dict[str, any]:
        """
        Test multiple prediction-actual pairs.

        Args:
            predictions: List of predicted distributions
            actuals: List of actual distributions
            labels: Labels for each pair (e.g., persona IDs)

        Returns:
            Dict with individual results and aggregate statistics
        """
        results = []

        for pred, actual, label in zip(predictions, actuals, labels):
            result = self.test_distributions(pred, actual)
            result["label"] = label
            results.append(result)

        # Compute aggregate statistics
        similarities = [r["similarity"] for r in results]
        pass_rate = sum(r["passes_threshold"] for r in results) / len(results)

        aggregate = {
            "individual_results": results,
            "aggregate": {
                "mean_similarity": float(np.mean(similarities)),
                "median_similarity": float(np.median(similarities)),
                "min_similarity": float(np.min(similarities)),
                "max_similarity": float(np.max(similarities)),
                "std_similarity": float(np.std(similarities)),
                "pass_rate": float(pass_rate),
                "num_tests": len(results),
            },
        }

        return aggregate

    def _distribution_to_samples(
        self,
        distribution: np.ndarray,
        n_samples: int = 1000,
    ) -> np.ndarray:
        """
        Convert probability distribution to samples.

        Args:
            distribution: Probability distribution (e.g., [0.1, 0.2, 0.4, 0.2, 0.1])
            n_samples: Number of samples to generate

        Returns:
            Array of samples
        """
        # Assume distribution corresponds to values [1, 2, 3, 4, 5] (Likert scale)
        values = np.arange(1, len(distribution) + 1)

        # Normalize distribution
        distribution = np.array(distribution)
        distribution = distribution / distribution.sum()

        # Generate samples
        samples = np.random.choice(values, size=n_samples, p=distribution)

        return samples

    def compare_to_baseline(
        self,
        predicted: np.ndarray,
        actual: np.ndarray,
        baseline: np.ndarray,
    ) -> Dict[str, any]:
        """
        Compare model predictions to a baseline.

        Args:
            predicted: Model predictions
            actual: Actual distribution
            baseline: Baseline predictions (e.g., uniform distribution)

        Returns:
            Dict with model and baseline results, plus improvement
        """
        model_result = self.test_distributions(predicted, actual)
        baseline_result = self.test_distributions(baseline, actual)

        improvement = model_result["similarity"] - baseline_result["similarity"]
        improvement_pct = (improvement / baseline_result["similarity"]) * 100

        return {
            "model": model_result,
            "baseline": baseline_result,
            "improvement": {
                "absolute": float(improvement),
                "percent": float(improvement_pct),
                "better_than_baseline": improvement > 0,
            },
        }
