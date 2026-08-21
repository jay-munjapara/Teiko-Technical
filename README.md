# Teiko Technical Assessment

## Overview

This project analyzes immune cell population data from a clinical trial using Python, SQLite, statistical testing, and an interactive Streamlit dashboard.

The workflow is designed to be fully reproducible and includes:

1. Loading `cell-count.csv` into a normalized SQLite database
2. Calculating relative frequencies for each immune cell population per sample
3. Comparing miraclib responders and non-responders for melanoma PBMC samples
4. Performing statistical significance testing across immune cell populations
5. Analyzing baseline melanoma PBMC samples
6. Generating output tables and visualizations
7. Serving the results through an interactive Streamlit dashboard

## Project Structure

```text
Teiko-Technical/
├── cell-count.csv
├── inspect_data.py
├── load_data.py
├── analysis.py
├── dashboard.py
├── requirements.txt
├── Makefile
├── README.md
├── teiko.db
│
├── src/
│   ├── __init__.py
│   ├── queries.py
│   └── statistics.py
│
└── outputs/
    ├── cell_frequencies.csv
    ├── statistical_results.csv
    ├── responder_boxplot.html
    ├── baseline_samples.csv
    ├── baseline_project_counts.csv
    ├── baseline_response_counts.csv
    ├── baseline_gender_counts.csv
    └── q1_answer.txt
```

## Setup and Running the Project

### Install Dependencies

Run `make setup`.

This installs all required Python packages listed in `requirements.txt`.

### Optional Virtual Environment

For local development, you can create and activate a virtual environment before installing dependencies.

Run `python3 -m venv .venv`.

Then activate it with `source .venv/bin/activate`.

After activation, run `make setup`.

### Run the Full Data Pipeline

Run `make pipeline`.

This command executes the complete workflow automatically:

1. Creates and initializes the SQLite database
2. Loads all rows from `cell-count.csv`
3. Generates the cell population relative frequency table
4. Runs the responder vs non-responder statistical analysis
5. Generates the responder boxplot
6. Runs the baseline subset analysis
7. Calculates the Q1 result

All generated analysis files are written to the `outputs/` directory.

### Run the Dashboard

Run `make dashboard`.

## Part 1: Database Schema

The project uses a normalized SQLite relational database with five main tables:

- `projects`
- `subjects`
- `samples`
- `cell_populations`
- `cell_counts`

This separates project metadata, subject metadata, sample metadata, cell population definitions, and individual cell-count measurements.

The normalized design reduces duplication and makes the database easier to extend as the number of projects, samples, subjects, and immune cell populations grows.
This starts the interactive Streamlit dashboard.

The dashboard includes:

- Data Overview
- Cell Population Frequencies
- Miraclib Response Analysis
- Statistical Results
- Baseline Analysis

When running locally, Streamlit will display the dashboard URL in the terminal.

### Projects and Subjects

The `projects` table stores each unique project identifier.

The `subjects` table stores subject-level information including:

- `project_id`
- `subject_id`
- `condition`
- `age`
- `sex`
- `response`

The `subjects` table uses a composite primary key of `project_id` and `subject_id`.

This allows the same subject identifier to appear in different projects without creating a conflict.

The `response` field is nullable because some rows in the source dataset do not contain a recorded response.

### Samples, Cell Populations, and Cell Counts

The `samples` table stores sample-level metadata including:

- `sample_id`
- `project_id`
- `subject_id`
- `sample_type`
- `treatment`
- `time_from_treatment_start`

Each sample is linked back to its subject using `project_id` and `subject_id`.

The `cell_populations` table stores the immune cell population names:

- `b_cell`
- `cd8_t_cell`
- `cd4_t_cell`
- `nk_cell`
- `monocyte`

The `cell_counts` table stores one measurement per sample and cell population using:

- `sample_id`
- `population_id`
- `count`

The combination of `sample_id` and `population_id` is used as the primary key, ensuring that each sample has only one count for each immune cell population.

### Schema Design Rationale and Scalability

The source CSV stores immune cell populations as separate columns, but the database stores them as rows in the `cell_counts` table.

This normalized design avoids hard-coding each cell population as its own database column and makes the schema easier to extend if new immune cell types are added later.

The design also reduces duplication by separating project, subject, sample, and measurement data into different tables.

For larger datasets with hundreds of projects and thousands of samples, the same structure can continue to scale by:

- adding indexes to frequently queried columns
- using efficient bulk inserts
- moving from SQLite to PostgreSQL or another production relational database if needed
- caching frequently used aggregate results
- storing large analytical outputs in formats such as Parquet

The overall relational model can remain the same even if the underlying database technology changes.

## Part 2: Cell Population Relative Frequencies

For each sample, the total cell count is calculated by summing the five immune cell populations:

`b_cell + cd8_t_cell + cd4_t_cell + nk_cell + monocyte`

The relative frequency for each population is then calculated as:

`percentage = population_count / total_count * 100`

The generated summary contains the required columns:

- `sample`
- `total_count`
- `population`
- `count`
- `percentage`

The dataset contains 10,500 samples and 5 immune cell populations, producing 52,500 rows in the long-format output.

The generated file is:

`outputs/cell_frequencies.csv`

For each sample, the five population percentages sum to approximately 100%.

## Part 3: Statistical Analysis

The treatment-response analysis focuses on samples that meet all of the following criteria:

- `condition = melanoma`
- `treatment = miraclib`
- `sample_type = PBMC`
- `response = yes` or `response = no`

The analysis compares the relative frequency of each immune cell population between responders and non-responders.

Welch's independent two-sample t-test is used because it does not assume equal variance between the two groups.

Because five immune cell populations are tested, Benjamini-Hochberg false discovery rate correction is applied to reduce the chance of false-positive findings.

A population is considered statistically significant when:

`adjusted_p_value < 0.05`

The analysis found that `cd4_t_cell` was the only statistically significant population after FDR correction.

Key result:

- Responder mean: `30.5378%`
- Non-responder mean: `29.9023%`
- Adjusted p-value: `0.025063`

The remaining populations were not statistically significant after correction.

The complete statistical results are stored in:

`outputs/statistical_results.csv`

The responder vs non-responder boxplot is stored in:

`outputs/responder_boxplot.html`

## Part 4: Baseline Subset Analysis

The baseline analysis includes samples that meet all of the following criteria:

- `condition = melanoma`
- `sample_type = PBMC`
- `treatment = miraclib`
- `time_from_treatment_start = 0`

The query identified a total of `656` baseline samples.

### Samples per Project

- `prj1`: 384 samples
- `prj3`: 272 samples

### Responders and Non-Responders

Because the requirement asks for subjects, distinct subjects are counted rather than sample rows.

- Responders: 331
- Non-responders: 325

### Male and Female Subjects

Distinct subjects are also used for the sex summary.

- Female: 312
- Male: 344

The generated outputs are stored in:

- `outputs/baseline_samples.csv`
- `outputs/baseline_project_counts.csv`
- `outputs/baseline_response_counts.csv`
- `outputs/baseline_gender_counts.csv`

## Q1 Result

Question:

Considering melanoma males of all sample and treatment types, what is the average number of B cells for responders at `time_from_treatment_start = 0`?

The calculation uses the following filters:

- `condition = melanoma`
- `sex = M`
- `response = yes`
- `time_from_treatment_start = 0`
- `population = b_cell`

The calculation intentionally does not filter by treatment or sample type because the question specifies all sample and treatment types.

The average B-cell count is:

`10206.15`

The result is also saved in:

`outputs/q1_answer.txt`

## Code Structure

The project is split into small, focused modules so that data loading, querying, statistical analysis, and visualization remain separate.

### `load_data.py`

Responsible for:

- reading `cell-count.csv`
- creating the SQLite database schema
- loading projects, subjects, samples, populations, and cell counts
- preserving missing response values
- validating subject-level metadata consistency

Running `python load_data.py` creates `teiko.db` in the repository root.

### `src/queries.py`

Contains reusable SQL queries for:

- Part 2 relative frequency calculations
- joining sample metadata with cell measurements
- Part 4 baseline filtering
- Q1 calculation

### `src/statistics.py`

Contains the statistical analysis logic for:

- filtering melanoma PBMC samples treated with miraclib
- separating responders and non-responders
- Welch's t-test
- Benjamini-Hochberg FDR correction

### `analysis.py`

Coordinates the full analytical workflow for Parts 2 through 4.

It:

- generates the relative frequency table
- validates frequency calculations
- performs responder vs non-responder analysis
- generates the response boxplot
- creates baseline subset outputs
- calculates Q1

### `dashboard.py`

Provides the interactive Streamlit dashboard for exploring:

- overall dataset information
- relative cell frequencies
- responder vs non-responder comparisons
- statistical results
- baseline subset analysis

This separation keeps the project easier to test, maintain, and extend.

## Generated Outputs

Running `make pipeline` generates the SQLite database and all required analysis outputs.

The generated database is:

- `teiko.db`

The generated analysis files are:

- `outputs/cell_frequencies.csv`
- `outputs/statistical_results.csv`
- `outputs/responder_boxplot.html`
- `outputs/baseline_samples.csv`
- `outputs/baseline_project_counts.csv`
- `outputs/baseline_response_counts.csv`
- `outputs/baseline_gender_counts.csv`
- `outputs/q1_answer.txt`

These files contain the results for Parts 2 through 4 and can be regenerated at any time by running `make pipeline`.

## Dashboard

The project includes an interactive Streamlit dashboard for exploring the analysis results.

The dashboard provides four main sections:

- Overview
- Cell Frequencies
- Response Analysis
- Baseline Analysis

The Overview section displays high-level information such as the number of projects, subjects, samples, and treatments.

The Cell Frequencies section displays the relative frequency of each immune cell population for individual samples.

The Response Analysis section compares miraclib responders and non-responders for melanoma PBMC samples using interactive boxplots and statistical results.

The Baseline Analysis section displays the baseline melanoma PBMC cohort, including samples by project, responder status, and sex.

Run the dashboard locally with `make dashboard`.

## Key Findings

The main findings from the analysis are:

- The dataset contains 10,500 samples and 5 immune cell populations.
- The relative frequency analysis generated 52,500 sample-population records.
- For melanoma PBMC samples treated with miraclib, `cd4_t_cell` was the only population with a statistically significant difference between responders and non-responders after FDR correction.
- The mean CD4 T-cell relative frequency was approximately `30.54%` for responders and `29.90%` for non-responders.
- The adjusted p-value for `cd4_t_cell` was `0.025063`.
- The baseline melanoma PBMC miraclib cohort contained 656 samples.
- `prj1` contributed 384 baseline samples and `prj3` contributed 272.
- The baseline cohort contained 331 responder subjects and 325 non-responder subjects.
- The baseline cohort contained 344 male subjects and 312 female subjects.
- The Q1 average B-cell count for melanoma male responders at time 0 across all sample and treatment types was `10206.15`.

Overall, the analysis suggests that CD4 T-cell relative frequency may be associated with response to miraclib in this melanoma PBMC cohort, while the other measured immune cell populations did not show statistically significant differences after multiple-testing correction.
