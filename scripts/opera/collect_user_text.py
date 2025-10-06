from pathlib import Path
import glob, pandas as pd
def main():
    S = pd.concat([pd.read_parquet(p,columns=["session_id","user_id"])
                   for p in glob.glob("DATA/opera/filtered_session/train/*.parquet")],
                  ignore_index=True).drop_duplicates("session_id")
    A = pd.concat([pd.read_parquet(p, columns=["session_id","input_text"])
                   for p in glob.glob("DATA/opera/filtered_action/train/*.parquet")],
                  ignore_index=True).merge(S, on="session_id", how="left").dropna(subset=["user_id"])
    agg = (A.groupby("user_id")["input_text"]
             .apply(lambda s: " ".join(x for x in s.astype(str) if x and x!="nan"))
             .reset_index().rename(columns={"input_text":"actions_text"}))
    U = pd.concat([pd.read_parquet(p, columns=["user_id","survey","interview_transcript_processed"])
                   for p in glob.glob("DATA/opera/filtered_user/train/*.parquet")],
                  ignore_index=True)
    U["base_text"] = (U["interview_transcript_processed"].fillna("")+" "+U["survey"].fillna(""))
    out = U[["user_id","base_text"]].merge(agg, on="user_id", how="left")
    out["full_text"] = (out["base_text"].fillna("")+" "+out["actions_text"].fillna("")).str.strip()
    Path("DATA/derived").mkdir(parents=True, exist_ok=True)
    out[["user_id","full_text"]].to_parquet("DATA/derived/user_fulltext.parquet", index=False)
    print("Wrote DATA/derived/user_fulltext.parquet", len(out))
if __name__=="__main__": main()
