# Solo Definition of Done (DoD)

**Project:** LacDictée
**Author:** Ibrahim Ulucan
**Last updated:** 2026-04-20

---

## Baseline (Powercoders Required)

- [ ] **Logic:** The system uses an LLM to perform a task that standard code cannot do easily (Claude AI compares two texts and explains French language errors)
- [ ] **Persistence:** The system logs correction sessions (student name, date, score, errors) to a JSON file or SQLite database
- [ ] **Security:** All credentials in `.env` file — `ANTHROPIC_API_KEY` never hardcoded or committed
- [ ] **Documentation:** Professional `README.md` with setup instructions and project description
- [ ] **Stability:** The "Happy Path" (upload photo → get error report) works 100% of the time during live demo

---

## Extended (Ibrahim's additions)

- [ ] French accent errors are detected separately (é vs e = `accent` error type, not `spelling`)
- [ ] Error report is downloadable as PDF
- [ ] CI passes on GitHub Actions (pytest with mocked Claude)
- [ ] Triage Log documents at least 3 real bugs encountered and solved
- [ ] Pitch tells an impact story: "Teachers save X hours/week"
- [ ] No PII stored — student names are optional, no photos are persisted
- [ ] `.gitignore` excludes all `.env` files and uploaded images

---

## Progress Tracker

| Item | Sprint | Status |
|------|--------|--------|
| Project structure + skeletons | Sprint 1 | ✅ Done |
| OCR image upload | Sprint 1 | 🔄 In Progress |
| Claude correction engine | Sprint 1 | 🔄 In Progress |
| Error report UI | Sprint 1 | 🔄 In Progress |
| PDF export | Sprint 2 | ⏳ Planned |
| Persistence (JSON/SQLite) | Sprint 2 | ⏳ Planned |
| Triage Log | Sprint 2 | ⏳ Planned |
| Teacher dashboard | Sprint 3 | ⏳ Planned |
| Final pitch deck | Sprint 3 | ⏳ Planned |
| Security audit checklist | Sprint 3 | ⏳ Planned |
