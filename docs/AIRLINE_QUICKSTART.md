# Airline Digital Twin - Quick Start Guide

Get up and running in **5 minutes**.

---

## Prerequisites

- Python 3.9+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- ~$0.10-0.50 for testing (depending on how much you test)

---

## Step 1: Setup (2 minutes)

```bash
# 1. Navigate to project
cd mvp_v1.0

# 2. Configure API key
nano .env
# Add line: export OPENAI_API_KEY=sk-your-key-here
# Save and exit (Ctrl+X, Y, Enter)

# 3. Load environment
source .env

# 4. Verify
echo $OPENAI_API_KEY
# Should print your key
```

---

## Step 2: First Decision (1 minute)

```bash
python scripts/ask_twin_decision.py \
  --twin twin_002 \
  --offer legroom \
  --discount 0.20
```

**Expected Output:**
```
================================================================================
DECISION RESULT
================================================================================
Twin: Comfort seeker 35-44 male business traveler (business)
Offer: Extra Legroom Seat
Discount: 20% off
Final Price: $20.00

Decision: YES
Probability: 0.85
Rationale: I prioritize comfort on long flights and this discount makes
           it worthwhile for the added space.
================================================================================
```

**Cost:** ~$0.01-0.02

---

## Step 3: Compare Twins (2 minutes)

```bash
python scripts/compare_twins.py \
  --twins twin_002,twin_006,twin_011 \
  --offer legroom \
  --discount 0.20
```

See how different personas respond:
- `twin_002` (comfort-seeker) → High acceptance
- `twin_006` (value-conscious) → Lower acceptance (needs bigger discount)
- `twin_011` (value + punctuality) → Moderate acceptance

**Cost:** ~$0.03-0.06 (3 decisions)

---

## Step 4: Explore (Optional)

### Try Different Offers

```bash
# WiFi offer
python scripts/ask_twin_decision.py --twin twin_001 --offer wifi --discount 0.25

# Lounge access
python scripts/ask_twin_decision.py --twin twin_009 --offer lounge --discount 0.30

# Priority boarding
python scripts/ask_twin_decision.py --twin twin_003 --offer boarding --discount 0.15
```

### Try Different Discounts

```bash
# Low discount (10%)
python scripts/ask_twin_decision.py --twin twin_006 --offer legroom --discount 0.10

# High discount (40%)
python scripts/ask_twin_decision.py --twin twin_006 --offer legroom --discount 0.40
```

Observe: Higher discount → Higher probability ✅

---

## Step 5: Batch Processing (Optional)

### Test All Twins on One Offer

```bash
python scripts/batch_decisions.py \
  --all-twins \
  --offer legroom \
  --discount 0.20
```

**Output:** Comparison table showing all 12 twins sorted by acceptance probability.

**Cost:** ~$0.12-0.24 (12 decisions)

### Test One Twin on All Offers

```bash
python scripts/batch_decisions.py \
  --twin twin_002 \
  --all-offers \
  --discounts 0.20
```

**Output:** How one twin responds to all 5 offer types.

**Cost:** ~$0.05-0.10 (5 decisions)

---

## Step 6: Check Decision Log

All decisions are automatically logged to `DATA/airline/decisions/ledger.csv`.

```bash
# View recent decisions
tail -5 DATA/airline/decisions/ledger.csv

# Or open in Excel/Numbers for analysis
```

**Columns:**
- timestamp, twin_id, offer_name, discount_pct, decision, probability, rationale, etc.

---

## Common Commands Cheat Sheet

```bash
# Single decision
python scripts/ask_twin_decision.py \
  --twin <TWIN_ID> \
  --offer <OFFER_TYPE> \
  --discount <0.XX>

# Compare multiple twins
python scripts/compare_twins.py \
  --twins <ID1,ID2,ID3> \
  --offer <OFFER_TYPE> \
  --discount <0.XX>

# Batch: All twins × one offer
python scripts/batch_decisions.py \
  --all-twins \
  --offer <OFFER_TYPE> \
  --discounts <0.XX,0.YY>

# Batch: One twin × all offers
python scripts/batch_decisions.py \
  --twin <TWIN_ID> \
  --all-offers \
  --discounts <0.XX>

# Run evaluation
python scripts/evaluate_twins.py \
  --save-report DATA/airline/evaluation_report.md
```

---

## Available Options

### Twin IDs
`twin_001`, `twin_002`, ..., `twin_012`

### Offer Types
`legroom`, `wifi`, `lounge`, `boarding`, `baggage`

### Context Options (Optional)
```bash
--flight-length <short|medium|long>
--trip-purpose <business|leisure>
--time-pressure <low|medium|high>
--recent-delays <none|minor|major>
```

### Other
```bash
--seed <INT>           # For deterministic results
--save <PATH>          # Save decision to JSON file
--verbose              # Show full prompts
```

---

## Troubleshooting

### "OPENAI_API_KEY not found"

```bash
# Make sure you sourced .env
source .env

# Check if it's set
echo $OPENAI_API_KEY

# If empty, edit .env and add your key
nano .env
```

### "Twin not found"

```bash
# List available twins
ls DATA/airline/twins/

# Make sure twin ID is correct (e.g., twin_001, not just 001)
```

### "Rate limit exceeded"

You've hit OpenAI's rate limit. Wait 1 minute and try again, or:
- Upgrade your OpenAI account tier
- Switch to GPT-3.5-turbo (higher limits):
  ```bash
  # Edit CONFIGS/airline/twin_config.yaml
  model: "gpt-3.5-turbo"
  ```

### "Invalid JSON response"

The LLM didn't follow the JSON format. Try:
- Using GPT-4 instead of GPT-3.5-turbo (more reliable)
- The system will automatically retry with a reminder

---

## Next Steps

✅ **You're ready!** You now know how to:
- Ask twins about offers
- Compare different personas
- Process batch decisions
- View decision history

### Learn More

- **[Complete Documentation](AIRLINE_README.md)** - Full feature guide
- **[Architecture](AIRLINE_ARCHITECTURE.md)** - How it works under the hood
- **[Evaluation](AIRLINE_EVALUATION.md)** - Testing and validation

### Try Advanced Features

- Run full evaluation suite
- Generate custom twin cards
- Build your own prompts
- Add new offers or tags

---

**Questions?** Check the [main README](AIRLINE_README.md) or open an issue.

**Happy simulating! 🎉**
