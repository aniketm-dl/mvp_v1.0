# API Schemas (Pydantic v2)

CTAStep (internal)
user_id: str
session_id: str
ts: datetime
context: dict  // page_type, category, price stats, visible products, url mask
task: choose_product | refine | stop | nav_action
action_id: str

RecommendRequest
cta_seq: list[CTAStep]
context_now: dict
task: same literals as CTAStep.task
topk: int
explain: bool

RecommendResponse
topN: list[{id, p}]
twin_weights: dict[twin_id, float]
primary_twin: {id, label}
why: str | null

ScenarioPatch
See SPECS. Fields outside ALLOWED_MUTABLES → 422.

SimulateRequest
{
  "cta_seq": [CTAStep] | null,
  "z_or_user_id": "optional",
  "task": "choose_product" | "refine",
  "scenarios": [ScenarioPatch],
  "topk": 5,
  "explain": "none" | "blend" | "per_twin",
  "deterministic": true,
  "seed": 17,
  "mixture": {"auto_from_cta": true} | {"weights": {"k3":0.6,"k7":0.4}}
}

SimulateResponse
{
  "by_scenario": [{
    "variant_id": "V1",
    "topN": [{"id":"A1","p":0.42}],
    "why": "Wants SPF 50 under 800.",
    "by_twin": [{"twin_id":"k3","picks":[{"id":"A1","p":0.71}],"why":"Hunts deals under 800."}],
    "deltas": {"A1": +0.07, "A2": -0.05}
  }],
  "twin_weights": {"k3":0.6, "k7":0.4},
  "primary_twin": {"id":"k3","label":"Deal-seeking Explorer"},
  "sim_config": {"run_id":"...", "seed":17}
}

Errors
400 schema mismatch
422 empty candidate set or disallowed context key
503 models not warmed up
