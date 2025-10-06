from __future__ import annotations
from typing import Any, Dict, List
from pathlib import Path
import json, random

def from_personas_synthetic(n_per_twin: int = 50) -> List[Dict[str, Any]]:
    personas = json.loads((Path("DATA")/"personas.json").read_text())
    out = []
    for p in personas["personas"]:
        tid, label = p["id"], p["label"]
        for i in range(n_per_twin):
            user = "I care about price and delivery." if i%2==0 else "Quality and reliability matter."
            resp = "I look for a fair price and quick shipping." if i%2==0 else "I pay for quality that lasts."
            out.append({"twin_id": tid, "input": f"User: {user}\nAssistant:", "output": resp, "meta": {"psychographic_tags": p.get("tags",[])}})
    return out

def main():
    outdir = Path("DATA/sft"); outdir.mkdir(parents=True, exist_ok=True)
    data = from_personas_synthetic(50)
    by_twin: Dict[str, List[Dict[str, Any]]] = {}
    for ex in data:
        by_twin.setdefault(ex["twin_id"], []).append(ex)
    for tid, rows in by_twin.items():
        fp = outdir / f"{tid}.jsonl"
        fp.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
        print(f"Wrote {len(rows)} rows -> {fp}")

if __name__ == "__main__":
    main()
