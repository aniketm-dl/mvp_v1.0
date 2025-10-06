from fastapi.testclient import TestClient
from src.api.service import app

c = TestClient(app)

def _cta():
    return [{
        "user_id":"u1","session_id":"s1","ts":"2025-06-01T12:00:00",
        "context":{"page_type":"search","visible_products":["A1","A2","A3"],"promo_badge":True,"delivery_eta_days":2},
        "task":"choose_product","action_id":"A2"
    }]

def test_versions_endpoint():
    r = c.get("/versions")
    assert r.status_code == 200
    j = r.json()
    assert "twin_bank_version" in j and "policy_heads" in j

def test_admin_pin_flow_and_simulate_with_pin():
    # create pin
    r = c.post("/admin/pin", headers={"X-Admin-Token":"changeme"}, json={"name":"demo","weights":{"k1":0.5,"k2":0.5}})
    assert r.status_code == 200
    # list pin
    r2 = c.get("/admin/pins", headers={"X-Admin-Token":"changeme"})
    assert r2.status_code == 200 and "demo" in r2.json()["pins"]
    # simulate with pin
    payload = {"cta_seq": _cta(), "task":"choose_product",
               "scenarios":[{"variant_id":"base","context_overrides":{}}],
               "deterministic":True, "seed":17, "use_pin":"demo"}
    s = c.post("/simulate", json=payload)
    assert s.status_code == 200
    # delete pin
    d = c.delete("/admin/pin/demo", headers={"X-Admin-Token":"changeme"})
    assert d.status_code == 200
