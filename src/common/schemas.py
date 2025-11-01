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

class ValidationMetrics(BaseModel):
    """Metrics from model validation and training"""
    silhouette_score: float
    jensen_shannon_divergence: float
    ari_stability: float
    thresholds: Dict[str, float]

class TwinMetrics(BaseModel):
    """Metrics for individual twin"""
    twin_id: str
    label: str
    customer_count: int
    cohort_prior: float
    satisfaction_rate: Optional[float] = None

class MetricsResponse(BaseModel):
    """Response for metrics endpoint"""
    validation_metrics: ValidationMetrics
    training_info: Dict[str, Any]
    twin_metrics: List[TwinMetrics]
    dataset_info: Dict[str, Any]


# ============================================================================
# USER ASSIGNMENT & EXPLAINABILITY SCHEMAS
# ============================================================================

class FeatureImportance(BaseModel):
    """Feature importance for persona assignment"""
    feature: str
    importance: float
    user_value: float
    twin_value: float
    difference: float


class TwinDistance(BaseModel):
    """Distance from user to a twin center"""
    twin_id: str
    label: str
    distance: float
    similarity: float


class PrimaryTwinInfo(BaseModel):
    """Detailed info about assigned twin"""
    twin_id: str
    label: str
    distance: float
    similarity: float


class UserAssignmentResponse(BaseModel):
    """Complete explanation for user's persona assignment"""
    user_id: str
    primary_twin: PrimaryTwinInfo
    feature_importance: List[FeatureImportance]
    natural_language: str
    all_distances: List[TwinDistance]
    alternatives: List[TwinDistance]
    confidence: float
    metadata: Dict[str, Any]


# ============================================================================
# CLUSTER VISUALIZATION SCHEMAS
# ============================================================================

class ClusterPoint(BaseModel):
    """2D point in cluster visualization"""
    user_id: str
    x: float
    y: float
    twin_id: str
    label: str


class ClusterCenter(BaseModel):
    """Cluster center in 2D projection"""
    twin_id: str
    label: str
    x: float
    y: float
    size: int  # Number of users in cluster


class ClusterMapResponse(BaseModel):
    """Cluster map visualization data"""
    points: List[ClusterPoint]
    centers: List[ClusterCenter]
    projection_method: str
    metadata: Dict[str, Any]


# ============================================================================
# HIERARCHICAL CLUSTERING SCHEMAS
# ============================================================================

class DendrogramData(BaseModel):
    """Dendrogram visualization data"""
    icoord: List[List[float]]
    dcoord: List[List[float]]
    ivl: List[str]
    leaves: List[int]
    color_list: List[str]


class DecisionTreeNode(BaseModel):
    """Decision tree node for persona splits"""
    type: Literal["decision", "leaf"]
    feature: Optional[str] = None
    threshold: Optional[float] = None
    samples: int
    left: Optional['DecisionTreeNode'] = None
    right: Optional['DecisionTreeNode'] = None
    class_label: Optional[str] = None
    value: Optional[List[float]] = None

    model_config = ConfigDict(extra="allow")


class TwinPair(BaseModel):
    """Twin pair with distance"""
    twin1: str
    twin2: str
    distance: float


class ClusterSummary(BaseModel):
    """Summary statistics for a cluster"""
    twin_id: str
    label: str
    n_users: int
    percentage: float
    cohesion: float
    top_features: List[Dict[str, Any]]
    center: List[float]


class HierarchyResponse(BaseModel):
    """Hierarchical clustering analysis"""
    hierarchical_clustering: Dict[str, Any]
    decision_tree: Dict[str, Any]
    persona_analysis: Dict[str, Any]
    cluster_summaries: List[ClusterSummary]
    metadata: Dict[str, Any]
