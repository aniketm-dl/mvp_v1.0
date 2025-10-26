from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from src.ssr.trainer import SSRTrainer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SSRInference:
    """
    Inference engine for SSR (Semantic Similarity Rating) model.

    Provides fast prediction of Likert distributions for new stimuli.
    """

    def __init__(self, model_path: Path, device: Optional[str] = None):
        """
        Initialize SSR inference engine.

        Args:
            model_path: Path to saved SSR model directory
            device: Device to run inference on (cuda/cpu)
        """
        self.model_path = model_path
        self.device = device

        # Load trained model
        logger.info(f"Loading SSR model from {model_path}")
        self.trainer = SSRTrainer.load_complete_model(model_path, device=device)
        logger.info("✅ SSR model loaded and ready for inference")

    def predict(
        self,
        stimulus_text: str,
        return_distribution: bool = True,
    ) -> Dict[str, any]:
        """
        Predict Likert rating for a stimulus.

        Args:
            stimulus_text: Input text (e.g., "20% off all laptops")
            return_distribution: Whether to return full distribution

        Returns:
            Dict with:
            - mean: Expected Likert rating (1-5)
            - std: Standard deviation
            - mode: Most likely rating
            - distribution: P(Likert=1..5) (if return_distribution=True)
        """
        distribution, metrics = self.trainer.predict_likert_distribution(stimulus_text)

        result = metrics.copy()
        if return_distribution:
            result["distribution"] = distribution.tolist()

        return result

    def predict_batch(
        self,
        stimulus_texts: List[str],
        return_distributions: bool = False,
    ) -> List[Dict[str, any]]:
        """
        Predict Likert ratings for multiple stimuli.

        Args:
            stimulus_texts: List of input texts
            return_distributions: Whether to return full distributions

        Returns:
            List of prediction dicts
        """
        results = []
        for text in stimulus_texts:
            result = self.predict(text, return_distribution=return_distributions)
            results.append(result)

        return results

    def compare_scenarios(
        self,
        base_text: str,
        variant_texts: List[str],
        variant_ids: Optional[List[str]] = None,
    ) -> Dict[str, any]:
        """
        Compare base scenario against variants.

        Args:
            base_text: Base scenario text
            variant_texts: List of variant scenario texts
            variant_ids: Optional IDs for variants

        Returns:
            Dict with base prediction and deltas for each variant
        """
        # Predict base
        base_pred = self.predict(base_text, return_distribution=True)

        # Predict variants
        variants = []
        for i, text in enumerate(variant_texts):
            variant_id = variant_ids[i] if variant_ids else f"variant_{i+1}"
            variant_pred = self.predict(text, return_distribution=True)

            # Compute deltas
            delta_mean = variant_pred["mean"] - base_pred["mean"]
            delta_dist = (
                np.array(variant_pred["distribution"]) - np.array(base_pred["distribution"])
            ).tolist()

            variants.append({
                "id": variant_id,
                "text": text,
                "prediction": variant_pred,
                "delta_mean": delta_mean,
                "delta_distribution": delta_dist,
                "lift_percent": (delta_mean / base_pred["mean"]) * 100 if base_pred["mean"] > 0 else 0.0,
            })

        return {
            "base": {
                "text": base_text,
                "prediction": base_pred,
            },
            "variants": variants,
        }

    def get_model_info(self) -> Dict[str, any]:
        """Get information about loaded model."""
        return {
            "model_path": str(self.model_path),
            "embedding_dim": self.trainer.embedding_dim,
            "device": self.device,
            "base_model": self.trainer.base_model,
        }
