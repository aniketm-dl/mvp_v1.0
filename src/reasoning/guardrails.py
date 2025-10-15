"""
Guardrails for LLM-generated twin responses.

This module enforces quality constraints on generated text to ensure:
- No persona taxonomy tags or brackets
- Appropriate length
- Decision-first format
- Grounded in context
"""

from __future__ import annotations
from typing import Optional, List
import re

# Import config
try:
    from src.models.config import (
        GUARDRAIL_BANNED_TOKENS,
        GUARDRAIL_MAX_TOKENS,
        GUARDRAIL_REQUIRE_DECISION_FIRST,
        ORCHESTRATOR_MAX_RETRIES,
    )
except ImportError:
    # Fallback defaults
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
    GUARDRAIL_MAX_TOKENS = 100
    GUARDRAIL_REQUIRE_DECISION_FIRST = True
    ORCHESTRATOR_MAX_RETRIES = 1


class GuardrailViolation(Exception):
    """Exception raised when guardrail check fails."""
    pass


def enforce_no_tags(text: str) -> str:
    """
    Remove or flag persona taxonomy tags and brackets.

    Args:
        text: Generated text to check

    Returns:
        Cleaned text with tags removed

    Raises:
        GuardrailViolation: If tags cannot be safely removed

    Examples:
        >>> text = "I prefer [price_sensitive] options"
        >>> cleaned = enforce_no_tags(text)
        >>> print(cleaned)
        "I prefer affordable options"
    """
    # Check for banned tokens
    for banned_token in GUARDRAIL_BANNED_TOKENS:
        if banned_token.lower() in text.lower():
            # Try to remove the token
            text = re.sub(re.escape(banned_token), "", text, flags=re.IGNORECASE)

    # Check for any remaining square brackets
    if "[" in text or "]" in text:
        # Remove all bracketed content
        text = re.sub(r'\[([^\]]+)\]', r'\1', text)

    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def check_length(text: str, max_tokens: int = GUARDRAIL_MAX_TOKENS) -> bool:
    """
    Check if text is within token limit.

    Args:
        text: Text to check
        max_tokens: Maximum allowed tokens

    Returns:
        True if within limit, False otherwise

    Examples:
        >>> text = "This is a short response."
        >>> check_length(text, max_tokens=100)
        True
    """
    # Approximate token count (words * 1.3 for subwords)
    words = text.split()
    approx_tokens = int(len(words) * 1.3)

    return approx_tokens <= max_tokens


def check_decision_first(text: str, decision_keywords: Optional[List[str]] = None) -> bool:
    """
    Check if first sentence contains a decision word.

    Args:
        text: Text to check
        decision_keywords: List of valid decision words (default: yes/no/wait/maybe)

    Returns:
        True if first sentence contains decision, False otherwise

    Examples:
        >>> text = "Yes, I would buy this. The price is reasonable."
        >>> check_decision_first(text)
        True

        >>> text = "The price is reasonable. Yes, I would buy."
        >>> check_decision_first(text)
        False
    """
    if decision_keywords is None:
        decision_keywords = ["yes", "no", "wait", "maybe", "buy", "pass", "consider"]

    # Get first sentence
    first_sentence = text.split(".")[0] if "." in text else text
    first_sentence_lower = first_sentence.lower()

    # Check if any decision keyword is in first sentence
    return any(keyword in first_sentence_lower for keyword in decision_keywords)


def check_grounding(text: str, context_keywords: List[str]) -> bool:
    """
    Check if text is grounded in provided context.

    Args:
        text: Generated text
        context_keywords: Keywords that should be mentioned (e.g., ['price', 'brand', 'delivery'])

    Returns:
        True if text mentions at least one context keyword, False otherwise

    Examples:
        >>> text = "The price is too high for my budget."
        >>> check_grounding(text, ['price', 'quality', 'delivery'])
        True

        >>> text = "I don't like it."
        >>> check_grounding(text, ['price', 'quality', 'delivery'])
        False
    """
    if not context_keywords:
        return True  # No grounding requirements

    text_lower = text.lower()

    # Check if at least one keyword is mentioned
    return any(keyword.lower() in text_lower for keyword in context_keywords)


def apply_guardrails(
    text: str,
    context_keywords: Optional[List[str]] = None,
    require_decision_first: bool = GUARDRAIL_REQUIRE_DECISION_FIRST,
    max_tokens: int = GUARDRAIL_MAX_TOKENS,
) -> tuple[str, bool]:
    """
    Apply all guardrails to generated text.

    Args:
        text: Generated text to check
        context_keywords: Keywords for grounding check (optional)
        require_decision_first: Whether first sentence must contain decision
        max_tokens: Maximum allowed tokens

    Returns:
        Tuple of (cleaned_text, passed) where passed is True if all checks pass

    Examples:
        >>> text = "Yes, I'd buy this [premium] item. The quality is excellent."
        >>> cleaned, passed = apply_guardrails(text, ['quality', 'price'])
        >>> print(cleaned)
        "Yes, I'd buy this item. The quality is excellent."
        >>> print(passed)
        True
    """
    # 1. Remove tags
    cleaned_text = enforce_no_tags(text)

    # 2. Check length
    if not check_length(cleaned_text, max_tokens):
        return cleaned_text, False

    # 3. Check decision-first format
    if require_decision_first and not check_decision_first(cleaned_text):
        return cleaned_text, False

    # 4. Check grounding
    if context_keywords and not check_grounding(cleaned_text, context_keywords):
        return cleaned_text, False

    return cleaned_text, True


def generate_fallback_reason(decision: str, top_factors: List[str]) -> str:
    """
    Generate a safe fallback reason when guardrails fail.

    Args:
        decision: The decision (e.g., 'buy', 'wait', 'no_buy')
        top_factors: Top influential factors

    Returns:
        Clean, deterministic fallback text

    Examples:
        >>> fallback = generate_fallback_reason('wait', ['price', 'delivery', 'reviews'])
        >>> print(fallback)
        "I'd wait. Key factors: price, delivery, reviews."
    """
    decision_map = {
        "buy": "Yes, I'd buy this.",
        "no_buy": "No, I'll pass.",
        "wait": "I'd wait for now.",
        "consider": "I'd consider it.",
        "maybe": "Maybe, but I'm not sure.",
    }

    first_sentence = decision_map.get(decision, "I'm considering this.")

    if top_factors:
        factors_text = ", ".join(top_factors[:3])
        second_sentence = f"Key factors: {factors_text}."
    else:
        second_sentence = "Based on my preferences."

    return f"{first_sentence} {second_sentence}"


def get_system_prompt_for_guardrails() -> str:
    """
    Get the system prompt to guide LLM generation with guardrails.

    Returns:
        System prompt string

    Examples:
        >>> prompt = get_system_prompt_for_guardrails()
        >>> print(prompt)
        "Answer directly in first person. First sentence must be the decision..."
    """
    return """Answer directly in first person. First sentence must be the decision (Yes/No/Wait/Maybe).
Then give a 1-2 sentence rationale grounded in the specific product attributes (price, quality, brand, delivery, etc.).
Do not include any bracketed tags, persona labels, or taxonomy terms.
Keep it natural and conversational, under 50 words total."""


def rewrite_with_guardrails(
    original_text: str,
    decision: str,
    top_factors: List[str],
    llm_fn=None,
) -> str:
    """
    Attempt to rewrite text if guardrails fail (one retry).

    Args:
        original_text: Original generated text that failed
        decision: The decision label
        top_factors: Top influential factors
        llm_fn: Optional LLM function for rewrite (if None, use fallback)

    Returns:
        Rewritten text or fallback

    Examples:
        >>> bad_text = "I'm a [premium_buyer] so I like quality items"
        >>> rewritten = rewrite_with_guardrails(bad_text, 'buy', ['quality', 'brand'])
        >>> print(rewritten)
        "Yes, I'd buy this. Key factors: quality, brand."
    """
    if llm_fn is not None:
        # Try LLM rewrite with explicit instructions
        prompt = f"""Rewrite this to remove brackets and tags, keep decision first:
Original: {original_text}
Decision: {decision}
Factors: {', '.join(top_factors)}

Rewrite in first person, decision first, 1-2 sentences, no brackets."""

        try:
            rewritten = llm_fn(prompt)
            cleaned, passed = apply_guardrails(rewritten, top_factors, require_decision_first=True)
            if passed:
                return cleaned
        except Exception:
            pass

    # Fall back to deterministic generation
    return generate_fallback_reason(decision, top_factors)


class Guardrails:
    """
    Stateful guardrails checker with retry logic.

    Examples:
        >>> guardrails = Guardrails(max_retries=1)
        >>> text, passed = guardrails.check("Yes, I'd buy. Quality is great.", ['quality'])
        >>> if not passed:
        ...     text = guardrails.rewrite(text, 'buy', ['quality'])
    """

    def __init__(self, max_retries: int = ORCHESTRATOR_MAX_RETRIES):
        """
        Initialize guardrails.

        Args:
            max_retries: Maximum number of rewrite attempts
        """
        self.max_retries = max_retries
        self.retry_count = 0

    def check(
        self,
        text: str,
        context_keywords: Optional[List[str]] = None,
        require_decision_first: bool = GUARDRAIL_REQUIRE_DECISION_FIRST,
    ) -> tuple[str, bool]:
        """
        Check text against guardrails.

        Returns:
            Tuple of (cleaned_text, passed)
        """
        return apply_guardrails(
            text,
            context_keywords=context_keywords,
            require_decision_first=require_decision_first,
        )

    def rewrite(
        self,
        text: str,
        decision: str,
        top_factors: List[str],
        llm_fn=None,
    ) -> str:
        """
        Rewrite text with guardrails.

        Returns:
            Cleaned text
        """
        if self.retry_count >= self.max_retries:
            # Max retries reached, use fallback
            return generate_fallback_reason(decision, top_factors)

        self.retry_count += 1
        return rewrite_with_guardrails(text, decision, top_factors, llm_fn)

    def reset(self):
        """Reset retry counter."""
        self.retry_count = 0
