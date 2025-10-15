from __future__ import annotations
from typing import Dict, List, Tuple, Optional
import numpy as np
from pathlib import Path
import json

# Import config
try:
    from .config import (
        MIXTURE_TAU_DEFAULT,
        MIXTURE_USE_ENTMAX,
        MIXTURE_ENTMAX_ALPHA,
        MIXTURE_MIN_WEIGHT_THRESHOLD,
    )
except ImportError:
    # Fallback defaults
    MIXTURE_TAU_DEFAULT = 0.8
    MIXTURE_USE_ENTMAX = False
    MIXTURE_ENTMAX_ALPHA = 1.3
    MIXTURE_MIN_WEIGHT_THRESHOLD = 0.01

# Path to twin bank (pre-computed twin embeddings)
TWIN_BANK_PATH = Path("DATA/twin_bank.json")


class TwinMixture:
    """
    Mixture model for twin selection using cosine similarity and temperature scaling.

    This class computes mixture weights over a bank of twins using cosine similarity
    followed by temperature-scaled softmax (or optionally sparse entmax).
    """

    def __init__(
        self,
        twin_bank: Dict[str, np.ndarray],
        tau: float = MIXTURE_TAU_DEFAULT,
        sparse_entmax: bool = MIXTURE_USE_ENTMAX,
        entmax_alpha: float = MIXTURE_ENTMAX_ALPHA,
    ):
        """
        Initialize twin mixture model.

        Args:
            twin_bank: Dictionary mapping twin_id -> 15-D embedding vector
            tau: Temperature for softmax (lower = more peaked, higher = smoother)
            sparse_entmax: If True, use entmax instead of softmax for sparse weights
            entmax_alpha: Alpha parameter for entmax (1.0 = softmax, higher = more sparse)

        Examples:
            >>> twin_bank = load_twin_bank()
            >>> mixture = TwinMixture(twin_bank, tau=0.8)
            >>> weights = mixture.weights(query_vec)
            >>> primary_id = mixture.primary(query_vec)
        """
        self.twin_bank = twin_bank
        self.tau = tau
        self.sparse_entmax = sparse_entmax
        self.entmax_alpha = entmax_alpha

        # Validate twin bank
        if not twin_bank:
            raise ValueError("Twin bank cannot be empty")

        # Ensure all embeddings are 15-D
        for twin_id, embedding in twin_bank.items():
            if len(embedding) != 15:
                raise ValueError(f"Twin {twin_id} has embedding dim {len(embedding)}, expected 15")

    def weights(self, query_vec: np.ndarray) -> Dict[str, float]:
        """
        Compute mixture weights for a query vector.

        Uses cosine similarity followed by temperature-scaled softmax.

        Args:
            query_vec: 15-D query embedding vector

        Returns:
            Dictionary mapping twin_id -> weight (sums to 1.0)

        Examples:
            >>> weights = mixture.weights(user_embedding)
            >>> print(weights)
            {'k0': 0.15, 'k1': 0.60, 'k2': 0.25}
        """
        if len(query_vec) != 15:
            raise ValueError(f"Query vector has dim {len(query_vec)}, expected 15")

        # Compute cosine similarities
        similarities = {}
        for twin_id, twin_embed in self.twin_bank.items():
            sim = cosine_similarity(query_vec, twin_embed)
            similarities[twin_id] = sim

        # Apply temperature scaling and normalization
        if self.sparse_entmax:
            # Use entmax for sparse weights
            weights = self._entmax_weights(similarities)
        else:
            # Use softmax
            weights = self._softmax_weights(similarities)

        # Filter out very small weights
        weights = {
            tid: w for tid, w in weights.items()
            if w >= MIXTURE_MIN_WEIGHT_THRESHOLD
        }

        # Re-normalize after filtering
        total = sum(weights.values())
        if total > 0:
            weights = {tid: w / total for tid, w in weights.items()}

        return weights

    def primary(self, query_vec: np.ndarray) -> str:
        """
        Get the primary twin ID (highest weight).

        Args:
            query_vec: 15-D query embedding vector

        Returns:
            Twin ID with highest mixture weight

        Examples:
            >>> primary_twin = mixture.primary(user_embedding)
            >>> print(primary_twin)
            'k1'
        """
        weights = self.weights(query_vec)
        if not weights:
            return ""

        primary_id = max(weights.items(), key=lambda x: x[1])[0]
        return primary_id

    def _softmax_weights(self, similarities: Dict[str, float]) -> Dict[str, float]:
        """Apply temperature-scaled softmax to similarities."""
        # Apply temperature scaling
        scaled_sims = {tid: sim / self.tau for tid, sim in similarities.items()}

        # Softmax with numerical stability
        max_sim = max(scaled_sims.values())
        exp_sims = {tid: np.exp(sim - max_sim) for tid, sim in scaled_sims.items()}

        total = sum(exp_sims.values())
        if total == 0:
            # Uniform fallback
            n = len(similarities)
            return {tid: 1.0 / n for tid in similarities.keys()}

        weights = {tid: exp_sim / total for tid, exp_sim in exp_sims.items()}
        return weights

    def _entmax_weights(self, similarities: Dict[str, float]) -> Dict[str, float]:
        """
        Apply sparse entmax transformation to similarities.

        Note: This is a simplified entmax. For production, consider using
        the entmax library: https://github.com/deep-spin/entmax
        """
        # For now, use a simpler sparsemax approximation
        # (Full entmax requires more complex root-finding)

        # Scale by temperature
        scaled_sims = {tid: sim / self.tau for tid, sim in similarities.items()}

        # Sort similarities
        sorted_items = sorted(scaled_sims.items(), key=lambda x: x[1], reverse=True)

        # Sparsemax algorithm
        twin_ids = [tid for tid, _ in sorted_items]
        values = np.array([sim for _, sim in sorted_items])

        # Find threshold
        cumsum = np.cumsum(values)
        k_array = np.arange(1, len(values) + 1)
        threshold_vals = (cumsum - 1) / k_array

        support = values > threshold_vals
        k_star = np.where(support)[0][-1] + 1 if support.any() else 1

        tau_star = threshold_vals[k_star - 1]

        # Compute weights
        weights_array = np.maximum(values - tau_star, 0)

        # Map back to twin IDs
        weights = {twin_ids[i]: float(weights_array[i]) for i in range(len(twin_ids))}

        return weights

    def set_temperature(self, tau: float):
        """
        Update temperature parameter.

        Args:
            tau: New temperature value (lower = more peaked, higher = smoother)
        """
        if tau <= 0:
            raise ValueError(f"Temperature must be positive, got {tau}")
        self.tau = tau


def load_twin_bank() -> Dict[str, np.ndarray]:
    """
    Load pre-computed twin embeddings from the twin bank.

    Returns:
        Dictionary mapping twin_id -> 15-D embedding vector
    """
    if not TWIN_BANK_PATH.exists():
        # Return mock twin bank with 15-D embeddings for development
        personas_path = Path("DATA/personas.json")
        if personas_path.exists():
            personas_data = json.loads(personas_path.read_text())
            personas = personas_data.get("personas", [])

            # Create mock embeddings for each persona
            twin_bank = {}
            for i, persona in enumerate(personas):
                twin_id = persona["id"]
                # Create deterministic mock embedding based on persona traits
                psychographic_tags = persona.get("psychographic_tags", [])

                # Initialize 15-D vector [8 behavior + 4 psychographic + 3 demographic]
                embedding = np.zeros(15, dtype=np.float32)

                # Behavior features (8-D) - mock based on persona type
                if "price_sensitive" in psychographic_tags or "budget_conscious" in psychographic_tags:
                    embedding[0] = 0.9  # High price sensitivity
                    embedding[4] = 0.3  # Low impulse
                elif "quality_focused" in psychographic_tags or "premium_buyer" in psychographic_tags:
                    embedding[0] = 0.2  # Low price sensitivity
                    embedding[2] = 0.9  # High quality focus
                    embedding[5] = 0.8  # High research depth

                # Promo response
                if "deal_seeker" in psychographic_tags:
                    embedding[1] = 0.9
                else:
                    embedding[1] = 0.5

                # Delivery sensitivity
                if "time_conscious" in psychographic_tags or "convenience_focused" in psychographic_tags:
                    embedding[2] = 0.9
                else:
                    embedding[2] = 0.5

                # Psychographic features (4-D)
                embedding[8] = 1.0 if "price_sensitive" in psychographic_tags else 0.3   # Thrift
                embedding[9] = 1.0 if "innovation_seeker" in psychographic_tags else 0.3  # Novelty
                embedding[10] = 1.0 if "quality_focused" in psychographic_tags else 0.3   # Quality
                embedding[11] = 1.0 if "time_conscious" in psychographic_tags else 0.3    # Speed

                # Demographic features (3-D) - mock defaults
                embedding[12] = 0.5  # Age (varied)
                embedding[13] = 0.6  # Urban (slightly urban-leaning)
                embedding[14] = 0.5  # Gender (balanced)

                twin_bank[twin_id] = embedding

            return twin_bank
        else:
            # Fallback: minimal mock twin bank
            return {
                "k0": np.array([0.9, 0.8, 0.4, 0.3, 0.3, 0.5, 0.6, 0.8, 1.0, 0.2, 0.4, 0.3, 0.5, 0.6, 0.5], dtype=np.float32),
                "k1": np.array([0.2, 0.4, 0.7, 0.6, 0.5, 0.8, 0.7, 0.8, 0.3, 0.5, 0.9, 0.4, 0.5, 0.6, 0.5], dtype=np.float32),
                "k2": np.array([0.5, 0.9, 0.6, 0.5, 0.7, 0.6, 0.8, 0.8, 0.5, 0.8, 0.6, 0.7, 0.5, 0.6, 0.5], dtype=np.float32),
            }

    # Load from file
    with open(TWIN_BANK_PATH) as f:
        data = json.load(f)

    twin_bank = {}

    # Handle nested structure: {"version": "...", "twins": [...]}
    if "twins" in data and isinstance(data["twins"], list):
        for twin_obj in data["twins"]:
            twin_id = twin_obj.get("id")
            center = twin_obj.get("center")
            if twin_id and center:
                twin_bank[twin_id] = np.array(center, dtype=np.float32)
    else:
        # Handle flat structure: {twin_id: [embedding]}
        for twin_id, embedding_list in data.items():
            if isinstance(embedding_list, list):
                twin_bank[twin_id] = np.array(embedding_list, dtype=np.float32)

    return twin_bank


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity in range [-1, 1]
    """
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(np.dot(vec1, vec2) / (norm1 * norm2))


def responsibilities(user_embed: np.ndarray, twin_bank: Optional[Dict[str, np.ndarray]] = None) -> Dict[str, float]:
    """
    Compute mixture weights (responsibilities) for each twin using cosine similarity + softmax.

    This is a legacy wrapper around TwinMixture for backward compatibility.

    Args:
        user_embed: 15-D user embedding
        twin_bank: Dictionary of twin embeddings (loaded if not provided)

    Returns:
        Dictionary mapping twin_id -> weight (sums to 1.0)
    """
    if twin_bank is None:
        twin_bank = load_twin_bank()

    if not twin_bank:
        return {}

    # Use TwinMixture class
    mixture = TwinMixture(twin_bank, tau=MIXTURE_TAU_DEFAULT)
    return mixture.weights(user_embed)


def primary_twin(weights: Dict[str, float]) -> Tuple[str, float]:
    """
    Select the primary twin with the highest mixture weight.

    Args:
        weights: Dictionary of twin weights

    Returns:
        Tuple of (twin_id, weight)
    """
    if not weights:
        return ("", 0.0)

    primary = max(weights.items(), key=lambda x: x[1])
    return primary


def calibrate_temperature(
    validation_data: List[Tuple[np.ndarray, str]],
    twin_bank: Dict[str, np.ndarray],
    tau_range: Tuple[float, float] = (0.1, 2.0),
    n_steps: int = 20,
) -> float:
    """
    Calibrate temperature parameter using validation data.

    Performs grid search to find the temperature that minimizes negative log-likelihood.

    Args:
        validation_data: List of (query_vec, true_twin_id) pairs
        twin_bank: Dictionary of twin embeddings
        tau_range: Range of temperatures to search (min, max)
        n_steps: Number of grid points

    Returns:
        Optimal temperature value

    Examples:
        >>> # Assuming you have validation data
        >>> val_data = [(query1, 'k0'), (query2, 'k1'), ...]
        >>> optimal_tau = calibrate_temperature(val_data, twin_bank)
        >>> print(f"Optimal temperature: {optimal_tau}")
    """
    tau_min, tau_max = tau_range
    tau_values = np.linspace(tau_min, tau_max, n_steps)

    best_tau = MIXTURE_TAU_DEFAULT
    best_nll = float('inf')

    for tau in tau_values:
        mixture = TwinMixture(twin_bank, tau=tau)

        # Compute negative log-likelihood
        nll = 0.0
        for query_vec, true_twin in validation_data:
            weights = mixture.weights(query_vec)
            prob = weights.get(true_twin, 1e-10)  # Small epsilon to avoid log(0)
            nll -= np.log(prob)

        nll /= len(validation_data)

        if nll < best_nll:
            best_nll = nll
            best_tau = tau

    return best_tau
