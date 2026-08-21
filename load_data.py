import sqlite3
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "cell-count.csv"
DB_PATH = ROOT / "teiko.db"


CELL_TYPES = [
    "b_cell",
    "cd8_t_cell",
    "cd4_t_cell",
    "nk_cell",
    "monocyte",
]


# ---------------------------------------------------------
# Database schema
# ---------------------------------------------------------

def create_schema(conn):
    """
    Create a normalized relational schema.

    Main entities:
    - projects
    - subjects
    - samples
    - cell_populations
    - cell_counts
    """

    conn.executescript(
        """
        DROP TABLE IF EXISTS cell_counts;
        DROP TABLE IF EXISTS cell_populations;
        DROP TABLE IF EXISTS samples;
        DROP TABLE IF EXISTS subjects;
        DROP TABLE IF EXISTS projects;


        CREATE TABLE projects (
            project_id TEXT PRIMARY KEY
        );


        CREATE TABLE subjects (
            project_id TEXT NOT NULL,
            subject_id TEXT NOT NULL,
            condition TEXT NOT NULL,
            age INTEGER NOT NULL,
            sex TEXT NOT NULL,
            response TEXT,

            PRIMARY KEY (project_id, subject_id),

            FOREIGN KEY (project_id)
                REFERENCES projects(project_id)
        );


        CREATE TABLE samples (
            sample_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            subject_id TEXT NOT NULL,
            sample_type TEXT NOT NULL,
            treatment TEXT NOT NULL,
            time_from_treatment_start INTEGER NOT NULL,

            FOREIGN KEY (project_id, subject_id)
                REFERENCES subjects(project_id, subject_id)
        );


        CREATE TABLE cell_populations (
            population_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );


        CREATE TABLE cell_counts (
            sample_id TEXT NOT NULL,
            population_id INTEGER NOT NULL,
            count INTEGER NOT NULL CHECK (count >= 0),

            PRIMARY KEY (sample_id, population_id),

            FOREIGN KEY (sample_id)
                REFERENCES samples(sample_id),

            FOREIGN KEY (population_id)
                REFERENCES cell_populations(population_id)
        );


        CREATE INDEX idx_subject_condition
        ON subjects(condition);


        CREATE INDEX idx_subject_response
        ON subjects(response);


        CREATE INDEX idx_subject_sex
        ON subjects(sex);


        CREATE INDEX idx_sample_treatment
        ON samples(treatment);


        CREATE INDEX idx_sample_type
        ON samples(sample_type);


        CREATE INDEX idx_sample_time
        ON samples(time_from_treatment_start);
        """
    )


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

def validate_subject_metadata(df):
    """
    Check that subject-level metadata does not conflict
    across different samples for the same subject.
    """

    subject_columns = [
        "condition",
        "age",
        "sex",
        "response",
    ]

    grouped = df.groupby(
        ["project", "subject"],
        dropna=False,
    )

    for column in subject_columns:
        conflicts = grouped[column].nunique(dropna=True)

        if (conflicts > 1).any():
            raise ValueError(
                f"Conflicting values found for subject column: {column}"
            )


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------

def load_projects(conn, df):
    projects = (
        df[["project"]]
        .drop_duplicates()
        .rename(columns={"project": "project_id"})
    )

    projects.to_sql(
        "projects",
        conn,
        if_exists="append",
        index=False,
    )


def load_subjects(conn, df):
    validate_subject_metadata(df)

    subjects = (
        df[
            [
                "project",
                "subject",
                "condition",
                "age",
                "sex",
                "response",
            ]
        ]
        .groupby(
            ["project", "subject"],
            as_index=False,
            dropna=False,
        )
        .first()
        .rename(
            columns={
                "project": "project_id",
                "subject": "subject_id",
            }
        )
    )

    subjects.to_sql(
        "subjects",
        conn,
        if_exists="append",
        index=False,
    )


def load_samples(conn, df):
    samples = df[
        [
            "sample",
            "project",
            "subject",
            "sample_type",
            "treatment",
            "time_from_treatment_start",
        ]
    ].rename(
        columns={
            "sample": "sample_id",
            "project": "project_id",
            "subject": "subject_id",
        }
    )

    samples.to_sql(
        "samples",
        conn,
        if_exists="append",
        index=False,
    )


def load_cell_populations(conn):
    population_ids = {}

    for population in CELL_TYPES:
        cursor = conn.execute(
            """
            INSERT INTO cell_populations (name)
            VALUES (?)
            """,
            (population,),
        )

        population_ids[population] = cursor.lastrowid

    return population_ids


def load_cell_counts(conn, df, population_ids):
    rows = []

    for row in df.itertuples(index=False):

        for population in CELL_TYPES:

            rows.append(
                (
                    row.sample,
                    population_ids[population],
                    int(getattr(row, population)),
                )
            )

    conn.executemany(
        """
        INSERT INTO cell_counts (
            sample_id,
            population_id,
            count
        )
        VALUES (?, ?, ?)
        """,
        rows,
    )


# ---------------------------------------------------------
# Verification
# ---------------------------------------------------------

def print_summary(conn):
    tables = [
        "projects",
        "subjects",
        "samples",
        "cell_populations",
        "cell_counts",
    ]

    print("\nDatabase load summary")
    print("---------------------")

    for table in tables:

        count = conn.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]

        print(f"{table}: {count:,} rows")


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Could not find input file: {CSV_PATH}"
        )

    print(f"Reading: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)

    print(f"Loaded {len(df):,} CSV rows")

    conn = sqlite3.connect(DB_PATH)

    try:
        # Enforce SQLite foreign keys.
        conn.execute("PRAGMA foreign_keys = ON")

        create_schema(conn)

        load_projects(conn, df)

        load_subjects(conn, df)

        load_samples(conn, df)

        population_ids = load_cell_populations(conn)

        load_cell_counts(
            conn,
            df,
            population_ids,
        )

        conn.commit()

        print_summary(conn)

        print(f"\nDatabase created successfully:")
        print(DB_PATH)

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    main()
