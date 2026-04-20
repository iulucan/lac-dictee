# Sprint 1 — MVP

**Dates:** April 20 – April 27, 2026
**Goal:** A working end-to-end MVP: teacher uploads a photo → OCR extracts text → Claude corrects it → error report displayed.

---

## Sprint Goal (One Sentence)

> By April 27, a teacher can upload a photo of a handwritten French dictation and receive a structured error report with a score.

---

## Issues (GitHub)

| # | Title | Status |
|---|-------|--------|
| [#2](https://github.com/codibrahim/lac-dictee/issues/2) | Project setup: Python environment + dependencies | ✅ Done |
| [#3](https://github.com/codibrahim/lac-dictee/issues/3) | OCR: Image upload and text extraction | 🔄 In Progress |
| [#4](https://github.com/codibrahim/lac-dictee/issues/4) | AI correction: Claude compares OCR text vs correct text | 🔄 In Progress |
| [#5](https://github.com/codibrahim/lac-dictee/issues/5) | UI: Error report display | ⏳ To Do |

---

## Definition of Done for Sprint 1

- [ ] `streamlit run app.py` launches without errors
- [ ] Upload a JPG photo → OCR text appears in UI
- [ ] Enter correct text → Claude returns structured JSON error report
- [ ] Error report shows: score, error list with type + explanation
- [ ] All credentials loaded from `.env`
- [ ] Tests pass (`pytest tests/`)
- [ ] CI green on GitHub Actions
- [ ] PR merged to `main`

---

## Daily Notes

### Monday Apr 20
- Project kick-off
- Repo created, README written, GitHub Project board set up
- Classroom docs saved to `docs/classroom/`
- Agent `lac-dictee.md` created

### Tuesday Apr 21 *(planned)*
- Start OCR implementation (`src/ocr.py`)
- Test with sample handwritten photo

### Wednesday Apr 22 *(planned)*
- Implement Claude correction (`src/correction.py`)
- Unit tests with mocked client

### Thursday Apr 23 *(planned)*
- Wire up Streamlit UI (`app.py`)
- End-to-end test: photo → report

### Friday Apr 24 *(planned)*
- Bug fixes, polish
- **Architecture Defense presentation** (Lean Canvas + Blueprint + Pitch)
- PR to main

---

## Retrospective *(to be filled Apr 27)*

**What went well:**

**What was hard:**

**What to do differently in Sprint 2:**
