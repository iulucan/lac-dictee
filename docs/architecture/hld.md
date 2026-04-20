# High Level Design — LacDictée

**Version:** 1.0  
**Date:** 2026-04-20  
**Author:** Ibrahim Ulucan

---

## 1. System Overview

LacDictée automates French dictation correction for teachers. The teacher uploads a photo of a student's handwritten dictation — the system reads it, compares it to the correct text using AI, and produces an instant structured error report.

---

## 2. Current Architecture — Sprint 1 (MVP)

```mermaid
flowchart TD
    A[👩‍🏫 Teacher\nBrowser] -->|Upload JPG/PNG| B[Streamlit UI\napp.py]
    B -->|Image bytes| C[OCR Module\nsrc/ocr.py\npytesseract + Pillow]
    C -->|Extracted text| B
    B -->|Student text +\nCorrect text| D[Correction Module\nsrc/correction.py\nClaude claude-sonnet-4-6]
    D -->|CorrectionResult JSON| B
    B -->|Score + Error list| A

    style A fill:#4CAF50,color:#fff
    style B fill:#2196F3,color:#fff
    style C fill:#FF9800,color:#fff
    style D fill:#9C27B0,color:#fff
```

**Flow:**
1. Teacher uploads handwritten dictation photo
2. pytesseract extracts text (French lang pack `fra`)
3. Teacher reviews/corrects OCR output
4. Teacher enters the reference correct text
5. Claude compares both → structured JSON error report
6. UI renders: score, error list with type + explanation

---

## 3. Proposed Architecture — Sprint 2+ (Enhanced)

```mermaid
flowchart TD
    A[👩‍🏫 Teacher\nBrowser] -->|Upload photo| B[Streamlit UI]
    B -->|Image| C{OCR Strategy}
    C -->|Option A - local| D[pytesseract\nFree, offline]
    C -->|Option B - better| E[Claude Vision API\nDirect image understanding]
    D -->|Text| F[Correction Engine\nClaude claude-sonnet-4-6]
    E -->|Text + OCR| F
    B -->|Select from library| G[Dictation Library\ndata/samples JSON\nA1 - B2 levels]
    G -->|Reference text| F
    F -->|CorrectionResult| B
    B -->|Report| H[(SQLite DB\nSessions log)]
    B -->|Download| I[PDF Export\nfpdf2]
    B -->|Score + Errors| A

    style A fill:#4CAF50,color:#fff
    style B fill:#2196F3,color:#fff
    style C fill:#607D8B,color:#fff
    style D fill:#FF9800,color:#fff
    style E fill:#9C27B0,color:#fff
    style F fill:#9C27B0,color:#fff
    style G fill:#00BCD4,color:#fff
    style H fill:#795548,color:#fff
    style I fill:#F44336,color:#fff
```

---

## 4. Future Architecture — Sprint 3 (Dashboard + Deployment)

```mermaid
flowchart TD
    subgraph Client
        A[👩‍🏫 Teacher\nBrowser / Mobile]
    end

    subgraph App ["Streamlit Cloud"]
        B[Streamlit UI\napp.py]
        C[OCR Module]
        D[Correction Engine]
        E[Dashboard Module]
        F[Dictation Library]
    end

    subgraph Storage
        G[(SQLite\nSessions)]
        H[JSON\nDictation Texts]
    end

    subgraph External
        I[Claude API\nAnthropic]
    end

    A <-->|HTTPS| B
    B --> C
    B --> D
    B --> E
    B --> F
    C --> D
    D <-->|API call| I
    D --> G
    E --> G
    F --> H
```

---

## 5. OCR Strategy Decision

### Why Claude Vision is better than pytesseract for handwriting

```mermaid
quadrantChart
    title OCR Options — Accuracy vs Cost
    x-axis Low Cost --> High Cost
    y-axis Low Accuracy --> High Accuracy
    quadrant-1 Best Value
    quadrant-2 Premium
    quadrant-3 Avoid
    quadrant-4 Overpriced
    pytesseract: [0.05, 0.45]
    Claude Vision: [0.55, 0.85]
    Google Cloud Vision: [0.70, 0.90]
    Azure OCR: [0.65, 0.82]
    Tesseract+preprocessing: [0.10, 0.60]
```

| Model | Handwriting | French Accents | Cost | Setup |
|-------|-------------|---------------|------|-------|
| **pytesseract** (current) | ⚠️ Mediocre | ⚠️ Needs `fra` pack | Free | System install |
| **Claude Vision** (proposed) | ✅ Excellent | ✅ Native | ~$0.003/image | Already integrated |
| **Google Cloud Vision** | ✅ Best | ✅ Good | ~$1.50/1000 img | New API key |
| **Azure OCR** | ✅ Excellent | ✅ Good | ~$1/1000 img | New API key |

**Decision:** Migrate from pytesseract → **Claude Vision** in Sprint 2.

**Why:**
- Already paying for Claude API — no extra cost
- No system dependency (no `brew install tesseract`)
- Dramatically better handwriting recognition
- Handles French accents natively
- Simplifies CI (no tesseract-ocr-fra in GitHub Actions)

---

## 6. LLM Strategy Decision

```mermaid
quadrantChart
    title LLM Options — Quality vs Cost per correction
    x-axis Low Cost --> High Cost
    y-axis Low Quality --> High Quality
    quadrant-1 Sweet Spot
    quadrant-2 Best Quality
    quadrant-3 Avoid
    quadrant-4 Overpriced
    Claude Haiku: [0.15, 0.60]
    GPT-4o-mini: [0.10, 0.55]
    GPT-4o: [0.60, 0.82]
    Gemini 1.5 Pro: [0.45, 0.78]
    Claude Sonnet 4.6: [0.65, 0.90]
    Claude Opus: [0.90, 0.95]
```

| Model | French Quality | Structured JSON | Cost/correction | Decision |
|-------|---------------|-----------------|-----------------|----------|
| **Claude claude-sonnet-4-6** | ✅ Excellent | ✅ Reliable | ~$0.003 | ✅ **Selected** |
| GPT-4o | ✅ Excellent | ✅ Reliable | ~$0.003 | Comparable, extra key |
| Claude Haiku 4.5 | ✅ Good | ✅ Good | ~$0.0005 | Fallback option |
| GPT-4o-mini | ⚠️ Good | ⚠️ OK | ~$0.0002 | Demo risk |
| Gemini 1.5 Pro | ✅ Good | ✅ Good | ~$0.002 | No advantage here |

**Decision: Claude claude-sonnet-4-6**

**Why not GPT-4o:**
- Already integrated with Claude
- No second API key to manage
- Claude is better at structured JSON output
- Prompt caching available (cheaper for repeated system prompts)

**Why not Haiku:**
- Demo quality matters — explanations must be clear for teachers
- Score difference visible in error explanations

---

## 7. Data Flow Detail

```mermaid
sequenceDiagram
    actor Teacher
    participant UI as Streamlit UI
    participant OCR as OCR Module
    participant LLM as Claude API
    participant DB as SQLite

    Teacher->>UI: Upload photo
    UI->>OCR: Image bytes
    OCR->>OCR: Preprocess (grayscale, contrast)
    OCR->>LLM: [Sprint 2] Image → extract text
    LLM-->>OCR: Extracted text + confidence
    OCR-->>UI: OCRResult(text, confidence, warning)
    UI-->>Teacher: Show extracted text (editable)

    Teacher->>UI: Confirm/edit text + enter correct text
    UI->>LLM: student_text + correct_text
    LLM-->>UI: CorrectionResult(score, errors[])
    UI->>DB: Save session (name, date, score, errors)
    UI-->>Teacher: Error report + score
    Teacher->>UI: Click "Download PDF"
    UI-->>Teacher: PDF report
```

---

## 8. Security Model

```mermaid
flowchart LR
    A[ANTHROPIC_API_KEY] -->|stored in| B[.env file\nlocal only]
    A -->|stored in| C[Streamlit Secrets\nencrypted]
    A -->|stored in| D[GitHub Secrets\nfor CI]
    B -->|loaded by| E[python-dotenv]
    C -->|loaded by| F[st.secrets]
    D -->|injected by| G[GitHub Actions]

    style B fill:#f44336,color:#fff
    style C fill:#4CAF50,color:#fff
    style D fill:#4CAF50,color:#fff
```

**Rules:**
- `.env` never committed (`.gitignore`)
- No API keys in source code
- Student photos not persisted (processed in memory)
- Student names optional (privacy)

---

## 9. Sprint Milestones

```mermaid
gantt
    title LacDictée Development Timeline
    dateFormat  YYYY-MM-DD
    section Sprint 1
    Project setup           :done, s1a, 2026-04-20, 1d
    OCR implementation      :done, s1b, 2026-04-20, 1d
    Claude correction       :done, s1c, 2026-04-20, 1d
    Error report UI         :done, s1d, 2026-04-20, 1d
    CI/CD setup             :done, s1e, 2026-04-20, 1d
    section Sprint 2
    Claude Vision OCR       :s2a, 2026-04-28, 2d
    PDF export              :s2b, 2026-04-30, 2d
    Multi-student + SQLite  :s2c, 2026-05-02, 2d
    section Sprint 3
    Teacher dashboard       :s3a, 2026-05-05, 3d
    Dictation library       :s3b, 2026-05-07, 2d
    Streamlit Cloud deploy  :s3c, 2026-05-09, 1d
    Pitch deck              :s3d, 2026-05-09, 2d
```
