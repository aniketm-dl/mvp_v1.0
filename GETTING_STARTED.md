# Getting Started - Darpan Labs Digital Twin UI

Complete guide to run the full system end-to-end.

---

## Prerequisites

1. **Python 3.11+** (Note: System has 3.9, may need upgrade for full functionality)
2. **Node.js 18+** and npm
3. **OpenAI API Key** (for LLM twin decisions)

---

## Quick Start (5 Steps)

### Step 1: Configure API Key

```bash
# Edit .env file
nano .env

# Add your OpenAI API key:
export OPENAI_API_KEY=sk-your-actual-key-here

# Save and load
source .env

# Verify
echo $OPENAI_API_KEY
```

### Step 2: Install Frontend Dependencies

```bash
cd ui
npm install
```

This will install:
- React 18 + TypeScript
- Vite (dev server)
- Tailwind CSS (with neon theme)
- Recharts (charts)
- Zustand (state management)
- React Query (API caching)
- Axios (HTTP client)

### Step 3: Start Backend API Server

```bash
# From project root
python3 -m uvicorn src.api.service:app --reload --host 0.0.0.0 --port 8000

# Or using make:
make serve
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
```

### Step 4: Start Frontend Development Server

```bash
# In a new terminal, from project root
cd ui
npm run dev
```

Expected output:
```
  VITE v6.0.7  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### Step 5: Open in Browser

Navigate to: **http://localhost:5173**

You should see:
- Header: "From Hunches to Evidence"
- 12 digital twin cards
- Experiment configuration panel
- Green/blue neon theme

---

## Usage Guide

### Running an Experiment

1. **Select Twins**: Click on twin cards to select/deselect (all selected by default)
2. **Configure Offer**:
   - Choose offer type (Legroom, WiFi, Lounge, Boarding, Baggage)
   - Adjust discount slider (0-50%)
   - Set flight context (length, purpose, time pressure, delays)
3. **Run Experiment**: Click "Run Experiment (X Twins)" button
4. **View Results**:
   - Aggregated stats: Acceptance rate, avg probability, decision split
   - Chart: Bar chart of probabilities by twin
   - Table: Detailed results with rationales
   - Individual insights: Tabbed view for each twin

### Understanding Results

- **Green bars/badges**: Accepted offers
- **Red bars/badges**: Declined offers
- **Probability**: Confidence level (0-100%)
- **Rationale**: LLM-generated explanation

### Tips

- **Deterministic results**: Set same seed value for reproducible experiments
- **Compare scenarios**: Run multiple experiments with different configurations
- **Export data**: Use GET `/api/airline/decisions/export?format=json` endpoint

---

## API Endpoints (Backend)

The UI uses these endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/airline/twins` | GET | List all 12 twins |
| `/airline/decide` | POST | Single twin decision |
| `/airline/batch_decide` | POST | Batch decisions (used by UI) |
| `/airline/decisions/export` | GET | Export ledger (CSV/JSON) |
| `/health` | GET | Health check |

### API Documentation

Visit http://localhost:8000/docs for interactive Swagger UI.

---

## Troubleshooting

### "Connection refused" error in UI

**Problem**: Frontend can't reach backend

**Solution**:
```bash
# Check if backend is running
curl http://localhost:8000/health

# Should return: {"status":"ok",...}

# If not, start backend:
make serve
```

### "OPENAI_API_KEY not found"

**Problem**: API key not configured

**Solution**:
```bash
# Check if set
echo $OPENAI_API_KEY

# If empty, edit .env and source it
nano .env
source .env
```

### "Failed to load twins"

**Problem**: Backend airline endpoints not working

**Solution**:
```bash
# Verify twins exist
ls -la DATA/airline/twins/

# Should show 12 twin_*.json files

# Test endpoint directly
curl http://localhost:8000/airline/twins
```

### Vite build errors

**Problem**: Missing dependencies or TypeScript errors

**Solution**:
```bash
cd ui
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Python dependency issues

**Problem**: Missing Python packages

**Solution**:
```bash
# Install core dependencies
python3 -m pip install fastapi uvicorn pydantic pyyaml openai anthropic

# For full setup (requires Python 3.11+):
python3 -m pip install -e .
```

---

## Development Workflow

### Making Changes to UI

1. Edit files in `ui/src/`
2. Vite hot-reload automatically updates browser
3. No build step needed for development

### Making Changes to API

1. Edit files in `src/api/service.py` or `src/airline/`
2. Uvicorn auto-reloads with `--reload` flag
3. Test endpoint in browser or Swagger UI

### Building for Production

```bash
# Build frontend
cd ui
npm run build

# Output in ui/dist/
# Serve via FastAPI static files or deploy separately
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND (React + Vite) - http://localhost:5173          │
│  - TwinSelector: Select twins                               │
│  - ExperimentPanel: Configure offer & context               │
│  - ResultsAggregated: Charts & tables                       │
│  - TwinInsights: Individual twin details                    │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP Requests (Axios)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  BACKEND (FastAPI) - http://localhost:8000                 │
│  - /airline/twins: List twins                               │
│  - /airline/batch_decide: Run experiments                   │
│  - CORS: Allows localhost:5173                              │
└────────────────────┬────────────────────────────────────────┘
                     │ Load twins & call LLM
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  DATA & LLM                                                  │
│  - DATA/airline/twins/*.json: 12 twin personas              │
│  - PROMPTS/airline/*: System & user prompts                 │
│  - OpenAI/Anthropic API: LLM decision making                │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite 6
- **Styling**: Tailwind CSS (neon green/blue theme)
- **State**: Zustand
- **API**: Axios + React Query
- **Charts**: Recharts
- **Icons**: Lucide React

### Backend
- **Framework**: FastAPI
- **Runtime**: Uvicorn (ASGI server)
- **Validation**: Pydantic v2
- **LLM**: OpenAI GPT-4 / Anthropic Claude

---

## Next Steps

### Enhancements You Can Make

1. **Chat Interface**: Implement conversational UI with twins
2. **Export Feature**: Add CSV/JSON download button in UI
3. **Comparison Mode**: Side-by-side scenario comparison
4. **History**: Save and load past experiments
5. **Authentication**: Add user login for multi-user access
6. **Real-time**: WebSocket for live updates
7. **Analytics Dashboard**: Long-term trends and insights

### Adding New Offer Types

1. Edit `src/airline/schemas.py`:
   ```python
   def create_custom_offer(discount_pct: float, price: float = 50.0) -> OfferDetails:
       return OfferDetails(
           name="Custom Offer Name",
           offer_kind="service_addon",
           discount_pct=discount_pct,
           absolute_price_delta=price * (1 - discount_pct),
           constraints=["your constraints"]
       )
   ```

2. Add to `OFFER_FACTORIES` in `src/api/service.py`:
   ```python
   OFFER_FACTORIES = {
       # ...existing...
       "custom": create_custom_offer,
   }
   ```

3. Add option to UI dropdown in `ExperimentPanel.tsx`:
   ```tsx
   <option value="custom">Custom Offer Name</option>
   ```

---

## Support

**Issues**: Open an issue on GitHub
**Docs**: See `docs/AIRLINE_*.md` for detailed documentation
**API Docs**: http://localhost:8000/docs

---

## Cost Estimate

- **Per twin decision**: ~$0.01-0.02 (OpenAI GPT-4)
- **12 twins experiment**: ~$0.12-0.24
- **100 experiments**: ~$12-24/month
- **Use GPT-3.5-turbo**: 10x cheaper, slightly less reliable

---

**Built with ❤️ by Darpan Labs**

*From Hunches to Evidence - Simulate real customers, instantly.*
