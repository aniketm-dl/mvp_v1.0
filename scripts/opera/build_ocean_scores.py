from __future__ import annotations
from pathlib import Path
import re, glob, numpy as np, pandas as pd
import pyarrow.parquet as pq

LEX = {
  "O": [r"\bcurious\b", r"\bcreativ", r"\bnovel", r"\bexplor", r"\bimagin", r"\bart\b", r"\bvariety\b"],
  "C": [r"\bplan\b", r"\bschedule", r"\borganize", r"\bdeadline", r"\bcareful", r"\btask\b", r"\bneat\b"],
  "E": [r"\bsocial\b", r"\boutgoing\b", r"\bparty\b", r"\btalk", r"\bgroup\b", r"\benergetic\b"],
  "A": [r"\bkind\b", r"\bhelp", r"\bcooperat", r"\btrust", r"\bconsiderate\b", r"\bfriendly\b"],
  "N": [r"\bworr", r"\banxi", r"\bstress", r"\bupset\b", r"\bnervous\b", r"\bdepress"],
}

def norm_score(text: str, pats: list[str]) -> float:
    if not isinstance(text, str) or not text.strip():
        return 0.5
    t = " " + re.sub(r"[^a-z0-9\s]", " ", text.lower()) + " "
    n_tok = max(1, len(t.split()))
    hits = sum(len(re.findall(p, t)) for p in pats)
    s = hits / n_tok
    return float(1 / (1 + np.exp(-50 * (s - 0.01))))

def main() -> None:
    files = sorted(glob.glob("DATA/opera/filtered_user/train/*.parquet"))
    if not files:
        raise SystemExit("No filtered_user/train/*.parquet found.")

    keep = ["user_id", "survey", "interview_transcript_processed"]
    parts = []
    for p in files:
        schema_cols = set(pq.ParquetFile(p).schema.names)
        cols = [c for c in keep if c in schema_cols]
        if not cols:
            continue
        parts.append(pd.read_parquet(p, columns=cols))

    if not parts:
        raise SystemExit("None of the expected user columns were found.")

    U = pd.concat(parts, ignore_index=True)
    U["__text"] = (
        U.get("interview_transcript_processed", "").fillna("")
        + " "
        + U.get("survey", "").fillna("")
    ).astype(str)

    rows = []
    for uid, s in zip(U["user_id"], U["__text"]):
        O = norm_score(s, LEX["O"]); C = norm_score(s, LEX["C"])
        E = norm_score(s, LEX["E"]); A = norm_score(s, LEX["A"]); N = norm_score(s, LEX["N"])
        rows.append({"user_id": uid, "O": O, "C": C, "E": E, "A": A, "N": N})

    out = pd.DataFrame(rows).drop_duplicates("user_id")
    Path("DATA/derived").mkdir(parents=True, exist_ok=True)
    out.to_parquet("DATA/derived/user_ocean.parquet", index=False)
    print("Wrote DATA/derived/user_ocean.parquet:", len(out))

if __name__ == "__main__":
    main()