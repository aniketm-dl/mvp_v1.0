# ✅ System is Running!

## Status: LIVE & OPERATIONAL

Both backend and frontend are running successfully!

---

## Access Points

### Frontend (User Interface)
**URL**: http://localhost:5173

Open this in your browser to access the Digital Twin UI:
- Neon green/blue themed interface
- 12 digital twin cards
- Experiment configuration panel
- Results visualization with charts
- Individual twin insights

### Backend API
**URL**: http://localhost:8000

API endpoints:
- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs
- Twins list: http://localhost:8000/airline/twins

---

## System Configuration

✅ **OpenAI API Key**: Configured
✅ **LLM Model**: GPT-4 (as required)
✅ **Backend**: Running on port 8000
✅ **Frontend**: Running on port 5173
✅ **CORS**: Enabled for localhost:5173
✅ **Twins**: 12 airline passenger personas loaded

---

## What You Can Do Now

### 1. Open the UI
```bash
# Open in your default browser
open http://localhost:5173

# Or paste this URL in your browser:
# http://localhost:5173
```

### 2. Run an Experiment
1. **Select twins**: All 12 are pre-selected (click to deselect)
2. **Configure offer**:
   - Choose offer type (Legroom, WiFi, Lounge, Boarding, Baggage)
   - Adjust discount slider (0-50%)
   - Set flight context
3. **Click "Run Experiment"**
4. **View results**:
   - Aggregated stats and charts
   - Individual twin insights
   - Detailed rationales

### 3. Test a Single Twin Decision
```bash
# Test twin_001 with 20% discount on legroom
curl -X POST http://localhost:8000/airline/decide \
  -H "Content-Type: application/json" \
  -d '{
    "twin_id": "twin_001",
    "offer_type": "legroom",
    "discount_pct": 0.20,
    "flight_length": "medium",
    "trip_purpose": "business"
  }'
```

---

## Cost Information

- **Single decision**: ~$0.01-0.02 (GPT-4)
- **12 twins batch**: ~$0.12-0.24
- **Model used**: gpt-4 (configured in CONFIGS/airline/twin_config.yaml line 7)

---

## Stopping the System

### Stop both servers:
```bash
# Find and kill uvicorn (backend)
pkill -f "uvicorn src.api.service_airline"

# Find and kill vite (frontend)
pkill -f "vite"

# Or kill all Node.js and Python processes (careful!)
pkill node
pkill python3
```

### Restart if needed:
```bash
# Backend:
cd /Users/aniketniranjanmishra/Desktop/Darpan\ Labs/mvp_v1.0
export PYTHONPATH="/Users/aniketniranjanmishra/Desktop/Darpan Labs/mvp_v1.0"
source .env  # Load API keys from .env file
/Users/aniketniranjanmishra/Library/Python/3.9/bin/uvicorn src.api.service_airline:app --host 0.0.0.0 --port 8000 &

# Frontend:
cd ui
npm run dev &
```

---

## Troubleshooting

### UI not loading?
- Check frontend is running: `curl http://localhost:5173`
- Check browser console for errors (F12)

### API errors?
- Check backend health: `curl http://localhost:8000/health`
- Should return: `{"status":"ok","service":"airline-twins","llm_gateway":"initialized"}`

### "LLM gateway not initialized" error?
- Check OpenAI API key is set correctly
- Verify: `echo $OPENAI_API_KEY`

---

## Next Steps

1. **Experiment**: Run different scenarios and compare results
2. **Analyze**: Look at individual twin rationales
3. **Compare**: Try different discounts and offers
4. **Export**: Use `/airline/decisions/export?format=json` to download results
5. **Extend**: Modify twins or add new offer types

---

## Files & Documentation

- **Getting Started**: [GETTING_STARTED.md](GETTING_STARTED.md)
- **Implementation Details**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **Airline Documentation**: [docs/AIRLINE_README.md](docs/AIRLINE_README.md)
- **API Service**: [src/api/service_airline.py](src/api/service_airline.py)
- **Frontend Code**: [ui/src/](ui/src/)

---

## Features Available

✅ 12 Digital Twin Personas
✅ 5 Offer Types (Legroom, WiFi, Lounge, Boarding, Baggage)
✅ Discount Configuration (0-50%)
✅ Flight Context Controls
✅ Batch Decisions (all twins at once)
✅ Aggregated Results View
✅ Individual Twin Insights
✅ Probability Charts (Recharts)
✅ Detailed Rationales
✅ Color-coded Decisions
✅ Responsive Design
✅ Neon Theme (Green/Blue)
✅ Deterministic Mode (seed-based)
✅ Real-time LLM Decisions (GPT-4)

---

**🎉 Enjoy experimenting with your Digital Twins!**

**From Hunches to Evidence - Evidence is Live!**
