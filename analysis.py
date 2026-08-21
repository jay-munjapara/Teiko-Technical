import sqlite3
from pathlib import Path

import plotly.express as px

from src.queries import (
    get_cell_frequencies,
    get_analysis_data,
    get_baseline_samples,
    get_q1_average_b_cells,
)

from src.statistics import (
    compare_responders,
    filter_miraclib_pbmc,
)


ROOT = Path(__file__).resolve().parent

DB_PATH = ROOT / "teiko.db"
OUTPUT_DIR = ROOT / "outputs"

FREQUENCY_OUTPUT = OUTPUT_DIR / "cell_frequencies.csv"
STATISTICS_OUTPUT = OUTPUT_DIR / "statistical_results.csv"
BOXPLOT_OUTPUT = OUTPUT_DIR / "responder_boxplot.html"

BASELINE_OUTPUT = OUTPUT_DIR / "baseline_samples.csv"

PROJECT_COUNTS_OUTPUT = (
    OUTPUT_DIR / "baseline_project_counts.csv"
)

RESPONSE_COUNTS_OUTPUT = (
    OUTPUT_DIR / "baseline_response_counts.csv"
)

GENDER_COUNTS_OUTPUT = (
    OUTPUT_DIR / "baseline_gender_counts.csv"
)

Q1_OUTPUT = OUTPUT_DIR / "q1_answer.txt"


def validate_frequencies(df):
    """
    Validate the Part 2 output.
    """

    expected_columns = [
        "sample",
        "total_count",
        "population",
        "count",
        "percentage",
    ]

    if list(df.columns) != expected_columns:
        raise ValueError(
            "Frequency output columns do not match requirements."
        )

    populations_per_sample = (
        df.groupby("sample")["population"].nunique()
    )

    if not (populations_per_sample == 5).all():
        raise ValueError(
            "Every sample should contain exactly 5 populations."
        )

    percentage_sums = (
        df.groupby("sample")["percentage"].sum()
    )

    if not percentage_sums.between(
        99.99,
        100.01,
    ).all():
        raise ValueError(
            "Population percentages should sum to approximately 100%."
        )


def create_response_boxplot(df):
    """
    Create an interactive boxplot comparing
    responders vs non-responders for Part 3.
    """

    filtered = filter_miraclib_pbmc(df)

    fig = px.box(
        filtered,
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

    fig.write_html(
        BOXPLOT_OUTPUT,
        include_plotlyjs="cdn",
    )


def run_baseline_analysis(conn):
    """
    Run Part 4 baseline subset analysis.
    """

    baseline = get_baseline_samples(conn)

    if baseline.empty:
        raise ValueError(
            "No melanoma PBMC miraclib baseline samples were found."
        )

    # Save all qualifying samples.
    baseline.to_csv(
        BASELINE_OUTPUT,
        index=False,
    )

    # ---------------------------------------------
    # Samples from each project
    # ---------------------------------------------

    project_counts = (
        baseline
        .groupby("project")["sample"]
        .nunique()
        .reset_index(name="sample_count")
    )

    project_counts.to_csv(
        PROJECT_COUNTS_OUTPUT,
        index=False,
    )

    # ---------------------------------------------
    # Unique responder/non-responder subjects
    # ---------------------------------------------

    known_response = baseline[
        baseline["response"]
        .str.lower()
        .isin(["yes", "no"])
    ]

    response_counts = (
        known_response
        .groupby("response")["subject"]
        .nunique()
        .reset_index(name="subject_count")
    )

    response_counts.to_csv(
        RESPONSE_COUNTS_OUTPUT,
        index=False,
    )

    # ---------------------------------------------
    # Unique male/female subjects
    # ---------------------------------------------

    gender_counts = (
        baseline
        .groupby("sex")["subject"]
        .nunique()
        .reset_index(name="subject_count")
    )

    gender_counts.to_csv(
        GENDER_COUNTS_OUTPUT,
        index=False,
    )

    # ---------------------------------------------
    # Q1
    # ---------------------------------------------

    q1_average = get_q1_average_b_cells(conn)

    with open(Q1_OUTPUT, "w") as file:
        file.write(
            "Average B-cell count for male melanoma "
            "responders at time 0: "
            f"{q1_average:.2f}\n"
        )

    return (
        baseline,
        project_counts,
        response_counts,
        gender_counts,
        q1_average,
    )


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            "Database not found. Run 'python load_data.py' first."
        )

    OUTPUT_DIR.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    try:
        # -------------------------------------------------
        # Part 2: Cell Population Relative Frequencies
        # -------------------------------------------------

        print("\nGenerating Part 2 cell frequency summary...")

        frequencies = get_cell_frequencies(conn)

        validate_frequencies(frequencies)

        frequencies.to_csv(
            FREQUENCY_OUTPUT,
            index=False,
        )

        print(
            f"Generated {len(frequencies):,} frequency rows"
        )

        print("\nFirst 10 rows:")
        print(
            frequencies.head(10).to_string(index=False)
        )

        print(
            f"\nPart 2 output saved to: "
            f"{FREQUENCY_OUTPUT}"
        )

        # -------------------------------------------------
        # Part 3: Statistical Analysis
        # -------------------------------------------------

        print(
            "\nGenerating Part 3 responder vs "
            "non-responder analysis..."
        )

        analysis_data = get_analysis_data(conn)

        statistics = compare_responders(
            analysis_data
        )

        statistics.to_csv(
            STATISTICS_OUTPUT,
            index=False,
        )

        create_response_boxplot(
            analysis_data
        )

        print("\nStatistical results:")

        print(
            statistics.to_string(
                index=False
            )
        )

        significant = statistics[
            statistics["significant"]
        ]

        print("\nSignificant populations:")

        if significant.empty:
            print(
                "No populations were significant "
                "after FDR correction."
            )
        else:
            print(
                significant[
                    [
                        "population",
                        "responder_mean",
                        "non_responder_mean",
                        "adjusted_p_value",
                    ]
                ].to_string(index=False)
            )

        print(
            f"\nPart 3 statistics saved to: "
            f"{STATISTICS_OUTPUT}"
        )

        print(
            f"Part 3 boxplot saved to: "
            f"{BOXPLOT_OUTPUT}"
        )

        # -------------------------------------------------
        # Part 4: Baseline Subset Analysis
        # -------------------------------------------------

        print("\nGenerating Part 4 baseline analysis...")

        (
            baseline,
            project_counts,
            response_counts,
            gender_counts,
            q1_average,
        ) = run_baseline_analysis(conn)

        print(
            f"\nBaseline samples found: "
            f"{baseline['sample'].nunique():,}"
        )

        print("\nSamples per project:")
        print(
            project_counts.to_string(
                index=False
            )
        )

        print("\nResponder / non-responder subjects:")
        print(
            response_counts.to_string(
                index=False
            )
        )

        print("\nMale / female subjects:")
        print(
            gender_counts.to_string(
                index=False
            )
        )

        print("\nQ1 Answer:")
        print(
            f"Average B-cell count = "
            f"{q1_average:.2f}"
        )

        print(
            f"\nBaseline samples saved to: "
            f"{BASELINE_OUTPUT}"
        )

        print(
            f"Project counts saved to: "
            f"{PROJECT_COUNTS_OUTPUT}"
        )

        print(
            f"Response counts saved to: "
            f"{RESPONSE_COUNTS_OUTPUT}"
        )

        print(
            f"Gender counts saved to: "
            f"{GENDER_COUNTS_OUTPUT}"
        )

        print(
            f"Q1 answer saved to: "
            f"{Q1_OUTPUT}"
        )

        print("\nAnalysis completed successfully.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
