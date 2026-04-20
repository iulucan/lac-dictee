"""
LacDictée — AI-powered French dictation correction for teachers.

Entry point: streamlit run app.py
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

st.title("🇫🇷 LacDictée")
st.caption("AI-powered French dictation correction for teachers")

# --- Step 1: Upload ---
st.header("Step 1 — Upload student's dictation photo")
uploaded_file = st.file_uploader(
    "Upload a photo of the student's handwritten dictation",
    type=["jpg", "jpeg", "png"],
)

ocr_text = ""
if uploaded_file:
    st.image(uploaded_file, caption="Uploaded dictation", use_container_width=True)
    with st.spinner("Reading handwriting with OCR…"):
        ocr_text = extract_text_from_image(uploaded_file)
    st.subheader("Extracted text (OCR)")
    ocr_text = st.text_area("Edit if OCR made mistakes:", value=ocr_text, height=150)

# --- Step 2: Correct text ---
st.header("Step 2 — Enter the correct dictation text")
correct_text = st.text_area(
    "Type or paste the original correct text:",
    height=150,
    placeholder="Le chat mange une souris dans le jardin.",
)

# --- Step 3: Correct ---
if st.button("✅ Correct dictation", disabled=not (ocr_text and correct_text)):
    with st.spinner("Claude is analysing errors…"):
        result = correct_dictation(
            student_text=ocr_text,
            correct_text=correct_text,
        )

    # --- Step 4: Report ---
    st.header("Step 3 — Error Report")

    score = result.get("score", 0)
    errors = result.get("errors", [])
    total_words = result.get("total_words", 1)

    col1, col2, col3 = st.columns(3)
    col1.metric("Score", f"{score}/100")
    col2.metric("Errors", len(errors))
    col3.metric("Total words", total_words)

    if errors:
        st.subheader("Errors")
        for err in errors:
            color = {"spelling": "🔴", "grammar": "🟠", "accent": "🟡"}.get(
                err.get("type", "spelling"), "⚪"
            )
            st.markdown(
                f"{color} **{err.get('wrong', '')}** → `{err.get('correct', '')}` "
                f"*({err.get('type', '')})*: {err.get('explanation', '')}"
            )
    else:
        st.success("Perfect dictation! No errors found.")
