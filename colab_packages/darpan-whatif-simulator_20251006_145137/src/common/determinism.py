from __future__ import annotations
import random
import os
import math
from typing import Any, Iterable, List, Dict

# numpy/torch are optional at this stage
try:
    import numpy as np
except Exception:
    np = None  # type: ignore

try:
    import torch
except Exception:
    torch = None  # type: ignore

def set_global_seed(seed: int) -> None:
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    if np is not None:
        np.random.seed(seed)
    if torch is not None:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        try:
            torch.use_deterministic_algorithms(True)  # type: ignore[attr-defined]
        except Exception:
            pass

def quantize(x: float, eps: float = 1e-6) -> float:
    if math.isnan(x) or math.isinf(x):
        return x
    q = round(x / eps) * eps
    return float(f"{q:.12f}")

def canonical_sort(topN: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Sort by p desc, then id asc for tie-breaks
    return sorted(topN, key=lambda r: (-float(r.get("p", 0.0)), str(r.get("id",""))))
