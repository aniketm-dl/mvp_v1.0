from __future__ import annotations
import hashlib, json
from typing import Any

def stable_hash(obj: Any, take: int = 12) -> str:
    s = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:take]
