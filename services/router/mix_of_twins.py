from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
import math
import numpy as np

from services.router.embedding_loader import EmbeddingLoader


class MixtureOfTwins:
    """
    Mixture-of-twins router with configurable embedding backend.

    Supports:
    - Legacy 15-D embeddings from twin_bank.json
    - New 256-D embeddings from trained encoder

    Feature flag in CONFIGS/discovery.yaml controls backend.
    """

    def __init__(self, config_path: Path = Path("CONFIGS/discovery.yaml")):
        """
        Initialize mixture router.

        Args:
            config_path: Path to discovery config
        """
        self.loader = EmbeddingLoader(config_path)
        self.twin_centers = self.loader.get_twin_centers()
        self.temperature = self.loader.get_temperature()

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

    def _softmax(self, scores: List[float], temperature: float) -> List[float]:
        """Apply softmax with temperature."""
        # Numerical stability: subtract max
        max_score = max(scores) if scores else 0.0
        exps = [math.exp((s - max_score) / max(temperature, 1e-6)) for s in scores]
        total = sum(exps) or 1.0
        return [e / total for e in exps]

    def compute_responsibilities(
        self,
        session_embedding: np.ndarray
    ) -> Dict[str, float]:
        """
        Compute mixture responsibilities (soft assignment).

        Args:
            session_embedding: Session embedding vector (normalized)

        Returns:
            Dict mapping twin_id -> responsibility weight
        """
        # Compute similarities to all twin centers
        twin_ids = list(self.twin_centers.keys())
        similarities = [
            self._cosine_similarity(session_embedding, self.twin_centers[tid])
            for tid in twin_ids
        ]

        # Apply softmax
        weights = self._softmax(similarities, self.temperature)

        # Return as dict
        responsibilities = {
            tid: float(w)
            for tid, w in zip(twin_ids, weights)
        }

        # Sort by weight (descending) then by ID (ascending) for determinism
        responsibilities = dict(
            sorted(responsibilities.items(), key=lambda kv: (-kv[1], kv[0]))
        )

        return responsibilities

    def primary_twin(
        self,
        responsibilities: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Select primary twin (highest responsibility).

        Args:
            responsibilities: Dict mapping twin_id -> weight

        Returns:
            Dict with primary twin info:
                - id: twin ID
                - label: human-readable label
                - weight: responsibility weight
        """
        if not responsibilities:
            return {"id": None, "label": None, "weight": 0.0}

        # Primary is already first due to sorting in compute_responsibilities
        primary_id = list(responsibilities.keys())[0]
        primary_weight = responsibilities[primary_id]

        # Get label from loader
        twin_info = self.loader.twins.get(primary_id, {})
        label = twin_info.get("label", primary_id)

        return {
            "id": primary_id,
            "label": label,
            "weight": primary_weight
        }

    def route(
        self,
        session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route session to twin mixture.

        Args:
            session_data: Session information
                - For legacy: {"embedding": [15-D vector]}
                - For encoder: {"seq_tokens": [...], ...}

        Returns:
            Dict with routing results:
                - responsibilities: Dict[twin_id, weight]
                - primary: Dict with primary twin info
                - embedding_dim: Dimension of embedding used
                - backend: "legacy" or "encoder"
        """
        # Encode session to embedding
        embedding = self.loader.encode_session(session_data)

        # Compute responsibilities
        responsibilities = self.compute_responsibilities(embedding)

        # Select primary
        primary = self.primary_twin(responsibilities)

        return {
            "responsibilities": responsibilities,
            "primary": primary,
            "embedding_dim": self.loader.get_embedding_dim(),
            "backend": "encoder" if self.loader.use_encoder else "legacy"
        }


def responsibilities(
    embedding: List[float],
    bank: Dict[str, Any]
) -> Dict[str, float]:
    """
    Legacy compatibility function.

    Mirrors the API of src/models/mixture.py:responsibilities()
    but routes through the new MixtureOfTwins router.

    Args:
        embedding: List of floats (15-D or 256-D)
        bank: Twin bank dict (can be empty, will use config-based loader)

    Returns:
        Dict mapping twin_id -> weight
    """
    # Convert to numpy
    emb = np.array(embedding, dtype=np.float32)

    # Create router
    router = MixtureOfTwins()

    # Compute responsibilities
    # For legacy compatibility, assume embedding is already computed
    session_data = {"embedding": embedding}
    result = router.route(session_data)

    return result["responsibilities"]


def primary_twin(
    weights: Dict[str, float],
    bank: Dict[str, Any]
) -> Dict[str, str] | None:
    """
    Legacy compatibility function.

    Mirrors the API of src/models/mixture.py:primary_twin()

    Args:
        weights: Dict mapping twin_id -> weight
        bank: Twin bank dict (not used, kept for compatibility)

    Returns:
        Dict with primary twin ID and label
    """
    if not weights:
        return None

    # Create router to access twin labels
    router = MixtureOfTwins()

    # Select primary
    primary = router.primary_twin(weights)

    return {
        "id": primary["id"],
        "label": primary["label"]
    }
