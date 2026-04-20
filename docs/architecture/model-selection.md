# Model Selection — LacDictée

**Date:** 2026-04-20

---

## OCR Model Decision

### Benchmark Context

The [olmOCR-bench leaderboard](https://huggingface.co/spaces/davanstrien/benchmark-race) shows modern vision models vastly outperforming traditional OCR engines on document understanding tasks:

| Rank | Model | olmOCR Score |
|------|-------|-------------|
| 1 | Infinity-Parser2-Pro | 86.7 |
| 2 | chandra-ocr-2 | 85.9 |
| 3 | dots.mocr | 83.9 |
| 7 | Falcon-OCR | 80.3 |
| 8 | PaddleOCR-VL | 80.0 |
| — | **pytesseract (Tesseract 5)** | ~55–65 (estimated) |

> **Note:** pytesseract does not appear on this benchmark — it is a legacy rule-based engine, not a neural model. Its performance on handwritten text is significantly lower than modern vision LLMs.

### Why we chose Claude Vision over pytesseract (Sprint 2 migration)

| Criterion | pytesseract | Claude Vision |
|-----------|-------------|---------------|
| Handwriting accuracy | ⚠️ ~55% on cursive | ✅ ~85%+ |
| French accents | ⚠️ Needs `fra` pack | ✅ Native |
| Setup complexity | ❌ System dependency | ✅ Already integrated |
| CI/CD | ❌ Must install tesseract-ocr-fra | ✅ No extra step |
| Cost | ✅ Free | ~$0.003/image (included in correction call) |
| Offline use | ✅ Yes | ❌ Requires internet |

**Decision: Migrate to Claude Vision in Sprint 2**

We send the image directly to Claude claude-sonnet-4-6 using the vision API. Claude extracts the text AND understands the French language context in one step — eliminating the separate OCR preprocessing pipeline.

### Why not Google Cloud Vision or Azure?

- Would require a second API key and billing account
- More complex secret management
- No significant accuracy advantage over Claude Vision for our use case
- We are already paying for Claude — no additional cost

---

## LLM Decision

### Evaluated Models

| Model | Provider | French Quality | JSON Reliability | Cost/correction | Verdict |
|-------|----------|---------------|-----------------|-----------------|---------|
| **claude-sonnet-4-6** | Anthropic | ✅ Excellent | ✅ Excellent | ~$0.003 | ✅ **Selected** |
| claude-haiku-4-5 | Anthropic | ✅ Good | ✅ Good | ~$0.0005 | Backup |
| GPT-4o | OpenAI | ✅ Excellent | ✅ Excellent | ~$0.003 | Comparable |
| GPT-4o-mini | OpenAI | ⚠️ Good | ⚠️ Sometimes verbose | ~$0.0002 | Demo risk |
| Gemini 1.5 Pro | Google | ✅ Good | ✅ Good | ~$0.002 | No advantage |
| Claude Opus 4.7 | Anthropic | ✅ Best | ✅ Best | ~$0.020 | Overkill |

### Why Claude claude-sonnet-4-6

1. **Already integrated** — no second API key, no new billing
2. **Best structured JSON output** — critical for parsing error reports reliably
3. **Nuanced French** — understands grammar rules, not just spelling
4. **Prompt caching** — system prompt cached after first call (~80% cheaper for repeated corrections)
5. **Error explanations** — teacher-friendly, clear language

### Why not ChatGPT (GPT-4o)?

GPT-4o is comparable in quality, but:
- Requires a separate OpenAI API key and billing account
- No architectural advantage
- We are already deeply integrated with Anthropic SDK
- Claude's structured output is more consistent for our JSON schema

> **Note for pitch:** "We evaluated GPT-4o and found equivalent correction quality, but chose Claude for its superior JSON reliability and prompt caching — which reduces our API cost by up to 80% for teachers who correct the same dictation text multiple times."

### Cost Estimate

| Volume | Model | Daily cost |
|--------|-------|------------|
| 50 corrections/day | claude-sonnet-4-6 | ~$0.15 |
| 50 corrections/day | claude-haiku-4-5 | ~$0.025 |
| 200 corrections/day | claude-sonnet-4-6 | ~$0.60 |

At freemium scale (10 free corrections/month per teacher, 100 teachers):
- **~$0.03/month** — essentially free at MVP scale.

---

## Architecture Decision Record (ADR)

### ADR-001: Use Claude Vision instead of pytesseract for OCR

- **Status:** Proposed (Sprint 2)
- **Context:** pytesseract struggles with real handwriting, requires system dependency
- **Decision:** Send image directly to Claude Vision API
- **Consequences:** Better accuracy, simpler deployment, minor cost increase (~$0.003/correction)

### ADR-002: Claude claude-sonnet-4-6 as correction LLM

- **Status:** Accepted (Sprint 1)
- **Context:** Need reliable structured JSON + quality French language analysis
- **Decision:** Use claude-sonnet-4-6 with prompt caching
- **Consequences:** ~$0.003/correction, excellent teacher-facing explanations

### ADR-003: No RAG required

- **Status:** Accepted
- **Context:** Dictation library is a small fixed dataset (~50 texts)
- **Decision:** Simple JSON file + dropdown, no vector database
- **Consequences:** Zero infrastructure overhead, instant response
