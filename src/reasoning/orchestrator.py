"""
Orchestrator for policy-first decision making with verbalization.

This module implements the decide_then_verbalize workflow:
1. Use policy heads to get decision probabilities
2. Extract top influential factors
3. Call verbalizer to generate natural language
4. Apply guardrails to ensure quality
"""

from __future__ import annotations
from typing import Dict, Any, Tuple, Callable, Optional, List
import numpy as np

from src.models.policy_heads import TwinPolicyHeadSet
from src.reasoning.guardrails import (
    Guardrails,
    generate_fallback_reason,
    get_system_prompt_for_guardrails,
)


def default_verbalizer(payload: Dict[str, Any]) -> str:
    """
    Default verbalizer function that formats decision JSON into natural language.

    Args:
        payload: Decision payload with keys: decision, probs, top_factors, confidence

    Returns:
        Natural language string

    Examples:
        >>> payload = {
        ...     'decision': 'wait',
        ...     'probs': {'buy': 0.22, 'wait': 0.48, 'no_buy': 0.30},
        ...     'top_factors': ['price', 'delivery', 'reviews'],
        ...     'confidence': 0.48
        ... }
        >>> text = default_verbalizer(payload)
        >>> print(text)
        "I'd wait for now. The price and delivery matter most to me."
    """
    decision = payload.get("decision", "consider")
    probs = payload.get("probs", {})
    top_factors = payload.get("top_factors", [])
    confidence = payload.get("confidence", 0.5)

    # Map decision to first sentence
    decision_map = {
        "buy": "Yes, I'd buy this.",
        "no_buy": "No, I'll pass on this.",
        "wait": "I'd wait for now.",
        "consider": "I'd consider it.",
    }

    first_sentence = decision_map.get(decision, "Let me think about it.")

    # Build second sentence from top factors
    if top_factors:
        if len(top_factors) == 1:
            factor_text = f"The {top_factors[0]} is the key factor."
        elif len(top_factors) == 2:
            factor_text = f"The {top_factors[0]} and {top_factors[1]} matter most to me."
        else:
            factors_list = ", ".join(top_factors[:2])
            factor_text = f"The {factors_list} matter most to me."

        # Add confidence hint if low
        if confidence < 0.4:
            factor_text += " Though I'm not entirely sure."
    else:
        factor_text = "Based on my preferences."

    return f"{first_sentence} {factor_text}"


def decide_then_verbalize(
    *,
    twin_vec: np.ndarray,
    offer_feats: Optional[np.ndarray],
    policy: TwinPolicyHeadSet,
    verbalizer_fn: Optional[Callable[[Dict[str, Any]], str]] = None,
    guardrails: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], str]:
    """
    Policy-first decision pipeline with verbalization and guardrails.

    Workflow:
    1. Call policy.predict_proba() to get decision probabilities
    2. Pick argmax decision and extract top_factors
    3. Build compact JSON payload
    4. Call verbalizer_fn to generate natural language
    5. Apply guardrails (strip tags, check format)
    6. Return (payload, text)

    Args:
        twin_vec: 15-D twin embedding vector
        offer_feats: Optional offer/product features (e.g., [price, quality, delivery, ...])
        policy: TwinPolicyHeadSet instance
        verbalizer_fn: Callable that takes payload dict and returns string
                       If None, uses default_verbalizer
        guardrails: Optional guardrail config dict with keys:
                    - 'enabled': bool
                    - 'context_keywords': List[str]
                    - 'max_retries': int

    Returns:
        Tuple of (decision_payload, natural_text) where:
        - decision_payload: Dict with decision, probs, top_factors, confidence
        - natural_text: Clean natural language string (no brackets/tags)

    Examples:
        >>> from src.models.policy_heads import TwinPolicyHeadSet
        >>> import numpy as np
        >>>
        >>> policy = TwinPolicyHeadSet()
        >>> twin_vec = np.array([0.9, 0.5, 0.6, 0.4, 0.3, ...])  # 15-D
        >>> offer_feats = np.array([50.0, 0.8, 0.7, 2])  # [price, quality, brand, delivery]
        >>>
        >>> payload, text = decide_then_verbalize(
        ...     twin_vec=twin_vec,
        ...     offer_feats=offer_feats,
        ...     policy=policy
        ... )
        >>>
        >>> print(payload)
        {
            'decision': 'wait',
            'probs': {'buy': 0.22, 'wait': 0.48, 'no_buy': 0.30},
            'top_factors': ['price', 'delivery', 'promo_discount'],
            'confidence': 0.48
        }
        >>>
        >>> print(text)
        "I'd wait for now. The price and delivery matter most to me."
    """
    # Use default verbalizer if none provided
    if verbalizer_fn is None:
        verbalizer_fn = default_verbalizer

    # Initialize guardrails
    guardrails_enabled = True
    context_keywords = []
    max_retries = 1

    if guardrails is not None:
        guardrails_enabled = guardrails.get("enabled", True)
        context_keywords = guardrails.get("context_keywords", [])
        max_retries = guardrails.get("max_retries", 1)

    guard = Guardrails(max_retries=max_retries) if guardrails_enabled else None

    # Step 1: Get decision probabilities from policy
    probs = policy.predict_proba(twin_vec, offer_feats)

    # Step 2: Pick argmax decision
    decision = max(probs.items(), key=lambda x: x[1])[0]
    confidence = probs[decision]

    # Step 3: Get top influential factors
    top_factors = policy.top_factors(twin_vec, offer_feats, k=3)

    # Step 4: Build payload
    payload = {
        "decision": decision,
        "probs": probs,
        "top_factors": top_factors,
        "confidence": float(confidence),
    }

    # Step 5: Verbalize
    try:
        raw_text = verbalizer_fn(payload)
    except Exception as e:
        # Fallback if verbalizer fails
        raw_text = generate_fallback_reason(decision, top_factors)

    # Step 6: Apply guardrails
    if guard is not None:
        cleaned_text, passed = guard.check(
            raw_text,
            context_keywords=context_keywords if context_keywords else top_factors,
            require_decision_first=True,
        )

        if not passed:
            # Attempt rewrite
            cleaned_text = guard.rewrite(cleaned_text, decision, top_factors)
    else:
        cleaned_text = raw_text

    return (payload, cleaned_text)


def batch_decide_then_verbalize(
    *,
    twin_vecs: List[np.ndarray],
    offer_feats_list: List[Optional[np.ndarray]],
    policy: TwinPolicyHeadSet,
    verbalizer_fn: Optional[Callable[[Dict[str, Any]], str]] = None,
    guardrails: Optional[Dict[str, Any]] = None,
) -> List[Tuple[Dict[str, Any], str]]:
    """
    Batch version of decide_then_verbalize for multiple queries.

    Args:
        twin_vecs: List of 15-D twin embedding vectors
        offer_feats_list: List of optional offer features (one per twin_vec)
        policy: TwinPolicyHeadSet instance
        verbalizer_fn: Optional verbalizer function
        guardrails: Optional guardrail config

    Returns:
        List of (payload, text) tuples

    Examples:
        >>> twin_vecs = [vec1, vec2, vec3]
        >>> offer_feats = [feats1, feats2, feats3]
        >>> results = batch_decide_then_verbalize(
        ...     twin_vecs=twin_vecs,
        ...     offer_feats_list=offer_feats,
        ...     policy=policy
        ... )
        >>> for payload, text in results:
        ...     print(f"{payload['decision']}: {text}")
    """
    results = []

    for twin_vec, offer_feats in zip(twin_vecs, offer_feats_list):
        result = decide_then_verbalize(
            twin_vec=twin_vec,
            offer_feats=offer_feats,
            policy=policy,
            verbalizer_fn=verbalizer_fn,
            guardrails=guardrails,
        )
        results.append(result)

    return results


def get_decision_system_prompt() -> str:
    """
    Get system prompt for LLM-based verbalizers.

    Returns:
        System prompt string with guardrail instructions

    Examples:
        >>> prompt = get_decision_system_prompt()
        >>> # Use this prompt when calling LLM verbalizer
    """
    return get_system_prompt_for_guardrails()


class DecisionOrchestrator:
    """
    Stateful orchestrator for policy-first decisions.

    This class manages the full pipeline with configuration and state.

    Examples:
        >>> orchestrator = DecisionOrchestrator(policy)
        >>> payload, text = orchestrator.decide(twin_vec, offer_feats)
        >>> print(text)
        "Yes, I'd buy this. The price and quality matter most."
    """

    def __init__(
        self,
        policy: TwinPolicyHeadSet,
        verbalizer_fn: Optional[Callable[[Dict[str, Any]], str]] = None,
        guardrails_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize decision orchestrator.

        Args:
            policy: TwinPolicyHeadSet instance
            verbalizer_fn: Optional custom verbalizer
            guardrails_config: Optional guardrail configuration
        """
        self.policy = policy
        self.verbalizer_fn = verbalizer_fn or default_verbalizer
        self.guardrails_config = guardrails_config or {"enabled": True}

    def decide(
        self,
        twin_vec: np.ndarray,
        offer_feats: Optional[np.ndarray] = None,
    ) -> Tuple[Dict[str, Any], str]:
        """
        Make a decision for a single query.

        Args:
            twin_vec: 15-D twin embedding
            offer_feats: Optional offer features

        Returns:
            Tuple of (payload, text)
        """
        return decide_then_verbalize(
            twin_vec=twin_vec,
            offer_feats=offer_feats,
            policy=self.policy,
            verbalizer_fn=self.verbalizer_fn,
            guardrails=self.guardrails_config,
        )

    def batch_decide(
        self,
        twin_vecs: List[np.ndarray],
        offer_feats_list: List[Optional[np.ndarray]],
    ) -> List[Tuple[Dict[str, Any], str]]:
        """
        Make decisions for multiple queries.

        Args:
            twin_vecs: List of twin embeddings
            offer_feats_list: List of offer features

        Returns:
            List of (payload, text) tuples
        """
        return batch_decide_then_verbalize(
            twin_vecs=twin_vecs,
            offer_feats_list=offer_feats_list,
            policy=self.policy,
            verbalizer_fn=self.verbalizer_fn,
            guardrails=self.guardrails_config,
        )

    def set_verbalizer(self, verbalizer_fn: Callable[[Dict[str, Any]], str]):
        """
        Update verbalizer function.

        Args:
            verbalizer_fn: New verbalizer function
        """
        self.verbalizer_fn = verbalizer_fn

    def configure_guardrails(self, config: Dict[str, Any]):
        """
        Update guardrail configuration.

        Args:
            config: New guardrail config
        """
        self.guardrails_config = config
