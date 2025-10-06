from __future__ import annotations
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

Task = Literal["choose_product","refine","stop","nav_action"]
ExplainMode = Literal["none","blend","per_twin"]

class Candidate(BaseModel):
    id: str

class CTAStep(BaseModel):
    user_id: str
    session_id: str
    ts: datetime
    context: Dict[str, Any]
    task: Task
    action_id: str
    model_config = ConfigDict(extra="ignore")

class ScenarioPatch(BaseModel):
    variant_id: str
    context_overrides: Dict[str, Any] = Field(default_factory=dict)
    candidates: Optional[List[Candidate]] = None
    model_config = ConfigDict(extra="forbid")

class Mixture(BaseModel):
    auto_from_cta: Optional[bool] = None
    weights: Optional[Dict[str, float]] = None
    model_config = ConfigDict(extra="forbid")

class Conditioning(BaseModel):
    behavior_archetype: Optional[str] = None       # e.g., "deal_seeking"
    psychographic_tags: Optional[List[str]] = None # e.g., ["thrift","speed_low"]
    demographic_profile: Optional[Dict[str, Any]] = None # e.g., {"age_band":"25_34","locale":"urban","sex":"F"}

class MatchRequest(BaseModel):
    cta_seq: Optional[List[CTAStep]] = None
    z_or_user_id: Optional[str] = None
    conditioning: Optional[Conditioning] = None
    model_config = ConfigDict(extra="forbid")

class MatchResponse(BaseModel):
    twin_weights: Dict[str, float]
    primary_twin: Optional[Dict[str, str]] = None

class TwinChatRequest(BaseModel):
    twin_id: str
    history: List[Dict[str, str]] = Field(default_factory=list)  # [{"role":"user|assistant","content":"..."}]
    prompt: str
    conditioning: Optional[Conditioning] = None

class TwinChatResponse(BaseModel):
    twin_id: str
    reply: str

class TwinDecideRequest(BaseModel):
    twin_id: str
    context: Dict[str, Any]
    candidates: List[Candidate]
    max_tokens: int = 20
    conditioning: Optional[Conditioning] = None

class TwinDecision(BaseModel):
    pick: str
    why: str

class TwinDecideResponse(BaseModel):
    twin_id: str
    decision: TwinDecision

class SimulateRequest(BaseModel):
    cta_seq: Optional[List[CTAStep]] = None
    z_or_user_id: Optional[str] = None
    task: Literal["choose_product","refine"]
    scenarios: List[ScenarioPatch]
    topk: int = 5
    explain: ExplainMode = "none"
    deterministic: bool = True
    seed: int = 17
    mixture: Optional[Mixture] = None
    conditioning: Optional[Conditioning] = None
    use_pin: Optional[str] = None  # NEW: named mixture override
    model_config = ConfigDict(extra="forbid")

class TwinPick(BaseModel):
    twin_id: str
    picks: List[Dict[str, Any]]
    why: Optional[str] = None

class ScenarioResult(BaseModel):
    variant_id: str
    topN: List[Dict[str, Any]]
    why: Optional[str] = None
    by_twin: Optional[List[TwinPick]] = None
    deltas: Dict[str, float] = Field(default_factory=dict)

class SimulateResponse(BaseModel):
    by_scenario: List[ScenarioResult]
    twin_weights: Dict[str, float]
    primary_twin: Optional[Dict[str, str]] = None
    sim_config: Dict[str, Any]
