from __future__ import annotations
import json, http.client, argparse

def _get(path):
    conn = http.client.HTTPConnection("127.0.0.1", 8000)
    conn.request("GET", path)
    r = conn.getresponse()
    print(r.status, r.reason)
    print(r.read().decode())
    conn.close()

def _post(path, payload, headers=None):
    conn = http.client.HTTPConnection("127.0.0.1", 8000)
    conn.request("POST", path, body=json.dumps(payload), headers={"Content-Type":"application/json", **(headers or {})})
    r = conn.getresponse()
    print(r.status, r.reason)
    print(r.read().decode())
    conn.close()

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("bank")
    p = sub.add_parser("inspect")
    p.add_argument("--twin")
    c = sub.add_parser("chat")
    c.add_argument("--twin")
    c.add_argument("--prompt", default="What do you value?")
    d = sub.add_parser("decide")
    d.add_argument("--twin")
    d.add_argument("--cands", default="A1,A2,A3")
    r = sub.add_parser("reload")
    r.add_argument("--twin")
    r.add_argument("--token", default="changeme")
    args = ap.parse_args()

    if args.cmd=="bank":
        _get("/twin/bank")
    elif args.cmd=="inspect":
        _get(f"/twin/{args.twin}/inspect")
    elif args.cmd=="chat":
        _post("/twin/chat", {"twin_id":args.twin,"history":[],"prompt":args.prompt})
    elif args.cmd=="decide":
        cands=[{"id":x.strip()} for x in args.cands.split(",")]
        _post("/twin/decide", {"twin_id":args.twin,"context":{"page_type":"search","visible_products":[x["id"] for x in cands]},"candidates":cands,"max_tokens":20})
    elif args.cmd=="reload":
        _post(f"/admin/twin/{args.twin}/reload", {}, headers={"X-Admin-Token":args.token})

if __name__ == "__main__":
    main()
