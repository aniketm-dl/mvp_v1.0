from __future__ import annotations
import json, time, subprocess, sys
from pathlib import Path
import http.client
import yaml

def _read_yaml(p): return yaml.safe_load(Path(p).read_text())

def _flip_stub_false(llm_yaml="CONFIGS/serve/llm.yaml"):
    y = _read_yaml(llm_yaml)
    if y["llm"].get("use_stub") is True:
        y["llm"]["use_stub"] = False
        Path(llm_yaml).write_text(yaml.safe_dump(y, sort_keys=False))
        print("Set llm.use_stub:false")

def _api_post(path, payload, headers=None):
    conn = http.client.HTTPConnection("127.0.0.1", 8000, timeout=4)
    conn.request("POST", path, body=json.dumps(payload), headers={"Content-Type":"application/json", **(headers or {})})
    r = conn.getresponse(); body = r.read().decode(); conn.close()
    return r.status, (json.loads(body) if body and body[0] in "{[" else body)

def _api_get(path, headers=None):
    conn = http.client.HTTPConnection("127.0.0.1", 8000, timeout=4)
    conn.request("GET", path, headers=headers or {})
    r = conn.getresponse(); body = r.read().decode(); conn.close()
    return r.status, (json.loads(body) if body and body[0] in "{[" else body)

def main():
    train_cfg = _read_yaml("CONFIGS/opera/training.yaml")
    personas = json.loads(Path("DATA/personas.json").read_text(encoding="utf-8"))["personas"]
    print(f"Training {len(personas)} personas")

    # 1) Generate SFT from OPeRA (per fields.yaml rules)
    subprocess.check_call([sys.executable, "scripts/opera/sft_all_from_opera.py", "--fields_cfg", "CONFIGS/opera/fields.yaml"])

    # 2) Train LoRA adapters per twin id
    ok_all = True
    for p in personas:
        tid = p["id"]
        print(f"[train] {tid}")
        code = subprocess.call([sys.executable, "scripts/train_llm_persona_sft.py", "--twin_id", tid])
        ok_all = ok_all and (code == 0)

    # 3) Flip to real runtime and reload adapters
    if train_cfg["runtime_after_train"]["set_use_stub_false"]:
        _flip_stub_false()
    if train_cfg["runtime_after_train"]["reload_all_adapters"]:
        for p in personas:
            tid = p["id"]
            st, _ = _api_post(f"/admin/twin/{tid}/reload", {}, headers={"X-Admin-Token":"changeme"})
            print(f"[reload] {tid} -> {st}")

    # 4) Verify: chat with a few
    prompt = train_cfg["verify"]["chat_prompt"]
    max_check = int(train_cfg["verify"]["max_check"])
    st, bank = _api_get("/twin/bank")
    ids = [t["id"] for t in (bank.get("twins") or [])][:max_check]
    for tid in ids:
        st, j = _api_post("/twin/chat", {"twin_id": tid, "history": [], "prompt": prompt})
        print(f"[chat] {tid} -> {st} | {j}")

    print("Pipeline completed.")

if __name__ == "__main__":
    main()
