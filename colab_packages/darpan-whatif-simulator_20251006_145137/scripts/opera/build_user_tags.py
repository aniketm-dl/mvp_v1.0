from __future__ import annotations
from pathlib import Path
import re, json, glob, pandas as pd
LEX = {
  "price_sensitive": r"\b(budget|cheap|low price|value|afford|cost|save)\b",
  "deal_hunter":     r"\b(deal|discount|sale|promo|coupon)\b",
  "speed_focus":     r"\b(fast|quick|delivery|ship|same[- ]day|2[- ]day)\b",
  "quality_first":   r"\b(quality|durable|reliable|premium|build)\b",
  "brand_loyal":     r"\b(brand|loyal|preferred brand)\b",
  "eco_conscious":   r"\b(eco|sustainab|green|recycl|environment)\b",
  "novelty_seeking": r"\b(new|latest|launch|innovative|cutting edge)\b",
  "convenience":     r"\b(easy|convenient|hassle[- ]free|quick checkout)\b",
}

def to_tags(text: str) -> list[str]:
    if not isinstance(text, str) or not text.strip():
        return ["generalist"]
    t = text.lower()
    out = [k for k,pat in LEX.items() if re.search(pat, t)]
    return out or ["generalist"]
def main():
    users = sorted(glob.glob("DATA/opera/filtered_user/train/*.parquet"))
    if not users:
        raise SystemExit("No filtered_user/train/*.parquet found.")
    df = pd.concat([pd.read_parquet(p, columns=["user_id","survey","interview_transcript_processed"]) for p in users], ignore_index=True)
    df["__text"] = df["interview_transcript_processed"].fillna("") + " " + df["survey"].fillna("")
    df["psych_tags"] = df["__text"].map(lambda s: ",".join(to_tags(s)))
    out = df[["user_id","psych_tags"]].drop_duplicates("user_id")
    Path("DATA/derived").mkdir(parents=True, exist_ok=True)
    out.to_parquet("DATA/derived/user_tags.parquet", index=False)
    print("Wrote DATA/derived/user_tags.parquet with", len(out), "rows")
if __name__ == "__main__":
    main()
