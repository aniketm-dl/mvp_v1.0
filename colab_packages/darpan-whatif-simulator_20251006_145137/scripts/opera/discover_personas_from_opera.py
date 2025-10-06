from __future__ import annotations
import json, ast
from pathlib import Path
import argparse, pandas as pd

def _as_list(x):
    if x is None or (isinstance(x, float) and pd.isna(x)): return []
    if isinstance(x, list): return x
    s = str(x).strip()
    try:
        v = ast.literal_eval(s)
        if isinstance(v, list): return v
    except Exception:
        pass
    return [t.strip() for t in s.split(",") if t.strip()]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--opera_path", default="DATA/opera/opera_events.parquet")
    ap.add_argument("--format", default="parquet", choices=["parquet","csv"])
    ap.add_argument("--psych_col", default="psych_tags")
    ap.add_argument("--min_rows", type=int, default=200)
    ap.add_argument("--max_personas", type=int, default=24)
    ap.add_argument("--personas_json", default="DATA/personas.json")
    ap.add_argument("--augment", action="store_true", help="append discovered personas to existing personas.json")
    args = ap.parse_args()

    df = pd.read_parquet(args.opera_path) if args.format=="parquet" else pd.read_csv(args.opera_path)
    df["_tags"] = df[args.psych_col].map(_as_list)
    # normalize into sorted tag tuples as keys
    df["_key"] = df["_tags"].map(lambda xs: "|".join(sorted(xs)) if xs else "(none)")
    grp = df.groupby("_key").size().sort_values(ascending=False)

    discovered = []
    for key, n in grp.items():
        if n < args.min_rows: break
        if len(discovered) >= args.max_personas: break
        label = key if key!="(none)" else "generalist"
        tid = f"ko_{abs(hash(key))%100000}"
        discovered.append({"id": tid, "label": f"{label} persona", "tags": [t for t in key.split("|") if t and t!="(none)"]})

    # Load/seed personas.json
    pj = Path(args.personas_json)
    if pj.exists():
        base = json.loads(pj.read_text(encoding="utf-8"))
    else:
        base = {"personas": []}

    out = base.copy()
    if args.augment:
        existing_ids = {p["id"] for p in base["personas"]}
        for d in discovered:
            if d["id"] not in existing_ids:
                out["personas"].append(d)
    else:
        out["personas"] = discovered

    pj.parent.mkdir(parents=True, exist_ok=True)
    pj.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {args.personas_json} with {len(out['personas'])} personas")

if __name__ == "__main__":
    main()
