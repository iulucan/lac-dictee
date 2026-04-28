<p align="center">
  <img src="docs/logo/Logo_LacDictee_transparent.png" width="200" alt="LacDictée Logo"/>
</p>

<h1 align="center">LacDictée</h1>
<p align="center"><em>AI-powered French dictation correction for teachers</em></p>

<p align="center">
  <a href="https://github.com/codibrahim/lac-dictee/actions/workflows/ci.yml">
    <img src="https://github.com/codibrahim/lac-dictee/actions/workflows/ci.yml/badge.svg" alt="CI"/>
  </a>
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python"/>
  <img src="https://img.shields.io/badge/streamlit-1.44-red.svg" alt="Streamlit"/>
  <a href="https://github.com/codibrahim/lac-dictee/wiki">
    <img src="https://img.shields.io/badge/docs-wiki-8b5cf6.svg" alt="Wiki"/>
  </a>
</p>

---

## The Problem

French dictation (*dictée*) is a core exercise in French language education. Teachers spend **3–5 hours per week** manually correcting handwritten dictations — checking spelling, grammar, accents, and punctuation word by word. For a class of 25 students, this is unsustainable.

**LacDictée eliminates that manual work entirely.**

---

## How It Works

```
Teacher uploads photo of student's handwriting
                ↓
    OCR — Claude Vision / Groq Vision / Tesseract
    extracts the written text
                ↓
    Teacher provides the correct reference text
                ↓
    AI compares both texts
    identifies every error with explanation
                ↓
    Instant error report:
    score · error list · type · explanation · PDF download
                ↓
    📊 Class Analytics Dashboard
    score distribution · error heatmap · exercise comparison
```

---

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| UI | Streamlit 1.44 | Multi-page app |
| OCR | Claude Vision (haiku-4-5) | Primary — best for handwriting |
| OCR fallback 1 | Groq Vision (llama-4-scout-17b) | Free, uses GROQ_API_KEY |
| OCR fallback 2 | Infinity-Parser-7B (HuggingFace) | Free, no key needed |
| OCR fallback 3 | Tesseract | Last resort, offline |
| AI Correction | Claude (sonnet-4-6) | Primary — best quality |
| AI fallback | Groq (llama-3.3-70b) | Free tier |
| PDF Export | fpdf2 | Downloadable error reports |
| Analytics | Plotly | Teacher dashboard |
| Storage | SQLite | Correction history |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/codibrahim/lac-dictee.git
cd lac-dictee

# 2. Create virtualenv & install
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Add your ANTHROPIC_API_KEY and GROQ_API_KEY to .env

# 4. (Optional) Pre-warm OCR engine
python3 warmup.py

# 5. Launch
streamlit run app.py
```

---

## Project Structure

```
lac-dictee/
├── app.py                    # Main Streamlit app
├── pages/
│   └── analytics.py          # Teacher analytics dashboard
├── src/
│   ├── ocr.py                # OCR pipeline (Claude → Groq → Infinity → Tesseract)
│   ├── correction.py         # AI correction (Claude → Groq)
│   ├── pdf_export.py         # PDF report generation
│   ├── storage.py            # SQLite persistence
│   └── annotation.py         # Annotated image overlay
├── batch_correct.py          # Process a single student file
├── batch_tv5monde.py         # Batch: 8 Champignons + 8 Renaissance students
├── warmup.py                 # Pre-warm Infinity-Parser HuggingFace Space
├── docs/
│   ├── logo/                 # Project logos (transparent PNG)
│   ├── presentation/         # Lean Canvas, Empathy Map, SWOT, DoD
│   ├── research/             # Model selection diagrams
│   ├── maps/                 # Switzerland maps & animations
│   └── architecture/         # HLD diagrams
├── tests/
│   └── test_accuracy.py      # End-to-end accuracy tests
├── data/
│   └── testing/              # Test dictation samples
├── .env.example
├── requirements.txt
└── README.md
```

---

## Wiki

Full project documentation — sprints, deliverables, business model, architecture diagrams, demo guide:

**[→ github.com/codibrahim/lac-dictee/wiki](https://github.com/codibrahim/lac-dictee/wiki)**

---

## License

MIT
