# What-If Simulator — Engineering Spec

Purpose
Given a base context and multiple scenario patches, return the option each twin would pick, short grounded reasons, and the blended result. Deterministic by default. Twins remain differentiable.

Allowed edits (ALLOWED_MUTABLES)
price_mean, price_min, price_max
promo_badge (bool)
delivery_eta_days (int)
copy_variant_id (str; references CopyVariant)

We never expand the candidate set. Candidates are the page-visible items or UI actions.

Data contracts (additions)
ScenarioPatch
{
  "variant_id": "string",
  "context_overrides": {
    "price_mean": 799.0,
    "promo_badge": true,
    "delivery_eta_days": 2,
    "copy_variant_id": "C2"
  },
  "candidates": [{"id":"A1"},{"id":"A2"}]
}

CopyVariant table
copy_variant_id: str (pk)
slot: search_snippet | pdp_badge | banner
text: str (<=120)

context_now additions
promo_badge: bool
delivery_eta_days: int
copy_variant_id: str | null

Determinism
Single seed per call; set deterministic flags.
Temperature 0 for reasons; canonical sort by p desc then id asc.
Quantize floats at feature boundary; bucket rounded numerics used in reasons.
Cache reasons by (twin|mixture, scenario_hash, candidate_id).
Byte-equal JSON across identical runs.

Twin separability
Center loss and inter-twin margin on embeddings.
Policy diversity penalty using pairwise JSD on shared mini-batches.
Thresholds: silhouette ≥ 0.35; mean pairwise JSD ≥ 0.10; ARI ≥ 0.80 across seeds.

Reasons
≤ 20 tokens. Visible-only facts from page/scenario. Use rounded numerics.
ReasonGuard: schema check, numeric audit, length, re-query stability.
Fallback templater when the LLM fails checks.

Evaluation
ScenarioSuite: directional checks for price, promo, copy effects.
ReproSuite: triple-run byte equality. ReasonRepeat: identical strings at temp 0.
SeparationSuite: thresholds above; fail the build if violated.
Keep accuracy and calibration targets from the base MVP.

Performance
/simulate p95 ≤ 200 ms for 5 scenarios × top-5 using distilled heads.
≤ 1 s with per-twin reasons.
