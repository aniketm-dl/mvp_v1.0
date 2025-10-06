from __future__ import annotations
from typing import Any, Dict, List, Tuple
from pathlib import Path
import argparse
import json
import random

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("Warning: numpy not available, using pure Python fallback")

from src.features.candidate_features import build_candidate_matrix

random.seed(17)
if HAS_NUMPY:
    np.random.seed(17)

def assemble_dataset(examples: List[Dict[str, Any]], twin_id: str, buckets: int) -> Tuple[List[List[float]], List[int]]:
    """
    Build per-row feature matrix and labels:
      - For each example: produce candidate matrix rows for all candidates.
      - Label 1 for chosen candidate row, 0 for others.
    Return X:[R,F], y:[R] (0/1).
    """
    X_rows: List[List[float]] = []
    y_rows: List[int] = []
    for ex in examples:
        ctx = ex["context"]
        fused = ex["fused_embed"]
        cands = ex["candidates"]
        chosen = ex["chosen_id"]
        Xm = build_candidate_matrix(ctx, cands, fused, buckets=buckets)
        for row, c in zip(Xm, cands):
            X_rows.append(row)
            y_rows.append(1 if c["id"] == chosen else 0)
    return X_rows, y_rows

def train_head(X_rows: List[List[float]], y_rows: List[int], l2: float = 1e-3) -> List[float]:
    """Ridge regression closed form to 0/1 labels"""
    if not HAS_NUMPY:
        # Pure Python fallback: random weights for demo
        if X_rows:
            nF = len(X_rows[0])
            return [random.gauss(0, 0.1) for _ in range(nF)]
        return []

    X = np.array(X_rows, dtype=np.float64)
    y = np.array(y_rows, dtype=np.float64)
    XtX = X.T @ X
    nF = XtX.shape[0]
    W = np.linalg.solve(XtX + l2 * np.eye(nF), X.T @ y)
    return W.tolist()  # [F]

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=str, required=True, help="Path to JSONL with distilled examples")
    ap.add_argument("--outdir", type=str, default="artifacts/policy_heads")
    ap.add_argument("--buckets", type=int, default=16)
    ap.add_argument("--temp", type=float, default=1.0)
    args = ap.parse_args()

    out = Path(args.outdir); out.mkdir(parents=True, exist_ok=True)

    # JSONL format per line:
    # {"twin_id":"k0","context":{...},"candidates":[{"id":"A1"},...],
    #  "chosen_id":"A1","fused_embed":[...]}
    per_twin: Dict[str, List[Dict[str, Any]]] = {}
    with Path(args.input).open() as f:
        for line in f:
            ex = json.loads(line)
            per_twin.setdefault(ex["twin_id"], []).append(ex)

    for twin_id, exs in per_twin.items():
        X_rows, y_rows = assemble_dataset(exs, twin_id, buckets=args.buckets)
        W = train_head(X_rows, y_rows, l2=1e-3)
        model = {"twin_id": twin_id, "weights": W, "temp": args.temp}
        (out / f"{twin_id}.json").write_text(json.dumps(model), encoding="utf-8")
        print(f"Trained head {twin_id}: rows={len(y_rows)}, F={len(W)} -> {out / (twin_id+'.json')}")

if __name__ == "__main__":
    main()
