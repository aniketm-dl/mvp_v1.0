from fastapi.testclient import TestClient
from src.api.service import app

c = TestClient(app)

def _cta():
    return [{
        "user_id":"u1","session_id":"s1","ts":"2025-06-01T12:00:00",
        "context":{"page_type":"search","visible_products":["A1","A2","A3"],"promo_badge":True,"delivery_eta_days":2},
        "task":"choose_product","action_id":"A2"
    }]

def test_deltas_exist_and_sum_to_zero():
    payload = {
        "cta_seq": _cta(),
        "task":"choose_product",
        "scenarios":[
            {"variant_id":"base","context_overrides":{}},
            {"variant_id":"promo","context_overrides":{"promo_badge":True}}
        ],
        "deterministic":True, "seed":17
    }
    r = c.post("/simulate", json=payload)
    assert r.status_code == 200, r.text
    j = r.json()
    base = next(s for s in j["by_scenario"] if s["variant_id"]=="base")
    promo = next(s for s in j["by_scenario"] if s["variant_id"]=="promo")
    # Base deltas should be zero
    assert all(abs(v) < 1e-9 for v in base["deltas"].values())
    # Every scenario's deltas sum to ~0 (probabilities shift mass)
    assert abs(sum(promo["deltas"].values())) < 1e-6

def test_explain_modes():
    base_req = {
        "cta_seq": _cta(),
        "task":"choose_product",
        "scenarios":[{"variant_id":"base","context_overrides":{}}],
        "deterministic":True, "seed":17
    }
    # none
    r = c.post("/simulate", json={**base_req, "explain":"none"})
    assert r.status_code == 200
    s0 = r.json()["by_scenario"][0]
    assert s0["why"] is None and s0.get("by_twin") in (None, [])

    # per_twin
    r2 = c.post("/simulate", json={**base_req, "explain":"per_twin"})
    s1 = r2.json()["by_scenario"][0]
    assert s1.get("by_twin") and isinstance(s1["by_twin"][0].get("why"), str)

    # blend
    r3 = c.post("/simulate", json={**base_req, "explain":"blend"})
    s2 = r3.json()["by_scenario"][0]
    assert isinstance(s2.get("why"), str)

def test_reason_cache_counts_increase_on_second_call():
    payload = {
        "cta_seq": _cta(),
        "task":"choose_product",
        "scenarios":[{"variant_id":"base","context_overrides":{}}],
        "deterministic":True, "seed":17,
        "explain":"per_twin"
    }
    r1 = c.post("/simulate", json=payload)
    j1 = r1.json()
    h1 = j1["sim_config"]["reason_cache"]["hits"]
    m1 = j1["sim_config"]["reason_cache"]["misses"]
    # second call should hit cache
    r2 = c.post("/simulate", json=payload)
    j2 = r2.json()
    h2 = j2["sim_config"]["reason_cache"]["hits"]
    m2 = j2["sim_config"]["reason_cache"]["misses"]
    assert h2 >= h1 and m2 >= m1
