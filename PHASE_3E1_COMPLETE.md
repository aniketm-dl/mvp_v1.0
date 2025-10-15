# Phase 3E.1 Complete: OPeRA Parser and Dataloader

## Overview

Successfully implemented a complete OPeRA (Observation-Persona-Rationale-Action) dataloader system for parsing session logs into aligned sequences ready for encoder training and evaluation.

## Deliverables

### 1. Configuration
- **[CONFIGS/opera.yaml](CONFIGS/opera.yaml)**: Centralized configuration for paths, token budgets, splits, and quality filters
  - Token limits: observation ≤120, rationale ≤60
  - Deterministic with seed 17
  - 70/15/15 train/val/test splits

### 2. Schemas
- **[src/data/opera/schemas.py](src/data/opera/schemas.py)**: Pydantic models for type-safe validation
  - `OPeRAStep`: Single step with token budget enforcement
  - `OPeRASession`: Complete session with alignment validation
  - `PersonaVector`: 12-D embedding with bounds checking
  - `OPeRAConfig`: Configuration loader

### 3. Parser
- **[src/data/opera/parse_opera.py](src/data/opera/parse_opera.py)**: HTML-aware parser with normalization
  - Strips scripts/styles, converts semantic tags to markdown
  - Enforces token budgets (120/60 tokens)
  - Stratified splits by user_id
  - Deterministic processing
  - Rich CLI with statistics tables

### 4. Dataset
- **[src/data/opera/dataset.py](src/data/opera/dataset.py)**: PyTorch Dataset and DataModule
  - Four aligned views per step: seq_tokens, rationale_tokens, persona_vec, catalog_vec
  - Shared vocabulary across splits
  - Automatic tokenization and padding
  - DataLoader integration

### 5. Tests
- **[TESTS/test_opera_parse_and_dataset.py](TESTS/test_opera_parse_and_dataset.py)**: Comprehensive test suite
  - HTML normalization tests
  - Schema validation tests
  - Token budget enforcement tests
  - Parser functionality tests
  - Dataset loading tests
  - **17 tests, all passing ✓**

### 6. CI/CD
- **[.github/workflows/opera-ci.yml](.github/workflows/opera-ci.yml)**: GitHub Actions workflow
  - Runs on Python 3.10 and 3.11
  - Schema validation
  - Token budget checks
  - Config validation
  - Linting with ruff and black

### 7. Documentation
- **[src/data/opera/spec.md](src/data/opera/spec.md)**: Full technical specification
- **[src/data/opera/README.md](src/data/opera/README.md)**: Usage guide and examples

### 8. Sample Data
- **[DATA/OPeRA/raw/sample_sessions.jsonl](DATA/OPeRA/raw/sample_sessions.jsonl)**: 6 sample sessions with 15 steps
- **[DATA/OPeRA/processed/](DATA/OPeRA/processed/)**: Parsed train/val/test parquet files

## Usage

### Parse Raw Data
```bash
python scripts/parse_opera.py \
  --in DATA/OPeRA/raw \
  --out DATA/OPeRA/processed \
  --config CONFIGS/opera.yaml
```

### Load in Python
```python
from src.data.opera.dataset import OPeRADataModule

dm = OPeRADataModule('DATA/OPeRA/processed', batch_size=32)
dm.setup()

train_loader = dm.train_dataloader()
for batch in train_loader:
    # batch['seq_tokens']: [batch, 120] observation tokens
    # batch['rationale_tokens']: [batch, 60] rationale tokens
    # batch['persona_vec']: [batch, 12] persona embedding
    # batch['catalog_vec']: [batch, 10] context features
    # batch['action_label']: [batch] integer action
    pass
```

### Run Tests
```bash
pytest TESTS/test_opera_parse_and_dataset.py -v
```

## Validation Results

### Test Coverage
- ✅ HTML normalization (4 tests)
- ✅ Schema validation (5 tests)
- ✅ Parser functionality (5 tests)
- ✅ Dataset loading (3 tests)

### Quality Metrics (Sample Data)
- **Observation Coverage**: 100% (15/15 steps have observation)
- **Action Coverage**: 100% (15/15 steps have valid action)
- **Rationale Coverage**: 53.33% (8/15 steps have rationale)
- **Token Budget Compliance**: 100% (all enforced at schema level)

### Code Quality
- ✅ Ruff linting passed (F, E, W, I checks)
- ✅ All future imports present
- ✅ Type hints on all functions
- ✅ Line length ≤100 characters
- ✅ No hardcoded parameters (all in config)

## Architecture Highlights

### Determinism
- Fixed seed (17) for reproducibility
- Stable user ordering for splits
- Canonical vocabulary ordering
- No randomness in preprocessing

### Step-Level Alignment
- Every step has observation + action
- Rationales optional (nullable)
- Sequential step indices (0, 1, 2, ...)
- Alignment validated by Pydantic

### Token Budget Enforcement
- Observation: whitespace tokenization, truncate to 120
- Rationale: whitespace tokenization, truncate to 60
- Enforced at both parser level (with warnings) and schema level (with errors)

### Stratified Splits
- Users grouped, not sessions
- Minimum 2 sessions per user required
- Users sorted deterministically
- Prevents data leakage

## File Structure
```
src/data/opera/
├── __init__.py
├── schemas.py          # Pydantic models
├── parse_opera.py      # Parser with HTML normalization
├── dataset.py          # PyTorch Dataset and DataModule
├── spec.md             # Technical specification
├── README.md           # Usage documentation
└── __tests__/
    └── test_parse_and_dataset.py

CONFIGS/
└── opera.yaml          # Configuration

DATA/OPeRA/
├── raw/                # Raw JSONL files
└── processed/          # Parsed parquet splits
    ├── train.parquet
    ├── val.parquet
    └── test.parquet

scripts/
└── parse_opera.py      # Wrapper script for CLI

TESTS/
└── test_opera_parse_and_dataset.py

.github/workflows/
└── opera-ci.yml        # CI pipeline
```

## Constraints Met

✅ All paths and sizes in `CONFIGS/opera.yaml`
✅ No network calls
✅ Deterministic preprocessing (seed 17)
✅ Rationale and persona fields available as separate views
✅ OPeRA alignment preserved (step-level)
✅ HTML normalized to ≤120 tokens per observation
✅ Rationale trimmed to ≤60 tokens
✅ Stratified train/val/test splits by user
✅ Token budget tests passing
✅ ≥90% steps have non-empty observation
✅ ≥90% steps have valid action
✅ Rationales align to steps (nullable where missing)
✅ CI passing on schema errors

## Dependencies Added
- `beautifulsoup4`: HTML parsing
- `lxml`: BeautifulSoup backend
- `ruff`, `black`: Linting and formatting

## Next Steps

### Phase 3E.2: Encoder Training
Use this dataloader to train behavior encoders:

```python
from src.data.opera.dataset import OPeRADataModule
from src.models.encoder import BehaviorEncoder

dm = OPeRADataModule('DATA/OPeRA/processed')
dm.setup()

encoder = BehaviorEncoder(
    vocab_size=dm.get_vocab_size(),
    embed_dim=256,
    hidden_dim=512,
    persona_dim=12
)

# Train encoder with aligned observations + persona
```

### Integration with Existing System
- Use parsed OPeRA data to augment twin training
- Replace mock behavior embeddings with encoder outputs
- Integrate persona features into mixture model

## Performance Notes

Parsing times on M1 Mac:
- 6 sessions (15 steps): ~0.5 seconds
- Estimated 1K sessions: ~2 seconds
- Estimated 10K sessions: ~15 seconds
- Estimated 100K sessions: ~2 minutes

Memory usage scales linearly with session count. For large datasets (>1M sessions), consider chunked processing.

## Summary

Phase 3E.1 delivers a production-ready OPeRA parser and dataloader with:
- 17 passing tests
- Complete CI/CD pipeline
- Comprehensive documentation
- Sample data demonstrating end-to-end flow
- Type-safe schemas with validation
- Deterministic, reproducible processing
- Token budget enforcement
- Stratified splits preventing data leakage

All deliverables complete. Ready for encoder training (Phase 3E.2).
