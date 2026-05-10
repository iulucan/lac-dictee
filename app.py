"""
LacDictée — AI-powered French dictation correction for teachers.
Run: streamlit run app.py
"""

import streamlit as st
from dotenv import load_dotenv
from pathlib import Path
import fitz  # PyMuPDF
from src.ocr import extract_text_from_image
from src.correction import correct_dictation, reconstruct_reference
from src.pdf_export import generate_pdf
from src.storage import save_correction, list_corrections
from src.annotation import generate_annotated_html, generate_annotated_image, overlay_annotations_on_image

load_dotenv()

import json
_SAMPLES_DIR = Path(__file__).parent / "data" / "samples"

def _load_library() -> list[dict]:
    idx = _SAMPLES_DIR / "index.json"
    return json.loads(idx.read_text(encoding="utf-8")) if idx.exists() else []

TYPE_LABELS = {
    "spelling":     ("🔴", "Spelling"),
    "grammar":      ("🟠", "Grammar"),
    "accent":       ("🟡", "Accent"),
    "missing_word": ("🔵", "Missing word"),
    "extra_word":   ("⚪", "Extra word"),
}


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


def _score_color(score: int) -> str:
    if score >= 80:
        return "#10b981"
    if score >= 60:
        return "#f59e0b"
    return "#ef4444"


def _render_report(correction, student_name: str, correct_text: str,
                   student_text: str = "", uploaded_file=None):
    """Render a full correction report (used for both live and history view)."""
    sc = _score_color(correction.score)
    emoji = "🏆" if correction.score >= 80 else "📈" if correction.score >= 60 else "📚"

    st.markdown(f"""
    <div style="
        background:white;border-radius:16px;padding:1.5rem 2rem;
        box-shadow:0 2px 12px rgba(0,0,0,0.08);border-left:6px solid {sc};
        margin:0.5rem 0 1.5rem;display:flex;align-items:center;gap:2.5rem;flex-wrap:wrap
    ">
        <div style="text-align:center;min-width:90px">
            <div style="font-size:4rem;font-weight:900;color:{sc};line-height:1.1">{correction.score}</div>
            <div style="font-size:0.95rem;color:#6b7280;font-weight:600">/ 100 &nbsp;{emoji}</div>
        </div>
        <div style="display:flex;gap:2.5rem;flex-wrap:wrap;align-items:center">
            <div>
                <div style="font-size:1.75rem;font-weight:700;color:#1f2937">{correction.error_count}</div>
                <div style="color:#6b7280;font-size:0.78rem;text-transform:uppercase;letter-spacing:.06em">Errors</div>
            </div>
            <div>
                <div style="font-size:1.75rem;font-weight:700;color:#1f2937">{correction.total_words}</div>
                <div style="color:#6b7280;font-size:0.78rem;text-transform:uppercase;letter-spacing:.06em">Words</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if correction.error_count == 0:
        st.success("🎉 Perfect dictation! No errors found.")
    else:
        st.subheader("Error breakdown")
        by_type = correction.errors_by_type
        n_cols = min(len(by_type), 2) if by_type else 1
        cols = st.columns(n_cols)
        for i, (etype, count) in enumerate(by_type.items()):
            icon, label = TYPE_LABELS.get(etype, ("⚫", etype))
            cols[i % n_cols].metric(f"{icon} {label}", count)

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

    col_pdf, col_new = st.columns(2)
    with col_pdf:
        st.download_button(
            "⬇️ Download PDF Report", data=pdf_bytes,
            file_name=fname, mime="application/pdf", use_container_width=True,
        )
    with col_new:
        if st.button("✏️ New Dictée", use_container_width=True, type="secondary", key="btn_new_dictee"):
            for k in ["history_id", "history_rec", "ocr_text_area", "correct_text_area",
                      "_ocr_file_id", "view_mode"]:
                st.session_state.pop(k, None)
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG + CSS
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="LacDictée", page_icon="🇫🇷", layout="wide")

st.markdown("""
<style>
/* ── Base ─────────────────────────────────────────── */
.stApp { background: #f0f4f8; }
.block-container { padding-top: 1.5rem; }

/* ── Sidebar ──────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: white;
    border-right: 1px solid #e2e8f0;
}

/* ── Step header badges ───────────────────────────── */
.step-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 1.5rem 0 0.6rem;
}
.step-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px; height: 36px;
    border-radius: 50%;
    font-weight: 800;
    font-size: 1.05rem;
    color: white;
    flex-shrink: 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.18);
}
.step-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #1e293b;
    margin: 0;
}

/* ── Metric cards ─────────────────────────────────── */
[data-testid="stMetric"] {
    background: white;
    border-radius: 12px;
    padding: 0.75rem 1rem;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

/* ── Primary "Analyze" button ─────────────────────── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
    border: none;
    border-radius: 12px;
    font-weight: 700;
    font-size: 1.1rem;
    letter-spacing: 0.03em;
    min-height: 54px;
    box-shadow: 0 4px 14px rgba(37,99,235,0.35);
    transition: transform .15s, box-shadow .15s;
}
.stButton > button[kind="primary"]:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(37,99,235,0.45);
}
.stButton > button[kind="primary"]:disabled {
    background: #94a3b8;
    box-shadow: none;
}

/* ── Tabs ─────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] { gap: 0.5rem; }
.stTabs [data-baseweb="tab"] { border-radius: 8px 8px 0 0; }

/* ── Success / info / warning ─────────────────────── */
.stSuccess, .stInfo, .stWarning { border-radius: 10px; }

/* ── File uploader ────────────────────────────────── */
[data-testid="stFileUploader"] {
    background: white;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    padding: 0.5rem;
}

/* ── Text areas ───────────────────────────────────── */
.stTextArea textarea {
    border-radius: 10px;
    border-color: #e2e8f0;
    font-size: 0.95rem;
}

/* ── Mobile ───────────────────────────────────────── */
@media (max-width: 768px) {
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }
    .stButton > button { min-height: 48px; font-size: 16px !important; }
    .block-container { padding: 1rem 1rem 2rem !important; }
    [data-testid="stFileUploader"] section { min-height: 80px; }
}
</style>
""", unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────────
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
            ex = f" · {rec.exercise_name}" if rec.exercise_name else ""
            dt = rec.created_at[:19].replace("T", "  ")
            badge = "🟢" if rec.score >= 80 else "🟡" if rec.score >= 60 else "🔴"
            is_active = st.session_state.get("history_id") == rec.id
            if st.button(
                f"{badge} {label}{ex} — {rec.score}/100\n{dt}",
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
    with st.expander("📖 Quick Load"):
        st.caption("Load a built-in exercise instantly.")
        library = _load_library()
        for ex in library[:4]:
            if st.button(
                f"{ex['level']} · {ex['title']}",
                key=f"sample_{ex['id']}",
                use_container_width=True,
            ):
                txt_path = _SAMPLES_DIR / ex["file"]
                if txt_path.exists():
                    st.session_state["correct_text_area"] = txt_path.read_text(encoding="utf-8").strip()
                    st.session_state["exercise_name"] = ex["title"]
                    st.rerun()
        st.page_link("pages/library.py", label="Browse all exercises →", use_container_width=True)

    st.divider()
    st.page_link("pages/analytics.py", label="📊 Class Analytics", use_container_width=True)
    st.page_link("pages/library.py", label="📚 Dictation Library", use_container_width=True)


# ── Page header ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.1rem">
    <span style="font-size:2.2rem">🇫🇷</span>
    <h1 style="margin:0;font-size:2rem;font-weight:800;color:#1e293b;line-height:1.2">LacDictée</h1>
</div>
<p style="color:#64748b;margin:0 0 0.75rem;font-size:1rem">
    AI-powered French dictation correction for teachers
</p>
""", unsafe_allow_html=True)
st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# HISTORY VIEW
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

# ── Student + Exercise names ───────────────────────────────────────────────────
col_name, col_ex = st.columns(2)
with col_name:
    student_name = st.text_input(
        "Student name (optional)",
        placeholder="e.g. Marie Dupont",
        key="student_name",
    )
with col_ex:
    exercise_name = st.text_input(
        "Exercise name (optional)",
        placeholder="e.g. Les Champignons",
        key="exercise_name",
    )

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Reference text
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="step-header">
    <span class="step-badge" style="background:#2563eb">1</span>
    <span class="step-title">Enter the correct dictation text</span>
</div>
""", unsafe_allow_html=True)

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
    st.caption("Use the 📖 Quick Load in the sidebar, or browse the full 📚 Dictation Library ←")

correct_text = st.text_area(
    "Reference text (what the student should have written):",
    height=130,
    placeholder="Le chat mange une souris dans le jardin.",
    key="correct_text_area",
)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Upload student photo
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="step-header">
    <span class="step-badge" style="background:#7c3aed">2</span>
    <span class="step-title">Upload student's dictation photo</span>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Take a photo or upload a scanned PDF of the student's handwritten dictation",
    type=["jpg", "jpeg", "png", "pdf"],
    help="On mobile: tap to open camera. Supports JPG, PNG, and scanned PDF.",
)

ocr_text = ""

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        st.info(f"PDF uploaded: {uploaded_file.name}")
    else:
        st.image(uploaded_file, caption="Uploaded dictation", use_container_width=True)

    # Cache OCR result by file identity to avoid re-running on every widget interaction
    file_id = getattr(uploaded_file, "file_id", None) or uploaded_file.name
    if st.session_state.get("_ocr_file_id") != file_id:
        with st.spinner("Reading handwriting with OCR…"):
            uploaded_file.seek(0)
            result = extract_text_from_image(uploaded_file)
        st.session_state["_ocr_file_id"] = file_id
        st.session_state["_ocr_confidence"] = result.confidence
        st.session_state["_ocr_warning"] = result.warning
        if not st.session_state.get("ocr_text_area"):
            st.session_state["ocr_text_area"] = result.text

    warning = st.session_state.get("_ocr_warning")
    confidence = st.session_state.get("_ocr_confidence", 0)
    if warning:
        st.warning(warning)
    else:
        st.success(f"✅ OCR completed — confidence: {int(confidence * 100)}%")

    st.caption("Review and correct any OCR mistakes before running:")
    ocr_text = st.text_area(
        "Extracted student text:", height=130, key="ocr_text_area",
    )

    # AI reconstruct option (only useful if reference text is missing)
    if not correct_text.strip():
        with st.expander("🔮 Don't have the reference text?"):
            st.warning("⚠️ **Lower accuracy mode** — AI guesses the reference. Results may miss real errors.")
            if st.button("Generate reference from OCR output", use_container_width=True):
                with st.spinner("Claude is reconstructing the reference text…"):
                    st.session_state["correct_text_area"] = reconstruct_reference(ocr_text)
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# ANALYZE button
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
run_disabled = not (ocr_text.strip() and correct_text.strip())
if run_disabled and (uploaded_file or correct_text):
    st.info("Upload a student photo and enter the reference text to run the correction.")

if st.button("✅  Analyze Dictation", disabled=run_disabled,
             use_container_width=True, type="primary"):
    with st.spinner("Claude is analysing errors…"):
        correction = correct_dictation(student_text=ocr_text, correct_text=correct_text)

    save_correction(correction, student_name, correct_text, ocr_text, exercise_name)

    st.markdown("""
    <div class="step-header">
        <span class="step-badge" style="background:#10b981">3</span>
        <span class="step-title">Error Report</span>
    </div>
    """, unsafe_allow_html=True)
    _render_report(correction, student_name, correct_text, ocr_text, uploaded_file)
