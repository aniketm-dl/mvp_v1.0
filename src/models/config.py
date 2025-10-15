"""
Configuration for twin encoding, mixture, and policy models.

This module centralizes all hyperparameters for:
- Learned fusion MLP in encoder
- Temperature calibration in mixture
- Policy head calibration
"""

from __future__ import annotations
from typing import Dict, Any
from pathlib import Path

# ==============================================================================
# ENCODER FUSION CONFIGURATION
# ==============================================================================

# Learned fusion MLP settings
FUSION_HIDDEN_DIM = 32
"""Hidden dimension for fusion MLP."""

FUSION_DROPOUT = 0.1
"""Dropout probability for fusion MLP."""

FUSION_ACTIVATION = "gelu"
"""Activation function: 'gelu', 'relu', 'tanh'."""

FUSION_WEIGHT_DECAY = 0.01
"""L2 regularization for fusion weights."""

FUSION_USE_LAYER_NORM = True
"""Whether to apply LayerNorm before MLP."""

FUSION_MODEL_PATH = Path("artifacts/fusion_mlp.pt")
"""Path to save/load trained fusion MLP weights."""

# ==============================================================================
# MIXTURE CONFIGURATION
# ==============================================================================

MIXTURE_TAU_DEFAULT = 0.8
"""Default temperature for softmax over cosine similarities.
Lower values (e.g., 0.5) make the distribution more peaked (sharper).
Higher values (e.g., 1.5) make it more uniform (smoother).
"""

MIXTURE_USE_ENTMAX = False
"""If True, use sparse entmax instead of softmax."""

MIXTURE_ENTMAX_ALPHA = 1.3
"""Alpha parameter for entmax (1.0 = softmax, higher = more sparse)."""

MIXTURE_MIN_WEIGHT_THRESHOLD = 0.01
"""Twins with weight below this are excluded from mixture."""

# ==============================================================================
# POLICY HEAD CONFIGURATION
# ==============================================================================

POLICY_CALIBRATION_ENABLED = True
"""Whether to apply probability calibration (Platt scaling)."""

POLICY_CALIBRATION_METHOD = "temperature"
"""Calibration method: 'temperature', 'platt', 'isotonic'."""

POLICY_TEMPERATURE_DEFAULT = 1.0
"""Default temperature for policy calibration."""

POLICY_TOP_K_FACTORS = 3
"""Number of top influential factors to return."""

# ==============================================================================
# ORCHESTRATOR CONFIGURATION
# ==============================================================================

ORCHESTRATOR_MAX_RETRIES = 1
"""Maximum retries for guardrail failures."""

ORCHESTRATOR_VERBALIZE_MODE = "concise"
"""Verbalization mode: 'concise', 'detailed', 'technical'."""

# ==============================================================================
# GUARDRAILS CONFIGURATION
# ==============================================================================

GUARDRAIL_BANNED_TOKENS = [
    "[price_sensitive]",
    "[quality_focused]",
    "[deal_seeker]",
    "[premium_buyer]",
    "[budget_conscious]",
    "[innovation_seeker]",
    "[time_conscious]",
    "[convenience_focused]",
]
"""List of persona taxonomy tokens to block in generation."""

GUARDRAIL_MAX_TOKENS = 100
"""Maximum allowed tokens in generated text."""

GUARDRAIL_REQUIRE_DECISION_FIRST = True
"""Whether first sentence must contain the decision."""

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_fusion_config() -> Dict[str, Any]:
    """
    Get fusion MLP configuration as a dictionary.

    Returns:
        Dictionary with fusion configuration
    """
    return {
        "hidden_dim": FUSION_HIDDEN_DIM,
        "dropout": FUSION_DROPOUT,
        "activation": FUSION_ACTIVATION,
        "weight_decay": FUSION_WEIGHT_DECAY,
        "use_layer_norm": FUSION_USE_LAYER_NORM,
        "model_path": str(FUSION_MODEL_PATH),
    }

def get_mixture_config() -> Dict[str, Any]:
    """
    Get mixture configuration as a dictionary.

    Returns:
        Dictionary with mixture configuration
    """
    return {
        "tau": MIXTURE_TAU_DEFAULT,
        "use_entmax": MIXTURE_USE_ENTMAX,
        "entmax_alpha": MIXTURE_ENTMAX_ALPHA,
        "min_weight_threshold": MIXTURE_MIN_WEIGHT_THRESHOLD,
    }

def get_policy_config() -> Dict[str, Any]:
    """
    Get policy head configuration as a dictionary.

    Returns:
        Dictionary with policy configuration
    """
    return {
        "calibration_enabled": POLICY_CALIBRATION_ENABLED,
        "calibration_method": POLICY_CALIBRATION_METHOD,
        "temperature": POLICY_TEMPERATURE_DEFAULT,
        "top_k_factors": POLICY_TOP_K_FACTORS,
    }

def get_guardrail_config() -> Dict[str, Any]:
    """
    Get guardrail configuration as a dictionary.

    Returns:
        Dictionary with guardrail configuration
    """
    return {
        "banned_tokens": GUARDRAIL_BANNED_TOKENS,
        "max_tokens": GUARDRAIL_MAX_TOKENS,
        "require_decision_first": GUARDRAIL_REQUIRE_DECISION_FIRST,
    }
