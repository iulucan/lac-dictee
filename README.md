# LacDictée 🇫🇷

> AI-powered French dictation correction for teachers. Upload a photo → instant error analysis.

[![CI](https://github.com/codibrahim/lac-dictee/actions/workflows/ci.yml/badge.svg)](https://github.com/codibrahim/lac-dictee/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.45-red.svg)](https://streamlit.io/)
[![HLD](https://img.shields.io/badge/architecture-HLD%20diagram-8b5cf6.svg)](https://codibrahim.github.io/lac-dictee/docs/architecture/hld-visual.html)

---

## The Problem

French dictation (*dictée*) is a core exercise in French language education. Teachers spend **3–5 hours per week** manually correcting handwritten dictations — checking spelling, grammar, accents, and punctuation word by word. For a class of 25 students, this is unsustainable.

**LacDictée eliminates that manual work entirely.**

---

## How It Works

```
Teacher uploads photo of student's handwriting
                ↓
    OCR (pytesseract, French lang pack)
    extracts the written text
                ↓
    Teacher confirms / pastes correct text
                ↓
    Claude AI compares both texts
    identifies every error with explanation
                ↓
    Instant error report:
    score · error list · type · explanation
```

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| UI | Streamlit | Pure Python — zero frontend code for MVP |
| OCR | pytesseract + Pillow | Open source, offline, French (`fra`) support |
| AI | Claude API (`claude-sonnet-4-6`) | Best-in-class text analysis + explanations |
| PDF Export | fpdf2 | Lightweight, pure Python *(Sprint 2)* |
| Storage | JSON → SQLite | Simple start, easy to migrate *(Sprint 2)* |

---

## Quick Start

### Prerequisites

```bash
# macOS
brew install tesseract tesseract-lang

# Ubuntu / Debian
sudo apt install tesseract-ocr tesseract-ocr-fra
```

### Run

```bash
# 1. Clone
git clone https://github.com/codibrahim/lac-dictee.git
cd lac-dictee

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Open .env and add your ANTHROPIC_API_KEY

# 4. Launch
streamlit run app.py
```

---

## Project Structure

```
lac-dictee/
├── app.py                    # Streamlit UI — main entry point
├── src/
│   ├── ocr.py                # Image preprocessing + text extraction (pytesseract)
│   └── correction.py         # Claude AI — text comparison + structured error report
├── tests/
│   └── test_correction.py    # Unit tests (mocked Claude client)
├── data/
│   └── samples/              # Sample French dictation texts (A1–B2)
├── docs/
│   ├── classroom/            # Powercoders assignment docs (Weeks 5–7)
│   ├── deliverables/         # Submitted deliverables (problem statement, DoD, etc.)
│   └── sprints/              # Sprint planning and retrospectives
├── .github/
│   └── workflows/ci.yml      # GitHub Actions CI (pytest on push/PR)
├── .env.example              # Environment variable template
├── requirements.txt
└── README.md
```

---

## Architecture

**[→ View Interactive HLD Diagram](https://codibrahim.github.io/lac-dictee/docs/architecture/hld-visual.html)**

Full system architecture with flow diagrams, model selection rationale, sprint roadmap, and security model.

---

## Definition of Done

- [ ] LLM performs dictation correction that standard code cannot replicate
- [ ] Persistence: correction sessions saved to JSON / SQLite
- [ ] Security: all credentials in `.env`, never hardcoded
- [ ] Documentation: README with setup + usage instructions
- [ ] Stability: Happy Path works 100% during live demo
- [ ] Error report shows: score, error list, type, explanation
- [ ] French accent handling: é, è, ê, à, â, ù, û, ü, ï, ô, œ, æ, ç

---

## Wiki

Full project documentation — sprints, deliverables, business model, architecture diagrams:

**[→ github.com/codibrahim/lac-dictee/wiki](https://github.com/codibrahim/lac-dictee/wiki)**

---

## License

MIT
