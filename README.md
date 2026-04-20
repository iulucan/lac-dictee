# LacDictée 🇫🇷

AI-powered French dictation correction tool for teachers.

Teachers upload a photo of a student's handwritten dictation — LacDictée reads it with OCR and uses Claude AI to compare it against the correct text, generating a detailed error report instantly.

## Features (MVP)

- Upload handwritten dictation photo
- OCR text extraction (pytesseract)
- Claude AI correction with error highlighting
- Error report: spelling, grammar, accents
- Score calculation

## Tech Stack

| Layer | Technology |
|-------|-----------|
| UI | Streamlit |
| OCR | pytesseract + Pillow |
| AI | Claude API (Anthropic) |
| Language | Python 3.11+ |

## Getting Started

```bash
# Clone
git clone https://github.com/codibrahim/lac-dictee.git
cd lac-dictee

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# Run
streamlit run app.py
```

## Project Structure

```
lac-dictee/
├── app.py              # Streamlit main app
├── ocr.py              # OCR processing
├── correction.py       # Claude AI correction logic
├── requirements.txt
├── .env.example
└── README.md
```

## Roadmap

- [x] Project setup
- [ ] Image upload + OCR
- [ ] AI correction engine
- [ ] Error report UI
- [ ] Export to PDF
- [ ] Multi-student support
- [ ] Teacher dashboard

## Inspiration

Inspired by [DiktatMeister](https://diktatmeister.de) — a German dictation app for immigrant families.

## License

MIT
