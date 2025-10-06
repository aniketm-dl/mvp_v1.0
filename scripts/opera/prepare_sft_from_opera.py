from pathlib import Path
import glob, json, pyarrow.parquet as pq, pandas as pd, yaml
FALLBACK = ["input_text","rationale","products","simplified_html","element_meta","page_meta"]
def have_cols(p): return set(pq.ParquetFile(p).schema.names)
def read_cols(p, cols): 
    cols=[c for c in cols if c]; wanted=[c for c in cols if c in have_cols(p)]
    return pd.read_parquet(p, columns=wanted) if wanted else pd.DataFrame()
def main():
    cfg=yaml.safe_load(Path("CONFIGS/opera/fields.yaml").read_text())
    src=cfg["source"]["path"]; C=cfg["columns"]; tag=C["psychographic_tags"]
    by_tag=cfg["assignment"]["by_tag"]; default=cfg["assignment"]["default_twin"]; cap=int(cfg.get("limits",{}).get("per_twin_max",2000))
    out=Path("DATA/sft"); out.mkdir(parents=True, exist_ok=True)
    buckets={tid:[] for tid in by_tag.values()}; buckets.setdefault(default,[])
    for p in sorted(glob.glob(f"{src}/*.parquet")):
        base=[C.get("user_id"),C.get("session_id"),C.get("timestamp"),C.get("action_type"),tag]
        text_cols=[c for c in FALLBACK if c in have_cols(p)]
        df=read_cols(p, base+text_cols)
        if df.empty: continue
        df["_text"]=df[text_cols].astype(str).apply(lambda r:" ".join([x for x in r.tolist() if x and x!="nan"]),axis=1) if text_cols else ""
        def route(t): return by_tag.get(t, default)
        df["_twin"]=df[tag].map(route)
        for tid,g in df.groupby("_twin"):
            room=cap-len(buckets.setdefault(tid,[]))
            for _,row in g.head(room).iterrows():
                buckets[tid].append({"twin_id":tid,"text":str(row["_text"])[:2000],"tag":row.get(tag,None)})
    wrote=0
    for tid,ex in buckets.items():
        if not ex: continue
        (out/f"{tid}.jsonl").write_text("\n".join(json.dumps(x) for x in ex), encoding="utf-8"); wrote+=1
    print("Wrote SFT for", wrote, "twins into DATA/sft/")
if __name__=="__main__": main()
