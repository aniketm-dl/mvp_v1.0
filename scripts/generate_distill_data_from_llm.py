from __future__ import annotations
from typing import Any, Dict, List
from pathlib import Path
import json
import argparse
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.encoder import encode_cta, project_psychographics, embed_demographics, fuse_joint
from src.profiles.loader import profile_vec_for_user
from src.reasoning.llm_twin import decide_as_twin

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=str, default="DATA/distill_llm.jsonl")
    args = ap.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Simple demo generator: use example CTA and candidates, ask each twin to decide
    cta = {
        "user_id":"u1","session_id":"s1","ts":"2025-06-01T12:00:00",
        "context":{"page_type":"search","visible_products":["A1","A2","A3"],"promo_badge":True,"delivery_eta_days":2,"price_mean":500},
        "task":"choose_product","action_id":"A2"
    }

    # Compute fused embedding
    prof = profile_vec_for_user("u1")
    z_b = encode_cta([cta])
    z_p = project_psychographics(prof)
    z_d = embed_demographics(prof)
    fused_embed = fuse_joint(z_b, z_p, z_d)

    cands = [{"id":"A1"},{"id":"A2"},{"id":"A3"}]
    lines = []
    for twin_id in ["k0","k1","k2"]:
        dec = decide_as_twin(twin_id, cta["context"], cands, max_tokens=20)
        ex = {
            "twin_id": twin_id,
            "context": cta["context"],
            "candidates": cands,
            "chosen_id": dec["pick"],
            "fused_embed": fused_embed
        }
        lines.append(json.dumps(ex))

    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(lines)} examples to {out}")

if __name__ == "__main__":
    main()
