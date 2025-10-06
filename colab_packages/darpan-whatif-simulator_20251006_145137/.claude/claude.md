# CLAUDE CODE INSTRUCTIONS FOR DARPAN LABS WHAT-IF SIMULATOR

## Purpose
Set up Claude Code to work in this repository with strict determinism and clear edit rules. The goal is to build and test an interactive what-if simulator driven by LLM "twins" that reflect behavior, psychographics, and demographics.

## Scope
1) Keep models and outputs deterministic
2) Use only page-visible candidates when deciding
3) Maintain twin separability and short grounded reasons
4) Support conditioning by behavior × psychographic × demographic

## Project Overview
This is a FastAPI-based digital twin simulator for e-commerce scenarios. It predicts how different user personas would respond to changes in price, promotions, delivery times, and ad copy.

## Key Architecture Principles

### 1. Deterministic Simulation
- Always use `set_global_seed(seed)` for reproducibility
- Use `canonical_sort()` for consistent ordering
- LLM twins use deterministic mock logic (k0: first, k1: middle, k2: last)

### 2. Twin Mixture System
- 15-D fused embeddings: behavior (8-D) + psychographic (4-D) + demographic (3-D)
- Cosine similarity + softmax for responsibilities
- Primary twin selected by max weight

### 3. Policy Heads (Fast Path)
- When `use_heads: true`, use linear heads for ranking
- Still call LLM twins for explanations when `explain != "none"`
- Heads blend per-twin probabilities using mixture weights

### 4. ReasonGuard
- All LLM twin reasons must pass guard before returning
- Max 20 tokens, no banned terms, no hallucinated numbers
- Context grounding required (mention candidates or context keywords)

### 5. Quality Gates
- Run `make gate` to check separation metrics
- Silhouette e 0.35, JSD e 0.10, ARI e 0.80
- Fail build if gates don't pass

## Testing Conventions

### Running Tests
```bash
make test          # Run all pytest tests
make gate          # Run separation gates
make guard         # Run guard-specific tests
make all           # Run everything (test + gate + guard)
```

### Test Data
- Mock twins: k0 (Budget), k1 (Premium), k2 (Deal-Hunter)
- Test users: u1 (thrifty), u2 (premium)
- Test products: A1, A2, A3

### Schema Requirements
When creating test payloads for `/simulate`:
- `cta_seq[].task` must be: "choose_product", "refine", "stop", or "nav_action"
- Top-level `task` must be: "choose_product" or "refine"
- Required CTA fields: user_id, session_id, ts, action, task, action_id

## Code Style

### Imports
```python
from __future__ import annotations
from typing import Dict, Any, List, Optional
```

### Error Handling
- Raise `HTTPException(status_code=422)` for validation errors
- Raise `HTTPException(status_code=404)` for missing resources
- Raise `HTTPException(status_code=500)` for server errors

### File Locations
- API endpoints: `src/api/service.py`
- Schemas: `src/common/schemas.py`
- Twins: `src/models/mixture.py`, `src/reasoning/llm_twin.py`
- Guards: `src/reasoning/guard.py`
- Tests: `TESTS/` (note: uppercase)
- Configs: `CONFIGS/`
- Data: `DATA/`

## Common Tasks

### Adding a New Endpoint
1. Add Pydantic schema to `src/common/schemas.py`
2. Implement endpoint in `src/api/service.py`
3. Add test in `TESTS/test_*.py`
4. Run `make test` to verify

### Modifying Twin Logic
1. Update decision logic in `src/reasoning/llm_twin.py`
2. If changing probabilities, retrain heads: `python scripts/distill_policies.py`
3. Update tests and run `make all`

### Changing Quality Gates
1. Edit thresholds in `CONFIGS/tests/gates.yaml`
2. Run `make gate` to verify
3. Update twin bank if separation drops below thresholds

## Files Claude Must Read First
1) README.md
2) SPECS/WHAT_IF_SIMULATOR_SPEC.md
3) API/SCHEMAS.md
4) CONFIGS/defaults.yaml
5) CONFIGS/serve/api.yaml and CONFIGS/serve/policy.yaml
6) CONFIGS/tests/gates.yaml
7) DATA/personas.json
8) API/examples/requests.json

## Repo Map
```
DOCS               plain-English and runbooks
SPECS              engineering spec
API                schemas and example payloads
CONFIGS            serve and training configs
PROMPTS            reason template
TESTS              acceptance and gates
DATA               copy variants and persona cards
src/api            FastAPI service
src/features       feature builders
src/models         encoder, mixture, policy heads, calibration
src/reasoning      LLM twin boundary, guard, cache
src/profiles       profile loader and mappers
scripts            distillation, eval, utilities
```

## Determinism Rules
1) Always set decoding to temperature 0 and top_p 1 in any LLM calls
2) Keep canonical sort by probability desc then id asc
3) Quantize only at feature boundaries that already exist
4) Use a single seed per request and thread it through
5) Do not introduce randomness in tests or scripts

## Core Contracts to Preserve

### Endpoints
1) GET /health
2) GET /twin/personas
3) POST /twin/chat
4) POST /twin/decide
5) POST /match
6) POST /simulate

### SimulateRequest Key Fields
- `cta_seq` or `z_or_user_id` (required)
- `task` ("choose_product" or "refine")
- `scenarios` (list of ScenarioPatch)
- `topk` (integer)
- `explain` ("none", "blend", or "per_twin")
- `deterministic` (boolean)
- `seed` (integer)
- `mixture` (optional)
- `conditioning` (optional)

### ScenarioPatch
- `variant_id` (string)
- `context_overrides` (limited to allowed_mutables)
- `candidates` (optional list of {id})

### Allowed Mutable Context Keys
- price_mean
- price_min
- price_max
- promo_badge
- delivery_eta_days
- copy_variant_id

## Twin and Conditioning Model
1) Twins are behavior-first archetypes with optional persona voice
2) Fused embedding z = fuse(behavior_embed, psychographic_embed, demographic_embed)
3) Conditioning object can override or set psychographic tags and demographic profile for interaction
4) Do not expand the candidate set. Decide only among visible items

## Reasons and Guard
1) Reason length up to 20 tokens
2) Reasons reference only visible context fields
3) Numeric audit checks that numbers in reasons match rounded context values
4) If a reason fails guard, emit a deterministic fallback from visible context

## Separation and Fairness Gates
Targets in CONFIGS/tests/gates.yaml:
- silhouette ≥ 0.35
- mean pairwise JSD ≥ 0.10
- ARI stability ≥ 0.80
- Counterfactual fairness L1 change ≤ eps_demo_delta when only demographics flip

## Default Commands

### Install
```bash
pip install -e .
```

### Unit Tests
```bash
pytest -q
```

### Serve API
```bash
uvicorn src.api.service:app --reload --host 0.0.0.0 --port 8000
```

### Distill Heads from Examples
```bash
python scripts/generate_distill_data_from_llm.py --out DATA/distill_llm.jsonl
python scripts/distill_policies.py --input DATA/distill_llm.jsonl --outdir artifacts/policy_heads --buckets 16 --temp 1.0
```

### Metrics and Gates
```bash
python scripts/eval_separation.py
make test
make gate
```

## Task Recipes Claude Should Follow

### A. Read and Summarize Before Editing
1) Read every file listed in "Files Claude must read first"
2) Print a short plan of the exact edits with file paths and line ranges
3) Apply minimal diffs and re-read files to confirm changes

### B. Add or Modify Code
1) Touch only files under src, scripts, CONFIGS, API, DATA unless told otherwise
2) Keep type hints and short functions
3) Maintain response models in API/SCHEMAS.md and src/common/schemas.py in sync

### C. Wire LLM Calls
1) Keep temperature 0 and top_p 1
2) Enforce decision JSON schema in twin decide mode
3) Pass conditioning through chat and decide paths

### D. Ranking Path
1) Use distilled policy heads for probabilities when available
2) Use LLM twins for reasons in explain modes
3) If heads are missing, fall back to LLM vote path

### E. Deltas and Explain Modes
1) Compute per-scenario probability distributions
2) Base scenario deltas are zero
3) Other scenarios deltas sum to about zero
4) For explain blend choose highest-weight twin's guarded reason

### F. ReasonGuard Use
1) Run guard on any emitted reason
2) If guard fails, replace with fallback_reason
3) Cache reasons by twin or mixture and scenario hash

### G. Matching and Profiles
1) Build fused embedding from CTA behavior and profile_vec
2) Allow optional conditioning to explore specific behavior × psychographic × demographic
3) Keep mixture weights normalized

### H. Tests Claude Must Keep Green
- tests/test_personas.py
- tests/test_twin_decide.py
- tests/test_conditioning_and_profiles.py
- tests/test_phase_d_simulator.py
- tests/test_policy_heads.py
- tests/test_counterfactual_fairness.py
- tests/test_reason_guard.py
- tests/test_repro_phase_f.py
- tests/test_separation_script_smoke.py

## API Examples for Quick Manual Checks

### List Personas
```bash
GET /twin/personas
```

### Chat with a Twin
```bash
POST /twin/chat
{"twin_id":"k3","history":[],"prompt":"What do you value","conditioning":{"psychographic_tags":["thrift"]}}
```

### Decide with a Twin
```bash
POST /twin/decide
{"twin_id":"k7","context":{"page_type":"search","visible_products":["A1","A2","A3"],"delivery_eta_days":2},"candidates":[{"id":"A1"},{"id":"A2"}],"max_tokens":20}
```

### Simulate
```bash
POST /simulate
# Use the object under "simulate_min" in API/examples/requests.json
# Add "explain":"per_twin" or "blend" to view reasons
```

## Edit Policy for Claude
1) Do not add new endpoints without updating API/SCHEMAS.md and tests
2) Do not change allowed_mutables without updating SPEC and tests
3) Do not introduce randomness or temperature above 0
4) Do not reference non-visible attributes in reasons
5) Do not expand candidate sets

## Error Handling
1) Return 400 on missing cta_seq and z_or_user_id
2) Return 422 on disallowed override keys or empty candidate sets
3) Return 500 only on schema violations or unexpected errors

## Deliverables Per Change
1) Code changes
2) Updated tests and passing test run
3) Short CHANGELOG.md entry when public interface changes
4) If models or configs change, log versions in sim_config

## Ready Signals Before Moving On
1) make test passes
2) make gate passes or prints metrics above thresholds
3) Repeated identical /simulate requests return byte-identical JSON
4) Reasons pass guard or fall back deterministically

## Operator Notes for OPeRA Data
1) When real OPeRA profiles are available implement a parquet reader in src/profiles/loader.py and map to a bounded profile_vec
2) Keep profile features bounded and stable across runs
3) Use behavior as the backbone and profiles as additional signal

## Important Notes
- **Never** modify `DATA/twin_bank.json` manually (regenerate via distillation)
- **Always** use guard when returning LLM twin reasons
- **Test files are in TESTS/** (uppercase), not tests/
- **Policy heads** are optional (controlled by `CONFIGS/serve/policy.yaml`)
- **Reason cache** improves performance for repeated queries
