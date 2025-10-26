# SSR Service – Draft API Design

The current MVP ships with a Streamlit demo and direct Python interfaces.  
This note captures the shape of the future HTTP API so that downstream teams can plan integrations.  
Implementation **status:** not started.

## Guiding Principles

- Thin FastAPI layer that wraps `src.ssr.inference.SSRInference`
- Synchronous JSON endpoints, no authentication baked in (to be handled by gateway)
- Responses expose both point estimates and full Likert distributions
- Strict request validation via Pydantic models

## Proposed Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/predict` | Score a single scenario |
| `POST` | `/predict_batch` | Score multiple scenarios in one call |
| `POST` | `/compare` | Compare variants against a baseline scenario |
| `GET`  | `/personas` | Return discovered persona metadata |
| `GET`  | `/health` | Lightweight readiness probe |

### `/predict`

```jsonc
POST /predict
{
  "stimulus": "20% off laptops this weekend",
  "persona_ids": ["core_all"],        // optional, defaults to all personas
  "return_distribution": true
}
```

```jsonc
200 OK
{
  "stimulus": "20% off laptops this weekend",
  "prediction": {
    "mean": 4.12,
    "std": 0.77,
    "mode": 4,
    "distribution": [0.03, 0.07, 0.21, 0.47, 0.22]
  },
  "personas": [
    {"id": "persona_01", "weight": 0.28},
    {"id": "persona_02", "weight": 0.19},
    {"id": "persona_03", "weight": 0.53}
  ]
}
```

### `/predict_batch`

Accepts up to 100 stimuli per request. Response mirrors `/predict` but keyed by stimulus ID.

### `/compare`

```jsonc
POST /compare
{
  "baseline": "Standard shipping ($5)",
  "variants": [
    {"id": "free_shipping", "stimulus": "Free shipping on orders over $50"},
    {"id": "express_upgrade", "stimulus": "Express delivery upgrade for $9.99"}
  ]
}
```

Response returns baseline prediction and, for each variant, the lift (%) versus baseline.

### `/personas`

Proxy to `models/persona_profiles.json`. Useful for UI dropdowns or experimentation dashboards.

## Serialization Models (Pydantic v2)

```python
class Scenario(BaseModel):
    id: str | None = None
    stimulus: str
    persona_ids: list[str] | None = None

class LikertPrediction(BaseModel):
    mean: float
    std: float
    mode: int
    distribution: tuple[float, float, float, float, float]

class PredictResponse(BaseModel):
    stimulus: str
    prediction: LikertPrediction
    personas: list[PersonaWeight]
```

## Next Steps

1. Implement FastAPI app in `src/api/ssr_service.py`
2. Add automated contract tests
3. Extend Streamlit client to optionally call the API
4. Document deployment recipe (Docker + ECS / EKS)

Until then, use the Streamlit demo or the Python API (`SSRInference`) for experimentation.
