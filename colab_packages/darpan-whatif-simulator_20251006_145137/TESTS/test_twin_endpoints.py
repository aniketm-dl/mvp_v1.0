from fastapi.testclient import TestClient
from src.api.service import app

client = TestClient(app)

def test_twin_personas_list():
    """Test GET /twin/personas returns persona cards."""
    r = client.get("/twin/personas")
    assert r.status_code == 200
    data = r.json()
    assert "personas" in data
    personas = data["personas"]
    assert len(personas) == 3

    # Check structure of first persona
    p = personas[0]
    assert "id" in p
    assert "label" in p
    assert "blurb" in p
    assert "system_prompt" in p
    assert "decision_constraints" in p

def test_twin_chat_budget_conscious():
    """Test /twin/chat with k0 (Budget-Conscious)."""
    payload = {
        "twin_id": "k0",
        "history": [],
        "prompt": "What do you look for when shopping?"
    }
    r = client.post("/twin/chat", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["twin_id"] == "k0"
    assert "reply" in data
    assert len(data["reply"]) > 0
    # Should mention price
    assert "price" in data["reply"].lower() or "deal" in data["reply"].lower()

def test_twin_chat_unknown_twin():
    """Test /twin/chat rejects unknown twin ID."""
    payload = {
        "twin_id": "k999",
        "history": [],
        "prompt": "Hello"
    }
    r = client.post("/twin/chat", json=payload)
    assert r.status_code == 404

def test_twin_decide_valid_decision():
    """Test /twin/decide returns valid decision structure."""
    payload = {
        "twin_id": "k0",
        "context": {"price_mean": 500},
        "candidates": [{"id": "A1"}, {"id": "A2"}, {"id": "A3"}],
        "max_tokens": 20
    }
    r = client.post("/twin/decide", json=payload)
    assert r.status_code == 200
    data = r.json()

    # Check structure
    assert "twin_id" in data
    assert "decision" in data
    dec = data["decision"]
    assert "pick" in dec
    assert "why" in dec

    # Pick should be one of the candidates
    assert dec["pick"] in ["A1", "A2", "A3"]

    # Reason should be non-empty and short
    assert len(dec["why"]) > 0
    assert len(dec["why"].split()) <= 20

def test_twin_decide_no_candidates():
    """Test /twin/decide rejects empty candidates."""
    payload = {
        "twin_id": "k0",
        "context": {},
        "candidates": []
    }
    r = client.post("/twin/decide", json=payload)
    assert r.status_code == 422

def test_twin_decide_deterministic():
    """Test that /twin/decide is deterministic."""
    payload = {
        "twin_id": "k1",
        "context": {"price_mean": 1000},
        "candidates": [{"id": "P1"}, {"id": "P2"}]
    }
    r1 = client.post("/twin/decide", json=payload)
    r2 = client.post("/twin/decide", json=payload)

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json() == r2.json()

def test_twin_separability():
    """Test that different twins make different decisions."""
    candidates = [{"id": "A"}, {"id": "B"}, {"id": "C"}]
    context = {"price_mean": 500}

    decisions = {}
    for twin_id in ["k0", "k1", "k2"]:
        payload = {
            "twin_id": twin_id,
            "context": context,
            "candidates": candidates
        }
        r = client.post("/twin/decide", json=payload)
        assert r.status_code == 200
        decisions[twin_id] = r.json()["decision"]["pick"]

    # At least two twins should pick differently (basic separability)
    unique_picks = len(set(decisions.values()))
    assert unique_picks >= 2, f"Twins made same pick: {decisions}"
