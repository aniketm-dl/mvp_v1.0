from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

from src.ssr.inference import SSRInference

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SSRClient:
    """
    Client wrapper for SSR inference in Streamlit app.

    Provides simplified interface for the UI components.
    """

    def __init__(self, model_path: str):
        """
        Initialize SSR client.

        Args:
            model_path: Path to trained SSR model directory
        """
        self.model_path = Path(model_path)
        self.inference_engine = SSRInference(self.model_path)
        logger.info(f"✅ SSR client initialized: {model_path}")

    def predict(
        self,
        stimulus_text: str,
        persona_id: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Predict rating for a stimulus.

        Args:
            stimulus_text: Input scenario text
            persona_id: Optional persona ID for conditioning (not yet implemented)

        Returns:
            Prediction dict with mean, std, mode, distribution
        """
        prediction = self.inference_engine.predict(
            stimulus_text,
            return_distribution=True,
        )

        return prediction

    def predict_batch(
        self,
        stimulus_texts: List[str],
        persona_id: Optional[str] = None,
    ) -> List[Dict[str, any]]:
        """
        Predict ratings for multiple stimuli.

        Args:
            stimulus_texts: List of scenario texts
            persona_id: Optional persona ID

        Returns:
            List of prediction dicts
        """
        predictions = self.inference_engine.predict_batch(
            stimulus_texts,
            return_distributions=True,
        )

        return predictions

    def compare_scenarios(
        self,
        base_text: str,
        variant_texts: List[str],
        variant_ids: Optional[List[str]] = None,
    ) -> Dict[str, any]:
        """
        Compare base scenario against variants.

        Args:
            base_text: Base scenario
            variant_texts: List of variant scenarios
            variant_ids: Optional variant IDs

        Returns:
            Comparison dict with base and deltas
        """
        comparison = self.inference_engine.compare_scenarios(
            base_text,
            variant_texts,
            variant_ids,
        )

        return comparison

    def get_model_info(self) -> Dict[str, any]:
        """Get model metadata."""
        return self.inference_engine.get_model_info()
