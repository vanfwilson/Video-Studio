# OpenRouter Models Reference

**Last Updated:** 2026-01-22

This document lists recommended OpenRouter models for Video Studio AI tasks.

---

## Quick Reference

| Use Case | Recommended Model | Cost | Why |
|----------|-------------------|------|-----|
| SWOT Analysis | `deepseek/deepseek-chat` | $0.14/1M | Accurate, cheap, doesn't hallucinate |
| Source Verification | `deepseek/deepseek-chat` | $0.14/1M | Grounded, won't make up URLs |
| Complex Reasoning | `deepseek/deepseek-r1` | $0.55/1M | Shows thinking process |
| Customer-Facing | `anthropic/claude-3-haiku` | $0.25/1M | Safe, won't say anything harmful |
| Fast Tasks | `google/gemini-flash-1.5` | $0.075/1M | Very fast response |
| Free Option | `meta-llama/llama-3.3-70b-instruct` | FREE | Good all-around |

---

## Models by Tier

### FREE Tier

These models have free tiers on OpenRouter (subject to rate limits):

| Model ID | Name | Use Case |
|----------|------|----------|
| `meta-llama/llama-3.3-70b-instruct` | Llama 3.3 70B | General purpose, coding, analysis |
| `qwen/qwen-2.5-72b-instruct` | Qwen 2.5 72B | Verification, multilingual |
| `google/gemma-2-27b-it` | Gemma 2 27B | Simple tasks, summarization |

### Budget Tier (Under $0.50/1M tokens)

Best value for money:

| Model ID | Name | Cost | Use Case |
|----------|------|------|----------|
| `deepseek/deepseek-chat` | **DeepSeek V3** | $0.14/$0.28 | **RECOMMENDED** - Best value, accurate |
| `google/gemini-flash-1.5` | Gemini Flash 1.5 | $0.075/$0.30 | Very fast, good for quick tasks |
| `anthropic/claude-3-haiku` | Claude 3 Haiku | $0.25/$1.25 | Safe, won't hallucinate |
| `mistralai/mistral-small-24b-instruct-2501` | Mistral Small | $0.10/$0.30 | JSON/structured output |
| `openai/gpt-4o-mini` | GPT-4o Mini | $0.15/$0.60 | Reliable, well-tested |

### Mid Tier ($0.50-$5/1M tokens)

For more complex tasks:

| Model ID | Name | Cost | Use Case |
|----------|------|------|----------|
| `deepseek/deepseek-r1` | DeepSeek R1 | $0.55/$2.19 | Deep reasoning, shows thinking |
| `anthropic/claude-3.5-sonnet` | Claude 3.5 Sonnet | $3/$15 | Best quality for complex tasks |
| `openai/gpt-4o` | GPT-4o | $2.50/$10 | Multimodal, reliable |

### Premium Tier ($5+/1M tokens)

For critical tasks requiring highest quality:

| Model ID | Name | Cost | Use Case |
|----------|------|------|----------|
| `anthropic/claude-3.5-opus` | Claude 3.5 Opus | $15/$75 | Highest quality analysis |

---

## Model Selection Guide

### For Source Verification (SWOT, Research)

**Best:** `deepseek/deepseek-chat` (DeepSeek V3)
- Doesn't hallucinate URLs
- Admits when it doesn't know
- Very cost-effective

**Free Alternative:** `qwen/qwen-2.5-72b-instruct`
- Good at admitting uncertainty
- Won't make things up

### For Customer-Facing Output

**Best:** `anthropic/claude-3-haiku`
- Won't say harmful things
- Polite and professional
- Admits limitations

### For Complex Business Analysis

**Best:** `deepseek/deepseek-r1`
- Shows reasoning process
- Good for strategy work
- Explains conclusions

### For Speed-Critical Tasks

**Best:** `google/gemini-flash-1.5`
- Very fast responses
- Good enough quality
- Extremely cheap

---

## Environment Configuration

Set in `.env`:

```env
# Your OpenRouter API key
OPENROUTER_API_KEY=sk-or-v1-xxxxx

# Model for SWOT analysis (default: DeepSeek V3)
OPENROUTER_SWOT_MODEL=deepseek/deepseek-chat
```

### Per-Company Model Preferences

Companies can have custom AI preferences stored in their profile:

```json
{
  "swotModel": "deepseek/deepseek-chat",
  "preferredTier": "budget",
  "customModels": []
}
```

---

## API Endpoint

Get available models:
```
GET /api/ai/models
```

Returns:
```json
{
  "currentModel": "deepseek/deepseek-chat",
  "models": {
    "free": [...],
    "budget": [...],
    "midTier": [...],
    "premium": [...]
  }
}
```

---

## Cost Calculation

OpenRouter charges per token (input/output):

| Task | ~Tokens | DeepSeek V3 Cost | GPT-4o Cost |
|------|---------|------------------|-------------|
| SWOT Analysis | 2K/2K | $0.0008 | $0.025 |
| 100 SWOT | 200K/200K | $0.08 | $2.50 |
| 1000 SWOT | 2M/2M | $0.84 | $25.00 |

**DeepSeek V3 is ~30x cheaper than GPT-4o for the same quality.**

---

## Getting an API Key

1. Go to https://openrouter.ai
2. Sign in with Google/GitHub
3. Go to Keys: https://openrouter.ai/keys
4. Create a new key
5. Add credits (free tier available)
6. Copy key to your `.env` file
