# Fresh Start: mvp_ryanair Branch

## ✅ What's Done

Successfully created a clean `mvp_ryanair` branch for the new LLM-based digital twin approach.

### Branch Setup
- **Branch:** `mvp_ryanair` (created from `main`)
- **Status:** Pushed to remote ✅
- **Purpose:** Build LLM-based digital twins using prompting (no fine-tuning)

### What's Available (Clean State)

#### 1. Airline Dataset
- **Location:** `DATA/airline/demo_airline.parquet`
- **Size:** 400 samples total
- **Split:** 80-20 (320 train, 80 test) via `scripts/resplit_airline_data.py`
- **Features:** Demographics, flight details, 14 service ratings (1-5), satisfaction label (0/1)

#### 2. Data Utilities
- `DATA/airline/airline_loader.py` - Load and parse airline data
- `DATA/airline/airline_processing.py` - Data preprocessing utilities
- `DATA/airline/airline_schema.json` - Dataset schema definition
- `DATA/airline/run_pipeline.py` - Data pipeline runner

#### 3. Scripts
- `scripts/resplit_airline_data.py` - Regenerate 80-20 train/test split
- All other existing scripts from main branch

### What's NOT Included (Intentionally)
- ❌ SSR neural network training code
- ❌ Embedding fine-tuning scripts
- ❌ Regression head training
- ❌ Any evaluation scripts from mvp_airline

This is a **clean slate** for the new approach.

---

## 🎯 New Approach: LLM-Based Digital Twins

Based on Darpan Labs pitch deck and your vision, here's what we're building:

### Core Concept
**Digital twins that respond like real customers using LLM prompting.**

No training, no fine-tuning - just rich context in prompts.

### Architecture

```
Customer Data → Rich Persona Prompt → LLM API → Natural Language Response → Extract Satisfaction + Rationale
```

### Example Flow

**Input:** Customer data for 18-year-old female, economy class, mixed service ratings

**Persona Prompt:**
```
You are an 18-year-old female airline passenger.

Your Profile:
- Customer Type: Loyal Customer
- Travel Purpose: Business travel
- Flight Class: Eco
- Flight Distance: 3456 miles

Your Experience:
- Inflight WiFi Service: 3/5 (average)
- Gate Location: 1/5 (very poor)
- Ease of Online Booking: 4/5 (good)
- [... other ratings ...]

Respond naturally as this passenger would about your flight experience.
```

**LLM Response:**
```
"The flight was okay overall, but honestly the gate location was terrible -
had to walk forever with my bags. The WiFi was decent and I appreciated
being able to book online easily. For economy class, I guess my expectations
weren't that high anyway, but that gate situation really annoyed me."
```

**Extract:** Dissatisfied + Rationale (gate location was poor)

**Ground Truth:** Dissatisfied ✅

---

## 📋 Next Steps

### Phase 1: Build Basic Twin Evaluator

Create `scripts/airline_llm_twin_evaluation.py` that:

1. Loads 80 test customers
2. For each customer:
   - Builds rich persona prompt (demographics + service ratings)
   - Calls LLM API (OpenAI/Anthropic) with prompt
   - Gets natural language response
   - Extracts satisfaction signal using sentiment analysis
   - Compares to ground truth
3. Reports accuracy and provides sample responses with rationales

**Target:** ~85% accuracy (per Stanford research cited in pitch deck)

### Phase 2: Improve Extraction Logic

Refine how we extract satisfaction from responses:
- Keyword matching (satisfied/dissatisfied)
- Sentiment scoring
- Contextual understanding
- Confidence levels

### Phase 3: Add Rationale Analysis

Analyze the "why" behind predictions:
- Extract key complaints/praises
- Identify service aspects mentioned
- Compare rationales to actual service ratings
- Generate insights reports

### Phase 4: Scale to Multiple Personas

Instead of one twin per customer, create archetypes:
- Budget-conscious economy travelers
- Premium business class flyers
- Deal-hunting frequent flyers
- Map test customers to archetypes
- Test archetype-based prediction

---

## 🔑 Key Differences from Old Approach

| Aspect | Old (SSR Neural Network) | New (LLM Twins) |
|--------|--------------------------|-----------------|
| **Training** | 10 epochs embedding + 20 epochs regression | Zero training, prompt-only |
| **Model** | Fine-tuned sentence transformer + NN | Pre-trained LLM (GPT-4/Claude) |
| **Output** | Probability distribution [0.0, 0.99, 0.0, 0.0, 0.0] | Natural language: "The gate was terrible..." |
| **Explainability** | None - black box | Full rationale in plain English |
| **Scalability** | Requires retraining for new data | Just update prompts |
| **Alignment** | Academic ML project | Darpan Labs product vision |

---

## 💾 Data Summary

### Airline Dataset Statistics
- **Total samples:** 400
- **Train set:** 320 (80%)
- **Test set:** 80 (20%)
- **Class distribution:** 65% dissatisfied, 35% satisfied
- **Features:** 14 service ratings + demographics + flight info
- **Target:** Binary satisfaction (0 = dissatisfied, 1 = satisfied)

### Service Ratings Available
1. Inflight WiFi Service
2. Departure/Arrival Time Convenience
3. Ease of Online Booking
4. Gate Location
5. Food and Drink
6. Online Boarding
7. Seat Comfort
8. Inflight Entertainment
9. On-board Service
10. Leg Room Service
11. Baggage Handling
12. Check-in Service
13. Inflight Service
14. Cleanliness

All rated on 1-5 Likert scale.

---

## 🚀 Ready to Build!

You now have:
- ✅ Clean branch with no legacy code
- ✅ Complete airline dataset (400 samples)
- ✅ Data utilities and loaders
- ✅ 80-20 train/test split
- ✅ Clear vision for LLM twin approach

**Next command to run:**
```bash
# Verify data is accessible
python DATA/airline/run_pipeline.py --validate

# Start building twin evaluator
# (to be implemented)
```

---

## 📚 Reference Documents

From your pitch deck:
- **Problem:** Traditional research is slow & costly
- **Solution:** AI-powered customer twins for instant insights
- **Tech Stack:** LLM tuning + Context engineering (page 7)
- **Accuracy Target:** ~85% (Stanford HAI 2025 research, page 9)
- **Use Cases:** Test campaigns, product changes, market research

**Key Quote from Pitch (Page 11):**
> "Once twins and customers become indistinguishable, imagination of the researchers becomes the only constraint in experiments"

This is what we're building! 🎯
