from pathlib import Path
import sqlite3
import pandas as pd

DB_FILE = Path("data/processed/boxoffice.db")
OUTPUT_FILE = Path("data/processed/recommendation_outputs.csv")
EXAMPLES_FILE = Path("data/processed/recommendation_examples.csv")

query = """
WITH movie_weeks AS (
    SELECT
        movie_title,
        week_start,
        week_number,
        theaters,
        days_in_release,
        per_theater,
        LAG(per_theater) OVER (
            PARTITION BY movie_title
            ORDER BY week_number
        ) AS prev_per_theater
    FROM box_office
),
changes AS (
    SELECT
        movie_title,
        week_start,
        week_number,
        theaters,
        days_in_release,
        per_theater,
        prev_per_theater,
        CASE
            WHEN prev_per_theater IS NOT NULL AND prev_per_theater != 0
            THEN (per_theater - prev_per_theater) / prev_per_theater
            ELSE NULL
        END AS pct_change_per_theater
    FROM movie_weeks
)
SELECT
    movie_title,
    week_start,
    week_number,
    theaters,
    days_in_release,
    per_theater,
    prev_per_theater,
    pct_change_per_theater,
    CASE
        WHEN pct_change_per_theater <= -0.45 AND theaters >= 1000 AND days_in_release > 7
            THEN 'REDUCE'
        WHEN pct_change_per_theater > -0.15 AND theaters >= 500
            THEN 'HOLD_OR_SUPPORT'
        WHEN pct_change_per_theater > 0
            THEN 'EXPAND_OR_SUPPORT'
        ELSE 'HOLD'
    END AS recommendation
FROM changes
WHERE prev_per_theater IS NOT NULL
ORDER BY week_start, recommendation, per_theater DESC;
"""

conn = sqlite3.connect(DB_FILE)
df = pd.read_sql_query(query, conn)
conn.close()

df.to_csv(OUTPUT_FILE, index=False)

# smaller sample file for easier review
examples_df = pd.concat([
    df[df["recommendation"] == "REDUCE"].head(10),
    df[df["recommendation"] == "EXPAND_OR_SUPPORT"].head(10),
    df[df["recommendation"] == "HOLD_OR_SUPPORT"].head(10),
    df[df["recommendation"] == "HOLD"].head(10),
], ignore_index=True)

examples_df.to_csv(EXAMPLES_FILE, index=False)

print(f"Saved full recommendation output to: {OUTPUT_FILE}")
print(f"Saved example recommendation output to: {EXAMPLES_FILE}")
print(f"Total recommendation rows: {len(df)}")
print("\nRecommendation counts:")
print(df["recommendation"].value_counts())
print("\nFirst 10 rows:")
print(df.head(10))