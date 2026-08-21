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
