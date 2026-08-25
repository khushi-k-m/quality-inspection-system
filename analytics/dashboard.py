import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px


# ======================================================
# PROJECT PATHS
# ======================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = ROOT_DIR / "database" / "inspection.db"


# ======================================================
# PAGE CONFIGURATION
# ======================================================

st.set_page_config(
    page_title="Steel Quality Analytics",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ======================================================
# CUSTOM CSS
# ======================================================

st.markdown(
    """
    <style>

    .main {
        padding-top: 1rem;
    }

    .dashboard-title {
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 0px;
    }

    .dashboard-subtitle {
        font-size: 15px;
        margin-bottom: 25px;
    }

    .section-title {
        font-size: 21px;
        font-weight: 600;
        margin-top: 20px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ======================================================
# DATABASE LOADER
# ======================================================

@st.cache_data(ttl=5)
def load_inspections():

    conn = sqlite3.connect(DATABASE_PATH)

    query = """
        SELECT
            id,
            inspection_id,
            timestamp,
            scratches,
            dents,
            rust,
            other,
            total_defects,
            quality_score,
            severity,
            status,
            inspector
        FROM inspections
        ORDER BY id DESC
    """

    try:

        df = pd.read_sql_query(
            query,
            conn
        )

    except Exception as e:

        conn.close()

        st.error(
            f"Database error: {e}"
        )

        st.stop()

    conn.close()

    return df


# ======================================================
# LOAD DATA
# ======================================================

df = load_inspections()


# ======================================================
# HEADER
# ======================================================

st.markdown(
    '<div class="dashboard-title">'
    '🏭 Steel Quality Analytics Dashboard'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="dashboard-subtitle">'
    'AI-Powered Quality Inspection & Production Monitoring System'
    '</div>',
    unsafe_allow_html=True
)


# ======================================================
# REFRESH BUTTON
# ======================================================

col_refresh, col_info = st.columns([1, 5])


with col_refresh:

    if st.button(
        "🔄 Refresh Data",
        use_container_width=True
    ):

        st.cache_data.clear()

        st.rerun()


with col_info:

    st.caption(
        f"Database: {DATABASE_PATH}"
    )


# ======================================================
# CHECK DATA
# ======================================================

if df.empty:

    st.warning(
        "⚠️ No inspection records available."
    )

    st.info(
        "Run the camera inspection system "
        "and save an inspection first."
    )

    st.stop()


# ======================================================
# DATA PREPROCESSING
# ======================================================

df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce"
)

df["date"] = df["timestamp"].dt.date


# Convert numeric fields safely

numeric_columns = [
    "scratches",
    "dents",
    "rust",
    "other",
    "total_defects",
    "quality_score"
]

for column in numeric_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# Missing quality scores

df["quality_score"] = df[
    "quality_score"
].fillna(100)


# Missing severity

df["severity"] = df[
    "severity"
].fillna("NONE")


# ======================================================
# SIDEBAR
# ======================================================

st.sidebar.title("🔎 Inspection Filters")


# ------------------------------------------------------
# STATUS FILTER
# ------------------------------------------------------

status_options = [
    "ALL",
    "PASS",
    "REWORK",
    "FAIL"
]

selected_status = st.sidebar.selectbox(
    "Inspection Status",
    status_options
)


# ------------------------------------------------------
# SEVERITY FILTER
# ------------------------------------------------------

severity_options = [
    "ALL",
    "NONE",
    "LOW",
    "MEDIUM",
    "HIGH"
]

selected_severity = st.sidebar.selectbox(
    "Severity",
    severity_options
)


# ------------------------------------------------------
# DATE FILTER
# ------------------------------------------------------

available_dates = sorted(
    df["date"]
    .dropna()
    .unique()
)


if available_dates:

    selected_date = st.sidebar.selectbox(
        "Inspection Date",
        ["ALL"] + available_dates
    )

else:

    selected_date = "ALL"


# ======================================================
# APPLY FILTERS
# ======================================================

filtered_df = df.copy()


if selected_status != "ALL":

    filtered_df = filtered_df[
        filtered_df["status"] == selected_status
    ]


if selected_severity != "ALL":

    filtered_df = filtered_df[
        filtered_df["severity"] == selected_severity
    ]


if selected_date != "ALL":

    filtered_df = filtered_df[
        filtered_df["date"] == selected_date
    ]


# ======================================================
# EMPTY FILTER RESULT
# ======================================================

if filtered_df.empty:

    st.warning(
        "No inspections match the selected filters."
    )

    st.stop()


# ======================================================
# KPI CALCULATIONS
# ======================================================

total_inspections = len(
    filtered_df
)


pass_count = len(
    filtered_df[
        filtered_df["status"] == "PASS"
    ]
)


rework_count = len(
    filtered_df[
        filtered_df["status"] == "REWORK"
    ]
)


fail_count = len(
    filtered_df[
        filtered_df["status"] == "FAIL"
    ]
)


# ------------------------------------------------------
# QUALITY RATES
# ------------------------------------------------------

quality_rate = (
    pass_count /
    total_inspections
) * 100


failure_rate = (
    fail_count /
    total_inspections
) * 100


rework_rate = (
    rework_count /
    total_inspections
) * 100


# ------------------------------------------------------
# QUALITY SCORE
# ------------------------------------------------------

average_quality_score = (
    filtered_df["quality_score"]
    .mean()
)


# ------------------------------------------------------
# DEFECT METRICS
# ------------------------------------------------------

total_defects = int(
    filtered_df["total_defects"]
    .sum()
)


average_defects = (
    total_defects /
    total_inspections
)


# ======================================================
# PRODUCTION OVERVIEW
# ======================================================

st.markdown(
    '<div class="section-title">'
    '📊 Production Overview'
    '</div>',
    unsafe_allow_html=True
)


col1, col2, col3, col4, col5 = st.columns(5)


with col1:

    st.metric(
        "Total Inspections",
        total_inspections
    )


with col2:

    st.metric(
        "✅ PASS",
        pass_count
    )


with col3:

    st.metric(
        "⚠️ REWORK",
        rework_count
    )


with col4:

    st.metric(
        "❌ FAIL",
        fail_count
    )


with col5:

    st.metric(
        "⭐ Avg Quality Score",
        f"{average_quality_score:.1f}%"
    )


st.divider()


# ======================================================
# SECOND KPI ROW
# ======================================================

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Quality Rate",
        f"{quality_rate:.1f}%"
    )


with col2:

    st.metric(
        "Failure Rate",
        f"{failure_rate:.1f}%"
    )


with col3:

    st.metric(
        "Rework Rate",
        f"{rework_rate:.1f}%"
    )


with col4:

    st.metric(
        "Total Defects",
        total_defects
    )


st.divider()


# ======================================================
# STATUS + SEVERITY
# ======================================================

col_left, col_right = st.columns(2)


# ======================================================
# STATUS DISTRIBUTION
# ======================================================

with col_left:

    st.subheader(
        "📊 Inspection Status"
    )

    status_data = (
        filtered_df["status"]
        .value_counts()
        .reset_index()
    )

    status_data.columns = [
        "Status",
        "Count"
    ]

    fig_status = px.pie(
        status_data,
        names="Status",
        values="Count",
        hole=0.45,
        title="PASS / REWORK / FAIL"
    )

    fig_status.update_layout(
        legend_title="Status"
    )

    st.plotly_chart(
        fig_status,
        use_container_width=True
    )


# ======================================================
# SEVERITY DISTRIBUTION
# ======================================================

with col_right:

    st.subheader(
        "🚨 Severity Distribution"
    )

    severity_data = (
        filtered_df["severity"]
        .value_counts()
        .reset_index()
    )

    severity_data.columns = [
        "Severity",
        "Count"
    ]

    fig_severity = px.bar(
        severity_data,
        x="Severity",
        y="Count",
        text="Count",
        title="Inspection Severity"
    )

    fig_severity.update_traces(
        textposition="outside"
    )

    st.plotly_chart(
        fig_severity,
        use_container_width=True
    )


# ======================================================
# DEFECT DISTRIBUTION
# ======================================================

st.subheader(
    "🔍 Defect Distribution"
)


defect_data = pd.DataFrame({

    "Defect Type": [
        "Scratches",
        "Dents",
        "Rust",
        "Other"
    ],

    "Count": [

        int(
            filtered_df[
                "scratches"
            ].sum()
        ),

        int(
            filtered_df[
                "dents"
            ].sum()
        ),

        int(
            filtered_df[
                "rust"
            ].sum()
        ),

        int(
            filtered_df[
                "other"
            ].sum()
        )
    ]
})


col_left, col_right = st.columns(2)


# ------------------------------------------------------
# DEFECT BAR
# ------------------------------------------------------

with col_left:

    fig_defects = px.bar(
        defect_data,
        x="Defect Type",
        y="Count",
        text="Count",
        title="Detected Defects"
    )

    fig_defects.update_traces(
        textposition="outside"
    )

    st.plotly_chart(
        fig_defects,
        use_container_width=True
    )


# ------------------------------------------------------
# DEFECT PIE
# ------------------------------------------------------

with col_right:

    fig_defect_pie = px.pie(
        defect_data[
            defect_data["Count"] > 0
        ],
        names="Defect Type",
        values="Count",
        hole=0.4,
        title="Defect Type Distribution"
    )

    st.plotly_chart(
        fig_defect_pie,
        use_container_width=True
    )


# ======================================================
# QUALITY SCORE TREND
# ======================================================

st.subheader(
    "📈 Quality Score Trend"
)


score_trend = filtered_df.copy()


score_trend = score_trend.sort_values(
    "id"
)


fig_score = px.line(
    score_trend,
    x="inspection_id",
    y="quality_score",
    markers=True,
    title="Quality Score by Inspection"
)


fig_score.update_yaxes(
    range=[0, 100],
    title="Quality Score (%)"
)


fig_score.update_xaxes(
    title="Inspection ID"
)


st.plotly_chart(
    fig_score,
    use_container_width=True
)


# ======================================================
# DEFECT TREND
# ======================================================

st.subheader(
    "📉 Defect Trend"
)


trend_df = filtered_df.copy()


trend_df["Date"] = (
    trend_df["timestamp"]
    .dt.date
)


daily_defects = (
    trend_df
    .groupby("Date")[
        "total_defects"
    ]
    .sum()
    .reset_index()
)


if not daily_defects.empty:

    fig_trend = px.line(
        daily_defects,
        x="Date",
        y="total_defects",
        markers=True,
        title="Total Defects Over Time"
    )

    fig_trend.update_layout(
        xaxis_title="Date",
        yaxis_title="Total Defects"
    )

    st.plotly_chart(
        fig_trend,
        use_container_width=True
    )


# ======================================================
# DAILY INSPECTION VOLUME
# ======================================================

st.subheader(
    "📦 Daily Inspection Volume"
)


daily_inspections = (
    trend_df
    .groupby("Date")
    .size()
    .reset_index(
        name="Inspections"
    )
)


if not daily_inspections.empty:

    fig_volume = px.bar(
        daily_inspections,
        x="Date",
        y="Inspections",
        text="Inspections",
        title="Daily Inspection Count"
    )

    fig_volume.update_traces(
        textposition="outside"
    )

    st.plotly_chart(
        fig_volume,
        use_container_width=True
    )


# ======================================================
# QUALITY SCORE DISTRIBUTION
# ======================================================

st.subheader(
    "⭐ Quality Score Distribution"
)


fig_score_distribution = px.histogram(
    filtered_df,
    x="quality_score",
    nbins=10,
    title="Distribution of Quality Scores",
    labels={
        "quality_score": "Quality Score (%)"
    }
)


fig_score_distribution.update_xaxes(
    range=[0, 100]
)


st.plotly_chart(
    fig_score_distribution,
    use_container_width=True
)


# ======================================================
# DEFECT ANALYSIS
# ======================================================

st.subheader(
    "⚠️ Defect Analysis"
)


defect_totals = {

    "Scratches": int(
        filtered_df[
            "scratches"
        ].sum()
    ),

    "Dents": int(
        filtered_df[
            "dents"
        ].sum()
    ),

    "Rust": int(
        filtered_df[
            "rust"
        ].sum()
    ),

    "Other": int(
        filtered_df[
            "other"
        ].sum()
    )
}


total_detected = sum(
    defect_totals.values()
)


if total_detected > 0:

    most_common_defect = max(
        defect_totals,
        key=defect_totals.get
    )

    most_common_count = (
        defect_totals[
            most_common_defect
        ]
    )

    st.success(
        f"Most common defect: "
        f"**{most_common_defect}** "
        f"({most_common_count} detections)"
    )

else:

    st.info(
        "No defects detected in the selected data."
    )


# ======================================================
# SEVERITY SUMMARY
# ======================================================

st.subheader(
    "🚨 Severity Summary"
)


severity_counts = (
    filtered_df["severity"]
    .value_counts()
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "NONE",
        int(
            severity_counts.get(
                "NONE",
                0
            )
        )
    )


with col2:

    st.metric(
        "LOW",
        int(
            severity_counts.get(
                "LOW",
                0
            )
        )
    )


with col3:

    st.metric(
        "MEDIUM",
        int(
            severity_counts.get(
                "MEDIUM",
                0
            )
        )
    )


with col4:

    st.metric(
        "HIGH",
        int(
            severity_counts.get(
                "HIGH",
                0
            )
        )
    )


# ======================================================
# INSPECTION HISTORY
# ======================================================

st.subheader(
    "📋 Inspection History"
)


display_df = filtered_df.copy()


display_df["timestamp"] = (
    display_df["timestamp"]
    .dt.strftime(
        "%d-%m-%Y %H:%M:%S"
    )
)


display_df = display_df[
    [
        "inspection_id",
        "timestamp",
        "total_defects",
        "quality_score",
        "severity",
        "status",
        "inspector"
    ]
]


display_df.columns = [

    "Inspection ID",

    "Date & Time",

    "Total Defects",

    "Quality Score",

    "Severity",

    "Status",

    "Inspector"
]


display_df["Quality Score"] = (
    display_df["Quality Score"]
    .apply(
        lambda x: f"{x:.0f}%"
    )
)


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# ======================================================
# OVERALL QUALITY SUMMARY
# ======================================================

st.divider()

st.subheader(
    "🏭 Overall Production Quality"
)


if average_quality_score >= 90:

    overall_status = "EXCELLENT"

elif average_quality_score >= 75:

    overall_status = "GOOD"

elif average_quality_score >= 60:

    overall_status = "NEEDS IMPROVEMENT"

else:

    overall_status = "CRITICAL"


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "Average Quality Score",
        f"{average_quality_score:.1f}%"
    )


with col2:

    st.metric(
        "Average Defects / Inspection",
        f"{average_defects:.2f}"
    )


with col3:

    st.metric(
        "Overall Quality",
        overall_status
    )


# ======================================================
# FOOTER
# ======================================================

st.divider()

st.caption(
    "AI-Powered Steel Quality Inspection System | "
    "YOLO + OpenCV + SQLite + Streamlit + Plotly"
)