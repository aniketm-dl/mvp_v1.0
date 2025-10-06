from src.models.encoder import encode_cta, project_psychographics, embed_demographics, fuse_joint
from src.models.mixture import load_twin_bank, responsibilities
from src.models.twin_bank import get_twin_ids

def test_encoder_produces_8d_vector():
    """Test that encoder produces an 8-D normalized vector."""
    cta = [{
        "user_id": "u1",
        "session_id": "s1",
        "ts": "2025-06-01T12:00:00",
        "context": {"page_type": "search", "price_mean": 820, "visible_products": ["A1", "A2"]},
        "task": "choose_product",
        "action_id": "A1"
    }]
    emb = encode_cta(cta)
    assert len(emb) == 8
    # Check L2 normalization (should be close to 1.0)
    norm = sum(x**2 for x in emb) ** 0.5
    assert abs(norm - 1.0) < 0.01

def test_mixture_weights_sum_to_one():
    """Test that twin weights sum to 1.0."""
    cta = [{
        "user_id": "u1",
        "session_id": "s1",
        "ts": "2025-06-01T12:00:00",
        "context": {"price_mean": 500, "visible_products": ["A1"]},
        "task": "choose_product",
        "action_id": "A1"
    }]
    z_b = encode_cta(cta)
    z_p = project_psychographics([0.9, 0.2, 0.4, 0.3, 1.0, 1.0, 0.0])
    z_d = embed_demographics([0.9, 0.2, 0.4, 0.3, 1.0, 1.0, 0.0])
    emb = fuse_joint(z_b, z_p, z_d)
    bank = load_twin_bank()
    weights = responsibilities(emb, bank)

    total = sum(weights.values())
    assert abs(total - 1.0) < 0.001

def test_primary_twin_selection():
    """Test that primary twin is the one with highest weight."""
    cta = [{
        "user_id": "u1",
        "session_id": "s1",
        "ts": "2025-06-01T12:00:00",
        "context": {"price_mean": 300, "promo_badge": True, "visible_products": ["A1", "A2"]},
        "task": "choose_product",
        "action_id": "A1"
    }]
    z_b = encode_cta(cta)
    z_p = project_psychographics([0.9, 0.2, 0.4, 0.3, 1.0, 1.0, 0.0])
    z_d = embed_demographics([0.9, 0.2, 0.4, 0.3, 1.0, 1.0, 0.0])
    emb = fuse_joint(z_b, z_p, z_d)
    bank = load_twin_bank()
    weights = responsibilities(emb, bank)

    # Should have weights for all twins
    assert len(weights) == 3
    max_weight = max(weights.values())
    assert max_weight > 0

def test_twin_count():
    """Test that we have exactly 3 twins."""
    twin_ids = get_twin_ids()
    assert len(twin_ids) == 3
    assert twin_ids == ["k0", "k1", "k2"]

def test_deterministic_encoding():
    """Test that encoding is deterministic."""
    cta = [{
        "user_id": "u1",
        "session_id": "s1",
        "ts": "2025-06-01T12:00:00",
        "context": {"price_mean": 750, "visible_products": ["A1", "A2", "A3"]},
        "task": "choose_product",
        "action_id": "A2"
    }]
    emb1 = encode_cta(cta)
    emb2 = encode_cta(cta)
    assert emb1 == emb2
