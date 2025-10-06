from fastapi.testclient import TestClient
from src.api.service import app
import copy

client = TestClient(app)

def test_simulate_is_reproducible():
    payload = {
        "cta_seq": [{
            "user_id":"u1","session_id":"s1","ts":"2025-06-01T12:00:00",
            "context":{"page_type":"search","category":"sunscreen","price_mean":820,"visible_products":["A1","A2","A3"]},
            "task":"choose_product","action_id":"A2"
        }],
        "task": "choose_product",
        "scenarios": [
            {"variant_id":"base","context_overrides":{}},
            {"variant_id":"promo","context_overrides":{"promo_badge":True}}
        ],
        "topk": 5, "explain": "blend", "deterministic": True, "seed": 17
    }
    r1 = client.post("/simulate", json=payload)
    r2 = client.post("/simulate", json=payload)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["by_scenario"] == r2.json()["by_scenario"]
    assert r1.json()["twin_weights"] == r2.json()["twin_weights"]

def test_simulate_uses_real_twin_weights():
    """Test that /simulate returns computed twin weights, not hardcoded."""
    payload = {
        "cta_seq": [{
            "user_id":"u1","session_id":"s1","ts":"2025-06-01T12:00:00",
            "context":{"price_mean":500,"visible_products":["A1","A2"]},
            "task":"choose_product","action_id":"A1"
        }],
        "task": "choose_product",
        "scenarios": [{"variant_id":"base","context_overrides":{}}],
        "topk": 3, "deterministic": True, "seed": 17
    }
    r = client.post("/simulate", json=payload)
    assert r.status_code == 200
    data = r.json()

    # Check twin weights sum to 1
    weights = data["twin_weights"]
    total = sum(weights.values())
    assert abs(total - 1.0) < 0.001

    # Check primary twin is in weights
    primary = data["primary_twin"]
    assert primary["id"] in weights
    assert primary["label"] is not None

    # Should have 3 twins
    assert len(weights) == 3

def test_simulate_with_per_twin_explain():
    """Test /simulate with per_twin explain mode returns twin decisions."""
    payload = {
        "cta_seq": [{
            "user_id":"u1","session_id":"s1","ts":"2025-06-01T12:00:00",
            "context":{"price_mean":700,"visible_products":["P1","P2","P3"]},
            "task":"choose_product","action_id":"P1"
        }],
        "task": "choose_product",
        "scenarios": [{"variant_id":"test","context_overrides":{}}],
        "topk": 3,
        "explain": "per_twin",
        "deterministic": True,
        "seed": 17
    }
    r = client.post("/simulate", json=payload)
    assert r.status_code == 200
    data = r.json()

    # Check by_twin is populated
    scenario = data["by_scenario"][0]
    assert scenario["by_twin"] is not None
    assert len(scenario["by_twin"]) == 3  # Should have all 3 twins

    # Check each twin made a pick
    for twin_pick in scenario["by_twin"]:
        assert "twin_id" in twin_pick
        assert "picks" in twin_pick
        assert len(twin_pick["picks"]) > 0
        assert "why" in twin_pick
        assert len(twin_pick["why"]) > 0

def test_simulate_weighted_blending():
    """Test that /simulate blends decisions using twin weights."""
    payload = {
        "cta_seq": [{
            "user_id":"u1","session_id":"s1","ts":"2025-06-01T12:00:00",
            "context":{"price_mean":800,"visible_products":["A","B","C"]},
            "task":"choose_product","action_id":"A"
        }],
        "task": "choose_product",
        "scenarios": [{"variant_id":"blend_test","context_overrides":{}}],
        "topk": 3,
        "explain": "none",
        "deterministic": True,
        "seed": 17
    }
    r = client.post("/simulate", json=payload)
    assert r.status_code == 200
    data = r.json()

    # Check topN has weighted probabilities
    topN = data["by_scenario"][0]["topN"]
    assert len(topN) > 0

    # Probabilities should sum to approximately 1.0 (weighted votes from twins)
    total_prob = sum(item["p"] for item in topN)
    assert abs(total_prob - 1.0) < 0.01
