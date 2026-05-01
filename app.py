"""
LacDictée — AI-powered French dictation correction for teachers.
Run: streamlit run app.py
"""

import streamlit as st
from dotenv import load_dotenv
import fitz  # PyMuPDF
from src.ocr import extract_text_from_image
from src.correction import correct_dictation, reconstruct_reference
from src.pdf_export import generate_pdf
from src.storage import save_correction, list_corrections
from src.annotation import generate_annotated_html, generate_annotated_image, overlay_annotations_on_image

load_dotenv()


def _extract_reference_text(file) -> tuple[str, str]:
    import pytesseract
    from PIL import Image
    import io

    if file.type == "text/plain":
        return file.read().decode("utf-8", errors="replace").strip(), "txt"

    raw = file.read()
    doc = fitz.open(stream=raw, filetype="pdf")
    pages_text = [page.get_text() for page in doc]
    combined = "\n".join(pages_text).strip()
    if combined:
        doc.close()
        return combined, "text"

    ocr_pages = []
    for page in doc:
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        ocr_pages.append(pytesseract.image_to_string(img, lang="fra"))
    doc.close()
    return "\n".join(ocr_pages).strip(), "ocr"


TYPE_LABELS = {
    "spelling":     ("🔴", "Spelling"),
    "grammar":      ("🟠", "Grammar"),
    "accent":       ("🟡", "Accent"),
    "missing_word": ("🔵", "Missing word"),
    "extra_word":   ("⚪", "Extra word"),
}


def _render_report(correction, student_name: str, correct_text: str,
                   student_text: str = "", uploaded_file=None):
    """Render a full correction report (used for both live and history view)."""
    col1, col2, col3 = st.columns(3)
    col1.metric("Score", f"{correction.score} / 100")
    col2.metric("Errors found", correction.error_count)
    col3.metric("Total words", correction.total_words)

    if correction.error_count == 0:
        st.success("🎉 Perfect dictation! No errors found.")
    else:
        st.subheader("Error breakdown")
        by_type = correction.errors_by_type
        cols = st.columns(len(by_type) if by_type else 1)
        for i, (etype, count) in enumerate(by_type.items()):
            icon, label = TYPE_LABELS.get(etype, ("⚫", etype))
            cols[i].metric(f"{icon} {label}", count)

        st.subheader("Annotated correction")
        tab_text, tab_image, tab_overlay = st.tabs(
            ["📝 Annotated text", "🖼️ Annotated image", "✍️ Original + overlay"]
        )
        with tab_text:
            st.caption("Wrong words struck through in red · correct form shown in green")
            st.markdown(generate_annotated_html(student_text, correction), unsafe_allow_html=True)

        with tab_image:
            st.caption("Teacher red-pen style — download to share with the student")
            ann_img = generate_annotated_image(student_text, correction)
            st.image(ann_img, use_container_width=True)
            st.download_button(
                "⬇️ Download annotated image", data=ann_img,
                file_name=f"lacdictee_annotated_{student_name or 'student'}.png",
                mime="image/png", use_container_width=True, key="dl_ann_img",
            )

        with tab_overlay:
            st.caption("Errors marked directly on the original handwritten image")
            if uploaded_file is not None:
                uploaded_file.seek(0)
                raw = uploaded_file.read()
                try:
                    overlay_img = overlay_annotations_on_image(raw, student_text, correction)
                    st.image(overlay_img, use_container_width=True)
                    st.download_button(
                        "⬇️ Download marked paper", data=overlay_img,
                        file_name=f"lacdictee_marked_{student_name or 'student'}.png",
                        mime="image/png", use_container_width=True, key="dl_overlay",
                    )
                except Exception as e:
                    st.warning(f"Could not generate overlay: {e}")
            else:
                st.info("Upload a photo or PDF to see the overlay on the original image.")

        st.subheader("Errors")
        for err in correction.errors:
            icon, label = TYPE_LABELS.get(err.type, ("⚫", err.type))
            with st.expander(f"{icon} **{err.wrong}** → `{err.correct}` ({label})"):
                st.write(err.explanation)

    st.divider()
    pdf_bytes = generate_pdf(correction, student_name, correct_text)
    fname = f"lacdictee_{student_name or 'report'}_{__import__('datetime').date.today()}.pdf"
    st.download_button(
        "⬇️ Download PDF Report", data=pdf_bytes,
        file_name=fname, mime="application/pdf", use_container_width=True,
    )


st.set_page_config(page_title="LacDictée", page_icon="🇫🇷", layout="wide")

# ── Sidebar — correction history ──────────────────────────────────────────────
with st.sidebar:
    st.image("docs/logo/LacDicteeLogo.png", use_container_width=True)
    st.divider()
    st.title("📋 History")
    st.caption("Last 20 corrections")
    records = list_corrections(limit=20)
    if not records:
        st.info("No corrections saved yet.")
    else:
        for rec in records:
            label = rec.student_name or "Unknown"
            # Show full datetime with seconds
            dt = rec.created_at[:19].replace("T", "  ")
            badge = "🟢" if rec.score >= 80 else "🟡" if rec.score >= 60 else "🔴"
            is_active = st.session_state.get("history_id") == rec.id
            if st.button(
                f"{badge} {label} — {rec.score}/100\n{dt}",
                key=f"rec_{rec.id}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state["history_id"] = rec.id
                st.session_state["history_rec"] = rec
                st.session_state["view_mode"] = "history"
                st.rerun()

    if st.session_state.get("view_mode") == "history":
        st.divider()
        if st.button("✏️ New correction", use_container_width=True):
            st.session_state["view_mode"] = "correct"
            st.session_state.pop("history_id", None)
            st.session_state.pop("history_rec", None)
            st.rerun()

    st.divider()
    st.page_link("pages/analytics.py", label="📊 Class Analytics", use_container_width=True)

# ── Page header ────────────────────────────────────────────────────────────────
st.title("🇫🇷 LacDictée")
st.caption("AI-powered French dictation correction for teachers")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# HISTORY VIEW — load stored record, no recomputation
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.get("view_mode") == "history":
    rec = st.session_state.get("history_rec")
    if rec:
        st.subheader(f"📄 {rec.student_name or 'Unknown'}  ·  {rec.created_at[:19].replace('T', '  ')}")
        st.caption("Loaded from history — no recomputation")
        correction = rec.to_correction_result()
        _render_report(correction, rec.student_name, rec.correct_text, rec.student_text)
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# NORMAL CORRECTION WORKFLOW
# ══════════════════════════════════════════════════════════════════════════════

# ── Student name ───────────────────────────────────────────────────────────────
student_name = st.text_input(
    "Student name (optional)",
    placeholder="e.g. Marie Dupont",
    key="student_name",
)

st.divider()

# ── Step 1: Upload ─────────────────────────────────────────────────────────────
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
        st.success(f"✅ OCR completed — confidence: {int(result.confidence * 100)}%")

    st.subheader("Extracted text (OCR)")
    st.caption("Review and correct any OCR mistakes before proceeding.")
    ocr_text = st.text_area(
        "Student text:", value=ocr_text, height=140, key="ocr_text_area",
    )

st.divider()

# ── Step 2: Reference text ─────────────────────────────────────────────────────
st.subheader("Step 2 — Enter the correct dictation text")

if "correct_text_area" not in st.session_state:
    st.session_state["correct_text_area"] = ""

tab_upload, tab_type = st.tabs(["📄 Upload PDF or TXT", "✏️ Type / paste"])

with tab_upload:
    ref_upload = st.file_uploader(
        "Upload the original dictation text", type=["pdf", "txt"], key="ref_upload",
    )
    if ref_upload:
        with st.spinner("Extracting text…"):
            extracted, source = _extract_reference_text(ref_upload)
        if extracted:
            st.session_state["correct_text_area"] = extracted
            if source == "ocr":
                st.warning(
                    f"⚠️ Scanned PDF — OCR used ({len(extracted.split())} words). "
                    "Review in the 'Type / paste' tab before running."
                )
            else:
                st.success(f"✅ {len(extracted.split())} words extracted — ready to correct")

with tab_type:
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
                "⚠️ **Lower accuracy mode** — Claude guesses the reference. "
                "Results may miss real errors."
            )
        if generate_clicked:
            with st.spinner("Claude is reconstructing the reference text…"):
                st.session_state["correct_text_area"] = reconstruct_reference(ocr_text)

correct_text = st.text_area(
    "Reference text (what the student should have written):",
    height=140,
    placeholder="Le chat mange une souris dans le jardin.",
    key="correct_text_area",
)

# ── Step 3: Run correction ─────────────────────────────────────────────────────
st.divider()
run_disabled = not (ocr_text.strip() and correct_text.strip())
if run_disabled and (uploaded_file or correct_text):
    st.info("Upload a photo and enter the correct text to run the correction.")

if st.button("✅ Correct dictation", disabled=run_disabled, use_container_width=True):
    with st.spinner("Claude is analysing errors…"):
        correction = correct_dictation(student_text=ocr_text, correct_text=correct_text)

    save_correction(correction, student_name, correct_text, ocr_text)

    st.divider()
    st.subheader("Step 3 — Error Report")
    _render_report(correction, student_name, correct_text, ocr_text, uploaded_file)
