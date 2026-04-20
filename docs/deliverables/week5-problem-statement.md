# Problem Statement — Week 5 Deliverable

**Due:** April 27, 2026
**Status:** 🔄 Draft

---

## Problem Title
**LacDictée: Automating French Dictation Correction for Teachers**

---

## Context / Background

French dictation (*la dictée*) is a standard language exercise used in French-speaking schools from primary through secondary level. Students listen to a text being read aloud, write it by hand, and submit it for correction.

Currently, correction is done entirely by hand: the teacher reads each student's paper word by word, marks errors, calculates a score, and writes feedback. For a class of 20–30 students, this takes **3–5 hours per week** — time that could be spent on actual teaching.

---

## The Problem

There is no accessible, teacher-friendly tool that automates the correction of handwritten French dictations using AI.

Existing solutions either:
- Require students to type their answers (losing the handwriting practice dimension)
- Are general OCR tools with no language-education focus
- Are expensive LMS platforms not suited to small/independent teachers

---

## Evidence / Data

- Average French primary school teacher corrects 25 dictations/week × 10–15 min each = **~4 hours/week**
- [Swiss Federal Statistical Office](https://www.bfs.admin.ch): 78,000+ primary school teachers in Switzerland alone
- [DiktatMeister](https://diktatmeister.de): proven demand for the same concept in German (active production app)

---

## Impact

**Who is affected:** Primary and secondary school French teachers (CH, FR, BE, CA)

**Consequences:**
- Teachers burn hours on repetitive manual work
- Feedback is delayed (students wait days for results)
- Inconsistent grading between teachers
- No data on class-wide error patterns

---

## Objectives / Goal

A teacher should be able to:
1. Upload a photo of a student's handwritten dictation
2. Receive a full error report (score, errors, types, explanations) in under 30 seconds
3. Download or share the report with the student/parent

**Success metric:** The Happy Path (upload → report) works 100% of the time in the live demo.
