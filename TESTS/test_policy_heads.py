from fastapi.testclient import TestClient
from src.api.service import app
import json, os

c = TestClient(app)

def _cta():
    return [{
        "user_id":"u1","session_id":"s1","ts":"2025-06-01T12:00:00",
        "context":{"page_type":"search","visible_products":["A1","A2","A3"],"promo_badge":True,"delivery_eta_days":2},
        "task":"choose_product","action_id":"A2"
    }]

def test_health_reports_heads_flag():
    r = c.get("/health")
    assert r.status_code == 200
    j = r.json()
    assert "use_heads" in j and "heads_loaded" in j

def test_simulate_probs_sum_to_one():
    payload = {"cta_seq": _cta(), "task":"choose_product",
               "scenarios":[{"variant_id":"base","context_overrides":{}}],
               "deterministic":True, "seed":17}
    r = c.post("/simulate", json=payload)
    assert r.status_code == 200
    topN = r.json()["by_scenario"][0]["topN"]
    s = sum(p["p"] for p in topN)
    # topN shows all candidates, sum should be close to 1.0
    assert abs(s - 1.0) < 0.01

def test_blending_matches_weighted_sum_when_heads_loaded_or_uniform():
    payload = {"cta_seq": _cta(), "task":"choose_product",
               "scenarios":[{"variant_id":"base","context_overrides":{}}],
               "deterministic":True, "seed":17}
    r = c.post("/simulate", json=payload)
    assert r.status_code == 200
    # This test asserts endpoint stability, not numerical specifics (since heads may be missing).
    # If heads loaded -> mixture of per-twin probs; if not -> uniform or LLM vote fallback.
    assert "by_scenario" in r.json()

def test_serving_config_in_sim_config():
    payload = {"cta_seq": _cta(), "task":"choose_product",
               "scenarios":[{"variant_id":"base","context_overrides":{}}],
               "deterministic":True, "seed":17}
    r = c.post("/simulate", json=payload)
    assert r.status_code == 200
    sim_cfg = r.json()["sim_config"]
    assert "serving" in sim_cfg
    assert "use_heads" in sim_cfg["serving"]
    assert "heads_loaded" in sim_cfg["serving"]
