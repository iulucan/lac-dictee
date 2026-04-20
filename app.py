"""
LacDictée — AI-powered French dictation correction for teachers.
Run: streamlit run app.py
"""

import streamlit as st
from dotenv import load_dotenv
from src.ocr import extract_text_from_image
from src.correction import correct_dictation

load_dotenv()

st.set_page_config(
    page_title="LacDictée",
    page_icon="🇫🇷",
    layout="centered",
)

# ── Header ──────────────────────────────────────────────────────────────────
st.title("🇫🇷 LacDictée")
st.caption("AI-powered French dictation correction for teachers")
st.divider()

# ── Step 1: Upload ───────────────────────────────────────────────────────────
st.subheader("Step 1 — Upload student's dictation photo")
uploaded_file = st.file_uploader(
    "Upload a photo of the student's handwritten dictation",
    type=["jpg", "jpeg", "png"],
    help="Take a clear photo in good lighting. The app supports jpg and png.",
)

ocr_text = ""
ocr_confidence = None

if uploaded_file:
    col_img, col_info = st.columns([2, 1])
    with col_img:
        st.image(uploaded_file, caption="Uploaded dictation", use_container_width=True)

    with st.spinner("Reading handwriting with OCR…"):
        uploaded_file.seek(0)
        result = extract_text_from_image(uploaded_file)
        ocr_text = result.text
        ocr_confidence = result.confidence

    if result.warning:
        st.warning(result.warning)
    else:
        conf_pct = int(ocr_confidence * 100)
        st.success(f"OCR completed — confidence: {conf_pct}%")

    st.subheader("Extracted text (OCR)")
    st.caption("Review and correct any OCR mistakes before proceeding.")
    ocr_text = st.text_area(
        "Student text:",
        value=ocr_text,
        height=140,
        key="ocr_text_area",
    )

st.divider()

# ── Step 2: Correct text ─────────────────────────────────────────────────────
st.subheader("Step 2 — Enter the correct dictation text")
correct_text = st.text_area(
    "Reference text (what the student should have written):",
    height=140,
    placeholder="Le chat mange une souris dans le jardin.",
    key="correct_text_area",
)

# ── Step 3: Run correction ────────────────────────────────────────────────────
st.divider()
run_disabled = not (ocr_text.strip() and correct_text.strip())
if run_disabled and (uploaded_file or correct_text):
    st.info("Upload a photo and enter the correct text to run the correction.")

if st.button("✅ Correct dictation", disabled=run_disabled, use_container_width=True):
    with st.spinner("Claude is analysing errors…"):
        correction = correct_dictation(
            student_text=ocr_text,
            correct_text=correct_text,
        )

    st.divider()
    st.subheader("Step 3 — Error Report")

    # ── Score metrics ─────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    score_color = "green" if correction.score >= 80 else "orange" if correction.score >= 60 else "red"
    col1.metric("Score", f"{correction.score} / 100")
    col2.metric("Errors found", correction.error_count)
    col3.metric("Total words", correction.total_words)

    if correction.error_count == 0:
        st.success("🎉 Perfect dictation! No errors found.")
    else:
        # ── Error type breakdown ──────────────────────────────────────────────
        st.subheader("Error breakdown")
        type_labels = {
            "spelling":     ("🔴", "Spelling"),
            "grammar":      ("🟠", "Grammar"),
            "accent":       ("🟡", "Accent"),
            "missing_word": ("🔵", "Missing word"),
            "extra_word":   ("⚪", "Extra word"),
        }
        by_type = correction.errors_by_type
        cols = st.columns(len(by_type) if by_type else 1)
        for i, (etype, count) in enumerate(by_type.items()):
            icon, label = type_labels.get(etype, ("⚫", etype))
            cols[i].metric(f"{icon} {label}", count)

        # ── Error list ────────────────────────────────────────────────────────
        st.subheader("Errors")
        for err in correction.errors:
            icon, label = type_labels.get(err.type, ("⚫", err.type))
            with st.expander(f"{icon} **{err.wrong}** → `{err.correct}` ({label})"):
                st.write(err.explanation)

    # ── Store result in session for future PDF export (Sprint 2) ─────────────
    st.session_state["last_correction"] = correction
    st.session_state["last_ocr_text"] = ocr_text
    st.session_state["last_correct_text"] = correct_text
