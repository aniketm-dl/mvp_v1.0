from __future__ import annotations
import json
import http.client
import argparse

def _post(host, port, path, payload, headers=None):
    conn = http.client.HTTPConnection(host, port)
    body = json.dumps(payload)
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    conn.request("POST", path, body=body, headers=h)
    resp = conn.getresponse()
    data = resp.read()
    print(resp.status, resp.reason)
    print(data.decode())
    conn.close()

def _get(host, port, path, headers=None):
    conn = http.client.HTTPConnection(host, port)
    h = headers or {}
    conn.request("GET", path, headers=h)
    resp = conn.getresponse()
    data = resp.read()
    print(resp.status, resp.reason)
    print(data.decode())
    conn.close()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("versions")

    p2 = sub.add_parser("pin")
    p2.add_argument("--name", required=True)
    p2.add_argument("--weights", required=True, help='JSON, e.g. {"k3":0.6,"k7":0.4}')
    p2.add_argument("--token", default="changeme")
    p2.add_argument("--conditioning", default=None, help="JSON or leave empty")

    p3 = sub.add_parser("pins")
    p3.add_argument("--token", default="changeme")

    p4 = sub.add_parser("simulate_pin")
    p4.add_argument("--pin", required=True)

    args = ap.parse_args()

    if args.cmd == "versions":
        _get(args.host, args.port, "/versions")
    elif args.cmd == "pins":
        _get(args.host, args.port, "/admin/pins", headers={"X-Admin-Token": args.token})
    elif args.cmd == "pin":
        cond = json.loads(args.conditioning) if args.conditioning else None
        _post(args.host, args.port, "/admin/pin",
              {"name": args.name, "weights": json.loads(args.weights), "conditioning": cond},
              headers={"X-Admin-Token": args.token})
    elif args.cmd == "simulate_pin":
        payload = {
            "cta_seq": [{
                "user_id":"u1","session_id":"s1","ts":"2025-06-01T12:00:00",
                "context":{"page_type":"search","visible_products":["A1","A2","A3"],"promo_badge":True,"delivery_eta_days":2},
                "task":"choose_product","action_id":"A2"
            }],
            "task":"choose_product",
            "scenarios":[{"variant_id":"base","context_overrides":{}},{"variant_id":"promo","context_overrides":{"promo_badge":True}}],
            "deterministic": True, "seed": 17,
            "use_pin": args.pin,
            "explain": "blend"
        }
        _post(args.host, args.port, "/simulate", payload)

if __name__ == "__main__":
    main()
