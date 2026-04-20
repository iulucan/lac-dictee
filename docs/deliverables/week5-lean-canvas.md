# Lean Canvas — LacDictée

**Due:** April 27, 2026
**Status:** 🔄 Draft

---

| Block | Content |
|-------|---------|
| **Problem** | Teachers spend 3–5h/week correcting handwritten French dictations manually. No tool automates this with handwriting recognition + AI. |
| **Customer Segments** | Primary & secondary French language teachers (Switzerland, France, Belgium, Canada) |
| **Unique Value Proposition** | Upload a photo of any handwritten dictation → get a full error report in 30 seconds, with explanations. Zero typing for the student. |
| **Solution** | Streamlit web app: OCR reads handwriting → Claude AI compares with correct text → structured error report with score |
| **Channels** | Direct outreach to teachers, teacher Facebook groups, Powercoders network |
| **Revenue Streams** | Freemium: free for 10 corrections/month, CHF 9/month for unlimited |
| **Cost Structure** | Anthropic API usage (~$0.01/correction), Streamlit hosting (free tier) |
| **Key Metrics** | Corrections per week, time-to-report (<30s), teacher retention rate |
| **Unfair Advantage** | Claude API for nuanced French language understanding; accent-aware error detection |
| **Existing Alternatives** | DiktatMeister (German only), generic OCR tools (no pedagogy), manual correction (status quo) |

---

## Why this passes the Green Light Filter

| Test | Result |
|------|--------|
| Business Case | ✅ Teachers spend 3–5h/week on this — real, quantifiable pain |
| AI/LLM Core | ✅ Claude classifies errors by type and explains them — not possible with regex/rules |
| Feasibility | ✅ MVP buildable in 4 days: Streamlit + pytesseract + Claude API |
| Data Availability | ✅ French dictation texts are publicly available; test photos can be handwritten |
