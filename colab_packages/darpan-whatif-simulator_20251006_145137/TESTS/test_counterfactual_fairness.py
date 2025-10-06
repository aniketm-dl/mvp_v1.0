"""
Test counterfactual fairness: flipping demographic features should not dramatically change decisions.
"""
from __future__ import annotations
from src.models.encoder import encode_cta, project_psychographics, embed_demographics, fuse_joint
from src.models.mixture import load_twin_bank, responsibilities
from src.reasoning.llm_twin import decide_as_twin

def test_counterfactual_stability():
    """Flipping demographics should produce similar twin weights (within tolerance)"""
    bank = load_twin_bank()

    # Base profile: behavior + psychographic + demographic
    z_b = encode_cta([{"user_id": "u1", "action": "choose", "page_type": "search", "visible_products": ["A1", "A2"]}])
    z_p = project_psychographics([0.9, 0.2, 0.4, 0.3])  # thrift, novelty, quality, speed

    # Original demographic: age_25_34=1.0, urban=1.0, female=0.0
    z_d_orig = embed_demographics([1.0, 1.0, 0.0])
    z_orig = fuse_joint(z_b, z_p, z_d_orig)
    w_orig = responsibilities(z_orig, bank)

    # Counterfactual: flip gender to female=1.0
    z_d_cf = embed_demographics([1.0, 1.0, 1.0])
    z_cf = fuse_joint(z_b, z_p, z_d_cf)
    w_cf = responsibilities(z_cf, bank)

    # Check L1 distance between weight vectors
    l1_dist = sum(abs(w_orig.get(tid, 0.0) - w_cf.get(tid, 0.0)) for tid in set(w_orig) | set(w_cf))

    # Tolerance: weights should not shift by more than 0.3 total L1 distance
    assert l1_dist < 0.3, f"Counterfactual instability: L1={l1_dist:.4f} exceeds 0.3"

def test_decision_counterfactual():
    """Flipping demographics should not change the pick in most cases"""
    context = {"page_type": "search", "visible_products": ["A1", "A2", "A3"], "price_mean": 500}
    candidates = [{"id": "A1"}, {"id": "A2"}, {"id": "A3"}]

    # Base conditioning
    cond_base = {
        "psychographic_tags": ["thrifty", "quality_oriented"],
        "demographic_profile": {"age_group": "25-34", "location_type": "urban", "gender": "male"}
    }

    # Counterfactual: flip gender
    cond_cf = {
        "psychographic_tags": ["thrifty", "quality_oriented"],
        "demographic_profile": {"age_group": "25-34", "location_type": "urban", "gender": "female"}
    }

    # Test each twin
    for twin_id in ["k0", "k1", "k2"]:
        dec_base = decide_as_twin(twin_id, context, candidates, 20, cond_base)
        dec_cf = decide_as_twin(twin_id, context, candidates, 20, cond_cf)

        # Picks should be the same (our mock twins don't use demographics)
        assert dec_base["pick"] == dec_cf["pick"], f"{twin_id}: pick changed under counterfactual"
