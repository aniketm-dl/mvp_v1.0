"""
Reproducibility test for Phase F: deterministic simulation with guard.
"""
from __future__ import annotations
from fastapi.testclient import TestClient
from src.api.service import app

client = TestClient(app)

def test_simulate_deterministic_with_guard():
    """Same seed should produce identical results, even with guard enabled"""
    payload = {
        "cta_seq": [
            {
                "user_id": "u1",
                "session_id": "s1",
                "ts": "2025-01-01T00:00:00Z",
                "action": "choose",
                "task": "choose_product",
                "action_id": "a1",
                "page_type": "search",
                "context": {
                    "visible_products": ["A1", "A2", "A3"],
                    "promo_badge": True,
                    "delivery_eta_days": 2,
                    "price_mean": 500
                }
            }
        ],
        "task": "choose_product",
        "scenarios": [
            {"variant_id": "base", "context_overrides": {}},
            {"variant_id": "promo_off", "context_overrides": {"promo_badge": False}}
        ],
        "explain": "blend",
        "topk": 3,
        "deterministic": True,
        "seed": 42
    }

    # Run twice with same seed
    r1 = client.post("/simulate", json=payload)
    r2 = client.post("/simulate", json=payload)

    assert r1.status_code == 200
    assert r2.status_code == 200

    d1 = r1.json()
    d2 = r2.json()

    # Check determinism
    assert d1["by_scenario"] == d2["by_scenario"], "Results should be identical with same seed"
    assert d1["twin_weights"] == d2["twin_weights"]
    assert d1["primary_twin"] == d2["primary_twin"]

def test_twin_decide_with_guard():
    """Guard should be applied to /twin/decide endpoint"""
    payload = {
        "twin_id": "k0",
        "context": {"page_type": "search", "price_mean": 500},
        "candidates": [{"id": "A1"}, {"id": "A2"}, {"id": "A3"}],
        "max_tokens": 20
    }

    r = client.post("/twin/decide", json=payload)
    assert r.status_code == 200

    data = r.json()
    assert "decision" in data
    assert "pick" in data["decision"]
    assert "why" in data["decision"]

    # Guard should enforce max_tokens (from gates.yaml: 20)
    why = data["decision"]["why"]
    assert len(why.split()) <= 20, f"Guard should limit tokens: {why}"
