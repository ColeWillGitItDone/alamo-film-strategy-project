from pathlib import Path
import pandas as pd
import sqlite3

RAW_FILE = Path("data/raw/weekly_box_office_2025_2026.csv")
DB_FILE = Path("data/processed/boxoffice.db")
CLEAN_CSV = Path("data/processed/weekly_box_office_cleaned.csv")

DB_FILE.parent.mkdir(parents=True, exist_ok=True)


def clean_currency(value):
    if pd.isna(value) or value == "":
        return None
    value = str(value).replace("$", "").replace(",", "").strip()
    try:
        return float(value)
    except ValueError:
        return None


def clean_integer(value):
    if pd.isna(value) or value == "":
        return None
    value = str(value).replace(",", "").strip()
    try:
        return int(value)
    except ValueError:
        return None


def clean_percent(value):
    if pd.isna(value) or value == "":
        return None

    value = str(value).strip()

    # keep blanks and clearly non-percent placeholders as null
    if value in ["", "(new)", "new", "—", "-", "nan", "None"]:
        return None

    # only parse values that actually look like percentages
    if "%" in value:
        value = value.replace("%", "").replace("+", "").replace(",", "").strip()
        try:
            return float(value) / 100
        except ValueError:
            return None

    # anything else is suspicious for this column, so return null
    return None


def create_is_new_release(days_in_release):
    if pd.isna(days_in_release):
        return 0
    return 1 if int(days_in_release) <= 7 else 0


def create_wide_release_flag(theaters):
    if pd.isna(theaters):
        return 0
    return 1 if int(theaters) >= 1000 else 0


df = pd.read_csv(RAW_FILE)

print("Raw columns found:")
print(df.columns.tolist())
print(f"Raw row count: {len(df)}")

df = df.rename(columns={
    "Rank": "rank",
    "Prev": "prev_rank_text",
    "Title": "movie_title",
    "Daily Gross": "weekly_gross",
    "Weekly Change": "weekly_change_pct",
    "Theaters": "theaters",
    "Theater Average": "per_theater",
    "Total Gross": "total_gross",
    "Days in Release": "days_in_release"
})

# optional debugging check: show suspicious values in weekly_change_pct
suspicious_weekly_change = df[
    df["weekly_change_pct"].notna() &
    ~df["weekly_change_pct"].astype(str).str.contains("%", regex=False)
]["weekly_change_pct"].astype(str).value_counts()

print("\nSuspicious non-percent values found in weekly_change_pct before cleaning:")
print(suspicious_weekly_change.head(20))

df["rank"] = df["rank"].apply(clean_integer)
df["weekly_gross"] = df["weekly_gross"].apply(clean_currency)
df["weekly_change_pct"] = df["weekly_change_pct"].apply(clean_percent)
df["theaters"] = df["theaters"].apply(clean_integer)
df["per_theater"] = df["per_theater"].apply(clean_currency)
df["total_gross"] = df["total_gross"].apply(clean_currency)
df["days_in_release"] = df["days_in_release"].apply(clean_integer)

df["week_start"] = pd.to_datetime(df["week_start"])

unique_weeks = sorted(df["week_start"].dropna().unique())
week_map = {week: i + 1 for i, week in enumerate(unique_weeks)}
df["week_number"] = df["week_start"].map(week_map)

df["is_new_release"] = df["days_in_release"].apply(create_is_new_release)
df["wide_release_flag"] = df["theaters"].apply(create_wide_release_flag)

df.to_csv(CLEAN_CSV, index=False)

conn = sqlite3.connect(DB_FILE)
df.to_sql("box_office", conn, if_exists="replace", index=False)
conn.close()

print(f"\nSaved cleaned CSV to: {CLEAN_CSV}")
print(f"Saved SQLite DB to: {DB_FILE}")
print(f"Rows loaded: {len(df)}")
print("Columns:")
print(df.columns.tolist())
print("\nFirst 5 cleaned rows:")
print(df.head())