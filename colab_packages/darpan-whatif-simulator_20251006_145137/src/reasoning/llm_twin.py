from __future__ import annotations
from typing import Any, Dict, List, Optional
import json
from pathlib import Path
from .llm_runtime import RUNTIME

_PERSONAS_PATH = Path(__file__).resolve().parents[2] / "DATA" / "personas.json"
_PERSONAS = json.loads(_PERSONAS_PATH.read_text(encoding="utf-8"))

def list_personas() -> List[Dict[str, Any]]:
    """Return all persona cards."""
    return _PERSONAS["personas"]

def get_persona(twin_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific persona by twin_id."""
    for p in _PERSONAS["personas"]:
        if p["id"] == twin_id:
            return p
    return None

def chat_with_twin(twin_id: str, history: List[Dict[str,str]], prompt: str, conditioning: Optional[Dict[str,Any]] = None) -> str:
    """
    Chat with a twin persona.
    Returns a persona-specific conversational reply.
    """
    p = get_persona(twin_id)
    if not p:
        return "Unknown twin."

    tags = []
    if conditioning and conditioning.get("psychographic_tags"):
        tags = list(conditioning["psychographic_tags"])

    return RUNTIME.chat(p["label"], twin_id, prompt, tags)

def decide_as_twin(
    twin_id: str,
    context: Dict[str,Any],
    candidates: List[Dict[str,Any]],
    max_tokens: int=20,
    conditioning: Optional[Dict[str,Any]] = None
) -> Dict[str,str]:
    """
    Make a decision as a specific twin.
    Returns {"pick": candidate_id, "why": short_reason}

    This is deterministic for testing. In production, would call LLM
    with temperature=0 and strict JSON mode + conditioning.
    """
    ids = sorted([c["id"] for c in candidates])
    if not ids:
        return {"pick":"", "why":"No visible options."}

    tags = (conditioning or {}).get("psychographic_tags") or []

    # Twin-specific deterministic pick logic (differs by twin)
    if twin_id == "k0":  # Budget-Conscious
        # Pick first alphabetically (simulating lowest price preference)
        pick = ids[0]
    elif twin_id == "k1":  # Premium Quality
        # Pick middle option (simulating quality preference)
        pick = ids[len(ids)//2] if len(ids) > 1 else ids[0]
    elif twin_id == "k2":  # Deal-Hunting Explorer
        # Pick last alphabetically (simulating feature-rich option)
        pick = ids[-1]
    else:
        pick = ids[0]

    # Override with psychographic tags if present
    if "speed_focus" in tags:
        pick = ids[-1]
    if "thrift" in tags:
        pick = ids[0]
    if "quality_focus" in tags:
        pick = ids[len(ids)//2] if len(ids) > 1 else ids[0]

    p = get_persona(twin_id)
    if p:
        why = RUNTIME.chat(p["label"], twin_id, f"Explain the choice briefly for context {list(context.keys())} and candidates {ids}.", tags)
    else:
        why = "Default selection."

    return {"pick": pick, "why": " ".join(why.split()[:max_tokens])}
