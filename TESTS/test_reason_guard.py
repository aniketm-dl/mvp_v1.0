"""
Test ReasonGuard enforcement.
"""
from __future__ import annotations
from src.reasoning.guard import ReasonGuard

def test_guard_max_tokens():
    """Guard should truncate reasons exceeding max_tokens"""
    guard = ReasonGuard({"max_tokens": 5, "banned_terms": [], "numeric_audit": {}})
    reason = "This is a very long reason that exceeds the token limit significantly"
    context = {"price_mean": 500}
    candidate_ids = ["A1", "A2"]

    audited = guard.audit(reason, context, candidate_ids)
    assert len(audited.split()) <= 5, f"Exceeded max_tokens: {audited}"

def test_guard_banned_terms():
    """Guard should replace reasons containing banned terms with fallback"""
    guard = ReasonGuard({
        "max_tokens": 20,
        "banned_terms": ["sorry", "unclear"],
        "numeric_audit": {},
        "fallback_reason": "Fallback reason."
    })
    reason = "Sorry, but this choice is unclear to me"
    context = {"price_mean": 500}
    candidate_ids = ["A1", "A2"]

    audited = guard.audit(reason, context, candidate_ids)
    assert audited == "Fallback reason.", f"Should use fallback for banned term: {audited}"

def test_guard_numeric_audit():
    """Guard should detect hallucinated numbers"""
    guard = ReasonGuard({
        "max_tokens": 20,
        "banned_terms": [],
        "numeric_audit": {"allow_hallucinated_numbers": False, "require_context_grounding": False},
        "fallback_reason": "Fallback reason."
    })

    # Reason with number not in context
    reason = "The price is 999 which is best"
    context = {"price_mean": 500}
    candidate_ids = ["A1", "A2"]

    audited = guard.audit(reason, context, candidate_ids)
    assert audited == "Fallback reason.", f"Should reject hallucinated number: {audited}"

def test_guard_context_grounding():
    """Guard should require context grounding"""
    guard = ReasonGuard({
        "max_tokens": 20,
        "banned_terms": [],
        "numeric_audit": {"allow_hallucinated_numbers": True, "require_context_grounding": True},
        "fallback_reason": "Fallback reason."
    })

    # Reason with no grounding
    reason = "Just because I feel like it"
    context = {"price_mean": 500}
    candidate_ids = ["A1", "A2"]

    audited = guard.audit(reason, context, candidate_ids)
    assert audited == "Fallback reason.", f"Should require grounding: {audited}"

    # Reason with grounding (mentions candidate)
    reason = "A1 has the best price"
    audited = guard.audit(reason, context, candidate_ids)
    assert audited == "A1 has the best price", f"Should accept grounded reason: {audited}"

def test_guard_decision():
    """Guard should audit full decision dict"""
    guard = ReasonGuard({
        "max_tokens": 5,
        "banned_terms": ["sorry"],
        "numeric_audit": {},
        "fallback_reason": "Fallback."
    })

    decision = {"pick": "A1", "why": "Sorry but this is a very long reason that should be truncated"}
    context = {"price_mean": 500}
    candidates = [{"id": "A1"}, {"id": "A2"}]

    audited = guard.audit_decision(decision, context, candidates)
    assert audited["pick"] == "A1", "Pick should be unchanged"
    assert audited["why"] == "Fallback.", "Should use fallback for banned term"
