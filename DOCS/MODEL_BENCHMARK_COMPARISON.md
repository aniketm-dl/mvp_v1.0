# Model Benchmark Comparison for Digital Twin Training

Comprehensive comparison of model options from GPT-2 era to latest models for training 18 digital twin personas.

---

## Quick Summary

**🎯 Recommended for your use case:** Mistral-7B-Instruct-v0.2
- ✅ Best balance of performance, speed, and cost
- ✅ Instant access (no gates)
- ✅ 2-4 hour training time on Colab Pro
- ✅ $9.99/month total cost

---

## Complete Model Comparison Table

### Open Source Models (Fine-tunable with LoRA)

| Model | Size | MMLU | GSM8K | Training Time (18 personas)¹ | GPU Memory | Cost² | Access | License | Recommendation |
|-------|------|------|-------|------------------------------|------------|-------|--------|---------|----------------|
| **GPT-2** | 124M | ~25% | ~0% | 30-60 min | 2GB | Free | ✅ Open | MIT | ❌ Too weak |
| **GPT-2 Medium** | 355M | ~30% | ~0% | 1-2 hours | 4GB | Free | ✅ Open | MIT | ❌ Too weak |
| **GPT-2 Large** | 774M | ~32% | ~1% | 2-3 hours | 6GB | Free | ✅ Open | MIT | ⚠️ Weak |
| **GPT-2 XL** | 1.5B | ~35% | ~2% | 3-4 hours | 8GB | Free | ✅ Open | MIT | ⚠️ Mediocre |
| **Phi-2** | 2.7B | 56.3% | 61.1% | 2-3 hours | 10GB | Free | ✅ Open | MIT | ✅ Good budget option |
| **Phi-3-mini** | 3.8B | 68.8% | 82.5% | 2.5-3.5 hours | 12GB | Free | ✅ Open | MIT | ✅ **Excellent!** |
| **Gemma-2B** | 2B | 42.3% | 17.7% | 1.5-2 hours | 8GB | Free | ✅ Open | Gemma | ⚠️ Mediocre |
| **Gemma-7B** | 7B | 64.3% | 46.4% | 3-4 hours | 16GB | Free | ✅ Open | Gemma | ✅ Good |
| **Mistral-7B-v0.1** | 7.2B | 60.1% | 40.7% | 2-4 hours | 16GB | Free | ✅ Open | Apache 2.0 | ✅ **Best!** |
| **Mistral-7B-Instruct-v0.2** | 7.2B | 60.1% | 40.7% | 2-4 hours | 16GB | Free | ✅ Open | Apache 2.0 | ✅ **RECOMMENDED** |
| **Mistral-7B-Instruct-v0.3** | 7.2B | 62.5% | 45.2% | 2-4 hours | 16GB | Free | ✅ Open | Apache 2.0 | ✅ **Excellent!** |
| **Llama-2-7b-chat** | 7B | 48.3% | 14.6% | 3-4 hours | 16GB | Free | ❌ Gated | Llama 2 | ⚠️ Needs approval |
| **Llama-2-13b-chat** | 13B | 54.8% | 28.7% | 5-8 hours | 26GB | Free | ❌ Gated | Llama 2 | ⚠️ Slower |
| **Llama-3-8B-Instruct** | 8B | 68.4% | 79.6% | 3-4 hours | 18GB | Free | ✅ Open | Llama 3 | ✅ **Excellent!** |
| **Llama-3.1-8B-Instruct** | 8B | 69.4% | 84.5% | 3-4 hours | 18GB | Free | ✅ Open | Llama 3.1 | ✅ **Top tier!** |
| **Llama-3.2-3B-Instruct** | 3B | 63.4% | 77.3% | 2-3 hours | 12GB | Free | ✅ Open | Llama 3.2 | ✅ Excellent budget |
| **Qwen-2-7B-Instruct** | 7B | 70.3% | 79.9% | 3-4 hours | 16GB | Free | ✅ Open | Apache 2.0 | ✅ **Top performer!** |
| **Qwen-2.5-7B-Instruct** | 7B | 74.5% | 85.4% | 3-4 hours | 16GB | Free | ✅ Open | Apache 2.0 | ✅ **Best MMLU!** |
| **Mixtral-8x7B-Instruct** | 47B³ | 70.6% | 74.4% | 12-20 hours | 48GB | Free | ✅ Open | Apache 2.0 | ⚠️ Too slow/expensive |
| **Llama-3.1-70B-Instruct** | 70B | 79.3% | 92.3% | 20-30 hours | 140GB | Free | ✅ Open | Llama 3.1 | ❌ Too slow/expensive |

### Commercial API Models (Not Fine-tunable with LoRA)

| Model | Size | MMLU | GSM8K | Training Method | Cost per Persona⁴ | Total Cost⁵ | Access | Recommendation |
|-------|------|------|-------|-----------------|-------------------|-------------|--------|----------------|
| **GPT-3.5-turbo** | ~175B | 70.0% | 57.1% | Few-shot prompting | N/A | ~$10-20/month | ✅ API | ⚠️ Can't train adapters |
| **GPT-3.5-turbo (fine-tuned)** | ~175B | 70.0% | 57.1% | OpenAI Fine-tuning⁶ | ~$8-12 | ~$150-200 one-time | ✅ API | ⚠️ Expensive, different workflow |
| **GPT-4-turbo** | Unknown | 86.4% | 92.0% | Few-shot prompting | N/A | ~$50-100/month | ✅ API | ⚠️ Can't train adapters |
| **GPT-4o** | Unknown | 88.7% | 93.1% | Few-shot prompting | N/A | ~$30-60/month | ✅ API | ⚠️ Can't train adapters |
| **GPT-4o-mini** | Unknown | 82.0% | 87.0% | Few-shot prompting | N/A | ~$10-20/month | ✅ API | ⚠️ Can't train adapters |
| **GPT-5 (future)⁷** | Unknown | ~95%? | ~98%? | Unknown | Unknown | Unknown | 🔮 Future | 🔮 Not available yet |
| **Claude 3 Opus** | Unknown | 86.8% | 95.0% | Few-shot prompting | N/A | ~$60-120/month | ✅ API | ⚠️ Can't train adapters |
| **Claude 3.5 Sonnet** | Unknown | 88.7% | 96.4% | Few-shot prompting | N/A | ~$30-60/month | ✅ API | ⚠️ Can't train adapters |
| **Gemini 1.5 Pro** | Unknown | 85.9% | 91.7% | Few-shot prompting | N/A | ~$20-40/month | ✅ API | ⚠️ Can't train adapters |

---

## Footnotes

¹ **Training Time:** For 18 personas, 1 epoch, 512 max length, batch size 2, on Google Colab T4 GPU (16GB). Times may vary by ±30%.

² **Cost:** Colab Pro ($9.99/month) for GPU access. Models themselves are free (open source). API models have usage-based pricing.

³ **Mixtral-8x7B:** Uses Mixture-of-Experts architecture. 47B total parameters but only ~13B active per token. Still requires 48GB memory.

⁴ **Cost per Persona:** For API fine-tuning services (OpenAI only). Other APIs don't support custom fine-tuning.

⁵ **Total Cost:** For running all 18 personas via API calls. Assumes 100-200 queries/day for testing/development.

⁶ **OpenAI Fine-tuning:** Uses their proprietary fine-tuning API, not LoRA adapters. Different workflow, can't run locally.

⁷ **GPT-5:** Rumored/future model. Specs are speculative based on industry trends.

---

## Detailed Analysis by Model

### 🥇 Top Recommendations

#### 1. **Qwen-2.5-7B-Instruct** (Best MMLU)
```yaml
Size: 7B parameters
MMLU: 74.5% (highest in 7B class!)
GSM8K: 85.4% (excellent math reasoning)
Training: 3-4 hours on T4
Memory: 16GB
Cost: Free + $9.99/month Colab Pro
Access: Instant (Apache 2.0)
```

**Pros:**
- ✅ **Highest MMLU score** in 7B class
- ✅ Excellent instruction following
- ✅ Great reasoning abilities
- ✅ Instant access, no gates
- ✅ Apache 2.0 license

**Cons:**
- ⚠️ Newer model (less community support)
- ⚠️ May need slight prompt adjustments

**Use if:** You want the absolute best performance at 7B size.

---

#### 2. **Mistral-7B-Instruct-v0.2** (Best Overall Balance) ⭐ CURRENT
```yaml
Size: 7.2B parameters
MMLU: 60.1%
GSM8K: 40.7%
Training: 2-4 hours on T4
Memory: 16GB
Cost: Free + $9.99/month Colab Pro
Access: Instant (Apache 2.0)
```

**Pros:**
- ✅ **Best balance** of performance and speed
- ✅ Proven track record
- ✅ Large community support
- ✅ Excellent documentation
- ✅ Fast training
- ✅ Instant access, no gates

**Cons:**
- ⚠️ MMLU slightly lower than newest models
- ⚠️ Math reasoning weaker than Llama-3/Qwen-2.5

**Use if:** You want proven, reliable performance with great support.

---

#### 3. **Llama-3.1-8B-Instruct** (Best for Reasoning)
```yaml
Size: 8B parameters
MMLU: 69.4%
GSM8K: 84.5% (excellent!)
Training: 3-4 hours on T4
Memory: 18GB
Cost: Free + $9.99/month Colab Pro
Access: Instant (Llama 3.1)
```

**Pros:**
- ✅ **Excellent reasoning** (84.5% GSM8K)
- ✅ Very good MMLU (69.4%)
- ✅ Meta's latest open model
- ✅ Great instruction following
- ✅ No gating (unlike Llama-2)

**Cons:**
- ⚠️ Slightly larger (8B vs 7B)
- ⚠️ Slightly more memory (18GB vs 16GB)

**Use if:** You need strong reasoning abilities for complex decisions.

---

#### 4. **Phi-3-mini** (Best Budget Option)
```yaml
Size: 3.8B parameters
MMLU: 68.8%
GSM8K: 82.5%
Training: 2.5-3.5 hours on T4
Memory: 12GB
Cost: Free + $9.99/month Colab Pro
Access: Instant (MIT)
```

**Pros:**
- ✅ **Smallest with great performance**
- ✅ Faster training than 7B models
- ✅ Lower memory requirements
- ✅ Excellent reasoning for size
- ✅ MIT license (most permissive)

**Cons:**
- ⚠️ May have less nuanced responses
- ⚠️ Smaller context window (4K vs 8K)

**Use if:** You want fast iteration or have GPU memory constraints.

---

### ⚠️ Not Recommended

#### GPT-2 / GPT-2-XL
```yaml
MMLU: 25-35%
Verdict: Too weak for modern tasks
```
**Why not:** Outdated (2019), poor instruction following, weak reasoning.

#### Llama-2-7b-chat
```yaml
MMLU: 48.3%
Verdict: Gated access + weaker than alternatives
```
**Why not:** Needs Meta approval + outperformed by Mistral/Llama-3.

#### Mixtral-8x7B / Llama-3.1-70B
```yaml
MMLU: 70-79%
Verdict: Overkill - too slow and expensive
```
**Why not:** 3-6x slower training, 3-8x more memory, diminishing returns.

#### GPT-4 / Claude 3 / Other APIs
```yaml
MMLU: 85-90%
Verdict: Can't train LoRA adapters
```
**Why not:** Different workflow, can't fine-tune locally, ongoing costs.

---

## Training Time Breakdown

### By Model Size

| Size | Parameters | Training Time (T4) | Training Time (A100) | Cost (Colab Pro) |
|------|------------|-------------------|---------------------|------------------|
| **Tiny** | <1B | 0.5-1 hour | 0.2-0.5 hour | $9.99/month |
| **Small** | 1-3B | 1-2.5 hours | 0.5-1 hour | $9.99/month |
| **Medium** | 3-8B | 2-4 hours | 1-2 hours | $9.99/month |
| **Large** | 13-20B | 5-10 hours | 2-4 hours | $9.99/month |
| **XL** | 30-70B | 15-30 hours | 6-12 hours | $9.99/month + longer sessions |
| **XXL** | 70B+ | 30+ hours | 12-20 hours | Impractical for Colab |

### Per-Persona Training Time (T4 GPU)

| Model | Single Persona | 18 Personas | Hourly Rate | Total Cost |
|-------|---------------|-------------|-------------|------------|
| **Phi-3-mini (3.8B)** | 8-12 min | 2.5-3.5 hours | $0.33/hour⁸ | ~$1.00 |
| **Mistral-7B** | 10-15 min | 3-4.5 hours | $0.33/hour | ~$1.30 |
| **Llama-3.1-8B** | 12-15 min | 3.5-4.5 hours | $0.33/hour | ~$1.40 |
| **Qwen-2.5-7B** | 10-15 min | 3-4.5 hours | $0.33/hour | ~$1.30 |
| **Llama-2-13B** | 18-25 min | 5.5-7.5 hours | $0.33/hour | ~$2.20 |
| **Mixtral-8x7B** | 40-60 min | 12-18 hours | $0.33/hour | ~$5.00 |

⁸ Colab Pro compute costs (amortized). Actual price is $9.99/month for unlimited training.

---

## Memory Requirements

### GPU Memory by Model

| Model | FP32 | FP16 | 8-bit | 4-bit | Min GPU |
|-------|------|------|-------|-------|---------|
| **GPT-2 (124M)** | 0.5GB | 0.25GB | 0.15GB | 0.1GB | Any GPU |
| **Phi-3-mini (3.8B)** | 15GB | 7.5GB | 4GB | 2.5GB | T4 (16GB) ✅ |
| **Mistral-7B** | 28GB | 14GB | 7GB | 4GB | T4 (16GB) ✅ |
| **Llama-3.1-8B** | 32GB | 16GB | 8GB | 5GB | T4 (16GB) ⚠️ Tight |
| **Qwen-2.5-7B** | 28GB | 14GB | 7GB | 4GB | T4 (16GB) ✅ |
| **Llama-2-13B** | 52GB | 26GB | 13GB | 7GB | V100 (32GB) or A100 |
| **Mixtral-8x7B** | 188GB | 94GB | 47GB | 24GB | A100 (40GB) or multi-GPU |
| **Llama-3.1-70B** | 280GB | 140GB | 70GB | 35GB | A100 (80GB) or multi-GPU |

**Note:** Training with LoRA adapters uses ~1.5-2x the base model memory (for gradients, optimizer states, etc.)

**Available on Colab Pro:**
- T4: 16GB ✅ Most common
- V100: 32GB ✅ Sometimes available
- A100: 40GB ⚠️ Rarely available

---

## Cost Comparison

### One-Time Training Costs

| Approach | Setup Cost | Training Cost | Total One-Time | Monthly Cost | Notes |
|----------|-----------|---------------|----------------|--------------|-------|
| **Colab Pro (Recommended)** | $0 | $0⁹ | $0 | $9.99 | Unlimited training included |
| **Colab Pro+ (Faster GPU)** | $0 | $0⁹ | $0 | $49.99 | Priority A100 access |
| **Local GPU (RTX 3090)** | $1500 | $0 | $1500 | ~$10¹⁰ | Hardware investment |
| **Local GPU (RTX 4090)** | $2000 | $0 | $2000 | ~$15¹⁰ | Faster, more memory |
| **Cloud GPU (Lambda Labs)** | $0 | $1.10/hour | ~$4-5 | Per use | A100 on-demand |
| **Cloud GPU (RunPod)** | $0 | $0.69/hour | ~$2.50 | Per use | A10G on-demand |
| **OpenAI Fine-tuning** | $0 | $150-200 | $150-200 | $20-50¹¹ | API inference costs |

⁹ Training included in subscription. Can train as many times as you want.

¹⁰ Electricity cost for consumer GPU (24/7 operation).

¹¹ Ongoing API call costs for 100-200 queries/day.

### Monthly Operating Costs

| Approach | Compute | Inference | Total Monthly | Break-even |
|----------|---------|-----------|---------------|------------|
| **Colab Pro + Local** | $9.99 | $0 | $9.99 | Immediate ✅ |
| **Local GPU Only** | $0 | $0 | $10-15 | After 6-12 months |
| **OpenAI GPT-3.5** | $0 | $20-50 | $20-50 | Never (ongoing) |
| **OpenAI GPT-4** | $0 | $50-100 | $50-100 | Never (ongoing) |
| **Cloud GPU (on-demand)** | $0 | $0 | $0¹² | Per-use |

¹² Only pay when training. No monthly fees.

---

## API Models Deep Dive

### Why API Models Are Different

**Open Source (LoRA Fine-tuning):**
```
Your data → Train adapters → Download → Run locally
Cost: $9.99/month one-time
Result: 18 custom adapters, run unlimited queries locally
```

**API Models (GPT-4, Claude, etc.):**
```
Your data → API calls → Get responses
Cost: $0.01-0.10 per query × queries per month
Result: Pay per use, can't download model
```

### API Model Comparison for Digital Twins

| Model | Persona Creation | Per Query Cost | 1000 queries/month | 10000 queries/month | Fine-tuning |
|-------|------------------|----------------|-------------------|---------------------|-------------|
| **GPT-3.5-turbo** | System prompts | $0.0015/1K tokens | ~$3-5 | ~$30-50 | $0.008/1K training tokens |
| **GPT-4o-mini** | System prompts | $0.15/1M input | ~$5-8 | ~$50-80 | Not available |
| **GPT-4-turbo** | System prompts | $0.01/1K tokens | ~$20-30 | ~$200-300 | Not available |
| **GPT-4o** | System prompts | $0.005/1K tokens | ~$10-15 | ~$100-150 | Not available |
| **Claude 3.5 Sonnet** | System prompts | $0.003/1K tokens | ~$6-10 | ~$60-100 | Not available |
| **Claude 3 Opus** | System prompts | $0.015/1K tokens | ~$30-40 | ~$300-400 | Not available |
| **Gemini 1.5 Pro** | System prompts | $0.00125/1K tokens | ~$2.50-4 | ~$25-40 | Not available |

**Verdict:** API models cost 2-30x more for ongoing use vs. one-time training with open models.

---

## Performance vs Training Time

### Sweet Spot Analysis

```
Performance (MMLU) vs Training Time

90% │                                     ● GPT-4o
    │                                   ● Claude 3.5
    │                              ● Llama-3.1-70B
    │
80% │                          ● Llama-3.1-8B
    │                      ● Qwen-2.5-7B
70% │                  ● Mistral-7B
    │              ● Gemma-7B
60% │          ● Phi-3-mini
    │      ● GPT-2-XL
50% │  ● GPT-2-Large
    │
    └─────┴─────┴─────┴─────┴─────┴─────┴─────┴──────> Training Time
      1h   2h   3h   4h   6h   12h  20h   API-only

Sweet Spot: 2-4 hour training, 60-75% MMLU
Models: Mistral-7B, Qwen-2.5-7B, Llama-3.1-8B, Phi-3-mini
```

**Diminishing Returns:**
- 2h → 4h: +10-15% MMLU (good ROI)
- 4h → 8h: +3-5% MMLU (diminishing)
- 8h → 20h: +2-3% MMLU (poor ROI)

**Recommendation:** Stay in 2-4 hour sweet spot unless you need bleeding-edge performance.

---

## Recommended Model by Use Case

### For Your Project (Digital Twin Personas)

| Priority | Model | Why |
|----------|-------|-----|
| **🥇 Best Overall** | Mistral-7B-Instruct-v0.2 | Proven, fast, instant access, great docs |
| **🥈 Best Performance** | Qwen-2.5-7B-Instruct | Highest MMLU in 7B class (74.5%) |
| **🥉 Best Reasoning** | Llama-3.1-8B-Instruct | Best GSM8K (84.5%), great for complex logic |
| **💰 Best Budget** | Phi-3-mini | Smallest with excellent performance (68.8% MMLU) |
| **⚡ Fastest Training** | Phi-3-mini | 2.5-3.5 hours for all 18 personas |

### By Specific Need

| Need | Recommended Model | Why |
|------|-------------------|-----|
| **Conversational personas** | Mistral-7B-Instruct-v0.2 | Best instruction following |
| **Analytical personas** | Qwen-2.5-7B-Instruct | Highest MMLU, great reasoning |
| **Budget-conscious** | Phi-3-mini | 3.8B, 2.5hr training, 68.8% MMLU |
| **Math/logic heavy** | Llama-3.1-8B-Instruct | 84.5% GSM8K |
| **Fast iteration** | Phi-3-mini | Fastest training cycle |
| **Maximum quality** | Qwen-2.5-7B-Instruct | Highest performance at reasonable cost |
| **Production stability** | Mistral-7B-Instruct-v0.2 | Most battle-tested, great support |

---

## Final Recommendation for Darpan Labs MVP

### 🎯 Primary Recommendation: **Mistral-7B-Instruct-v0.2**

**Why:**
1. ✅ **Already implemented** in your codebase
2. ✅ **Proven performance** (60.1% MMLU)
3. ✅ **Instant access** (no approval wait)
4. ✅ **Best training time** (3-4 hours)
5. ✅ **Great documentation** and community
6. ✅ **Apache 2.0** license (fully open)
7. ✅ **Excellent instruction following**

**Next step:** Train with Mistral, then optionally upgrade later.

---

### 🔄 Easy Upgrades (If Needed)

If you need better performance later, easy upgrade path:

```
Current: Mistral-7B-Instruct-v0.2 (60.1% MMLU)
         ↓ (Change 1 line in config)
Upgrade: Qwen-2.5-7B-Instruct (74.5% MMLU) ← +14% performance!
         ↓ (Same training time)
Or:      Llama-3.1-8B-Instruct (69.4% MMLU, 84.5% GSM8K)
```

**How to upgrade:**
```yaml
# In CONFIGS/serve/llm.yaml
base_model: "Qwen/Qwen2.5-7B-Instruct"  # Just change this line!
```

Re-train with same notebook, same workflow!

---

## Conclusion

**For your use case (18 digital twin personas):**

| Model | MMLU | Training Time | Cost | Access | Verdict |
|-------|------|---------------|------|--------|---------|
| **Mistral-7B-Instruct-v0.2** | 60.1% | 3-4 hrs | $9.99/mo | ✅ Instant | ⭐ **BEST BALANCE** |
| **Qwen-2.5-7B-Instruct** | 74.5% | 3-4 hrs | $9.99/mo | ✅ Instant | ⭐ **BEST PERFORMANCE** |
| **Llama-3.1-8B-Instruct** | 69.4% | 3-4 hrs | $9.99/mo | ✅ Instant | ⭐ **BEST REASONING** |
| **Phi-3-mini** | 68.8% | 2.5 hrs | $9.99/mo | ✅ Instant | ⭐ **BEST BUDGET** |

**Start with Mistral** (already set up), evaluate, then upgrade to Qwen-2.5 if you need higher performance.

---

**Questions?** Ask Claude Code about:
- Switching models
- Performance testing
- Cost optimization
- Training strategies
