# Missing Python Modules Analysis - Darpan Labs MVP v1.0

## Executive Summary

The FastAPI server is failing to start due to **3 critical missing modules** in `src/models/`:
1. `src.models.encoder` - MISSING
2. `src.models.mixture` - MISSING  
3. `src.models.policy_heads` - MISSING

Additionally, there are **data file dependencies** that must exist for the system to run:
- `DATA/personas.json` - MISSING
- `DATA/airline/twins/` - EXISTS (populated with 10+ twin cards)

## Module-by-Module Status

### CRITICAL MISSING MODULES

#### 1. `src.models.encoder` - ENCODER FUNCTIONS
**Status**: MISSING - Must be created

**Required Functions**:
```python
def encode_cta(cta_seq: List[Dict]) -> List[float]
    Returns: 8-D normalized vector from CTA sequence
    
def project_psychographics(vec: List[float]) -> List[float]
    Returns: 4-D projected psychographic embedding
    
def embed_demographics(vec: List[float]) -> List[float]
    Returns: 3-D demographic embedding
    
def fuse_joint(z_b: List[float], z_p: List[float], z_d: List[float]) -> List[float]
    Returns: 15-D fused embedding (8+4+3 dimensions)
```

**Usage**: 
- Called in `src/api/service.py` line 22
- Used in tests: `test_mixture.py`, `test_counterfactual_fairness.py`
- Must produce L2-normalized vectors
- Must be deterministic (no randomness)

**Expected Behavior**:
- `encode_cta()` produces 8-D behavior embedding from CTA action sequence
- `project_psychographics()` projects 4-D psychographic tag vectors
- `embed_demographics()` projects 3-D demographic profile vectors
- `fuse_joint()` combines three embeddings into 15-D vector via concatenation

---

#### 2. `src.models.mixture` - TWIN MIXTURE SYSTEM
**Status**: MISSING - Must be created

**Required Functions**:
```python
def load_twin_bank() -> Dict[str, Any]
    Returns: Twin bank dict with "version", "twins" list
    - Each twin has: "id", "label", "center" (embedding vector)
    
def responsibilities(z: List[float], bank: Dict) -> Dict[str, float]
    Returns: Twin weights dict {twin_id: weight, ...} that sum to 1.0
    - Uses cosine similarity + softmax
    
def primary_twin(weights: Dict[str, float], bank: Dict) -> Dict[str, str]
    Returns: {"id": highest_weight_twin_id, "label": twin_label}
```

**Usage**:
- Called in `src/api/service.py` lines 23, 81, 231, 306, 308
- Used in all tests that test twin selection
- The twin bank file must be in `DATA/twin_bank.json` (format: see spec)

**Expected Behavior**:
- `load_twin_bank()` reads from `DATA/twin_bank.json`
- `responsibilities()` computes mixture weights using:
  1. Cosine similarity between embedding z and each twin's center embedding
  2. Softmax normalization to get weights summing to 1.0
- Mock implementation: 3 twins (k0, k1, k2)
- Deterministic: no randomness in computations

**Twin Bank Format** (minimal example):
```json
{
  "version": "v1",
  "twins": [
    {"id": "k0", "label": "Budget-Conscious", "center": [...]},
    {"id": "k1", "label": "Premium", "center": [...]},
    {"id": "k2", "label": "Deal-Hunter", "center": [...]}
  ]
}
```

---

#### 3. `src.models.policy_heads` - POLICY HEAD LINEAR MODELS
**Status**: MISSING - Must be created

**Required Class**:
```python
class TwinPolicyHeadSet:
    def __init__(self, head_dir: str, default_temp: float)
        # Load distilled policy heads from head_dir
        
    def available() -> bool
        # Return True if heads successfully loaded
        
    def score_twin(twin_id: str, X: List[List[float]]) -> List[float]
        # Score candidates for a twin
        # X is candidate feature matrix (rows = candidates)
        # Returns probabilities for each candidate
```

**Usage**:
- Called in `src/api/service.py` lines 24, 82-84, 266-276
- Optional feature - if not available, fall back to LLM voting
- Used when `use_heads: true` in `CONFIGS/serve/policy.yaml`

**Expected Behavior**:
- Load pre-trained linear heads from `CONFIGS/serve/policy.yaml` head_dir
- Each head predicts ranking probabilities for candidates
- Blend per-twin predictions using mixture weights
- If heads missing or unavailable, gracefully degrade

**Feature Matrix Format**:
- Each row: `[ctx_feats(3) || fused_embed(15) || one_hot_hash(candidate_id)(buckets)]`
- Total: 3 + 15 + buckets dimensions

---

### OPTIONAL/WORKING MODULES

#### 4. `src.features.candidate_features` - EXISTS & WORKING
**Status**: COMPLETE ✓

**Functions**:
- `build_candidate_matrix()` - builds feature matrix for candidates
- `context_vector()` - extracts context features
- `one_hot()` - creates one-hot vectors
- `_hash_bucket()` - hashes candidate IDs to buckets

**File**: `/Users/aniketniranjanmishra/Desktop/Darpan Labs/mvp_v1.0/src/features/candidate_features.py`

---

#### 5. `src.reasoning.llm_twin` - EXISTS but needs DATA
**Status**: PARTIAL - has code but needs `/DATA/personas.json`

**Functions**:
- `list_personas()` - returns persona list
- `get_persona()` - retrieves persona by ID
- `chat_with_twin()` - conversational interface
- `decide_as_twin()` - makes decisions using mock logic

**Current Issue**: Reads from `DATA/personas.json` which doesn't exist yet

**File**: `/Users/aniketniranjanmishra/Desktop/Darpan Labs/mvp_v1.0/src/reasoning/llm_twin.py`

---

#### 6. `src.reasoning.reason_cache` - EXISTS & WORKING ✓
**Status**: COMPLETE ✓

**Class**: `ReasonCache` - LRU cache for LLM twin reasons

**File**: `/Users/aniketniranjanmishra/Desktop/Darpan Labs/mvp_v1.0/src/reasoning/reason_cache.py`

---

#### 7. `src.reasoning.guard` - EXISTS & WORKING ✓
**Status**: COMPLETE ✓

**Class**: `ReasonGuard` - enforces reason quality constraints

**Functions**:
- `guard_reason()` - audits single reason
- `guard_decision()` - audits full decision dict

**File**: `/Users/aniketniranjanmishra/Desktop/Darpan Labs/mvp_v1.0/src/reasoning/guard.py`

---

#### 8. `src.reasoning.llm_runtime` - EXISTS & WORKING ✓
**Status**: COMPLETE ✓

**Class**: `LLMRuntime` - manages adapter loading and LLM calls

**File**: `/Users/aniketniranjanmishra/Desktop/Darpan Labs/mvp_v1.0/src/reasoning/llm_runtime.py`

---

#### 9. `src.profiles.loader` - EXISTS & WORKING ✓
**Status**: COMPLETE ✓

**Functions**:
- `profile_vec_for_user()` - loads user profile vector
- `psych_tags_to_vec()` - converts psychographic tags to 4-D vector
- `demo_profile_to_vec()` - converts demographic profile to 3-D vector
- `merge_profile()` - merges base profile with conditioning overrides

**File**: `/Users/aniketniranjanmishra/Desktop/Darpan Labs/mvp_v1.0/src/profiles/loader.py`

---

#### 10. `src.admin.store` - EXISTS & WORKING ✓
**Status**: COMPLETE ✓

**Class**: `PinStore` - manages named mixture weight pins

**File**: `/Users/aniketniranjanmishra/Desktop/Darpan Labs/mvp_v1.0/src/admin/store.py`

---

#### 11. `src.airline.twin_card` - EXISTS & WORKING ✓
**Status**: COMPLETE ✓

**Classes**:
- `TwinCard` - airline twin persona
- `TwinCardDemographics`
- `TwinCardTravelProfile`
- `TwinCardServiceRatings`

**File**: `/Users/aniketniranjanmishra/Desktop/Darpan Labs/mvp_v1.0/src/airline/twin_card.py`

---

#### 12. `src.airline.schemas` - EXISTS & WORKING ✓
**Status**: COMPLETE ✓

**Classes**:
- `OfferDetails`
- `DecisionContext`
- `OfferAcceptanceTask`
- `DecisionResponse`
- `TwinDecision`

**File**: `/Users/aniketniranjanmishra/Desktop/Darpan Labs/mvp_v1.0/src/airline/schemas.py`

---

#### 13. `src.airline.prompt_composer` - EXISTS & WORKING ✓
**Status**: COMPLETE ✓

**File**: `/Users/aniketniranjanmishra/Desktop/Darpan Labs/mvp_v1.0/src/airline/prompt_composer.py`

---

#### 14. `src.airline.llm_gateway` - EXISTS & WORKING ✓
**Status**: COMPLETE ✓

**Class**: `LLMGateway` - OpenAI/Anthropic API integration

**File**: `/Users/aniketniranjanmishra/Desktop/Darpan Labs/mvp_v1.0/src/airline/llm_gateway.py`

---

## Data Files Status

### Missing Data Files

#### 1. `DATA/personas.json` - CRITICAL
**Status**: MISSING

**Format** (required by `src/reasoning/llm_twin.py`):
```json
{
  "personas": [
    {
      "id": "k0",
      "label": "Budget-Conscious User",
      "description": "...",
      "psychographics": ["thrift", "price_sensitive"],
      ...
    },
    {
      "id": "k1",
      "label": "Premium Quality Seeker",
      ...
    },
    {
      "id": "k2",
      "label": "Deal-Hunting Explorer",
      ...
    }
  ]
}
```

**Used By**: `src/reasoning/llm_twin.py` line 8

---

#### 2. `DATA/twin_bank.json` - CRITICAL
**Status**: MISSING

**Format** (required by `src/models/mixture.py`):
```json
{
  "version": "v1",
  "twins": [
    {
      "id": "k0",
      "label": "Budget-Conscious",
      "center": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
    },
    ...
  ]
}
```

**Used By**: `src/models/mixture.py` (to be created)

---

### Existing Data Files

#### 1. `DATA/airline/twins/` - EXISTS ✓
**Status**: COMPLETE with 10+ twin cards

**Files**:
- `twin_001.json` through `twin_010.json` (at least)
- Each contains: demographics, travel profile, psychographics, service ratings, cohort priors
- Populated by `scripts/generate_twin_cards.py`

**Location**: `/Users/aniketniranjanmishra/Desktop/Darpan Labs/mvp_v1.0/DATA/airline/twins/`

---

## Implementation Priority

### PHASE 1 - CRITICAL (Blocks API startup)
1. Create `src/models/encoder.py` with 4 functions
2. Create `src/models/mixture.py` with 3 functions
3. Create stub `src/models/policy_heads.py` (can be minimal/optional)
4. Generate `DATA/personas.json` (can use mock data)
5. Generate `DATA/twin_bank.json` (can use mock embeddings)

### PHASE 2 - OPTIONAL (Performance features)
1. Implement real policy heads in `src/models/policy_heads.py`
2. Train distilled heads: `scripts/distill_policies.py`
3. Load pre-trained heads from `CONFIGS/serve/policy.yaml` path

---

## Test Dependencies

Tests that require the missing modules:
- `TESTS/test_mixture.py` - needs encoder + mixture
- `TESTS/test_counterfactual_fairness.py` - needs encoder + mixture
- `TESTS/test_policy_heads.py` - needs policy_heads + heads on disk
- `TESTS/test_phase_d_simulator.py` - needs all three modules

---

## Configuration Files Involved

1. `CONFIGS/serve/policy.yaml` - specifies head_dir and use_heads flag
2. `CONFIGS/serve/llm.yaml` - LLM model config
3. `CONFIGS/serve/admin.yaml` - admin token and pin store path
4. `CONFIGS/serve/api.yaml` - CORS settings

---

## Next Steps for Implementation

1. **Create encoder.py** - Define behavioral, psychographic, demographic embeddings
2. **Create mixture.py** - Implement cosine similarity + softmax for twin weights  
3. **Create policy_heads.py** - Stub class for now, can add real heads later
4. **Generate mock personas.json** - Use 3 mock twins (k0, k1, k2)
5. **Generate mock twin_bank.json** - Create center embeddings for each twin
6. **Run tests** - `make test` should pass

---

## Summary Table

| Module | Status | File Path | Required |
|--------|--------|-----------|----------|
| encoder | MISSING | `src/models/encoder.py` | YES |
| mixture | MISSING | `src/models/mixture.py` | YES |
| policy_heads | MISSING | `src/models/policy_heads.py` | NO (optional) |
| candidate_features | EXISTS | `src/features/candidate_features.py` | YES |
| llm_twin | EXISTS* | `src/reasoning/llm_twin.py` | YES* |
| reason_cache | EXISTS | `src/reasoning/reason_cache.py` | YES |
| guard | EXISTS | `src/reasoning/guard.py` | YES |
| llm_runtime | EXISTS | `src/reasoning/llm_runtime.py` | YES |
| profiles.loader | EXISTS | `src/profiles/loader.py` | YES |
| admin.store | EXISTS | `src/admin/store.py` | YES |
| airline.twin_card | EXISTS | `src/airline/twin_card.py` | YES |
| airline.schemas | EXISTS | `src/airline/schemas.py` | YES |
| airline.prompt_composer | EXISTS | `src/airline/prompt_composer.py` | YES |
| airline.llm_gateway | EXISTS | `src/airline/llm_gateway.py` | YES |

*exists but needs DATA/personas.json

