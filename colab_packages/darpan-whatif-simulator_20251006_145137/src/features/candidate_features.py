from __future__ import annotations
from typing import Any, Dict, List
import hashlib
import math

def _hash_bucket(s: str, buckets: int) -> int:
    h = int(hashlib.sha256(s.encode("utf-8")).hexdigest(), 16)
    return h % max(1, buckets)

def one_hot(idx: int, size: int) -> List[float]:
    v = [0.0] * size
    if 0 <= idx < size:
        v[idx] = 1.0
    return v

def context_vector(context: Dict[str, Any]) -> List[float]:
    price = context.get("price_mean", 0.0)
    eta = context.get("delivery_eta_days", 0.0)
    promo = 1.0 if context.get("promo_badge") is True else 0.0
    # simple bounded scalers
    price_f = min(max(float(price)/1000.0, 0.0), 10.0)
    eta_f   = min(max(float(eta)/7.0, 0.0), 10.0)
    return [price_f, eta_f, promo]

def build_candidate_matrix(context: Dict[str, Any], candidates: List[Dict[str, Any]], fused_embed: List[float], buckets: int = 16) -> List[List[float]]:
    """
    Row per candidate:
      [ctx_feats(3) || fused_embed(D) || one_hot(hash(candidate_id), buckets)]
    """
    ctx = context_vector(context)
    X: List[List[float]] = []
    for c in candidates:
        cid = c["id"]
        hb = _hash_bucket(str(cid), buckets)
        row = list(ctx) + list(fused_embed) + one_hot(hb, buckets)
        X.append(row)
    return X
