from __future__ import annotations
from typing import Any, Dict, List, Optional
import numpy as np
from pathlib import Path

# Embedding dimensions per spec
BEHAVIOR_DIM = 8
PSYCHOGRAPHIC_DIM = 4
DEMOGRAPHIC_DIM = 3
FUSED_DIM = 15  # 8 + 4 + 3

# Import config (will use lazy import for torch to avoid dependency if not needed)
try:
    from .config import (
        FUSION_HIDDEN_DIM,
        FUSION_DROPOUT,
        FUSION_ACTIVATION,
        FUSION_USE_LAYER_NORM,
        FUSION_MODEL_PATH,
    )
except ImportError:
    # Fallback defaults if config not available
    FUSION_HIDDEN_DIM = 32
    FUSION_DROPOUT = 0.1
    FUSION_ACTIVATION = "gelu"
    FUSION_USE_LAYER_NORM = True
    FUSION_MODEL_PATH = Path("artifacts/fusion_mlp.pt")

# Global fusion MLP instance (lazy loaded)
_fusion_mlp = None


class FusionMLP:
    """
    Learned fusion network that transforms concatenated embeddings.

    Architecture:
        Concat(8D + 4D + 3D) → LayerNorm → Linear(15 → 32) → GELU → Dropout → Linear(32 → 15)

    This provides a learnable non-linear transformation instead of simple concatenation.
    """

    def __init__(
        self,
        hidden_dim: int = FUSION_HIDDEN_DIM,
        dropout: float = FUSION_DROPOUT,
        activation: str = FUSION_ACTIVATION,
        use_layer_norm: bool = FUSION_USE_LAYER_NORM,
    ):
        """
        Initialize fusion MLP.

        Args:
            hidden_dim: Hidden layer dimension
            dropout: Dropout probability
            activation: Activation function name ('gelu', 'relu', 'tanh')
            use_layer_norm: Whether to use LayerNorm
        """
        self.hidden_dim = hidden_dim
        self.dropout = dropout
        self.activation_name = activation
        self.use_layer_norm = use_layer_norm
        self.trained = False

        # Lazy load PyTorch
        try:
            import torch
            import torch.nn as nn
            self.torch = torch
            self.nn = nn
            self._build_network()
        except ImportError:
            # PyTorch not available, will fall back to concat-only mode
            self.torch = None
            self.nn = None

    def _build_network(self):
        """Build the MLP layers."""
        if self.torch is None:
            return

        layers = []

        # Layer norm
        if self.use_layer_norm:
            layers.append(self.nn.LayerNorm(FUSED_DIM))

        # First linear layer
        layers.append(self.nn.Linear(FUSED_DIM, self.hidden_dim))

        # Activation
        if self.activation_name == "gelu":
            layers.append(self.nn.GELU())
        elif self.activation_name == "relu":
            layers.append(self.nn.ReLU())
        elif self.activation_name == "tanh":
            layers.append(self.nn.Tanh())
        else:
            layers.append(self.nn.GELU())  # Default

        # Dropout
        layers.append(self.nn.Dropout(self.dropout))

        # Output layer
        layers.append(self.nn.Linear(self.hidden_dim, FUSED_DIM))

        self.model = self.nn.Sequential(*layers)
        self.model.eval()  # Start in eval mode

    def forward(self, concat_vec: np.ndarray) -> np.ndarray:
        """
        Apply learned fusion to concatenated vector.

        Args:
            concat_vec: 15-D concatenated [behavior, psychographic, demographic]

        Returns:
            15-D fused embedding after MLP transformation
        """
        if self.torch is None or not self.trained:
            # Fall back to identity (return as-is)
            return concat_vec

        # Convert to tensor
        x = self.torch.from_numpy(concat_vec).float()

        # Forward pass (no gradient needed for inference)
        with self.torch.no_grad():
            output = self.model(x)

        # Convert back to numpy
        return output.numpy().astype(np.float32)

    def load_weights(self, path: Optional[Path] = None) -> bool:
        """
        Load trained weights from file.

        Args:
            path: Path to weights file (.pt). If None, uses default from config.

        Returns:
            True if loaded successfully, False otherwise
        """
        if self.torch is None:
            return False

        if path is None:
            path = FUSION_MODEL_PATH

        if not Path(path).exists():
            return False

        try:
            state_dict = self.torch.load(path, map_location='cpu')
            self.model.load_state_dict(state_dict)
            self.model.eval()
            self.trained = True
            return True
        except Exception:
            return False

    def save_weights(self, path: Optional[Path] = None):
        """
        Save trained weights to file.

        Args:
            path: Path to save weights (.pt). If None, uses default from config.
        """
        if self.torch is None or not self.trained:
            return

        if path is None:
            path = FUSION_MODEL_PATH

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.torch.save(self.model.state_dict(), path)


def encode_cta(cta_seq: List[Dict[str, Any]]) -> np.ndarray:
    """
    Encode a sequence of CTA (Click-Through-Action) steps into an 8-D behavioral embedding.

    Args:
        cta_seq: List of CTA steps with context and actions

    Returns:
        8-D numpy array representing behavioral features
    """
    if not cta_seq:
        return np.zeros(BEHAVIOR_DIM, dtype=np.float32)

    # Extract behavioral signals from CTA sequence
    # Features: [avg_price_sensitivity, promo_response, delivery_sensitivity,
    #           brand_loyalty, impulse_score, research_depth, frequency, recency]

    features = np.zeros(BEHAVIOR_DIM, dtype=np.float32)

    for cta in cta_seq:
        context = cta.get("context", {})

        # Price sensitivity (0-1, higher = more sensitive)
        price_mean = context.get("price_mean", 0)
        if price_mean > 0:
            features[0] += 1.0 / (1.0 + price_mean / 100.0)  # Normalize

        # Promo response (0-1, higher = more responsive to promos)
        if context.get("promo_badge"):
            features[1] += 1.0

        # Delivery sensitivity (0-1, higher = prefers fast delivery)
        delivery_days = context.get("delivery_eta_days", 5)
        features[2] += max(0.0, 1.0 - delivery_days / 10.0)

        # Brand loyalty (mock - would analyze brand patterns)
        features[3] += 0.5

        # Impulse score (mock - would analyze time to purchase)
        task = cta.get("task", "")
        if task == "choose_product":
            features[4] += 0.7

        # Research depth (mock - would count refine actions)
        if task == "refine":
            features[5] += 1.0

        # Frequency score
        features[6] += 1.0

        # Recency (most recent = 1.0)
        features[7] = 1.0

    # Normalize by sequence length
    if len(cta_seq) > 0:
        features[:6] /= len(cta_seq)
        features[6] = min(1.0, features[6] / 10.0)  # Cap frequency

    return features

def project_psychographics(profile_vec: Optional[List[float]]) -> np.ndarray:
    """
    Extract psychographic features from a profile vector.

    Args:
        profile_vec: 7-D profile vector [thrift, novelty, quality_focus, speed_focus, age, urban, female]

    Returns:
        4-D numpy array [thrift, novelty, quality_focus, speed_focus]
    """
    if not profile_vec or len(profile_vec) < 4:
        return np.zeros(PSYCHOGRAPHIC_DIM, dtype=np.float32)

    # Extract first 4 dimensions (psychographic)
    return np.array(profile_vec[:4], dtype=np.float32)

def embed_demographics(profile_vec: Optional[List[float]]) -> np.ndarray:
    """
    Extract demographic features from a profile vector.

    Args:
        profile_vec: 7-D profile vector [thrift, novelty, quality_focus, speed_focus, age, urban, female]

    Returns:
        3-D numpy array [age_25_34, urban, female]
    """
    if not profile_vec or len(profile_vec) < 7:
        return np.zeros(DEMOGRAPHIC_DIM, dtype=np.float32)

    # Extract last 3 dimensions (demographic)
    return np.array(profile_vec[4:7], dtype=np.float32)

def fuse_joint(
    behavior_embed: np.ndarray,
    psychographic_embed: np.ndarray,
    demographic_embed: np.ndarray,
    use_learned_fusion: bool = False
) -> np.ndarray:
    """
    Fuse behavior, psychographic, and demographic embeddings into a single 15-D vector.

    Can use either simple concatenation (legacy) or learned fusion with MLP.

    Args:
        behavior_embed: 8-D behavioral embedding
        psychographic_embed: 4-D psychographic embedding
        demographic_embed: 3-D demographic embedding
        use_learned_fusion: If True, apply learned MLP. If False, use concat only.

    Returns:
        15-D fused embedding
    """
    # Ensure correct dimensions
    if len(behavior_embed) != BEHAVIOR_DIM:
        behavior_embed = np.resize(behavior_embed, BEHAVIOR_DIM)
    if len(psychographic_embed) != PSYCHOGRAPHIC_DIM:
        psychographic_embed = np.resize(psychographic_embed, PSYCHOGRAPHIC_DIM)
    if len(demographic_embed) != DEMOGRAPHIC_DIM:
        demographic_embed = np.resize(demographic_embed, DEMOGRAPHIC_DIM)

    # Concatenate into 15-D vector
    concat_vec = np.concatenate([
        behavior_embed,
        psychographic_embed,
        demographic_embed
    ]).astype(np.float32)

    # Apply learned fusion if requested
    if use_learned_fusion:
        global _fusion_mlp
        if _fusion_mlp is None:
            _fusion_mlp = FusionMLP()
            _fusion_mlp.load_weights()  # Try to load trained weights

        return _fusion_mlp.forward(concat_vec)

    return concat_vec


def build_twin_embedding(
    behavior8: np.ndarray,
    psycho4: np.ndarray,
    demo3: np.ndarray,
    *,
    use_learned_fusion: bool = False
) -> np.ndarray:
    """
    Public API for building twin embeddings with optional learned fusion.

    This is the main entry point for creating twin embeddings from components.

    Args:
        behavior8: 8-D behavioral features
        psycho4: 4-D psychographic features
        demo3: 3-D demographic features
        use_learned_fusion: If True, apply learned MLP transformation

    Returns:
        15-D twin embedding (float32)

    Examples:
        >>> # Legacy mode (simple concatenation)
        >>> embedding = build_twin_embedding(behavior, psycho, demo)

        >>> # Learned fusion mode (with trained MLP)
        >>> embedding = build_twin_embedding(behavior, psycho, demo, use_learned_fusion=True)
    """
    return fuse_joint(behavior8, psycho4, demo3, use_learned_fusion=use_learned_fusion)


def get_fusion_mlp() -> Optional[FusionMLP]:
    """
    Get the global fusion MLP instance.

    Returns:
        FusionMLP instance if available, None otherwise
    """
    global _fusion_mlp
    if _fusion_mlp is None:
        _fusion_mlp = FusionMLP()
        _fusion_mlp.load_weights()
    return _fusion_mlp
