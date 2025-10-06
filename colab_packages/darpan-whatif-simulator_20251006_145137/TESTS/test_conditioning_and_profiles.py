from fastapi.testclient import TestClient
from src.api.service import app

c = TestClient(app)

def _cta():
    return [{
        "user_id":"u1","session_id":"s1","ts":"2025-06-01T12:00:00",
        "context":{"page_type":"search","visible_products":["A1","A2","A3"],"promo_badge":True,"delivery_eta_days":2},
        "task":"choose_product","action_id":"A2"
    }]

def test_match_uses_fused_embedding():
    r = c.post("/match", json={"cta_seq": _cta()})
    assert r.status_code == 200
    w = r.json()["twin_weights"]
    assert abs(sum(w.values()) - 1.0) < 1e-6

def test_simulate_deterministic_with_profiles():
    payload = {"cta_seq": _cta(), "task":"choose_product", "scenarios":[{"variant_id":"base","context_overrides":{}}], "deterministic":True, "seed":17}
    r1 = c.post("/simulate", json=payload)
    r2 = c.post("/simulate", json=payload)
    # Compare everything except run_id (which is a UUID)
    j1 = r1.json()
    j2 = r2.json()
    assert j1["by_scenario"] == j2["by_scenario"]
    assert j1["twin_weights"] == j2["twin_weights"]
    assert j1["primary_twin"] == j2["primary_twin"]
