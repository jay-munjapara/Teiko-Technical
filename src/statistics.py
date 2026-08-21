import pandas as pd

from scipy.stats import ttest_ind
from statsmodels.stats.multitest import multipletests


def filter_miraclib_pbmc(df):
    """
    Keep only melanoma PBMC samples treated with miraclib
    and with a known yes/no response.
    """

    return df[
        (df["condition"].str.lower() == "melanoma")
        & (df["treatment"].str.lower() == "miraclib")
        & (df["sample_type"].str.upper() == "PBMC")
        & (df["response"].str.lower().isin(["yes", "no"]))
    ].copy()


def compare_responders(df):
    """
    Compare relative cell frequencies between responders
    and non-responders using Welch's t-test.
    """

    filtered = filter_miraclib_pbmc(df)

    results = []

    for population in sorted(filtered["population"].unique()):

        population_df = filtered[
            filtered["population"] == population
        ]

        responders = population_df[
            population_df["response"].str.lower() == "yes"
        ]["percentage"]

        non_responders = population_df[
            population_df["response"].str.lower() == "no"
        ]["percentage"]

        statistic, p_value = ttest_ind(
            responders,
            non_responders,
            equal_var=False,
            nan_policy="omit",
        )

        results.append(
            {
                "population": population,
                "responder_n": len(responders),
                "non_responder_n": len(non_responders),
                "responder_mean": responders.mean(),
                "non_responder_mean": non_responders.mean(),
                "mean_difference": (
                    responders.mean()
                    - non_responders.mean()
                ),
                "t_statistic": statistic,
                "p_value": p_value,
            }
        )

    results_df = pd.DataFrame(results)

    # Correct for multiple hypothesis tests.
    _, adjusted_p_values, _, _ = multipletests(
        results_df["p_value"],
        alpha=0.05,
        method="fdr_bh",
    )

    results_df["adjusted_p_value"] = adjusted_p_values

    results_df["significant"] = (
        results_df["adjusted_p_value"] < 0.05
    )

    return results_df
