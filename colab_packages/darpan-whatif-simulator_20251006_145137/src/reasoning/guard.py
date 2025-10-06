from __future__ import annotations
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml

_GATES_PATH = Path("CONFIGS/tests/gates.yaml")

def load_guard_config() -> Dict[str, Any]:
    """Load guard rules from gates.yaml"""
    if _GATES_PATH.exists():
        return yaml.safe_load(_GATES_PATH.read_text()).get("guard", {})
    return {}

class ReasonGuard:
    """Enforces reason quality constraints"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        cfg = config or load_guard_config()
        self.max_tokens = cfg.get("max_tokens", 20)
        self.banned_terms = set(t.lower() for t in cfg.get("banned_terms", []))
        self.numeric_audit = cfg.get("numeric_audit", {})
        self.fallback = cfg.get("fallback_reason", "Decision based on available context.")

    def audit(self, reason: str, context: Dict[str, Any], candidate_ids: List[str]) -> str:
        """
        Audit and potentially fix a reason string.
        Returns cleaned reason or fallback if violations detected.
        """
        # Token count check
        tokens = reason.split()
        if len(tokens) > self.max_tokens:
            reason = " ".join(tokens[:self.max_tokens])

        # Banned terms check
        lower_reason = reason.lower()
        for term in self.banned_terms:
            if term in lower_reason:
                return self.fallback

        # Numeric audit: check for hallucinated numbers
        if self.numeric_audit.get("allow_hallucinated_numbers") is False:
            # Extract numbers from reason
            reason_numbers = set(re.findall(r'\b\d+(?:\.\d+)?\b', reason))
            # Extract numbers from context
            context_str = str(context)
            context_numbers = set(re.findall(r'\b\d+(?:\.\d+)?\b', context_str))

            # If reason contains numbers not in context, it's hallucinated
            hallucinated = reason_numbers - context_numbers
            if hallucinated:
                return self.fallback

        # Context grounding check: must reference visible candidates or context fields
        if self.numeric_audit.get("require_context_grounding", True):
            # Check if reason mentions any candidate ID or common context terms
            has_grounding = False
            for cid in candidate_ids:
                if cid.lower() in lower_reason:
                    has_grounding = True
                    break

            # Also accept common context keywords
            context_keywords = ["price", "promo", "delivery", "eta", "badge", "discount", "quality"]
            for kw in context_keywords:
                if kw in lower_reason:
                    has_grounding = True
                    break

            if not has_grounding:
                return self.fallback

        return reason

    def audit_decision(self, decision: Dict[str, Any], context: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Audit a full decision dict with pick and why"""
        cids = [c["id"] for c in candidates]
        audited_why = self.audit(decision.get("why", ""), context, cids)
        return {"pick": decision["pick"], "why": audited_why}

_GUARD = ReasonGuard()

def guard_reason(reason: str, context: Dict[str, Any], candidate_ids: List[str]) -> str:
    """Convenience function for auditing a single reason"""
    return _GUARD.audit(reason, context, candidate_ids)

def guard_decision(decision: Dict[str, Any], context: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convenience function for auditing a decision"""
    return _GUARD.audit_decision(decision, context, candidates)
