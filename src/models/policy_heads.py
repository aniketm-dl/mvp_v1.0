from __future__ import annotations
from typing import Dict, List, Optional, Any
import numpy as np
from pathlib import Path
import pickle
import json

# Import config
try:
    from .config import (
        POLICY_CALIBRATION_ENABLED,
        POLICY_CALIBRATION_METHOD,
        POLICY_TEMPERATURE_DEFAULT,
        POLICY_TOP_K_FACTORS,
    )
except ImportError:
    # Fallback defaults
    POLICY_CALIBRATION_ENABLED = True
    POLICY_CALIBRATION_METHOD = "temperature"
    POLICY_TEMPERATURE_DEFAULT = 1.0
    POLICY_TOP_K_FACTORS = 3


class TwinPolicyHeadSet:
    """
    Fast policy heads for twin decision-making with probability calibration.

    This class loads pre-trained linear heads that map candidate features
    to probability distributions, enabling fast inference without LLM calls.

    Features:
    - Temperature/Platt scaling for calibrated probabilities
    - Top-K factor extraction for explainability
    - Per-twin and mixture-based predictions
    """

    def __init__(
        self,
        heads_dir: str = "artifacts/policy_heads",
        default_temp: float = POLICY_TEMPERATURE_DEFAULT,
        calibration_enabled: bool = POLICY_CALIBRATION_ENABLED,
    ):
        """
        Initialize policy head set.

        Args:
            heads_dir: Directory containing trained policy head weights
            default_temp: Default temperature for calibration
            calibration_enabled: Whether to apply probability calibration
        """
        self.heads_dir = Path(heads_dir)
        self.default_temp = default_temp
        self.calibration_enabled = calibration_enabled
        self.twin_heads: Dict[str, Dict[str, Any]] = {}
        self.loaded = False

        # Feature names for explainability (will be populated from data)
        self.feature_names = [
            "price",
            "quality_score",
            "brand_score",
            "delivery_days",
            "promo_discount",
            "reviews_count",
            "rating",
            "popularity",
        ]

    def load(self, twin_ids: Optional[List[str]] = None) -> bool:
        """
        Load policy heads for specified twins.

        Args:
            twin_ids: List of twin IDs to load. If None, loads all available.

        Returns:
            True if successful, False otherwise
        """
        if not self.heads_dir.exists():
            # No policy heads available - will fall back to LLM
            return False

        # Find available policy head files
        head_files = list(self.heads_dir.glob("*.pkl"))
        if not head_files:
            # Try JSON format
            head_files = list(self.heads_dir.glob("*.json"))

        if not head_files:
            return False

        # Load each policy head
        for head_file in head_files:
            twin_id = head_file.stem

            # Filter by requested twin_ids if provided
            if twin_ids and twin_id not in twin_ids:
                continue

            try:
                if head_file.suffix == ".pkl":
                    with open(head_file, "rb") as f:
                        head_data = pickle.load(f)
                else:  # .json
                    with open(head_file) as f:
                        head_data = json.load(f)
                        # Convert lists to numpy arrays
                        if isinstance(head_data, dict):
                            head_data = {
                                k: np.array(v, dtype=np.float32) if isinstance(v, list) else v
                                for k, v in head_data.items()
                            }

                # Set default temperature if not present
                if "temperature" not in head_data:
                    head_data["temperature"] = self.default_temp

                self.twin_heads[twin_id] = head_data

            except Exception as e:
                # Skip this head if loading fails
                continue

        self.loaded = len(self.twin_heads) > 0
        return self.loaded

    def predict_proba(
        self,
        twin_vec: np.ndarray,
        offer_feats: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """
        Predict calibrated class probabilities for buy/wait/no_buy decisions.

        Args:
            twin_vec: 15-D twin embedding vector
            offer_feats: Optional offer/product features

        Returns:
            Dictionary with calibrated probabilities, e.g.,
            {'buy': 0.22, 'wait': 0.48, 'no_buy': 0.30}

        Examples:
            >>> policy = TwinPolicyHeadSet()
            >>> policy.load()
            >>> probs = policy.predict_proba(twin_embedding)
            >>> print(probs)
            {'buy': 0.22, 'wait': 0.48, 'no_buy': 0.30}
        """
        # For now, return mock probabilities based on twin characteristics
        # This would be replaced with actual policy head predictions

        if offer_feats is not None and len(offer_feats) > 0:
            # Use first feature (e.g., price) to influence decision
            price_factor = offer_feats[0] if len(offer_feats) > 0 else 0.5
        else:
            price_factor = 0.5

        # Extract behavioral signals from twin_vec
        price_sensitivity = twin_vec[0] if len(twin_vec) > 0 else 0.5
        impulse_score = twin_vec[4] if len(twin_vec) > 4 else 0.5

        # Compute raw logits
        buy_logit = (1 - price_sensitivity) * price_factor + impulse_score
        wait_logit = 0.5
        no_buy_logit = price_sensitivity * (1 - price_factor)

        logits = np.array([buy_logit, wait_logit, no_buy_logit])

        # Apply temperature calibration
        if self.calibration_enabled:
            temp = self.default_temp
            logits = logits / temp

        # Softmax
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / np.sum(exp_logits)

        return {
            "buy": float(probs[0]),
            "wait": float(probs[1]),
            "no_buy": float(probs[2]),
        }

    def top_factors(
        self,
        twin_vec: np.ndarray,
        offer_feats: Optional[np.ndarray] = None,
        k: int = POLICY_TOP_K_FACTORS
    ) -> List[str]:
        """
        Return top-K influential factors for decision explainability.

        Args:
            twin_vec: 15-D twin embedding vector
            offer_feats: Optional offer/product features
            k: Number of top factors to return

        Returns:
            List of human-readable factor names (e.g., ['price', 'brand', 'delivery'])

        Examples:
            >>> factors = policy.top_factors(twin_embedding, offer_features, k=3)
            >>> print(factors)
            ['price', 'brand', 'delivery_days']
        """
        # Extract importance from twin embedding
        # This is a simplified heuristic - in production, you'd compute
        # feature importance from the linear weights

        factors_with_importance = []

        # Price sensitivity
        if len(twin_vec) > 0:
            factors_with_importance.append(("price", float(twin_vec[0])))

        # Promo response
        if len(twin_vec) > 1:
            factors_with_importance.append(("promo_discount", float(twin_vec[1])))

        # Delivery sensitivity
        if len(twin_vec) > 2:
            factors_with_importance.append(("delivery_days", float(twin_vec[2])))

        # Brand loyalty
        if len(twin_vec) > 3:
            factors_with_importance.append(("brand_score", float(twin_vec[3])))

        # Quality focus (from psychographic)
        if len(twin_vec) > 10:
            factors_with_importance.append(("quality_score", float(twin_vec[10])))

        # Novelty seeking
        if len(twin_vec) > 9:
            factors_with_importance.append(("novelty", float(twin_vec[9])))

        # Sort by importance (descending)
        factors_with_importance.sort(key=lambda x: x[1], reverse=True)

        # Return top-k factor names
        top_k_factors = [name for name, _ in factors_with_importance[:k]]

        return top_k_factors

    def predict_probs(
        self,
        twin_id: str,
        candidate_features: np.ndarray,
        candidate_ids: List[str]
    ) -> Dict[str, float]:
        """
        Predict probability distribution over candidates using policy head.

        Args:
            twin_id: ID of the twin
            candidate_features: NxD feature matrix for N candidates
            candidate_ids: List of candidate IDs

        Returns:
            Dictionary mapping candidate_id -> probability
        """
        if not self.loaded or twin_id not in self.twin_heads:
            # Fall back to uniform distribution
            n = len(candidate_ids)
            return {cid: 1.0 / n for cid in candidate_ids}

        head = self.twin_heads[twin_id]

        # Check if head contains weights (linear model)
        if "weights" in head and "bias" in head:
            weights = head["weights"]
            bias = head.get("bias", 0.0)
            temperature = head.get("temperature", self.default_temp)

            # Compute logits: features @ weights + bias
            logits = candidate_features @ weights + bias

            # Apply temperature calibration
            if self.calibration_enabled:
                logits = logits / temperature

            # Apply softmax
            exp_logits = np.exp(logits - np.max(logits))  # Numerical stability
            probs = exp_logits / np.sum(exp_logits)

            return {cid: float(prob) for cid, prob in zip(candidate_ids, probs)}

        # If head format is different, return uniform
        n = len(candidate_ids)
        return {cid: 1.0 / n for cid in candidate_ids}

    def predict_with_mixture(
        self,
        mixture_weights: Dict[str, float],
        candidate_features: np.ndarray,
        candidate_ids: List[str]
    ) -> Dict[str, float]:
        """
        Predict blended probability distribution using mixture weights.

        Args:
            mixture_weights: Dictionary of twin_id -> mixture weight
            candidate_features: NxD feature matrix for N candidates
            candidate_ids: List of candidate IDs

        Returns:
            Dictionary mapping candidate_id -> blended probability
        """
        if not self.loaded:
            # Fall back to uniform
            n = len(candidate_ids)
            return {cid: 1.0 / n for cid in candidate_ids}

        # Get probabilities from each twin
        blended_probs = {cid: 0.0 for cid in candidate_ids}

        for twin_id, weight in mixture_weights.items():
            if weight <= 0:
                continue

            twin_probs = self.predict_probs(twin_id, candidate_features, candidate_ids)

            # Add weighted twin probabilities
            for cid in candidate_ids:
                blended_probs[cid] += weight * twin_probs.get(cid, 0.0)

        # Normalize (should already sum to 1, but ensure it)
        total = sum(blended_probs.values())
        if total > 0:
            blended_probs = {cid: p / total for cid, p in blended_probs.items()}

        return blended_probs

    def calibrate(
        self,
        twin_id: str,
        validation_data: List[Tuple[np.ndarray, np.ndarray, int]],
        method: str = POLICY_CALIBRATION_METHOD
    ) -> float:
        """
        Calibrate policy head temperature using validation data.

        Args:
            twin_id: Twin ID to calibrate
            validation_data: List of (twin_vec, offer_feats, true_label) tuples
            method: Calibration method ('temperature', 'platt', 'isotonic')

        Returns:
            Optimal temperature value

        Examples:
            >>> val_data = [(twin_vec1, offer1, 0), (twin_vec2, offer2, 1), ...]
            >>> optimal_temp = policy.calibrate('k0', val_data)
        """
        if twin_id not in self.twin_heads:
            return self.default_temp

        if method == "temperature":
            return self._calibrate_temperature(twin_id, validation_data)
        elif method == "platt":
            # Platt scaling (fit logistic regression on logits)
            # For now, fall back to temperature
            return self._calibrate_temperature(twin_id, validation_data)
        else:
            return self.default_temp

    def _calibrate_temperature(
        self,
        twin_id: str,
        validation_data: List[Tuple[np.ndarray, np.ndarray, int]]
    ) -> float:
        """Simple temperature scaling calibration."""
        # Grid search for optimal temperature
        temps = np.linspace(0.1, 3.0, 30)
        best_temp = self.default_temp
        best_nll = float('inf')

        for temp in temps:
            nll = 0.0
            for twin_vec, offer_feats, true_label in validation_data:
                # Get probabilities with this temperature
                old_temp = self.default_temp
                self.default_temp = temp

                probs = self.predict_proba(twin_vec, offer_feats)
                labels = ["buy", "wait", "no_buy"]
                prob = probs.get(labels[true_label], 1e-10)

                nll -= np.log(prob)
                self.default_temp = old_temp

            nll /= len(validation_data)

            if nll < best_nll:
                best_nll = nll
                best_temp = temp

        # Update head with calibrated temperature
        self.twin_heads[twin_id]["temperature"] = best_temp
        return best_temp

    def available_twins(self) -> List[str]:
        """
        Get list of twins with loaded policy heads.

        Returns:
            List of twin IDs
        """
        return list(self.twin_heads.keys())

    def is_loaded(self) -> bool:
        """
        Check if policy heads are loaded.

        Returns:
            True if any heads are loaded
        """
        return self.loaded

    def set_calibration(self, enabled: bool):
        """
        Enable or disable probability calibration.

        Args:
            enabled: Whether to apply calibration
        """
        self.calibration_enabled = enabled
