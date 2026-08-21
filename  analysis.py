import sqlite3
from pathlib import Path

from src.queries import get_cell_frequencies


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "teiko.db"
OUTPUT_DIR = ROOT / "outputs"
FREQUENCY_OUTPUT = OUTPUT_DIR / "cell_frequencies.csv"


def validate_frequencies(df):
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


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            "Database not found. Run 'python load_data.py' first."
        )

    OUTPUT_DIR.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    try:
        print("Generating Part 2 cell frequency summary...")

        frequencies = get_cell_frequencies(conn)

        validate_frequencies(frequencies)

        frequencies.to_csv(
            FREQUENCY_OUTPUT,
            index=False,
        )

        print(f"Generated {len(frequencies):,} rows")

        print("\nFirst 10 rows:")
        print(
            frequencies.head(10).to_string(index=False)
        )

        print(
            f"\nOutput saved to: {FREQUENCY_OUTPUT}"
        )

    finally:
        conn.close()


if __name__ == "__main__":
    main()
