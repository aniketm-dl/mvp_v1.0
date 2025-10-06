from __future__ import annotations
from pathlib import Path
import json, glob, pandas as pd, http.client

PROMPT = """Rate the user's personality on the Big Five in JSON with keys O,C,E,A,N each in [0,1].
Base only on the text below. Do NOT explain. JSON only.
TEXT:
<<<
{TEXT}
>>>"""

def llm_rate(text:str) -> dict:
    # adjust base/port if needed; deterministic runtime assumed
    conn = http.client.HTTPConnection("127.0.0.1", 8000, timeout=8)
    payload = json.dumps({"prompt": PROMPT.replace("{TEXT}", text[:4000])})
    conn.request("POST","/admin/offline_llm_json", body=payload, headers={"Content-Type":"application/json","X-Admin-Token":"changeme"})
    r = conn.getresponse(); body = r.read().decode(); conn.close()
    try:
        return json.loads(body)
    except Exception:
        return {"O":0.5,"C":0.5,"E":0.5,"A":0.5,"N":0.5}

def main():
    files = glob.glob("DATA/opera/filtered_user/train/*.parquet")
    U = pd.concat([pd.read_parquet(p, columns=["user_id","survey","interview_transcript_processed"]) for p in files], ignore_index=True)
    U["__text"] = U.get("interview_transcript_processed","").fillna("") + " " + U.get("survey","").fillna("")
    rows=[]
    for uid, txt in U[["user_id","__text"]].itertuples(index=False):
        j = llm_rate(txt)
        rows.append({"user_id":uid, **{k: float(j.get(k,0.5)) for k in "OCEAN"}})
    df = pd.DataFrame(rows)
    Path("DATA/derived").mkdir(parents=True, exist_ok=True)
    df.to_parquet("DATA/derived/user_big5.parquet", index=False)
    print("Wrote DATA/derived/user_big5.parquet:", len(df))
if __name__ == "__main__":
    main()
