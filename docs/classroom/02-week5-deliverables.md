# Week 5 Deliverables — Architecture Defense

**Due:** April 27, 2026
**Presentation:** Architecture Defense to Board of Advisors (peers + coaches)

---

## Deliverable 1: Problem Statement

**Acceptance Criteria:**
- [x] Names a specific user (French language teachers)
- [x] Quantifies the pain (3–5 hours/week, ~45 min/correction)
- [x] Explains why existing solutions fail
- [x] Includes market evidence (Swiss FSO: ~18,600 teachers in Romandy)

**Delivered in:** Wiki → [Deliverables](https://github.com/codibrahim/lac-dictee/wiki/Deliverables)

---

## Deliverable 2: Lean Canvas

**Acceptance Criteria:**
- [x] Problem block: specific, measurable
- [x] Customer segment: named and sized
- [x] Unique Value Proposition: one clear sentence
- [x] Revenue model: defined
- [x] Unfair advantage: identified

**Delivered in:** Wiki → [Deliverables](https://github.com/codibrahim/lac-dictee/wiki/Deliverables)

---

## Deliverable 3: Technical Blueprint

**Acceptance Criteria:**
- [x] System architecture diagram (data flow: upload → OCR → AI → report)
- [x] Tech stack with rationale for each choice
- [x] Model selection comparison table
- [x] Sprint 2+ upgrade path documented
- [x] Security model described

**Delivered in:**
- Wiki → [Architecture](https://github.com/codibrahim/lac-dictee/wiki/Architecture)
- Wiki → [Model Selection](https://github.com/codibrahim/lac-dictee/wiki/Model-Selection)
- Interactive diagram: [HLD Visual](https://codibrahim.github.io/lac-dictee/docs/architecture/hld-visual.html)

---

## Deliverable 4: Mockup / UI Preview

**Acceptance Criteria:**
- [x] Shows main user flow (upload → correction → report)
- [x] Non-technical teacher can understand it without explanation

**Delivered in:** Wiki → [Mockup](https://github.com/codibrahim/lac-dictee/wiki/Mockup)

> Note: LacDictée has a working MVP — the mockup IS the actual app running on `streamlit run app.py`.

---

## Deliverable 5: Pitch Deck (3–5 slides)

**Acceptance Criteria:**
- [ ] Slide 1: Problem (1 punchy stat)
- [ ] Slide 2: Solution (how it works in 3 steps)
- [ ] Slide 3: Tech Stack (diagram)
- [ ] Slide 4: Business Case (Lean Canvas summary)
- [ ] Slide 5: Roadmap (Sprints 1–3)

**Status:** ⏳ In preparation — due Apr 27

---

## Architecture Defense Prep — Key Questions

The Board of Advisors will ask:

| Question | Answer |
|----------|--------|
| Why Streamlit? | Pure Python — zero frontend code needed for MVP; teachers use it in browser |
| Why pytesseract? | Free, offline, French (`fra`) lang pack; ~60% accuracy acceptable for MVP; Claude Vision upgrade in Sprint 2 |
| Why Claude over GPT-4o? | Already integrated; consistent JSON output; prompt caching reduces cost ~60% |
| Why SQLite over Postgres? | Single-user MVP; zero infra overhead; easy migration path if needed |
| How do you handle bad OCR? | Editable text field — teacher can correct before sending to Claude |
| Security? | `.env` for all keys; images not persisted; student names optional |
| What if Claude API is down? | Free fallback chain: Groq → Gemma-2-9B → graceful error |
