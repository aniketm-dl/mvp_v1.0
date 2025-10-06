from fastapi.testclient import TestClient
from src.api.service import app

client = TestClient(app)

def test_match_with_cta():
    """Test /match endpoint with CTA sequence."""
    payload = {
        "cta_seq": [{
            "user_id": "u1",
            "session_id": "s1",
            "ts": "2025-06-01T12:00:00",
            "context": {"page_type": "search", "price_mean": 820, "visible_products": ["A1", "A2"]},
            "task": "choose_product",
            "action_id": "A1"
        }]
    }
    r = client.post("/match", json=payload)
    assert r.status_code == 200
    data = r.json()

    # Check structure
    assert "twin_weights" in data
    assert "primary_twin" in data

    # Check weights sum to 1
    weights = data["twin_weights"]
    total = sum(weights.values())
    assert abs(total - 1.0) < 0.001

    # Check primary twin
    assert data["primary_twin"]["id"] in weights
    assert "label" in data["primary_twin"]

def test_match_without_input():
    """Test /match rejects request without cta_seq or user_id."""
    payload = {}
    r = client.post("/match", json=payload)
    assert r.status_code == 400
    assert "Provide cta_seq or z_or_user_id" in r.json()["detail"]

def test_match_deterministic():
    """Test that /match produces same results for same input."""
    payload = {
        "cta_seq": [{
            "user_id": "u1",
            "session_id": "s1",
            "ts": "2025-06-01T12:00:00",
            "context": {"price_mean": 500, "visible_products": ["A1"]},
            "task": "choose_product",
            "action_id": "A1"
        }]
    }
    r1 = client.post("/match", json=payload)
    r2 = client.post("/match", json=payload)

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json() == r2.json()

def test_match_different_cta_different_weights():
    """Test that different CTAs produce different twin weights."""
    payload1 = {
        "cta_seq": [{
            "user_id": "u1",
            "session_id": "s1",
            "ts": "2025-06-01T12:00:00",
            "context": {"price_mean": 200, "visible_products": ["A1"]},
            "task": "choose_product",
            "action_id": "A1"
        }]
    }
    payload2 = {
        "cta_seq": [{
            "user_id": "u2",
            "session_id": "s2",
            "ts": "2025-06-01T14:00:00",
            "context": {"price_mean": 2000, "promo_badge": True, "visible_products": ["B1", "B2"]},
            "task": "refine",
            "action_id": "B1"
        }]
    }
    r1 = client.post("/match", json=payload1)
    r2 = client.post("/match", json=payload2)

    assert r1.status_code == 200
    assert r2.status_code == 200

    # Different inputs should generally produce different weights
    weights1 = r1.json()["twin_weights"]
    weights2 = r2.json()["twin_weights"]
    # At least one weight should be different
    assert weights1 != weights2
