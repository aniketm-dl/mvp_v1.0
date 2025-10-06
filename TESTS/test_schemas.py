from src.common.schemas import CTAStep, SimulateRequest, ScenarioPatch
from datetime import datetime

def test_simulate_request_loads():
    cta = CTAStep(
        user_id="u1", session_id="s1", ts=datetime(2025,6,1,12,0,0),
        context={"page_type":"search","category":"sunscreen","price_mean":820,"visible_products":["A1","A2","A3"]},
        task="choose_product", action_id="A2"
    )
    req = SimulateRequest(
        cta_seq=[cta],
        task="choose_product",
        scenarios=[
            ScenarioPatch(variant_id="base", context_overrides={}),
            ScenarioPatch(variant_id="promo", context_overrides={"promo_badge": True}),
        ],
        topk=5, explain="blend", deterministic=True, seed=17
    )
    assert req.seed == 17
    assert req.scenarios[1].context_overrides["promo_badge"] is True
