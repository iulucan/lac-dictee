"""
LacDictée — AI-powered French dictation correction for teachers.
Run: streamlit run app.py
"""

import streamlit as st
from dotenv import load_dotenv
from src.ocr import extract_text_from_image
from src.correction import correct_dictation, reconstruct_reference
from src.pdf_export import generate_pdf
from src.storage import save_correction, list_corrections
from src.annotation import generate_annotated_html, generate_annotated_image

load_dotenv()

st.set_page_config(
    page_title="LacDictée",
    page_icon="🇫🇷",
    layout="wide",
)

# ── Sidebar — correction history ─────────────────────────────────────────────
with st.sidebar:
    st.title("📋 History")
    st.caption("Last 20 corrections")
    records = list_corrections(limit=20)
    if not records:
        st.info("No corrections saved yet.")
    else:
        for rec in records:
            label = rec.student_name or "Unknown"
            date_short = rec.created_at[:10]
            badge = "🟢" if rec.score >= 80 else "🟡" if rec.score >= 60 else "🔴"
            if st.button(
                f"{badge} {label} — {rec.score}/100\n{date_short}",
                key=f"rec_{rec.id}",
                use_container_width=True,
            ):
                st.session_state["sidebar_record"] = rec

    # ── Show selected record ──────────────────────────────────────────────────
    if "sidebar_record" in st.session_state:
        rec = st.session_state["sidebar_record"]
        st.divider()
        st.subheader(f"📄 {rec.student_name or 'Unknown'}")
        st.caption(rec.created_at[:10])
        st.metric("Score", f"{rec.score} / 100")
        correction = rec.to_correction_result()
        pdf_bytes = generate_pdf(correction, rec.student_name, rec.correct_text)
        st.download_button(
            "⬇️ Download PDF",
            data=pdf_bytes,
            file_name=f"lacdictee_{rec.student_name or 'report'}_{rec.created_at[:10]}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

# ── Main area ─────────────────────────────────────────────────────────────────
st.title("🇫🇷 LacDictée")
st.caption("AI-powered French dictation correction for teachers")
st.divider()

# ── Student name ──────────────────────────────────────────────────────────────
student_name = st.text_input(
    "Student name (optional)",
    placeholder="e.g. Marie Dupont",
    key="student_name",
)

st.divider()

# ── Step 1: Upload ────────────────────────────────────────────────────────────
st.subheader("Step 1 — Upload student's dictation photo")
uploaded_file = st.file_uploader(
    "Upload a photo or scanned PDF of the student's handwritten dictation",
    type=["jpg", "jpeg", "png", "pdf"],
    help="Supports JPG, PNG photos and scanned PDF files.",
)

ocr_text = ""

if uploaded_file:
    col_img, col_info = st.columns([2, 1])
    with col_img:
        if uploaded_file.type == "application/pdf":
            st.info(f"PDF uploaded: {uploaded_file.name}")
        else:
            st.image(uploaded_file, caption="Uploaded dictation", use_container_width=True)

    with st.spinner("Reading handwriting with OCR…"):
        uploaded_file.seek(0)
        result = extract_text_from_image(uploaded_file)
        ocr_text = result.text

    if result.warning:
        st.warning(result.warning)
    else:
        st.success(f"OCR completed — confidence: {int(result.confidence * 100)}%")

    st.subheader("Extracted text (OCR)")
    st.caption("Review and correct any OCR mistakes before proceeding.")
    ocr_text = st.text_area(
        "Student text:",
        value=ocr_text,
        height=140,
        key="ocr_text_area",
    )

st.divider()

# ── Step 2: Reference text ────────────────────────────────────────────────────
st.subheader("Step 2 — Enter the correct dictation text")

if ocr_text.strip():
    col_btn, col_info = st.columns([1, 2])
    with col_btn:
        generate_clicked = st.button(
            "🔮 Generate reference text",
            help="Ask Claude to reconstruct the likely correct text from the OCR output.",
            use_container_width=True,
        )
    with col_info:
        st.warning(
            "⚠️ **Lower accuracy mode** — without the original text, "
            "Claude guesses the reference. Results may miss real errors.",
            icon=None,
        )

    if generate_clicked:
        with st.spinner("Claude is reconstructing the reference text…"):
            st.session_state["correct_text_area"] = reconstruct_reference(ocr_text)

if "correct_text_area" not in st.session_state:
    st.session_state["correct_text_area"] = ""

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

    # Save to SQLite
    save_correction(correction, student_name, correct_text, ocr_text)

    st.divider()
    st.subheader("Step 3 — Error Report")

    # ── Score metrics ─────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    col1.metric("Score", f"{correction.score} / 100")
    col2.metric("Errors found", correction.error_count)
    col3.metric("Total words", correction.total_words)

    type_labels = {
        "spelling":     ("🔴", "Spelling"),
        "grammar":      ("🟠", "Grammar"),
        "accent":       ("🟡", "Accent"),
        "missing_word": ("🔵", "Missing word"),
        "extra_word":   ("⚪", "Extra word"),
    }

    if correction.error_count == 0:
        st.success("🎉 Perfect dictation! No errors found.")
    else:
        # ── Error type breakdown ──────────────────────────────────────────────
        st.subheader("Error breakdown")
        by_type = correction.errors_by_type
        cols = st.columns(len(by_type) if by_type else 1)
        for i, (etype, count) in enumerate(by_type.items()):
            icon, label = type_labels.get(etype, ("⚫", etype))
            cols[i].metric(f"{icon} {label}", count)

        # ── Annotated views ───────────────────────────────────────────────────
        st.subheader("Annotated correction")
        tab_text, tab_image = st.tabs(["📝 Annotated text", "🖼️ Annotated image"])

        with tab_text:
            st.caption("Wrong words struck through in red · correct form shown in green")
            html = generate_annotated_html(ocr_text, correction)
            st.markdown(html, unsafe_allow_html=True)

        with tab_image:
            st.caption("Teacher red-pen style — download to share with the student")
            ann_img = generate_annotated_image(ocr_text, correction)
            st.image(ann_img, use_container_width=True)
            st.download_button(
                "⬇️ Download annotated image",
                data=ann_img,
                file_name=f"lacdictee_annotated_{student_name or 'student'}.png",
                mime="image/png",
                use_container_width=True,
            )

        # ── Error list ────────────────────────────────────────────────────────
        st.subheader("Errors")
        for err in correction.errors:
            icon, label = type_labels.get(err.type, ("⚫", err.type))
            with st.expander(f"{icon} **{err.wrong}** → `{err.correct}` ({label})"):
                st.write(err.explanation)

    # ── PDF download ──────────────────────────────────────────────────────────
    st.divider()
    pdf_bytes = generate_pdf(correction, student_name, correct_text)
    fname = f"lacdictee_{student_name or 'report'}_{__import__('datetime').date.today()}.pdf"
    st.download_button(
        "⬇️ Download PDF Report",
        data=pdf_bytes,
        file_name=fname,
        mime="application/pdf",
        use_container_width=True,
    )
