import pandas as pd


def get_cell_frequencies(conn):
    """
    Return the relative frequency of each immune cell population
    for every sample.

    Output columns:
    - sample
    - total_count
    - population
    - count
    - percentage
    """

    query = """
    WITH sample_totals AS (
        SELECT
            sample_id,
            SUM(count) AS total_count
        FROM cell_counts
        GROUP BY sample_id
    )

    SELECT
        cc.sample_id AS sample,
        st.total_count,
        cp.name AS population,
        cc.count,
        ROUND(
            100.0 * cc.count / NULLIF(st.total_count, 0),
            4
        ) AS percentage

    FROM cell_counts cc

    JOIN sample_totals st
        ON cc.sample_id = st.sample_id

    JOIN cell_populations cp
        ON cc.population_id = cp.population_id

    ORDER BY
        cc.sample_id,
        cp.population_id;
    """

    return pd.read_sql_query(query, conn)


def get_analysis_data(conn):
    """
    Return sample metadata together with cell population
    counts and relative frequencies.
    """

    query = """
    WITH sample_totals AS (
        SELECT
            sample_id,
            SUM(count) AS total_count
        FROM cell_counts
        GROUP BY sample_id
    )

    SELECT
        s.sample_id AS sample,
        s.project_id AS project,
        s.subject_id AS subject,
        sub.condition,
        sub.age,
        sub.sex,
        sub.response,
        s.treatment,
        s.sample_type,
        s.time_from_treatment_start,
        cp.name AS population,
        cc.count,
        st.total_count,
        100.0 * cc.count /
            NULLIF(st.total_count, 0) AS percentage

    FROM samples s

    JOIN subjects sub
        ON s.project_id = sub.project_id
       AND s.subject_id = sub.subject_id

    JOIN cell_counts cc
        ON s.sample_id = cc.sample_id

    JOIN cell_populations cp
        ON cc.population_id = cp.population_id

    JOIN sample_totals st
        ON s.sample_id = st.sample_id;
    """

    return pd.read_sql_query(query, conn)


def get_baseline_samples(conn):
    """
    Part 4:
    Return melanoma PBMC baseline samples from subjects
    treated with miraclib.
    """

    query = """
    SELECT
        s.sample_id AS sample,
        s.project_id AS project,
        s.subject_id AS subject,
        sub.condition,
        sub.age,
        sub.sex,
        sub.response,
        s.treatment,
        s.sample_type,
        s.time_from_treatment_start

    FROM samples s

    JOIN subjects sub
        ON s.project_id = sub.project_id
       AND s.subject_id = sub.subject_id

    WHERE LOWER(sub.condition) = 'melanoma'
      AND LOWER(s.treatment) = 'miraclib'
      AND UPPER(s.sample_type) = 'PBMC'
      AND s.time_from_treatment_start = 0

    ORDER BY
        s.project_id,
        s.subject_id,
        s.sample_id;
    """

    return pd.read_sql_query(query, conn)


def get_q1_average_b_cells(conn):
    """
    Q1:
    Average B-cell count for male melanoma responders
    at time 0 across ALL sample types and treatments.
    """

    query = """
    SELECT
        AVG(cc.count) AS average_b_cells

    FROM samples s

    JOIN subjects sub
        ON s.project_id = sub.project_id
       AND s.subject_id = sub.subject_id

    JOIN cell_counts cc
        ON s.sample_id = cc.sample_id

    JOIN cell_populations cp
        ON cc.population_id = cp.population_id

    WHERE LOWER(sub.condition) = 'melanoma'
      AND UPPER(sub.sex) = 'M'
      AND LOWER(sub.response) = 'yes'
      AND s.time_from_treatment_start = 0
      AND cp.name = 'b_cell';
    """

    result = pd.read_sql_query(query, conn)

    return result.iloc[0]["average_b_cells"]
