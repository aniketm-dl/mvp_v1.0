from pathlib import Path
import json, argparse, numpy as np, pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
TRAITS=["O","C","E","A","N"]
def label_for(c, eps=0.03):
    idx=np.argsort(c)[::-1]; names=[TRAITS[i] for i in idx]; d=c[idx]
    return f"{names[0]}>{names[1]}>" + (names[2] if len(d)>=3 and d[1]-d[2]<eps else "") .rstrip(">")
ap=argparse.ArgumentParser(); ap.add_argument("--k",type=int,default=8); ap.add_argument("--min_rows",type=int,default=1); a=ap.parse_args()
df=pd.read_parquet("DATA/derived/user_ocean.parquet"); X=df[TRAITS].to_numpy("float32")
km=KMeans(n_clusters=a.k, n_init=20, random_state=17).fit(StandardScaler().fit_transform(X))
df["cluster"]=km.labels_; labels=[label_for(km.cluster_centers_[i]) for i in range(a.k)]; df["label"]=df["cluster"].map(lambda c:labels[int(c)])
Path("DATA/derived").mkdir(parents=True,exist_ok=True)
df[["user_id","cluster","label"]].to_parquet("DATA/derived/user_ocean_clusters.parquet", index=False)
pers=[]; counts=df["cluster"].value_counts().to_dict()
for i in range(a.k):
    if counts.get(i,0) >= a.min_rows: pers.append({"id":f"p{i+1:02d}","label":labels[i],"cluster_id":i,"tags":[labels[i]]})
Path("DATA").mkdir(exist_ok=True); Path("DATA/personas.json").write_text(json.dumps({"personas":pers},indent=2))
print("kept:",len(pers))
