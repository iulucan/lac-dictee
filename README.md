<p align="center">
  <img src="docs/logo/Logo_LacDictee_transparent.png" width="300" alt="LacDictée Logo"/>
</p>
<h1 align="center">LacDictée</h1>
<p align="center"><em>AI-powered French dictation correction for teachers</em></p>
<p align="center">
  <a href="https://lac-dictee.streamlit.app">
    <img src="https://img.shields.io/badge/🚀_Live_Demo-lac--dictee.streamlit.app-ff4b4b?style=for-the-badge" alt="Live Demo"/>
  </a>
</p>
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

## The Problem

French dictation (*dictée*) is a core exercise in French language education. Teachers spend **3–5 hours per week** manually correcting handwritten dictations — checking spelling, grammar, accents, and punctuation word by word. For a class of 25 students, this is unsustainable.

**LacDictée eliminates that manual work entirely.**

---

## Try It Now

### Web — no installation needed

Open **[lac-dictee.streamlit.app](https://lac-dictee.streamlit.app)** in any browser.

### Mobile — works on any smartphone

1. Open **[lac-dictee.streamlit.app](https://lac-dictee.streamlit.app)** on your phone
2. Tap the file uploader → your camera opens directly
3. Photograph the student's handwritten dictation
4. Get an instant correction report

**Add to home screen (optional):**
- **iPhone:** Share → "Add to Home Screen"
- **Android:** Browser menu → "Add to Home Screen"

The app icon appears on your home screen and opens full-screen, just like a native app.

---

## How It Works

```
Teacher photographs student's handwriting (phone or scanner)
                ↓
    OCR — Claude Vision / Groq Vision / Tesseract
    extracts the handwritten text
                ↓
    Teacher provides the correct reference text
                ↓
    AI compares both texts word by word
    identifies every error with type + explanation
                ↓
    Instant error report:
    score · annotated text · annotated image · PDF download
                ↓
    📊 Class Analytics Dashboard
    score distribution · error heatmap · exercise comparison
```

---

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| UI | Streamlit 1.44 | Multi-page, mobile-responsive |
| Deployment | Streamlit Community Cloud | Live at lac-dictee.streamlit.app |
| OCR primary | Claude Vision (haiku-4-5) | Best for handwriting |
| OCR fallback 1 | Groq Vision (llama-4-scout-17b) | Free, fast |
| OCR fallback 2 | Tesseract | Offline, last resort |
| AI Correction primary | Claude (sonnet-4-6) | Best quality |
| AI Correction fallback | Groq (llama-3.3-70b) | Free tier |
| AI Correction fallback 2 | Gemma-2-9B (HuggingFace) | No key needed |
| PDF Export | fpdf2 | Downloadable error reports |
| Analytics | Plotly | Teacher dashboard |
| Storage | SQLite | Correction history |

---

## Run Locally

```bash
# 1. Clone
git clone https://github.com/codibrahim/lac-dictee.git
cd lac-dictee

# 2. Create virtualenv & install
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Install Tesseract (macOS)
brew install tesseract tesseract-lang

# 4. Configure environment
cp .env.example .env
# Add GROQ_API_KEY (required) and ANTHROPIC_API_KEY (optional) to .env

# 5. Check engines are ready
python3 warmup.py

# 6. Launch
streamlit run app.py
```

App opens at **http://localhost:8501**

---

## Project Structure

```
lac-dictee/
├── app.py                    # Main Streamlit app (mobile-responsive)
├── pages/
│   └── analytics.py          # Teacher analytics dashboard
├── src/
│   ├── ocr.py                # OCR pipeline (Claude → Groq → Tesseract)
│   ├── correction.py         # AI correction with resilient provider fallback
│   ├── pdf_export.py         # PDF report generation
│   ├── storage.py            # SQLite persistence
│   └── annotation.py         # Annotated image + BB overlay
├── run_all_datasets.py       # Batch: process all datasets → PDFs + JSON summary
├── warmup.py                 # Pre-demo engine check
├── packages.txt              # System dependencies for Streamlit Cloud
├── docs/
│   ├── logo/
│   ├── presentation/
│   └── architecture/
├── tests/
├── data/
│   └── testing/
├── .env.example
├── requirements.txt
└── README.md
```

---

## Wiki

Full project documentation — sprints, architecture, business model, demo guide:

**[→ github.com/codibrahim/lac-dictee/wiki](https://github.com/codibrahim/lac-dictee/wiki)**

---

## License

MIT
