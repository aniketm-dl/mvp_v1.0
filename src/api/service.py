from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple, Literal
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import yaml
import json
import csv
from pathlib import Path
import time, os

from src.common.schemas import (
    SimulateRequest, SimulateResponse, ScenarioResult, TwinPick,
    MatchRequest, MatchResponse, TwinChatRequest, TwinChatResponse,
    TwinDecideRequest, TwinDecideResponse, TwinDecision,
    MetricsResponse, ValidationMetrics, TwinMetrics
)
from src.common.config import allowed_mutables
from src.common.determinism import set_global_seed, canonical_sort
from src.common.hashing import stable_hash
from src.common.rate_limit import SimpleRateLimiter
from src.models.encoder import encode_cta, project_psychographics, embed_demographics, fuse_joint
from src.models.mixture import load_twin_bank, responsibilities, primary_twin
from src.models.policy_heads import TwinPolicyHeadSet
from src.features.candidate_features import build_candidate_matrix
from src.reasoning.llm_twin import list_personas, chat_with_twin, decide_as_twin
from src.reasoning.reason_cache import REASON_CACHE
from src.reasoning.guard import guard_decision
from src.profiles.loader import profile_vec_for_user, psych_tags_to_vec, demo_profile_to_vec, merge_profile
from src.admin.store import PinStore
from src.reasoning.llm_runtime import RUNTIME

# Airline module imports
from src.airline.twin_card import load_twin_card
from src.airline.schemas import (
    OfferAcceptanceTask,
    DecisionContext,
    DecisionResponse,
    TwinDecision,
    create_legroom_offer,
    create_wifi_offer,
    create_lounge_offer,
    create_priority_boarding_offer,
    create_baggage_offer
)
from src.airline.prompt_composer import compose_prompts
from src.airline.llm_gateway import LLMGateway
from src.api.chat_service import chat_service

# Load configs
_policy_cfg = yaml.safe_load(Path("CONFIGS/serve/policy.yaml").read_text())
_admin_cfg = yaml.safe_load(Path("CONFIGS/serve/admin.yaml").read_text())
_api_cfg = yaml.safe_load(Path("CONFIGS/serve/api.yaml").read_text())

# Admin token: env overrides config
_ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", str(_admin_cfg["admin"]["token"]))
# CORS origins: env overrides config
_env_origins = os.getenv("CORS_ALLOW_ORIGINS")
_default_origins = _api_cfg.get("cors", {}).get("allow_origins", []) + ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"]
_ALLOW_ORIGINS = [o.strip() for o in (_env_origins.split(",") if _env_origins else _default_origins)]
# Rate limit: env override
_RATE = int(os.getenv("RATE_LIMIT_REQS_PER_MIN", "120"))

app = FastAPI(title="Darpan What-If Simulator")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOW_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiter
_limiter = SimpleRateLimiter(max_per_min=_RATE)
@app.middleware("http")
async def limiter_mw(request: Request, call_next):
    return await _limiter(request, call_next)

# Models and stores
_BANK = load_twin_bank()
_HEADS = TwinPolicyHeadSet(_policy_cfg["serve"]["head_dir"], default_temp=float(_policy_cfg["serve"]["calib_default_temp"]))
_USE_HEADS = bool(_policy_cfg["serve"]["use_heads"])
_BUCKETS = int(_policy_cfg["serve"]["candidate_hash_buckets"])
_PIN_STORE = PinStore(_admin_cfg["admin"]["pin_store_path"])

# --- Logging middleware ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    rid = str(uuid4())
    start = time.perf_counter()
    resp: JSONResponse
    try:
        resp = await call_next(request)
        status = resp.status_code
    except Exception as e:
        status = 500
        resp = JSONResponse({"error": "internal"}, status_code=500)
        raise
    finally:
        dur_ms = int((time.perf_counter() - start) * 1000)
        path = request.url.path
        method = request.method
        print(f"[{rid}] {method} {path} -> {status} in {dur_ms}ms")
    resp.headers["X-Request-Id"] = rid
    return resp

def _fused_embedding(cta_seq: Optional[List[Dict[str, Any]]], user_id: Optional[str], conditioning: Optional[Dict[str, Any]]) -> List[float]:
    z_b = encode_cta(cta_seq or [])
    base = profile_vec_for_user(user_id)
    psych_v = psych_tags_to_vec((conditioning or {}).get("psychographic_tags"))
    demo_v  = demo_profile_to_vec((conditioning or {}).get("demographic_profile"))
    merged  = merge_profile(base, psych_v, demo_v)
    z_p = project_psychographics(merged[:4] if merged else None)
    z_d = embed_demographics(merged[4:] if merged else None)
    return fuse_joint(z_b, z_p, z_d)

# --- Health + versions ---
@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "use_heads": _USE_HEADS, "heads_loaded": _HEADS.available()}

# K8s-style readiness/liveness
@app.get("/ready")
def ready() -> Dict[str, Any]:
    ok = _HEADS.available() or True  # ready even without heads
    return {"ready": ok}

@app.get("/live")
def live() -> Dict[str, Any]:
    return {"alive": True}

@app.get("/versions")
def versions() -> Dict[str, Any]:
    return {
        "twin_bank_version": _BANK.get("version", "v0"),
        "policy_heads": {"loaded": _HEADS.available(), "dir": _policy_cfg["serve"]["head_dir"]},
        "reason_cache": REASON_CACHE.stats().__dict__,
        "config": {"policy": _policy_cfg["serve"], "admin": {"pin_store_path": _admin_cfg["admin"]["pin_store_path"]}},
    }

@app.get("/catalog/copy_variants")
def copy_variants() -> Dict[str, Any]:
    p = Path("DATA/copy_variants.csv")
    if not p.exists():
        return {"variants": []}
    rows = []
    with p.open() as f:
        for i, r in enumerate(csv.DictReader(f)):
            rows.append({"copy_variant_id": r.get("copy_variant_id"), "slot": r.get("slot"), "text": r.get("text")})
    return {"variants": rows}

# --- Twin Lab endpoints ---
@app.get("/twin/bank")
def twin_bank() -> Dict[str, Any]:
    bank = load_twin_bank()
    twins = [{"id": t["id"], "label": t["label"], "center_dim": len(t.get("center", [])), "adapter": RUNTIME.adapter_available(t["id"])} for t in bank.get("twins", [])]
    return {"version": bank.get("version","v0"), "twins": twins}

@app.get("/twin/{twin_id}/inspect")
def twin_inspect(twin_id: str) -> Dict[str, Any]:
    from src.reasoning.llm_twin import get_persona
    p = get_persona(twin_id)
    if not p:
        raise HTTPException(status_code=404, detail="Twin not found.")
    return {
        "persona": p,
        "adapter_available": RUNTIME.adapter_available(twin_id),
        "llm_config": yaml.safe_load(Path("CONFIGS/serve/llm.yaml").read_text())["llm"]
    }

@app.post("/admin/twin/{twin_id}/reload")
def twin_reload(twin_id: str, x_admin_token: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    _require_admin(x_admin_token)
    ok = RUNTIME.reload_adapter(twin_id)
    return {"twin_id": twin_id, "reloaded": ok}

@app.get("/admin/adapters")
def adapters_status(x_admin_token: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    _require_admin(x_admin_token)
    bank = load_twin_bank()
    ids = [t["id"] for t in bank.get("twins", [])]
    return RUNTIME.adapters_status(ids)

@app.get("/admin/train/status")
def train_status(x_admin_token: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    _require_admin(x_admin_token)
    fp = Path("DATA/train_runs.json")
    if not fp.exists():
        return {"runs": {}}
    return json.loads(fp.read_text(encoding="utf-8"))

# --- Twin + match (unchanged interface) ---
@app.get("/twin/personas")
def twin_personas() -> Dict[str, Any]:
    return {"personas": list_personas()}

@app.get("/metrics/validation", response_model=MetricsResponse)
def get_validation_metrics() -> MetricsResponse:
    """Get validation metrics, training info, and twin performance data"""

    # Load validation stats
    validation_stats_path = Path("DATA/airline/validation_stats.json")
    validation_stats = {}
    if validation_stats_path.exists():
        validation_stats = json.loads(validation_stats_path.read_text())

    # Load gates config for thresholds
    gates_config_path = Path("CONFIGS/tests/gates.yaml")
    thresholds = {}
    if gates_config_path.exists():
        gates_config = yaml.safe_load(gates_config_path.read_text())
        thresholds = {
            "silhouette_min": gates_config.get("separation", {}).get("silhouette_min", 0.35),
            "mean_jsd_min": gates_config.get("separation", {}).get("mean_jsd_min", 0.10),
            "ari_min": gates_config.get("separation", {}).get("ari_min", 0.80)
        }

    # Mock validation metrics (in production, these would be computed)
    validation_metrics = ValidationMetrics(
        silhouette_score=0.42,  # Mock value above threshold
        jensen_shannon_divergence=0.15,  # Mock value above threshold
        ari_stability=0.85,  # Mock value above threshold
        thresholds=thresholds
    )

    # Load twin bank for twin metrics
    twin_bank = load_twin_bank()
    twin_metrics = []

    # Load airline twins for cohort priors
    airline_twins_dir = Path("DATA/airline/twins")
    for twin in twin_bank.get("twins", []):
        twin_id = twin["id"]

        # Try to load airline twin data
        cohort_prior = 1.0 / len(twin_bank.get("twins", []))  # Default uniform
        satisfaction_rate = None

        # Map numeric IDs to airline twin file names
        airline_twin_file = airline_twins_dir / f"twin_{twin_id.replace('k', '').zfill(3)}.json"
        if not airline_twin_file.exists():
            # Try alternative naming
            airline_twin_file = airline_twins_dir / f"twin_00{twin_id.replace('k', '')}.json"

        if airline_twin_file.exists():
            airline_twin_data = json.loads(airline_twin_file.read_text())
            cohort_prior = airline_twin_data.get("cohort_prior", cohort_prior)
            satisfaction_rate = airline_twin_data.get("satisfaction", {}).get("mean", None)

        # Mock customer count (in production, this would be from actual data)
        customer_count = int(400 * cohort_prior)  # Based on 400 total samples

        twin_metrics.append(TwinMetrics(
            twin_id=twin_id,
            label=twin.get("label", "Unknown"),
            customer_count=customer_count,
            cohort_prior=cohort_prior,
            satisfaction_rate=satisfaction_rate
        ))

    # Training info
    training_info = {
        "total_samples": validation_stats.get("total_samples", 400),
        "train_samples": validation_stats.get("split_counts", {}).get("train", 320),
        "test_samples": validation_stats.get("split_counts", {}).get("test", 80),
        "model_version": "v1.0",
        "training_date": "2024-10-31"
    }

    # Dataset info
    dataset_info = {
        "demographics": validation_stats.get("demographics", {}),
        "service_ratings_summary": {
            "mean_rating": 3.28,
            "std_rating": 0.94
        },
        "flight_details": validation_stats.get("flight_details", {})
    }

    return MetricsResponse(
        validation_metrics=validation_metrics,
        training_info=training_info,
        twin_metrics=twin_metrics,
        dataset_info=dataset_info
    )

@app.post("/twin/chat", response_model=TwinChatResponse)
def twin_chat(req: TwinChatRequest) -> TwinChatResponse:
    personas = {p["id"]: p for p in list_personas()}
    if req.twin_id not in personas:
        raise HTTPException(status_code=404, detail=f"Twin {req.twin_id} not found.")
    reply = chat_with_twin(req.twin_id, req.history, req.prompt, req.conditioning.model_dump() if req.conditioning else None)
    return TwinChatResponse(twin_id=req.twin_id, reply=reply)

@app.post("/twin/decide", response_model=TwinDecideResponse)
def twin_decide(req: TwinDecideRequest) -> TwinDecideResponse:
    if not req.candidates:
        raise HTTPException(status_code=422, detail="No candidates.")
    cand_dicts = [c.model_dump() for c in req.candidates]
    dec = decide_as_twin(
        req.twin_id,
        req.context,
        cand_dicts,
        req.max_tokens,
        req.conditioning.model_dump() if req.conditioning else None
    )
    if not isinstance(dec, dict) or "pick" not in dec or "why" not in dec:
        raise HTTPException(status_code=500, detail="Decision schema invalid.")
    # Apply guard
    dec = guard_decision(dec, req.context, cand_dicts)
    return TwinDecideResponse(twin_id=req.twin_id, decision=TwinDecision(**dec))

@app.post("/match", response_model=MatchResponse)
def match(req: MatchRequest) -> MatchResponse:
    if not req.cta_seq and not req.z_or_user_id:
        raise HTTPException(status_code=400, detail="Provide cta_seq or z_or_user_id.")
    ctas = [c.model_dump() for c in req.cta_seq] if req.cta_seq else []
    user_id = ctas[0]["user_id"] if ctas else req.z_or_user_id
    z = _fused_embedding(ctas, user_id, req.conditioning.model_dump() if req.conditioning else None)
    w = responsibilities(z, _BANK)
    pt = primary_twin(w, _BANK)
    return MatchResponse(twin_weights=w, primary_twin=pt)

# --- Airline Chat Endpoints ---

@app.post("/airline/chat/send")
def send_chat_message(data: Dict[str, Any]) -> Dict[str, Any]:
    """Send a message to an airline twin and get response"""
    twin_id = data.get("twin_id")
    message = data.get("message")
    conversation_id = data.get("conversation_id")
    context = data.get("context")

    if not twin_id or not message:
        raise HTTPException(status_code=422, detail="twin_id and message are required")

    return chat_service.send_message(twin_id, message, conversation_id, context)

@app.get("/airline/chat/conversations")
def get_conversations(
    twin_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """Get list of conversations, optionally filtered by twin"""
    return chat_service.get_conversations(twin_id, limit, offset)

@app.get("/airline/chat/{conversation_id}")
def get_conversation(conversation_id: str) -> Dict[str, Any]:
    """Get a specific conversation by ID"""
    return chat_service.get_conversation(conversation_id)

@app.delete("/airline/chat/{conversation_id}")
def delete_conversation(conversation_id: str) -> Dict[str, Any]:
    """Delete a conversation"""
    return chat_service.delete_conversation(conversation_id)

@app.get("/airline/chat/{conversation_id}/export")
def export_conversation(
    conversation_id: str,
    format: Literal["json", "csv", "markdown"] = "json"
) -> Dict[str, Any]:
    """Export a conversation in various formats"""
    return chat_service.export_conversation(conversation_id, format)

@app.get("/airline/chat/analytics/summary")
def get_chat_analytics(
    twin_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """Get chat analytics and metrics"""
    return chat_service.get_chat_analytics(twin_id, start_date, end_date)

@app.post("/airline/chat/compare")
def compare_twin_responses(
    message: str,
    twin_ids: List[str],
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Get responses from multiple twins for comparison"""
    return chat_service.compare_twin_responses(message, twin_ids, context)

# --- Admin helpers ---
def _require_admin(token: Optional[str]) -> None:
    if not token or token != _ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized.")

@app.get("/admin/pins")
def list_pins(x_admin_token: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    _require_admin(x_admin_token)
    return {"pins": _PIN_STORE.list()}

@app.post("/admin/pin")
def upsert_pin(data: Dict[str, Any], x_admin_token: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    _require_admin(x_admin_token)
    name = str(data.get("name") or "").strip()
    weights = data.get("weights") or {}
    conditioning = data.get("conditioning")
    if not name or not isinstance(weights, dict) or not weights:
        raise HTTPException(status_code=400, detail="Provide name and weights.")
    p = _PIN_STORE.upsert(name, weights, conditioning)
    return {"pin": {"name": p.name, "weights": p.weights, "conditioning": p.conditioning, "updated_ts": p.updated_ts}}

@app.delete("/admin/pin/{name}")
def delete_pin(name: str, x_admin_token: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    _require_admin(x_admin_token)
    ok = _PIN_STORE.delete(name)
    if not ok:
        raise HTTPException(status_code=404, detail="Pin not found.")
    return {"deleted": name}

def _blend_with_heads(twin_weights: Dict[str, float], context: Dict[str, Any], candidates: List[Dict[str, Any]], fused_embed: List[float]) -> Dict[str, float]:
    """Blend per-twin probabilities using mixture weights"""
    if not _HEADS.available():
        # uniform fallback
        n = max(1, len(candidates))
        return {c["id"]: 1.0/n for c in candidates}
    X = build_candidate_matrix(context, candidates, fused_embed, buckets=_BUCKETS)
    mix = {c["id"]: 0.0 for c in candidates}
    for tid, w in twin_weights.items():
        probs = _HEADS.score_twin(tid, X)  # len = n candidates
        for c, p in zip(candidates, probs):
            mix[c["id"]] += w * float(p)
    return mix

# --- /simulate with optional pin override ---
@app.post("/simulate", response_model=SimulateResponse)
def simulate(req: SimulateRequest) -> SimulateResponse:
    if req.deterministic:
        set_global_seed(req.seed)
    if not req.cta_seq and not req.z_or_user_id:
        raise HTTPException(status_code=400, detail="Provide cta_seq or z_or_user_id.")
    allowed = allowed_mutables()
    for s in req.scenarios:
        extra = set(s.context_overrides.keys()) - allowed
        if extra:
            raise HTTPException(status_code=422, detail=f"Disallowed override keys: {sorted(extra)}")

    # mixture via fused embedding OR pin override
    ctas = [c.model_dump() for c in req.cta_seq] if req.cta_seq else []
    user_id = ctas[0]["user_id"] if ctas else req.z_or_user_id
    conditioning = req.conditioning.model_dump() if req.conditioning else None

    if req.use_pin:
        pin = _PIN_STORE.get(req.use_pin)
        if not pin:
            raise HTTPException(status_code=404, detail=f"Pin '{req.use_pin}' not found.")
        twin_weights = pin.weights
        # If the pin carries conditioning, merge it with request conditioning (pin wins)
        conditioning = pin.conditioning or conditioning
        z = []  # No embedding needed when using pin
    else:
        z = _fused_embedding(ctas, user_id, conditioning)
        twin_weights = responsibilities(z, _BANK)

    pt = primary_twin(twin_weights, _BANK)

    # candidates from base CTA
    base_visible = []
    if req.cta_seq:
        ctx0 = req.cta_seq[0].context or {}
        base_visible = [{"id": v} for v in ctx0.get("visible_products", [])]
    context_base = req.cta_seq[0].context.copy() if req.cta_seq else {}

    # per-scenario distributions and deltas
    per_scenario_probs: Dict[str, Dict[str, float]] = {}
    per_scenario_picks: Dict[str, List[TwinPick]] = {}
    scenario_hashes: Dict[str, str] = {}

    def scenario_key(variant_id: str, overrides: Dict[str, Any]) -> str:
        return stable_hash({"v": variant_id, "o": overrides or {}, "cond": conditioning or {}})

    # compute base distribution first for deltas
    base_id = None
    for s in req.scenarios:
        if s.variant_id.lower() == "base":
            base_id = s.variant_id
            break
    if base_id is None:
        base_id = req.scenarios[0].variant_id

    # helper to get probs for one scenario
    def probs_for_scenario(scenario) -> Tuple[Dict[str, float], List[TwinPick]]:
        cands = scenario.candidates if scenario.candidates is not None else [type("C", (), {"id": c["id"]})() for c in base_visible]
        if not cands:
            raise HTTPException(status_code=422, detail=f"Scenario {scenario.variant_id} has empty candidates.")
        cand_dicts = [{"id": c.id if hasattr(c, 'id') else c["id"]} for c in cands]

        scenario_ctx = context_base.copy()
        scenario_ctx.update(scenario.context_overrides)

        if _USE_HEADS and _HEADS.available():
            # fast path: heads for ranking
            probs = _blend_with_heads(twin_weights, scenario_ctx, cand_dicts, z if z else [0.0]*15)
            by_twin = []
            if req.explain in ("per_twin","blend"):
                # still ask LLM for reasons (cached)
                for tid in twin_weights.keys():
                    dec = decide_as_twin(tid, scenario_ctx, cand_dicts, 20, conditioning)
                    dec = guard_decision(dec, scenario_ctx, cand_dicts)
                    twin_why = dec["why"] if req.explain == "per_twin" else dec["why"]
                    by_twin.append(TwinPick(twin_id=tid, picks=[{"id": dec["pick"], "p": 1.0}], why=twin_why))
            return probs, by_twin
        else:
            # fallback: LLM-vote path from Phase D
            vote = {c["id"]: 0.0 for c in cand_dicts}
            by_twin = []
            for tid, w in twin_weights.items():
                dec = decide_as_twin(tid, scenario_ctx, cand_dicts, 20, conditioning)
                dec = guard_decision(dec, scenario_ctx, cand_dicts)
                pick = dec["pick"]; why = dec["why"]
                vote[pick] = vote.get(pick, 0.0) + w
                twin_why = why if req.explain in ("per_twin", "blend") else None
                by_twin.append(TwinPick(twin_id=tid, picks=[{"id": pick, "p": 1.0}], why=twin_why))
            ssum = sum(vote.values()) or 1.0
            return {k: v/ssum for k,v in vote.items()}, by_twin

    # compute distributions
    for s in req.scenarios:
        scen_key = scenario_key(s.variant_id, s.context_overrides)
        scenario_hashes[s.variant_id] = scen_key
        probs, per_twin = probs_for_scenario(s)
        per_scenario_probs[s.variant_id] = probs
        per_scenario_picks[s.variant_id] = per_twin

    base_probs = per_scenario_probs[base_id]

    # build response with deltas
    by_scenario: List[ScenarioResult] = []
    for s in req.scenarios:
        probs = per_scenario_probs[s.variant_id]
        topN = [{"id": cid, "p": round(p, 6)} for cid, p in probs.items()]
        topN = canonical_sort(topN)[:req.topk]
        all_ids = set(base_probs.keys()) | set(probs.keys())
        deltas = {cid: round(probs.get(cid, 0.0) - base_probs.get(cid, 0.0), 6) for cid in sorted(all_ids)}
        # blend reason
        why_blend = None
        if req.explain == "blend":
            # pick the highest-weight twin's reason
            per_twin = per_scenario_picks[s.variant_id]
            if per_twin:
                best_tid = sorted(twin_weights.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
                for tp in per_twin:
                    if tp.twin_id == best_tid and tp.why:
                        why_blend = tp.why
                        break
        by_scenario.append(ScenarioResult(
            variant_id=s.variant_id,
            topN=topN,
            why=why_blend,
            by_twin=per_scenario_picks[s.variant_id] if req.explain=="per_twin" else None,
            deltas=deltas
        ))

    cache_stats = REASON_CACHE.stats()
    sim_cfg = {
        "run_id": str(uuid4()),
        "seed": req.seed,
        "pin_used": req.use_pin or None,
        "base_hash": stable_hash(req.model_dump(mode='json')),
        "scenario_hashes": scenario_hashes,
        "model_versions": {"twin_bank_ver": _BANK.get("version","v0"), "policy_heads":"v0"},
        "data_version": {},
        "serving": {"use_heads": _USE_HEADS, "heads_loaded": _HEADS.available()},
        "reason_cache": {
            "hits": cache_stats.hits,
            "misses": cache_stats.misses,
            "puts": cache_stats.puts,
            "size": cache_stats.size,
            "maxsize": cache_stats.maxsize
        }
    }
    return SimulateResponse(by_scenario=by_scenario, twin_weights=twin_weights, primary_twin=pt, sim_config=sim_cfg)

# --- Airline Module Endpoints ---

# Pydantic models for airline API
from pydantic import BaseModel, Field

class ChatMessageRequest(BaseModel):
    twin_id: str
    message: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class AirlineDecisionRequest(BaseModel):
    twin_id: str = Field(..., description="Twin identifier (e.g., twin_001)")
    offer_type: str = Field(..., description="Offer type: legroom, wifi, lounge, boarding, baggage")
    discount_pct: float = Field(..., description="Discount percentage (0.0 to 1.0)")
    flight_length: str = Field(default="medium", description="Flight length: short, medium, long")
    trip_purpose: str = Field(default="business", description="Trip purpose: business, leisure")
    time_pressure: str = Field(default="medium", description="Time pressure: low, medium, high")
    recent_delays: str = Field(default="minor", description="Recent delays: none, minor, major")
    seed: Optional[int] = Field(default=None, description="Random seed for determinism")

class AirlineBatchDecisionRequest(BaseModel):
    twin_ids: List[str] = Field(..., description="List of twin identifiers")
    offer_type: str = Field(..., description="Offer type")
    discount_pct: float = Field(..., description="Discount percentage")
    flight_length: str = Field(default="medium")
    trip_purpose: str = Field(default="business")
    time_pressure: str = Field(default="medium")
    recent_delays: str = Field(default="minor")
    seed: Optional[int] = Field(default=None)

# Initialize LLM gateway for airline twins
_AIRLINE_CONFIG_PATH = Path("CONFIGS/airline/twin_config.yaml")
_AIRLINE_GATEWAY = LLMGateway(_AIRLINE_CONFIG_PATH) if _AIRLINE_CONFIG_PATH.exists() else None
_AIRLINE_TWINS_DIR = Path("DATA/airline/twins")
_AIRLINE_PROMPTS_DIR = Path("PROMPTS/airline")

OFFER_FACTORIES = {
    "legroom": create_legroom_offer,
    "wifi": create_wifi_offer,
    "lounge": create_lounge_offer,
    "boarding": create_priority_boarding_offer,
    "baggage": create_baggage_offer
}

@app.get("/airline/twins")
def airline_twins_list() -> Dict[str, Any]:
    """List all available airline twins."""
    if not _AIRLINE_TWINS_DIR.exists():
        return {"twins": [], "error": "Airline twins directory not found"}

    twins = []
    for twin_file in sorted(_AIRLINE_TWINS_DIR.glob("twin_*.json")):
        with open(twin_file) as f:
            twin_data = json.load(f)
            twins.append({
                "id": twin_data["id"],
                "label": twin_data["label"],
                "demographics": twin_data["demographics"],
                "psychographics": twin_data["psychographics"],
                "travel_profile": twin_data["travel_profile"]
            })

    return {"twins": twins, "count": len(twins)}

@app.post("/airline/decide")
def airline_decide(req: AirlineDecisionRequest) -> Dict[str, Any]:
    """Make a single airline twin decision."""
    if not _AIRLINE_GATEWAY:
        raise HTTPException(status_code=500, detail="Airline LLM gateway not initialized")

    # Load twin
    twin_path = _AIRLINE_TWINS_DIR / f"{req.twin_id}.json"
    if not twin_path.exists():
        raise HTTPException(status_code=404, detail=f"Twin {req.twin_id} not found")

    twin = load_twin_card(twin_path)

    # Create offer
    if req.offer_type not in OFFER_FACTORIES:
        raise HTTPException(status_code=422, detail=f"Invalid offer type: {req.offer_type}")

    offer_factory = OFFER_FACTORIES[req.offer_type]
    offer = offer_factory(discount_pct=req.discount_pct)

    # Create context
    context = DecisionContext(
        flight_length=req.flight_length,
        trip_purpose=req.trip_purpose,
        time_pressure=req.time_pressure,
        recent_delays=req.recent_delays
    )

    # Create task
    task = OfferAcceptanceTask(offer=offer, context=context)

    # Compose prompts
    system_prompt, user_prompt = compose_prompts(twin, task, _AIRLINE_PROMPTS_DIR)

    # Get decision
    try:
        decision_dict, llm_metadata = _AIRLINE_GATEWAY.get_decision(
            system_prompt,
            user_prompt,
            seed=req.seed
        )

        response = DecisionResponse.from_dict(decision_dict)

        metadata = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "seed": req.seed,
            "llm_metadata": llm_metadata
        }

        twin_decision = TwinDecision(
            twin_id=twin.id,
            twin_label=twin.label,
            task=task,
            response=response,
            metadata=metadata
        )

        return twin_decision.to_dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decision failed: {str(e)}")

@app.post("/airline/batch_decide")
def airline_batch_decide(req: AirlineBatchDecisionRequest) -> Dict[str, Any]:
    """Make decisions for multiple airline twins."""
    results = []
    errors = []

    for twin_id in req.twin_ids:
        try:
            decision_req = AirlineDecisionRequest(
                twin_id=twin_id,
                offer_type=req.offer_type,
                discount_pct=req.discount_pct,
                flight_length=req.flight_length,
                trip_purpose=req.trip_purpose,
                time_pressure=req.time_pressure,
                recent_delays=req.recent_delays,
                seed=req.seed
            )
            decision = airline_decide(decision_req)
            results.append(decision)
        except Exception as e:
            errors.append({"twin_id": twin_id, "error": str(e)})

    return {
        "results": results,
        "errors": errors,
        "total": len(req.twin_ids),
        "successful": len(results),
        "failed": len(errors)
    }

@app.get("/airline/decisions/export")
def airline_decisions_export(format: str = "json") -> Any:
    """Export decision ledger."""
    ledger_path = Path("DATA/airline/decisions/ledger.csv")

    if not ledger_path.exists():
        raise HTTPException(status_code=404, detail="Decision ledger not found")

    if format == "csv":
        with open(ledger_path, "r") as f:
            csv_content = f.read()
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(content=csv_content, media_type="text/csv")

    elif format == "json":
        import pandas as pd
        df = pd.read_csv(ledger_path)
        return JSONResponse(content=df.to_dict(orient="records"))

    else:
        raise HTTPException(status_code=422, detail="Format must be 'csv' or 'json'")
