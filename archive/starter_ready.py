from __future__ import annotations
import json, http.client

BASE="127.0.0.1"; PORT=8000

def _get(p):
    c=http.client.HTTPConnection(BASE,PORT); c.request("GET",p); r=c.getresponse(); b=r.read().decode(); c.close(); return r.status, json.loads(b)

def _post(p,obj):
    c=http.client.HTTPConnection(BASE,PORT); c.request("POST",p,body=json.dumps(obj),headers={"Content-Type":"application/json"}); r=c.getresponse(); b=r.read().decode(); c.close(); return r.status, json.loads(b)

def main():
    st, bank = _get("/twin/bank")
    twins = bank.get("twins", [])
    ready = [t for t in twins if t.get("adapter")]
    if not ready:
        print("No adapters reported as available. Ensure training completed and adapters reloaded.")
        return
    tid = ready[0]["id"]
    print(f"Talking to {tid}...")
    st, msg = _post("/twin/chat", {"twin_id": tid, "history": [], "prompt": "What do you value when shopping?"})
    print(msg)
    ctx = {"page_type":"search","visible_products":["A1","A2","A3"],"promo_badge":True,"delivery_eta_days":2,"price_mean":799}
    st, dec = _post("/twin/decide", {"twin_id": tid, "context": ctx, "candidates":[{"id":"A1"},{"id":"A2"},{"id":"A3"}], "max_tokens":20})
    print(dec)

if __name__ == "__main__":
    main()
