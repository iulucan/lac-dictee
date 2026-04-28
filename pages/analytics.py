"""
Teacher Analytics Dashboard — exercise and student views from SQLite.
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from src.storage import list_all_corrections

st.set_page_config(page_title="Class Analytics", page_icon="📊", layout="wide")

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


def exercise_label(correct_text: str) -> str:
    first = correct_text.strip().split("\n")[0]
    return (first[:55] + "…") if len(first) > 55 else first


# ── Load data ─────────────────────────────────────────────────────────────────
st.title("📊 Class Analytics Dashboard")
st.caption("Teacher view — score distribution and error analysis")

all_records = list_all_corrections()
if not all_records:
    st.warning("No corrections found yet. Run at least one correction first.")
    st.stop()

# Group by exact correct_text → exercise
exercise_map: dict[str, list] = {}
for rec in all_records:
    label = exercise_label(rec.correct_text)
    exercise_map.setdefault(label, []).append(rec)

all_student_names = sorted({r.student_name for r in all_records if r.student_name})

tab_exercise, tab_student = st.tabs(["📚 By Exercise", "👤 By Student"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — BY EXERCISE
# ══════════════════════════════════════════════════════════════════════════════
with tab_exercise:
    filter_col, student_col = st.columns([3, 2])
    with filter_col:
        selected_ex = st.selectbox("Exercise", list(exercise_map.keys()))
    ex_records = exercise_map[selected_ex]
    ex_names = sorted({r.student_name or "Unknown" for r in ex_records})
    with student_col:
        chosen = st.multiselect(
            "Filter students (leave empty = all)",
            options=ex_names,
            default=[],
            placeholder="All students selected",
        )

    students = [r for r in ex_records if not chosen or (r.student_name or "Unknown") in chosen]
    if not students:
        st.info("No data for this selection.")
        st.stop()

    df_rows = []
    for r in students:
        ebt = r.to_correction_result().errors_by_type
        row = {
            "Student": r.student_name or "Unknown",
            "Score": r.score,
            "Errors": r.error_count,
            "Words": r.total_words,
            "Date": r.created_at[:10],
            **{ERROR_LABELS.get(k, k): v for k, v in ebt.items()},
        }
        df_rows.append(row)
    df = pd.DataFrame(df_rows)

    # KPI row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Students", len(students))
    col2.metric("Class average", f"{df['Score'].mean():.0f} / 100")
    col3.metric("Top score", f"{df['Score'].max()} / 100")
    col4.metric("Pass rate (≥60)", f"{(df['Score'] >= 60).mean():.0%}")
    st.divider()

    # Row 1: score bar + histogram
    left, right = st.columns(2)
    with left:
        st.subheader("Score per student")
        fig_scores = go.Figure(go.Bar(
            x=df["Student"], y=df["Score"],
            marker_color=[score_color(s) for s in df["Score"]],
            text=df["Score"], textposition="outside",
        ))
        fig_scores.add_hline(y=60, line_dash="dot", line_color="gray",
                             annotation_text="Pass (60)", annotation_position="top right")
        fig_scores.update_layout(yaxis=dict(range=[0, 110], title="Score / 100"),
                                 xaxis_title="Student", plot_bgcolor="rgba(0,0,0,0)",
                                 showlegend=False, height=340)
        st.plotly_chart(fig_scores, use_container_width=True)

    with right:
        st.subheader("Score distribution")
        fig_hist = px.histogram(df, x="Score", nbins=6,
                                color_discrete_sequence=["#636EFA"],
                                labels={"Score": "Score / 100", "count": "Students"})
        fig_hist.add_vline(x=df["Score"].mean(), line_dash="dash", line_color="#e74c3c",
                           annotation_text=f"Avg {df['Score'].mean():.0f}",
                           annotation_position="top right")
        fig_hist.update_layout(plot_bgcolor="rgba(0,0,0,0)", height=340, bargap=0.1)
        st.plotly_chart(fig_hist, use_container_width=True)

    # Row 2: error donut + heatmap
    left2, right2 = st.columns(2)
    all_errors: dict[str, int] = {}
    for r in students:
        for etype, cnt in r.to_correction_result().errors_by_type.items():
            all_errors[etype] = all_errors.get(etype, 0) + cnt

    with left2:
        st.subheader("Error type breakdown (class total)")
        if all_errors:
            labels = [ERROR_LABELS.get(k, k) for k in all_errors]
            values = list(all_errors.values())
            colors = [ERROR_COLORS.get(k, "#888") for k in all_errors]
            fig_pie = go.Figure(go.Pie(labels=labels, values=values,
                                       marker_colors=colors, hole=0.45,
                                       textinfo="label+percent"))
            fig_pie.update_layout(height=340, showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.success("No errors recorded!")

    with right2:
        st.subheader("Error heatmap (student × type)")
        error_types = sorted(all_errors.keys())
        heatmap_data = [[r.to_correction_result().errors_by_type.get(et, 0)
                         for et in error_types] for r in students]
        if error_types:
            fig_heat = go.Figure(go.Heatmap(
                z=heatmap_data,
                x=[ERROR_LABELS.get(t, t) for t in error_types],
                y=[r.student_name or "Unknown" for r in students],
                colorscale="Reds", text=heatmap_data,
                texttemplate="%{text}", showscale=True,
            ))
            fig_heat.update_layout(height=340,
                                   xaxis_title="Error type", yaxis_title="Student")
            st.plotly_chart(fig_heat, use_container_width=True)

    # Row 3: scatter + top mistakes
    left3, right3 = st.columns(2)
    with left3:
        st.subheader("Errors vs Score")
        fig_scatter = px.scatter(df, x="Errors", y="Score", text="Student",
                                 color="Score", color_continuous_scale="RdYlGn",
                                 range_color=[0, 100])
        fig_scatter.update_traces(textposition="top center", marker_size=12)
        fig_scatter.update_layout(height=340, plot_bgcolor="rgba(0,0,0,0)",
                                  showlegend=False)
        st.plotly_chart(fig_scatter, use_container_width=True)

    with right3:
        st.subheader("Most common mistakes")
        mistake_freq: dict[str, int] = {}
        for r in students:
            for e in r.to_correction_result().errors:
                key = f"{e.wrong} → {e.correct}"
                mistake_freq[key] = mistake_freq.get(key, 0) + 1
        top = sorted(mistake_freq.items(), key=lambda x: -x[1])[:10]
        if top:
            df_top = pd.DataFrame(top, columns=["Mistake", "Count"])
            fig_top = go.Figure(go.Bar(
                x=df_top["Count"], y=df_top["Mistake"], orientation="h",
                marker_color="#EF553B", text=df_top["Count"], textposition="outside",
            ))
            fig_top.update_layout(height=340, plot_bgcolor="rgba(0,0,0,0)",
                                  xaxis_title="Number of students",
                                  yaxis=dict(autorange="reversed"), showlegend=False)
            st.plotly_chart(fig_top, use_container_width=True)
        else:
            st.success("No common mistakes found!")

    # Exercise comparison (if multiple exercises exist)
    if len(exercise_map) > 1:
        st.divider()
        st.subheader("Exercise comparison (all exercises)")
        comp_data = []
        for ex_label, recs in exercise_map.items():
            for r in recs:
                comp_data.append({"Exercise": ex_label[:30], "Score": r.score,
                                  "Errors": r.error_count})
        df_comp = pd.DataFrame(comp_data)
        fig_comp = px.box(df_comp, x="Exercise", y="Score", color="Exercise",
                          points="all")
        fig_comp.update_layout(height=350, plot_bgcolor="rgba(0,0,0,0)",
                               showlegend=False,
                               yaxis=dict(range=[0, 110], title="Score / 100"))
        st.plotly_chart(fig_comp, use_container_width=True)

    with st.expander("Raw data table"):
        st.dataframe(df, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — BY STUDENT
# ══════════════════════════════════════════════════════════════════════════════
with tab_student:
    if not all_student_names:
        st.info("No named students found. Add student names when running corrections.")
        st.stop()

    selected_student = st.selectbox("Student", all_student_names)
    student_records = sorted(
        [r for r in all_records if r.student_name == selected_student],
        key=lambda r: r.created_at,
    )

    if not student_records:
        st.info("No corrections found for this student.")
        st.stop()

    scores = [r.score for r in student_records]

    # KPI row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Corrections done", len(student_records))
    col2.metric("Average score", f"{sum(scores) / len(scores):.0f} / 100")
    col3.metric("Best score", f"{max(scores)} / 100")
    trend = scores[-1] - scores[-2] if len(scores) >= 2 else None
    col4.metric("Last score", f"{scores[-1]} / 100",
                delta=f"{trend:+d}" if trend is not None else None)
    st.divider()

    dates = [r.created_at[:10] for r in student_records]
    ex_labels = [exercise_label(r.correct_text) for r in student_records]
    x_axis = list(range(1, len(scores) + 1))

    left_s, right_s = st.columns(2)
    with left_s:
        st.subheader("Score progression")
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=x_axis, y=scores,
            mode="lines+markers+text",
            text=[str(s) for s in scores],
            textposition="top center",
            marker=dict(size=10, color=[score_color(s) for s in scores]),
            line=dict(color="#636EFA", width=2),
            hovertext=[f"{d}<br>{ex}<br>{s}/100"
                       for d, ex, s in zip(dates, ex_labels, scores)],
            hoverinfo="text",
        ))
        fig_line.add_hline(y=60, line_dash="dot", line_color="gray",
                           annotation_text="Pass (60)", annotation_position="top right")
        fig_line.update_layout(
            xaxis=dict(title="Exercise #", tickmode="linear", dtick=1),
            yaxis=dict(range=[0, 110], title="Score / 100"),
            plot_bgcolor="rgba(0,0,0,0)", height=340, showlegend=False,
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with right_s:
        st.subheader("Error types over time")
        error_rows = []
        for i, r in enumerate(student_records, 1):
            for etype, cnt in r.to_correction_result().errors_by_type.items():
                error_rows.append({
                    "Exercise #": i,
                    "Type": ERROR_LABELS.get(etype, etype),
                    "Count": cnt,
                })
        if error_rows:
            df_err = pd.DataFrame(error_rows)
            fig_err = px.bar(
                df_err, x="Exercise #", y="Count", color="Type",
                color_discrete_map={v: ERROR_COLORS.get(k, "#888")
                                    for k, v in ERROR_LABELS.items()},
                barmode="stack",
            )
            fig_err.update_layout(height=340, plot_bgcolor="rgba(0,0,0,0)",
                                  xaxis=dict(tickmode="linear", dtick=1))
            st.plotly_chart(fig_err, use_container_width=True)
        else:
            st.success("No errors found in any session!")

    st.subheader("Exercise history")
    history_rows = [
        {
            "#": i,
            "Date": r.created_at[:10],
            "Exercise": exercise_label(r.correct_text),
            "Score": f"{r.score}/100",
            "Errors": r.error_count,
        }
        for i, r in enumerate(student_records, 1)
    ]
    st.dataframe(pd.DataFrame(history_rows), use_container_width=True, hide_index=True)
