"""
Teacher Analytics Dashboard — visualise class results across exercises.
"""
import json
from pathlib import Path
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Class Analytics", page_icon="📊", layout="wide")

ANALYTICS_PATH = Path(__file__).parent.parent / "reports" / "analytics.json"

# Back link
st.page_link("app.py", label="← Back to LacDictée", icon="🇫🇷")

ERROR_LABELS = {
    "spelling":     "Spelling",
    "grammar":      "Grammar",
    "accent":       "Accent",
    "missing_word": "Missing word",
    "extra_word":   "Extra word",
}
ERROR_COLORS = {
    "spelling":     "#EF553B",
    "grammar":      "#636EFA",
    "accent":       "#FECB52",
    "missing_word": "#AB63FA",
    "extra_word":   "#00CC96",
}


def score_color(score: int) -> str:
    if score >= 70:
        return "#2ecc71"
    if score >= 50:
        return "#f39c12"
    return "#e74c3c"


# ── Load data ─────────────────────────────────────────────────────────────────
st.title("📊 Class Analytics Dashboard")
st.caption("Teacher view — score distribution and error analysis")

if not ANALYTICS_PATH.exists():
    st.warning("No analytics data found. Run `batch_tv5monde.py` first to generate reports.")
    st.stop()

data = json.loads(ANALYTICS_PATH.read_text(encoding="utf-8"))
exercises = list(data.keys())

if not exercises:
    st.info("No exercise data available.")
    st.stop()

# ── Filters ───────────────────────────────────────────────────────────────────
filter_col, student_col = st.columns([2, 3])
with filter_col:
    selected = st.radio("Exercise", exercises, horizontal=True)

all_students = data[selected]
all_names = [s["name"].replace(f"{selected}_", "").replace("_", " ") for s in all_students]

with student_col:
    chosen = st.multiselect(
        "Filter students (leave empty = all)",
        options=all_names,
        default=[],
        placeholder="All students selected",
    )

students = (
    [s for s, n in zip(all_students, all_names) if n in chosen]
    if chosen else all_students
)

if not students:
    st.info("No student data for this exercise.")
    st.stop()

df = pd.DataFrame([
    {
        "Student": s["name"].replace(f"{selected}_", "").replace("_", " "),
        "Score": s["score"],
        "Errors": s["error_count"],
        "Words": s["total_words"],
        **{ERROR_LABELS.get(k, k): v for k, v in s.get("errors_by_type", {}).items()},
    }
    for s in students
])

# ── KPI row ────────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Students", len(students))
col2.metric("Class average", f"{df['Score'].mean():.0f} / 100")
col3.metric("Top score", f"{df['Score'].max()} / 100")
col4.metric("Pass rate (≥60)", f"{(df['Score'] >= 60).mean():.0%}")

st.divider()

# ── Row 1: Score bar + Score distribution ─────────────────────────────────────
left, right = st.columns(2)

with left:
    st.subheader("Score per student")
    fig_scores = go.Figure(go.Bar(
        x=df["Student"],
        y=df["Score"],
        marker_color=[score_color(s) for s in df["Score"]],
        text=df["Score"],
        textposition="outside",
    ))
    fig_scores.add_hline(y=60, line_dash="dot", line_color="gray",
                         annotation_text="Pass (60)", annotation_position="top right")
    fig_scores.update_layout(
        yaxis=dict(range=[0, 110], title="Score / 100"),
        xaxis_title="Student",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        height=340,
    )
    st.plotly_chart(fig_scores, use_container_width=True)

with right:
    st.subheader("Score distribution")
    fig_hist = px.histogram(
        df, x="Score", nbins=6,
        color_discrete_sequence=["#636EFA"],
        labels={"Score": "Score / 100", "count": "Students"},
    )
    fig_hist.add_vline(x=df["Score"].mean(), line_dash="dash", line_color="#e74c3c",
                       annotation_text=f"Avg {df['Score'].mean():.0f}", annotation_position="top right")
    fig_hist.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        height=340,
        bargap=0.1,
    )
    st.plotly_chart(fig_hist, use_container_width=True)

# ── Row 2: Error type breakdown + Error heatmap ───────────────────────────────
left2, right2 = st.columns(2)

# Aggregate error types across all students
all_errors: dict[str, int] = {}
for s in students:
    for etype, cnt in s.get("errors_by_type", {}).items():
        all_errors[etype] = all_errors.get(etype, 0) + cnt

with left2:
    st.subheader("Error type breakdown (class total)")
    if all_errors:
        labels = [ERROR_LABELS.get(k, k) for k in all_errors]
        values = list(all_errors.values())
        colors = [ERROR_COLORS.get(k, "#888") for k in all_errors]
        fig_pie = go.Figure(go.Pie(
            labels=labels, values=values,
            marker_colors=colors,
            hole=0.45,
            textinfo="label+percent",
        ))
        fig_pie.update_layout(height=340, showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.success("No errors recorded!")

with right2:
    st.subheader("Error heatmap (student × type)")
    error_types = sorted(all_errors.keys())
    heatmap_data = []
    for s in students:
        label = s["name"].replace(f"{selected}_", "").replace("_", " ")
        row = [s.get("errors_by_type", {}).get(et, 0) for et in error_types]
        heatmap_data.append(row)

    if error_types:
        fig_heat = go.Figure(go.Heatmap(
            z=heatmap_data,
            x=[ERROR_LABELS.get(t, t) for t in error_types],
            y=[s["name"].replace(f"{selected}_", "").replace("_", " ") for s in students],
            colorscale="Reds",
            text=heatmap_data,
            texttemplate="%{text}",
            showscale=True,
        ))
        fig_heat.update_layout(
            height=340,
            xaxis_title="Error type",
            yaxis_title="Student",
        )
        st.plotly_chart(fig_heat, use_container_width=True)

# ── Row 3: Errors vs Score scatter + top errors table ─────────────────────────
left3, right3 = st.columns(2)

with left3:
    st.subheader("Errors vs Score")
    fig_scatter = px.scatter(
        df, x="Errors", y="Score",
        text="Student",
        color="Score",
        color_continuous_scale="RdYlGn",
        range_color=[0, 100],
        size_max=18,
    )
    fig_scatter.update_traces(textposition="top center", marker_size=12)
    fig_scatter.update_layout(
        height=340,
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with right3:
    st.subheader("Most common mistakes")
    mistake_freq: dict[str, int] = {}
    for s in students:
        for e in s.get("errors", []):
            key = f"{e['wrong']} → {e['correct']}"
            mistake_freq[key] = mistake_freq.get(key, 0) + 1

    top = sorted(mistake_freq.items(), key=lambda x: -x[1])[:10]
    if top:
        df_top = pd.DataFrame(top, columns=["Mistake", "Count"])
        fig_top = go.Figure(go.Bar(
            x=df_top["Count"],
            y=df_top["Mistake"],
            orientation="h",
            marker_color="#EF553B",
            text=df_top["Count"],
            textposition="outside",
        ))
        fig_top.update_layout(
            height=340,
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Number of students",
            yaxis=dict(autorange="reversed"),
            showlegend=False,
        )
        st.plotly_chart(fig_top, use_container_width=True)
    else:
        st.success("No common mistakes found!")

# ── Comparison tab (both exercises side by side) ──────────────────────────────
if len(exercises) > 1:
    st.divider()
    st.subheader("Exercise comparison")

    comp_data = []
    for ex in exercises:
        for s in data[ex]:
            comp_data.append({"Exercise": ex, "Score": s["score"], "Errors": s["error_count"]})

    df_comp = pd.DataFrame(comp_data)
    fig_comp = px.box(
        df_comp, x="Exercise", y="Score",
        color="Exercise",
        points="all",
        color_discrete_map={"Champignons": "#00CC96", "Renaissance": "#636EFA"},
    )
    fig_comp.update_layout(
        height=350,
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        yaxis=dict(range=[0, 110], title="Score / 100"),
    )
    st.plotly_chart(fig_comp, use_container_width=True)

# ── Raw data table ─────────────────────────────────────────────────────────────
with st.expander("Raw data table"):
    st.dataframe(df, use_container_width=True)
