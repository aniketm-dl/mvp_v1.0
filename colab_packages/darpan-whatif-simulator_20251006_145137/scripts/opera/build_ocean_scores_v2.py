from pathlib import Path
import re, pandas as pd
LEX={"O":[r"curio\w*",r"creativ\w*",r"novel\w*",r"explor\w*",r"imagin\w*",r"art\w*",r"variet\w*"],
     "C":[r"plan\w*",r"schedule\w*",r"organize\w*",r"deadline\w*",r"careful\w*",r"task\w*",r"neat\w*"],
     "E":[r"social\w*",r"outgoing\w*",r"party\w*",r"talk\w*",r"group\w*",r"energetic\w*"],
     "A":[r"kind\w*",r"help\w*",r"cooperat\w*",r"trust\w*",r"considerate\w*",r"friendl\w*"],
     "N":[r"worr\w*",r"anxi\w*",r"stress\w*",r"upset\w*",r"nervous\w*",r"depress\w*"]}
T=["O","C","E","A","N"]
def hits(txt, pats):
    if not isinstance(txt,str) or not txt.strip(): return 0
    t=" "+re.sub(r"[^a-z0-9\s]"," ",txt.lower())+" "
    return sum(len(re.findall(p,t)) for p in pats)
ft=pd.read_parquet("DATA/derived/user_fulltext.parquet")
rows=[]
for uid,txt in ft[["user_id","full_text"]].itertuples(index=False):
    cnt={k:hits(txt,LEX[k]) for k in T}; tot=sum(cnt.values())
    share={k:(cnt[k]+1)/(tot+len(T)) for k in T}   # smooth within user
    rows.append({"user_id":uid,**share})
S=pd.DataFrame(rows)
for k in T: S[k]=S[k].rank(method="average", pct=True)  # percentile across users
Path("DATA/derived").mkdir(parents=True, exist_ok=True)
S.to_parquet("DATA/derived/user_ocean.parquet", index=False)
print("Wrote DATA/derived/user_ocean.parquet", len(S)); print(S.describe().T)
