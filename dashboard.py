import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.queries import (
    get_analysis_data,
    get_baseline_samples,
)


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "teiko.db"
OUTPUT_DIR = ROOT / "outputs"


st.set_page_config(
    page_title="Teiko Technical Assessment",
    page_icon="🧬",
    layout="wide",
)


@st.cache_data
def load_analysis_data():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            "teiko.db not found. Run python load_data.py first."
        )

    conn = sqlite3.connect(DB_PATH)

    try:
        return get_analysis_data(conn)
    finally:
        conn.close()


@st.cache_data
def load_baseline_data():
    conn = sqlite3.connect(DB_PATH)

    try:
        return get_baseline_samples(conn)
    finally:
        conn.close()


@st.cache_data
def load_statistics():
    path = OUTPUT_DIR / "statistical_results.csv"

    if not path.exists():
        return pd.DataFrame()

    return pd.read_csv(path)


df = load_analysis_data()
baseline = load_baseline_data()
statistics = load_statistics()


st.title("Teiko Technical Assessment")
st.caption(
    "Clinical trial immune cell population analysis"
)


# =========================================================
# Sidebar filters
# =========================================================

st.sidebar.header("Filters")

conditions = sorted(
    df["condition"]
    .dropna()
    .unique()
)

selected_conditions = st.sidebar.multiselect(
    "Condition",
    options=conditions,
)

treatments = sorted(
    df["treatment"]
    .dropna()
    .unique()
)

selected_treatments = st.sidebar.multiselect(
    "Treatment",
    options=treatments,
)

sample_types = sorted(
    df["sample_type"]
    .dropna()
    .unique()
)

selected_sample_types = st.sidebar.multiselect(
    "Sample Type",
    options=sample_types,
)

responses = sorted(
    df["response"]
    .dropna()
    .unique()
)

selected_responses = st.sidebar.multiselect(
    "Response",
    options=responses,
)


filtered = df.copy()

if selected_conditions:
    filtered = filtered[
        filtered["condition"].isin(
            selected_conditions
        )
    ]

if selected_treatments:
    filtered = filtered[
        filtered["treatment"].isin(
            selected_treatments
        )
    ]

if selected_sample_types:
    filtered = filtered[
        filtered["sample_type"].isin(
            selected_sample_types
        )
    ]

if selected_responses:
    filtered = filtered[
        filtered["response"].isin(
            selected_responses
        )
    ]


# =========================================================
# Tabs
# =========================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Overview",
        "Cell Frequencies",
        "Response Analysis",
        "Baseline Analysis",
    ]
)


# =========================================================
# Overview
# =========================================================

with tab1:
    st.header("Data Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Projects",
            filtered["project"].nunique(),
        )

    with col2:
        st.metric(
            "Subjects",
            filtered["subject"].nunique(),
        )

    with col3:
        st.metric(
            "Samples",
            filtered["sample"].nunique(),
        )

    with col4:
        st.metric(
            "Treatments",
            filtered["treatment"].nunique(),
        )

    st.subheader("Filtered Dataset")

    overview_columns = [
        "sample",
        "project",
        "subject",
        "condition",
        "age",
        "sex",
        "response",
        "treatment",
        "sample_type",
        "time_from_treatment_start",
    ]

    overview = (
        filtered[overview_columns]
        .drop_duplicates()
    )

    st.dataframe(
        overview,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# Cell Frequencies
# =========================================================

with tab2:
    st.header("Cell Population Relative Frequencies")

    frequency_table = filtered[
        [
            "sample",
            "total_count",
            "population",
            "count",
            "percentage",
        ]
    ].copy()

    frequency_table["percentage"] = (
        frequency_table["percentage"]
        .round(4)
    )

    st.dataframe(
        frequency_table,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader(
        "Average Relative Frequency by Population"
    )

    average_frequency = (
        filtered
        .groupby(
            "population",
            as_index=False,
        )["percentage"]
        .mean()
    )

    fig_frequency = px.bar(
        average_frequency,
        x="population",
        y="percentage",
        labels={
            "population": "Cell Population",
            "percentage": "Average Relative Frequency (%)",
        },
    )

    st.plotly_chart(
        fig_frequency,
        use_container_width=True,
    )


# =========================================================
# Response Analysis
# =========================================================

with tab3:
    st.header(
        "Miraclib Responders vs Non-Responders"
    )

    response_data = df[
        (df["condition"].str.lower() == "melanoma")
        & (
            df["treatment"].str.lower()
            == "miraclib"
        )
        & (
            df["sample_type"].str.upper()
            == "PBMC"
        )
        & (
            df["response"]
            .str.lower()
            .isin(["yes", "no"])
        )
    ].copy()

    responder_count = (
        response_data[
            response_data["response"] == "yes"
        ]["sample"]
        .nunique()
    )

    non_responder_count = (
        response_data[
            response_data["response"] == "no"
        ]["sample"]
        .nunique()
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Responder Samples",
            responder_count,
        )

    with col2:
        st.metric(
            "Non-Responder Samples",
            non_responder_count,
        )

    st.subheader(
        "Relative Frequency Distribution"
    )

    fig_response = px.box(
        response_data,
        x="population",
        y="percentage",
        color="response",
        points="all",
        title=(
            "Melanoma PBMC Cell Frequencies: "
            "Miraclib Responders vs Non-Responders"
        ),
        labels={
            "population": "Cell Population",
            "percentage": "Relative Frequency (%)",
            "response": "Response",
        },
    )

    st.plotly_chart(
        fig_response,
        use_container_width=True,
    )

    st.subheader("Statistical Results")

    if statistics.empty:
        st.warning(
            "Statistical results not found. "
            "Run python analysis.py first."
        )
    else:
        display_stats = statistics.copy()

        numeric_columns = [
            "responder_mean",
            "non_responder_mean",
            "mean_difference",
            "t_statistic",
            "p_value",
            "adjusted_p_value",
        ]

        for column in numeric_columns:
            display_stats[column] = (
                display_stats[column]
                .round(6)
            )

        st.dataframe(
            display_stats,
            use_container_width=True,
            hide_index=True,
        )

        significant = display_stats[
            display_stats["significant"]
            == True
        ]

        if significant.empty:
            st.info(
                "No statistically significant "
                "cell populations were identified."
            )
        else:
            names = ", ".join(
                significant["population"]
                .tolist()
            )

            st.success(
                f"Significant population(s): {names}"
            )

            st.write(
                "CD4 T-cell relative frequency is "
                "significantly higher in responders "
                "than non-responders after FDR correction."
            )


# =========================================================
# Baseline Analysis
# =========================================================

with tab4:
    st.header(
        "Melanoma Miraclib Baseline Analysis"
    )

    st.caption(
        "PBMC samples at "
        "time_from_treatment_start = 0"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Baseline Samples",
            baseline["sample"].nunique(),
        )

    with col2:
        responders = (
            baseline[
                baseline["response"] == "yes"
            ]["subject"]
            .nunique()
        )

        st.metric(
            "Responder Subjects",
            responders,
        )

    with col3:
        non_responders = (
            baseline[
                baseline["response"] == "no"
            ]["subject"]
            .nunique()
        )

        st.metric(
            "Non-Responder Subjects",
            non_responders,
        )

    st.subheader("Baseline Samples")

    st.dataframe(
        baseline,
        use_container_width=True,
        hide_index=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Samples by Project")

        project_counts = (
            baseline
            .groupby(
                "project",
                as_index=False,
            )["sample"]
            .nunique()
            .rename(
                columns={
                    "sample": "sample_count"
                }
            )
        )

        project_fig = px.bar(
            project_counts,
            x="project",
            y="sample_count",
            labels={
                "project": "Project",
                "sample_count": "Samples",
            },
        )

        st.plotly_chart(
            project_fig,
            use_container_width=True,
        )

    with col2:
        st.subheader("Subjects by Sex")

        sex_counts = (
            baseline
            .groupby(
                "sex",
                as_index=False,
            )["subject"]
            .nunique()
            .rename(
                columns={
                    "subject": "subject_count"
                }
            )
        )

        sex_fig = px.bar(
            sex_counts,
            x="sex",
            y="subject_count",
            labels={
                "sex": "Sex",
                "subject_count": "Subjects",
            },
        )

        st.plotly_chart(
            sex_fig,
            use_container_width=True,
        )

    st.subheader("Responder Status")

    response_counts = (
        baseline[
            baseline["response"]
            .isin(["yes", "no"])
        ]
        .groupby(
            "response",
            as_index=False,
        )["subject"]
        .nunique()
        .rename(
            columns={
                "subject": "subject_count"
            }
        )
    )

    st.dataframe(
        response_counts,
        use_container_width=True,
        hide_index=True,
    )
