"""
Dictation Library — browse and load built-in French exercises.
"""
import json
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Dictation Library", page_icon="📚", layout="wide")

_SAMPLES_DIR = Path(__file__).parent.parent / "data" / "samples"
_INDEX = _SAMPLES_DIR / "index.json"

LEVEL_COLORS = {
    "A1": ("#dcfce7", "#16a34a"),
    "A2": ("#dbeafe", "#2563eb"),
    "B1": ("#fef9c3", "#ca8a04"),
    "B2": ("#fce7f3", "#db2777"),
}
LEVEL_ORDER = ["A1", "A2", "B1", "B2"]


def _load_index() -> list[dict]:
    if not _INDEX.exists():
        return []
    return json.loads(_INDEX.read_text(encoding="utf-8"))


def _level_badge(level: str) -> str:
    bg, fg = LEVEL_COLORS.get(level, ("#f3f4f6", "#374151"))
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 10px;'
        f'border-radius:99px;font-weight:700;font-size:0.8rem">{level}</span>'
    )


st.markdown("""
<style>
.stApp { background: #f0f4f8; }
.block-container { padding-top: 1.5rem; }
.ex-card {
    background: white;
    border-radius: 14px;
    padding: 1.25rem 1.4rem;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}
.ex-title { font-size: 1.05rem; font-weight: 700; color: #1e293b; margin: 0; }
.ex-meta  { font-size: 0.8rem; color: #64748b; }
.ex-preview {
    font-size: 0.85rem; color: #475569;
    font-style: italic;
    border-left: 3px solid #e2e8f0;
    padding-left: 0.6rem;
    margin: 0.25rem 0;
    flex: 1;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    border: none; border-radius: 8px;
    font-weight: 600; font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

st.page_link("app.py", label="← Back to LacDictée", icon="🇫🇷")

st.markdown("""
<div style="margin-bottom:0.25rem">
    <h1 style="margin:0;font-size:1.9rem;font-weight:800;color:#1e293b">📚 Dictation Library</h1>
    <p style="color:#64748b;margin:0.25rem 0 0">Built-in French exercises — click any card to use it immediately</p>
</div>
""", unsafe_allow_html=True)
st.divider()

exercises = _load_index()
if not exercises:
    st.error("Library index not found. Make sure `data/samples/index.json` exists.")
    st.stop()

# ── Level filter ───────────────────────────────────────────────────────────────
levels_available = sorted({e["level"] for e in exercises}, key=lambda x: LEVEL_ORDER.index(x) if x in LEVEL_ORDER else 99)
all_levels = ["All"] + levels_available

selected_level = st.radio(
    "Filter by level",
    all_levels,
    horizontal=True,
    label_visibility="collapsed",
)

filtered = exercises if selected_level == "All" else [e for e in exercises if e["level"] == selected_level]

st.caption(f"{len(filtered)} exercise{'s' if len(filtered) != 1 else ''} found")
st.divider()

# ── Exercise cards ─────────────────────────────────────────────────────────────
cols = st.columns(3, gap="medium")

for i, ex in enumerate(filtered):
    txt_path = _SAMPLES_DIR / ex["file"]
    text = txt_path.read_text(encoding="utf-8").strip() if txt_path.exists() else ""
    word_count = len(text.split())
    preview = text[:120].replace("\n", " ") + ("…" if len(text) > 120 else "")

    with cols[i % 3]:
        st.markdown(f"""
        <div class="ex-card">
            <div>{_level_badge(ex["level"])}
                 <span style="color:#94a3b8;font-size:0.78rem;margin-left:0.5rem">{ex["category"]}</span>
            </div>
            <p class="ex-title">{ex["title"]}</p>
            <p class="ex-preview">{preview}</p>
            <p class="ex-meta">📝 {word_count} words</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Use this exercise →", key=f"use_{ex['id']}", use_container_width=True, type="primary"):
            st.session_state["correct_text_area"] = text
            st.session_state["exercise_name"] = ex["title"]
            st.switch_page("app.py")
