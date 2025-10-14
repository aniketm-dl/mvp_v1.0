# 🎯 Twin Interaction Guide

## Overview

You now have **3 trained digital twins** ready to interact with! Each twin represents a distinct customer archetype with unique shopping behaviors and preferences.

## 🧑‍🤝‍🧑 Your Digital Twins

| Twin ID | Persona | Behavior |
|---------|---------|----------|
| **k0** | Budget-Conscious Searcher | Prioritizes low prices and good deals |
| **k1** | Premium Quality Seeker | Values quality and reliability over price |
| **k2** | Deal-Hunting Explorer | Balances features, deals, and delivery speed |

## 🚀 Quick Start

### 1. Start the API Server

```bash
cd /Users/aniketniranjanmishra/Desktop/Darpan\ Labs/MVP/darpan-whatif-simulator

# Activate virtual environment
source .venv/bin/activate

# Start server
uvicorn src.api.service:app --host 0.0.0.0 --port 8000

# Or use make
make serve
```

### 2. Run the Interactive Examples

```bash
# Run all examples
python examples/interact_with_twins.py

# Or explore individual examples in the script
```

---

## 📚 API Endpoints for Twin Interaction

### 1️⃣ Chat with a Twin

**Endpoint:** `POST /twin/chat`

Ask a twin about their preferences, values, or opinions.

```bash
curl -X POST http://localhost:8000/twin/chat \
  -H "Content-Type: application/json" \
  -d '{
    "twin_id": "k0",
    "history": [],
    "prompt": "What do you value most when shopping?"
  }'
```

**Response:**
```json
{
  "twin_id": "k0",
  "reply": "I look for the best price and decent delivery."
}
```

**Python:**
```python
import requests

def chat_with_twin(twin_id: str, prompt: str):
    response = requests.post(
        "http://localhost:8000/twin/chat",
        json={
            "twin_id": twin_id,
            "history": [],
            "prompt": prompt
        }
    )
    return response.json()["reply"]

# Example
reply = chat_with_twin("k1", "What matters most to you?")
print(reply)  # "I pay for quality and reliability."
```

---

### 2️⃣ Get a Purchase Decision from a Twin

**Endpoint:** `POST /twin/decide`

Ask a twin to choose among products and explain why.

```bash
curl -X POST http://localhost:8000/twin/decide \
  -H "Content-Type: application/json" \
  -d '{
    "twin_id": "k2",
    "context": {
      "price_mean": 500,
      "promo_badge": true,
      "delivery_eta_days": 2
    },
    "candidates": [
      {"id": "Product_A"},
      {"id": "Product_B"},
      {"id": "Product_C"}
    ],
    "max_tokens": 20
  }'
```

**Response:**
```json
{
  "twin_id": "k2",
  "decision": {
    "pick": "Product_C",
    "why": "I hunt for the best deals and features."
  }
}
```

**Python:**
```python
def get_twin_decision(twin_id, context, candidates):
    response = requests.post(
        "http://localhost:8000/twin/decide",
        json={
            "twin_id": twin_id,
            "context": context,
            "candidates": candidates,
            "max_tokens": 20
        }
    )
    return response.json()["decision"]

# Example
decision = get_twin_decision(
    "k0",
    {"price_mean": 750, "promo_badge": False},
    [{"id": "A1"}, {"id": "A2"}]
)
print(f"Chose: {decision['pick']}, Why: {decision['why']}")
```

---

### 3️⃣ Match a User to Their Twin Profile

**Endpoint:** `POST /match`

Identify which twin(s) a user most closely resembles.

```bash
curl -X POST http://localhost:8000/match \
  -H "Content-Type: application/json" \
  -d '{
    "z_or_user_id": "u1"
  }'
```

**Response:**
```json
{
  "twin_weights": {
    "k0": 0.461,
    "k1": 0.287,
    "k2": 0.252
  },
  "primary_twin": {
    "id": "k0",
    "label": "Budget-Conscious Searcher"
  }
}
```

**Python:**
```python
def match_user_to_twins(user_id):
    response = requests.post(
        "http://localhost:8000/match",
        json={"z_or_user_id": user_id}
    )
    data = response.json()
    return data["twin_weights"], data["primary_twin"]

# Example
weights, primary = match_user_to_twins("u1")
print(f"Primary: {primary['label']}")
print(f"Weights: {weights}")
```

---

### 4️⃣ Run What-If Simulations

**Endpoint:** `POST /simulate`

Test how twins respond to changes in price, promotions, delivery, etc.

```bash
curl -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "cta_seq": [{
      "user_id": "u1",
      "session_id": "s1",
      "ts": "2025-06-01T12:00:00",
      "context": {
        "page_type": "search",
        "price_mean": 820,
        "visible_products": ["A1", "A2", "A3"]
      },
      "task": "choose_product",
      "action_id": "A2"
    }],
    "task": "choose_product",
    "scenarios": [
      {"variant_id": "base", "context_overrides": {}},
      {"variant_id": "10%_off", "context_overrides": {"price_mean": 738}},
      {"variant_id": "promo", "context_overrides": {"promo_badge": true}}
    ],
    "topk": 3,
    "explain": "blend",
    "deterministic": true,
    "seed": 17
  }'
```

**Response Structure:**
```json
{
  "by_scenario": [
    {
      "variant_id": "base",
      "topN": [{"id": "A1", "p": 0.377}, {"id": "A2", "p": 0.311}],
      "why": "I look for the best price and decent delivery.",
      "deltas": {"A1": 0.0, "A2": 0.0, "A3": 0.0}
    },
    {
      "variant_id": "10%_off",
      "topN": [...],
      "why": "...",
      "deltas": {"A1": +0.05, "A2": -0.03, "A3": -0.02}
    }
  ],
  "twin_weights": {"k0": 0.461, "k1": 0.287, "k2": 0.252},
  "primary_twin": {"id": "k0", "label": "Budget-Conscious Searcher"}
}
```

---

## 🔧 Current Mode: STUB (Deterministic Testing)

### What is Stub Mode?

The system is currently running in **stub mode** (`use_stub: true` in `CONFIGS/serve/llm.yaml`). This means:

✅ **Pros:**
- Lightning fast responses (<10ms)
- 100% deterministic and reproducible
- No GPU required
- Perfect for testing system logic
- All API functionality works

⚠️ **Limitations:**
- Fixed responses per twin (not context-adaptive)
- No natural language variation
- Limited to predefined personality traits

### Trained LLM Adapters (Ready for Production)

You have **fully trained LoRA adapters** for all 3 twins:

```
✅ k0: artifacts/llm_adapters/k0/adapter_model.safetensors (4.5MB)
✅ k1: artifacts/llm_adapters/k1/adapter_model.safetensors (4.5MB)
✅ k2: artifacts/llm_adapters/k2/adapter_model.safetensors (4.5MB)
```

### Switching to Real LLM Mode

To use the trained adapters (when ready for production):

1. **Edit config:**
   ```bash
   # Set use_stub: false in CONFIGS/serve/llm.yaml
   vim CONFIGS/serve/llm.yaml
   ```

2. **Restart server:**
   ```bash
   pkill -f uvicorn
   make serve
   ```

3. **Trade-offs:**
   - 🐌 Slower: ~200-500ms per request (model loading + generation)
   - 🧠 Smarter: Context-aware, natural language
   - 💾 Memory: Requires ~2GB RAM for GPT-2 base model

---

## 🎨 Use Cases

### Business Intelligence
```python
# Compare how different customer segments respond to a promotion
for twin_id in ["k0", "k1", "k2"]:
    decision = get_twin_decision(
        twin_id,
        {"price_mean": 500, "promo_badge": True},
        [{"id": "Product_A"}, {"id": "Product_B"}]
    )
    print(f"{twin_id}: {decision}")
```

### A/B Testing Simulation
```python
# Test price sensitivity before running real A/B test
scenarios = [
    {"variant_id": "control", "context_overrides": {"price_mean": 999}},
    {"variant_id": "test_10%_off", "context_overrides": {"price_mean": 899}},
    {"variant_id": "test_20%_off", "context_overrides": {"price_mean": 799}}
]

result = run_what_if_simulation(cta_seq, scenarios, explain="per_twin")
# Analyze deltas to predict conversion lift
```

### Personalization Engine
```python
# Match user to twin, then use twin preferences for recommendations
weights, primary = match_user_to_twins("u1234")

if primary["id"] == "k0":  # Budget-conscious
    show_price_sorted_results()
elif primary["id"] == "k1":  # Premium quality
    show_quality_sorted_results()
else:  # Deal hunter
    show_featured_deals()
```

---

## 📊 Available Context Variables

When making decisions or running simulations, twins consider:

| Variable | Type | Description |
|----------|------|-------------|
| `price_mean` | float | Average price of products |
| `price_min` | float | Minimum price |
| `price_max` | float | Maximum price |
| `promo_badge` | bool | Promotional badge present |
| `delivery_eta_days` | int | Expected delivery time |
| `copy_variant_id` | str | Ad copy variant |

**Allowed mutations** (for what-if scenarios):
- ✅ price_mean, price_min, price_max
- ✅ promo_badge
- ✅ delivery_eta_days
- ✅ copy_variant_id
- ❌ Cannot add new candidates (only choose from visible)

---

## 🧪 Testing & Validation

### Verify System Works
```bash
# Run all tests
make test

# Run quality gates
make gate

# Check twin separation metrics
python scripts/eval_separation.py
```

### Expected Metrics
```
✅ Silhouette Score: 1.0000 (target ≥ 0.35)
✅ Mean Pairwise JSD: 0.6931 (target ≥ 0.10)
✅ Adjusted Rand Index: 1.0000 (target ≥ 0.80)
```

---

## 🐛 Troubleshooting

### API not responding?
```bash
# Check if server is running
curl http://localhost:8000/health

# Check logs
tail -f /tmp/uvicorn_stub.log

# Restart server
pkill -f uvicorn && make serve
```

### Empty responses?
- Check that `use_stub: true` in `CONFIGS/serve/llm.yaml`
- Real LLM mode may hang if GPU not available

### Import errors?
```bash
# Reinstall dependencies
source .venv/bin/activate
pip install -e .
```

---

## 📁 File Locations

```
├── examples/
│   └── interact_with_twins.py          # 👈 Interactive examples
├── CONFIGS/serve/
│   └── llm.yaml                         # LLM mode config
├── DATA/
│   ├── personas.json                    # Twin definitions
│   └── sft/                             # Training data
│       ├── k0.jsonl
│       ├── k1.jsonl
│       └── k2.jsonl
├── artifacts/llm_adapters/              # Trained adapters
│   ├── k0/
│   ├── k1/
│   └── k2/
└── src/api/service.py                   # API implementation
```

---

## 🚀 Next Steps

1. **Explore the examples:**
   ```bash
   python examples/interact_with_twins.py
   ```

2. **Build your own use case:**
   - Copy `examples/interact_with_twins.py`
   - Modify for your specific scenario
   - Test different contexts and candidates

3. **Integrate with your app:**
   - Use the Python SDK patterns
   - Or call REST API directly
   - Consider caching for performance

4. **Production deployment:**
   - Switch to real LLM mode when ready
   - Monitor latency (target: <200ms p95)
   - Scale horizontally if needed

---

## 💡 Tips

- **Start with stub mode** for development and testing
- **Use `explain: "per_twin"`** to see how each twin thinks
- **Set `deterministic: true`** for reproducible results
- **Cache twin decisions** for repeated queries
- **Monitor deltas** to understand behavior changes

---

## 📞 Support

- Issues: https://github.com/anthropics/claude-code/issues
- Documentation: See DOCS/ folder
- Examples: examples/ folder

**Happy experimenting! 🎉**
