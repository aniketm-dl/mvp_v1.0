from __future__ import annotations

import logging
from typing import Dict, List, Tuple

import numpy as np
from scipy.stats import pearsonr, spearmanr

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CorrelationMetrics:
    """
    Correlation metrics for evaluating rating predictions.

    Computes Spearman (rank) and Pearson (linear) correlations.
    """

    def __init__(self, min_samples: int = 10):
        """
        Initialize correlation metrics.

        Args:
            min_samples: Minimum samples required for valid correlation
        """
        self.min_samples = min_samples

    def compute_spearman(
        self,
        predicted: np.ndarray,
        actual: np.ndarray,
    ) -> Tuple[float, float]:
        """
        Compute Spearman rank correlation.

        Args:
            predicted: Predicted ratings
            actual: Actual ratings

        Returns:
            (correlation, p_value)
        """
        if len(predicted) < self.min_samples or len(actual) < self.min_samples:
            logger.warning(f"Too few samples for correlation: {len(predicted)}")
            return 0.0, 1.0

        correlation, p_value = spearmanr(predicted, actual)
        return float(correlation), float(p_value)

    def compute_pearson(
        self,
        predicted: np.ndarray,
        actual: np.ndarray,
    ) -> Tuple[float, float]:
        """
        Compute Pearson linear correlation.

        Args:
            predicted: Predicted ratings
            actual: Actual ratings

        Returns:
            (correlation, p_value)
        """
        if len(predicted) < self.min_samples or len(actual) < self.min_samples:
            logger.warning(f"Too few samples for correlation: {len(predicted)}")
            return 0.0, 1.0

        correlation, p_value = pearsonr(predicted, actual)
        return float(correlation), float(p_value)

    def compute_all_metrics(
        self,
        predicted: np.ndarray,
        actual: np.ndarray,
    ) -> Dict[str, any]:
        """
        Compute all correlation metrics.

        Args:
            predicted: Predicted ratings
            actual: Actual ratings

        Returns:
            Dict with Spearman, Pearson, MAE, RMSE
        """
        # Spearman (primary metric for ordinal data like Likert)
        spearman_corr, spearman_p = self.compute_spearman(predicted, actual)

        # Pearson (linear correlation)
        pearson_corr, pearson_p = self.compute_pearson(predicted, actual)

        # Error metrics
        mae = float(np.mean(np.abs(predicted - actual)))
        rmse = float(np.sqrt(np.mean((predicted - actual) ** 2)))

        # Interpretation
        if spearman_corr >= 0.70:
            interpretation = "EXCELLENT: Strong positive correlation"
        elif spearman_corr >= 0.50:
            interpretation = "GOOD: Moderate positive correlation"
        elif spearman_corr >= 0.30:
            interpretation = "ACCEPTABLE: Weak positive correlation"
        else:
            interpretation = "POOR: Very weak or no correlation"

        return {
            "spearman": {
                "correlation": spearman_corr,
                "p_value": spearman_p,
                "significant": spearman_p < 0.05,
            },
            "pearson": {
                "correlation": pearson_corr,
                "p_value": pearson_p,
                "significant": pearson_p < 0.05,
            },
            "error_metrics": {
                "mae": mae,
                "rmse": rmse,
            },
            "interpretation": interpretation,
            "passes_threshold": spearman_corr >= 0.70,
        }

    def batch_correlations(
        self,
        predictions: List[np.ndarray],
        actuals: List[np.ndarray],
        labels: List[str],
    ) -> Dict[str, any]:
        """
        Compute correlations for multiple groups.

        Args:
            predictions: List of predicted rating arrays
            actuals: List of actual rating arrays
            labels: Labels for each group

        Returns:
            Dict with individual and aggregate results
        """
        results = []

        for pred, actual, label in zip(predictions, actuals, labels):
            result = self.compute_all_metrics(pred, actual)
            result["label"] = label
            results.append(result)

        # Aggregate statistics
        spearman_corrs = [r["spearman"]["correlation"] for r in results]
        pearson_corrs = [r["pearson"]["correlation"] for r in results]
        maes = [r["error_metrics"]["mae"] for r in results]
        rmses = [r["error_metrics"]["rmse"] for r in results]

        aggregate = {
            "individual_results": results,
            "aggregate": {
                "mean_spearman": float(np.mean(spearman_corrs)),
                "median_spearman": float(np.median(spearman_corrs)),
                "min_spearman": float(np.min(spearman_corrs)),
                "max_spearman": float(np.max(spearman_corrs)),
                "mean_pearson": float(np.mean(pearson_corrs)),
                "mean_mae": float(np.mean(maes)),
                "mean_rmse": float(np.mean(rmses)),
                "pass_rate": float(sum(r["passes_threshold"] for r in results) / len(results)),
            },
        }

        return aggregate

    def compute_confidence_interval(
        self,
        predicted: np.ndarray,
        actual: np.ndarray,
        confidence: float = 0.95,
        n_bootstrap: int = 1000,
    ) -> Dict[str, Tuple[float, float]]:
        """
        Compute bootstrap confidence intervals for correlations.

        Args:
            predicted: Predicted ratings
            actual: Actual ratings
            confidence: Confidence level (default 0.95 for 95% CI)
            n_bootstrap: Number of bootstrap samples

        Returns:
            Dict with confidence intervals for Spearman and Pearson
        """
        n = len(predicted)
        spearman_boots = []
        pearson_boots = []

        for _ in range(n_bootstrap):
            # Bootstrap sample
            indices = np.random.choice(n, size=n, replace=True)
            pred_boot = predicted[indices]
            actual_boot = actual[indices]

            # Compute correlations
            spearman_corr, _ = self.compute_spearman(pred_boot, actual_boot)
            pearson_corr, _ = self.compute_pearson(pred_boot, actual_boot)

            spearman_boots.append(spearman_corr)
            pearson_boots.append(pearson_corr)

        # Compute confidence intervals
        alpha = 1 - confidence
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100

        spearman_ci = (
            float(np.percentile(spearman_boots, lower_percentile)),
            float(np.percentile(spearman_boots, upper_percentile)),
        )

        pearson_ci = (
            float(np.percentile(pearson_boots, lower_percentile)),
            float(np.percentile(pearson_boots, upper_percentile)),
        )

        return {
            "spearman_ci": spearman_ci,
            "pearson_ci": pearson_ci,
            "confidence_level": confidence,
        }
