# Business Model — LacDictée

> AI-powered French dictation correction for teachers.
> Last updated: 2026-04-21

---

## Business Overview

### 1. Problem / Solution / Customer

**Customer:** Primary and secondary school teachers in French-speaking Switzerland (Romandy) and France who assign regular dictation exercises.

**Problem:**
- A teacher with 25 students spends **~45 minutes** correcting a single dictation manually
- A class of 25 students × 2 dictations/month = **~6 hours/month** lost to manual correction
- Feedback is delayed — students often receive corrections days later, reducing learning impact

**Solution:** LacDictée reduces correction time from 45 minutes to **under 2 minutes** per class:
1. Teacher photographs student's handwritten dictation
2. OCR reads the handwriting automatically
3. Claude AI compares with the reference text and generates a structured error report (score, error type breakdown, word-by-word feedback)

**Impact per teacher per year:**
- Time saved: ~70 hours/year
- Faster feedback loop: same-day correction possible

---

### 2. Market Opportunity

**Primary market — French-speaking Switzerland (Romandy):**

| Segment | Count | Source |
|---------|-------|--------|
| Primary school teachers (Romandy) | ~12,000 | Swiss Federal Statistical Office |
| Secondary school teachers (Romandy) | ~8,000 | Swiss Federal Statistical Office |
| **Total Romandy target** | **~20,000 teachers** | |

**Secondary market — France:**

| Segment | Count |
|---------|-------|
| Primary school teachers | ~320,000 |
| Secondary school teachers | ~390,000 |
| **Total France target** | **~710,000 teachers** |

**Market sizing (Romandy only — conservative):**
- Addressable: 20,000 teachers
- Realistically reachable (5% adoption): **1,000 teachers**
- At CHF 9/month per teacher: **CHF 9,000/month recurring revenue** at scale

---

### 3. Go-To-Market Strategy

**Phase 1 — Pilot (May–August 2026):**
- 5 pilot schools in the Lausanne–Vaud region (via Powercoders network)
- Free access in exchange for structured feedback
- Target: **50 active teachers**, **500 dictations corrected**

**Phase 2 — Referral Growth (September–December 2026):**
- Teachers share tool with colleagues in the same school
- 1 school = ~40 teachers on average → viral coefficient within institutions
- Target: **10 schools**, **400 teachers**

**Phase 3 — Institutional Sales (2027):**
- Direct outreach to cantonal education departments (DFJC in Vaud)
- School subscription model — IT buys for the whole school
- Target: **50 schools**, **2,000 teachers**

**Key channels:**
| Channel | Estimated reach | Cost |
|---------|----------------|------|
| Powercoders network | 5–10 schools | CHF 0 |
| Teacher Facebook groups (Romandy) | 5,000+ teachers | CHF 0 |
| Cantonal education events | 200+ decision-makers | Low |
| Word of mouth (teacher–teacher) | High multiplier | CHF 0 |

---

### 4. Revenue Model

**Freemium structure:**

| Tier | Price | Features |
|------|-------|----------|
| Free | CHF 0/month | 10 corrections/month, 1 teacher |
| Teacher Pro | CHF 9/month | Unlimited corrections, PDF export, history |
| School | CHF 149/month | Up to 50 teachers, admin dashboard, priority support |

**Revenue projections (conservative):**

| Timeline | Active users | MRR |
|----------|-------------|-----|
| Month 6 (Oct 2026) | 100 free, 20 Pro | CHF 180 |
| Month 12 (Apr 2027) | 500 free, 100 Pro, 3 schools | CHF 1,347 |
| Month 24 (Apr 2028) | 2,000 free, 400 Pro, 20 schools | CHF 6,580 |

**Unit economics:**
- Claude API cost per correction: ~CHF 0.02–0.05
- Gross margin at Pro tier: ~94%
- Customer acquisition cost (word of mouth): ~CHF 0

---

### 5. Organization

**Current structure — Solo founder (Powercoders Sprint):**

| Role | Person | Commitment |
|------|--------|-----------|
| Product / Dev / Design | Ibrahim Ulucan | Full-time (bootcamp) |
| Mentor / Advisor | Powercoders coaches | Weekly |

**Post-bootcamp structure (planned):**

| Role | Skills needed |
|------|--------------|
| Technical co-founder | Backend / DevOps |
| Education sales | Relationship with schools/cantons |
| UX designer | Teacher-facing interface |

**Key partnerships needed:**
- Swiss cantonal education departments (DFJC, DIP Geneva)
- Tesseract/OCR improvement partners
- Anthropic startup program (API cost reduction)

---

## SWOT Analysis

Scores: 1 (weak) → 5 (strong)

### Strengths

| # | Strength | Score | Evidence |
|---|----------|-------|---------|
| S1 | Solves a real, painful daily problem | 5 | Teachers spend 45 min/class on manual correction |
| S2 | No comparable tool exists in French | 4 | Market research found no direct competitor |
| S3 | Claude AI delivers explanation quality unmatched by rule-based tools | 5 | Error types + per-word explanation |
| S4 | Extremely low CAC (word-of-mouth channel) | 4 | Teacher communities are tight-knit |
| S5 | 94%+ gross margin | 4 | API cost < CHF 0.05 per correction |

**Strength score: 22 / 25**

---

### Weaknesses

| # | Weakness | Score | Mitigation |
|---|----------|-------|-----------|
| W1 | OCR accuracy depends on image quality | 3 | Preprocessing + user guidance ("good lighting") |
| W2 | French-only at launch | 2 | Narrows market; multilingual roadmap planned |
| W3 | Solo founder — execution risk | 3 | Powercoders mentorship + structured sprints |
| W4 | No brand recognition yet | 2 | Pilot schools build credibility |
| W5 | API dependency on Anthropic pricing | 3 | Prompt caching reduces cost by ~60% |

**Weakness score: 13 / 25** *(lower = less vulnerable)*

---

### Opportunities

| # | Opportunity | Score | Evidence |
|---|-------------|-------|---------|
| O1 | Digital transformation push in Swiss schools post-2023 | 5 | Federal digitalization strategy |
| O2 | 710,000 French teachers in France — large expansion market | 5 | French Ministry of Education data |
| O3 | Anthropic startup credits program | 4 | Up to $5,000 API credits available |
| O4 | Integration with school management platforms (EduLog, etc.) | 3 | API-first architecture makes this feasible |
| O5 | Government procurement cycles favor Swiss-made edtech | 4 | Swiss data residency preference |

**Opportunity score: 21 / 25**

---

### Threats

| # | Threat | Score | Response |
|---|--------|-------|---------|
| T1 | Large edtech (Google, Microsoft) adds dictation correction | 3 | Speed to market + French specialization |
| T2 | School IT procurement is slow (6–18 months) | 4 | Teacher-direct sales bypass IT |
| T3 | Teacher resistance to AI in grading | 3 | Position as assistant, not replacement |
| T4 | GDPR / Swiss data privacy for student work | 4 | No PII stored, images deleted post-correction |
| T5 | API cost increases from Anthropic | 2 | Prompt caching + volume discounts |

**Threat score: 16 / 25** *(lower = less exposed)*

---

### SWOT Summary Matrix

|  | Positive | Negative |
|--|---------|---------|
| **Internal** | Strengths: **22/25** | Weaknesses: **13/25** |
| **External** | Opportunities: **21/25** | Threats: **16/25** |

**Overall position: Strong** — high strengths + high opportunities, manageable weaknesses and threats.
