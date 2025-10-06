from __future__ import annotations
from typing import Dict, Any, Optional, List

# Mock store. Replace with a parquet reader that returns a compact vector in [0,1].
# Vector layout (example): [thrift, novelty, quality_focus, speed_focus, age_25_34, urban, female]
_MOCK = {
    "u1": [0.9, 0.2, 0.4, 0.3, 1.0, 1.0, 0.0],
    "u2": [0.3, 0.7, 0.6, 0.4, 0.0, 0.0, 1.0],
}

def profile_vec_for_user(user_id: Optional[str]) -> Optional[List[float]]:
    if not user_id:
        return None
    return _MOCK.get(user_id)

def psych_tags_to_vec(tags: Optional[List[str]]) -> Optional[List[float]]:
    """Convert psychographic tags to a 4-D vector."""
    if not tags:
        return None
    # Mock: map tags to dimensions [thrift, novelty, quality_focus, speed_focus]
    vec = [0.0, 0.0, 0.0, 0.0]
    for tag in tags:
        if "thrift" in tag.lower():
            vec[0] = 1.0
        if "novelty" in tag.lower() or "explore" in tag.lower():
            vec[1] = 1.0
        if "quality" in tag.lower():
            vec[2] = 1.0
        if "speed" in tag.lower() or "fast" in tag.lower():
            vec[3] = 1.0
    return vec

def demo_profile_to_vec(profile: Optional[Dict[str, Any]]) -> Optional[List[float]]:
    """Convert demographic profile to a 3-D vector."""
    if not profile:
        return None
    # Mock: [age_25_34, urban, female]
    vec = [0.0, 0.0, 0.0]
    age_band = profile.get("age_band", "")
    if "25_34" in age_band or "25-34" in age_band:
        vec[0] = 1.0
    locale = profile.get("locale", "")
    if "urban" in locale.lower():
        vec[1] = 1.0
    sex = profile.get("sex", "")
    if sex.lower() in ("f", "female"):
        vec[2] = 1.0
    return vec

def merge_profile(base: Optional[List[float]], psych: Optional[List[float]], demo: Optional[List[float]]) -> Optional[List[float]]:
    """Merge base profile with conditioning overrides."""
    if not base and not psych and not demo:
        return None
    # Start with base or zeros
    result = list(base) if base else [0.0] * 7
    # Override psychographic portion (first 4)
    if psych:
        for i, v in enumerate(psych[:4]):
            if i < len(result):
                result[i] = v
    # Override demographic portion (last 3)
    if demo:
        for i, v in enumerate(demo[:3]):
            idx = 4 + i
            if idx < len(result):
                result[idx] = v
    return result
