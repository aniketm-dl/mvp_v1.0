from pathlib import Path
import glob, pandas as pd
Path("DATA/opera/action_with_ocean/train").mkdir(parents=True, exist_ok=True)
clusters = pd.read_parquet("DATA/derived/user_ocean_clusters.parquet")[["user_id","label"]]
smap = pd.concat([pd.read_parquet(p, columns=["session_id","user_id"])
                  for p in glob.glob("DATA/opera/filtered_session/train/*.parquet")],
                 ignore_index=True).drop_duplicates("session_id")
for apath in sorted(glob.glob("DATA/opera/filtered_action/train/*.parquet")):
    A = pd.read_parquet(apath)
    A = A.merge(smap, on="session_id", how="left").merge(clusters, on="user_id", how="left")
    A = A.rename(columns={"label":"ocean_tag"})
    out = Path("DATA/opera/action_with_ocean/train") / Path(apath).name
    A.to_parquet(out, index=False)
    print("wrote", out, len(A))
