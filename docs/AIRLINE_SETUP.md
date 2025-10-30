# Airline Digital Twin Setup Guide

## Quick Start

### 1. Set Up OpenAI API Key

The airline twin system uses OpenAI's GPT models to power decision-making.

**Get your API key:**
1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy your key (it starts with `sk-...`)

**Add to environment:**

```bash
# Edit .env file
nano .env

# Add your key:
export OPENAI_API_KEY=sk-your-actual-key-here

# Load environment
source .env

# Verify
echo $OPENAI_API_KEY
```

### 2. Verify Data

```bash
# Check that twin cards exist
ls DATA/airline/twins/

# Should see: twin_001.json, twin_002.json, ..., twin_012.json
```

### 3. Make Your First Decision

```bash
# Ask twin_001 about extra legroom at 20% discount
python scripts/ask_twin_decision.py \
  --twin twin_001 \
  --offer legroom \
  --discount 0.20 \
  --flight-length long \
  --trip-purpose business
```

**Expected output:**
```
================================================================================
DECISION RESULT
================================================================================
Twin: Punctuality sensitive 18-24 male business traveler (eco)
Offer: Extra Legroom Seat
Discount: 20% off
Final Price: $20.00

Decision: YES/NO
Probability: 0.65
Rationale: [Twin's reasoning based on their profile]

Context: long business flight
Time Pressure: medium
Recent Delays: minor
================================================================================
```

---

## Available Twins

We have 12 diverse passenger personas:

| Twin ID | Description |
|---------|-------------|
| twin_001 | Punctuality sensitive 18-24 male business traveler (eco) |
| twin_002 | Comfort seeker 35-44 male business traveler (business) |
| twin_003 | Punctuality sensitive 55+ female leisure traveler (eco) |
| twin_004 | Typical 55+ male business traveler (eco-plus) |
| twin_005 | Punctuality sensitive 55+ male leisure traveler (business) |
| twin_006 | Value conscious 35-44 male leisure traveler (eco-plus) |
| twin_007 | Typical 45-54 female business traveler (eco) |
| twin_008 | Punctuality sensitive 35-44 female leisure traveler (eco) |
| twin_009 | Punctuality sensitive + business_oriented 25-34 male business traveler (business) |
| twin_010 | Punctuality sensitive 55+ male leisure traveler (business) |
| twin_011 | Punctuality sensitive + value_conscious 55+ female leisure traveler (eco-plus) |
| twin_012 | Punctuality sensitive 55+ male business traveler (eco-plus) |

---

## Offer Types

Available offers you can test:

| Offer | Description | Default Price |
|-------|-------------|---------------|
| `legroom` | Extra Legroom Seat | $25 |
| `wifi` | Inflight WiFi Access | $15 |
| `lounge` | Airport Lounge Access | $40 |
| `boarding` | Priority Boarding | $20 |
| `baggage` | Extra Checked Baggage | $30 |

---

## Context Options

Customize the decision context:

**Flight Length:**
- `short` - Under 1,000 miles
- `medium` - 1,000-2,500 miles
- `long` - Over 2,500 miles

**Trip Purpose:**
- `business` - Business travel
- `leisure` - Personal/vacation travel

**Time Pressure:**
- `low` - Relaxed schedule
- `medium` - Normal schedule
- `high` - Tight connection/urgent

**Recent Delays:**
- `none` - No recent delays
- `minor` - 1-15 minutes
- `major` - Over 60 minutes

---

## Example Scenarios

### Scenario 1: Budget-Conscious Traveler
```bash
python scripts/ask_twin_decision.py \
  --twin twin_006 \
  --offer lounge \
  --discount 0.40 \
  --flight-length short \
  --trip-purpose leisure \
  --time-pressure low
```

### Scenario 2: Business Traveler with Delay
```bash
python scripts/ask_twin_decision.py \
  --twin twin_009 \
  --offer boarding \
  --discount 0.15 \
  --flight-length long \
  --trip-purpose business \
  --time-pressure high \
  --recent-delays major
```

### Scenario 3: Comfort-Seeker on Long Flight
```bash
python scripts/ask_twin_decision.py \
  --twin twin_002 \
  --offer legroom \
  --discount 0.10 \
  --flight-length long \
  --trip-purpose business \
  --time-pressure medium
```

---

## Advanced Options

### Deterministic Results

Use `--seed` for reproducible decisions:

```bash
python scripts/ask_twin_decision.py \
  --twin twin_001 \
  --offer wifi \
  --discount 0.25 \
  --seed 42
```

Running this command multiple times with the same seed will produce identical results.

### Save Decision to File

```bash
python scripts/ask_twin_decision.py \
  --twin twin_003 \
  --offer baggage \
  --discount 0.30 \
  --save DATA/airline/decisions/twin_003_baggage_30off.json
```

### View Full Prompts

See exactly what's sent to the LLM:

```bash
python scripts/ask_twin_decision.py \
  --twin twin_005 \
  --offer lounge \
  --discount 0.20 \
  --verbose
```

---

## Configuration

Edit `CONFIGS/airline/twin_config.yaml` to customize:

- **LLM provider**: `openai` or `anthropic`
- **Model**: `gpt-4`, `gpt-3.5-turbo`, `claude-3-sonnet-20240229`
- **Temperature**: Lower = more deterministic (default: 0.2)
- **Max tokens**: Response length limit (default: 128)
- **Discount ladders**: Acceptance thresholds per persona type

---

## Troubleshooting

### Error: "OPENAI_API_KEY not found"

```bash
# Make sure .env is sourced
source .env

# Check if key is set
echo $OPENAI_API_KEY

# If empty, edit .env and add your key
```

### Error: "Twin not found"

```bash
# List available twins
ls DATA/airline/twins/

# Make sure you're using correct twin ID (e.g., twin_001, not just 001)
```

### Error: "Invalid JSON response"

This usually means the LLM didn't follow the JSON format. Try:
1. Using GPT-4 instead of GPT-3.5 (more reliable)
2. The system will automatically retry with an explicit reminder

### Rate Limits

If you hit OpenAI rate limits:
1. Wait a minute and try again
2. Upgrade your OpenAI account tier
3. Switch to a different model (gpt-3.5-turbo has higher limits)

---

## Cost Estimates

Approximate costs per decision (as of 2024):

| Model | Input Cost | Output Cost | Per Decision |
|-------|-----------|-------------|--------------|
| GPT-4 | $0.03/1K tokens | $0.06/1K tokens | ~$0.01-0.02 |
| GPT-3.5-turbo | $0.0015/1K tokens | $0.002/1K tokens | ~$0.0001-0.0003 |
| Claude 3 Sonnet | $0.003/1K tokens | $0.015/1K tokens | ~$0.001-0.003 |

**Budget-friendly option:** Use GPT-3.5-turbo for most testing, then switch to GPT-4 for final evaluation.

---

## Next Steps

- **Phase 5**: Run evaluation harness to test monotonicity and face validity
- **Phase 6**: Use CLI tool to interactively compare multiple twins
- **Phase 7**: Read full documentation in `DOCS/AIRLINE_TWINS.md`

---

**Need help?** Check the main README or open an issue on GitHub.
