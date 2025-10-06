from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Set
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_DEFAULTS = _ROOT / "CONFIGS" / "defaults.yaml"

def load_defaults() -> Dict[str, Any]:
    data = yaml.safe_load(_DEFAULTS.read_text(encoding="utf-8"))
    return data

def allowed_mutables() -> Set[str]:
    cfg = load_defaults()
    return set(cfg.get("scenario", {}).get("allowed_mutables", []))
