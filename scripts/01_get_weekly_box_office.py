from datetime import datetime, timedelta
from pathlib import Path
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup

# Weekly historical page format on The Numbers
BASE_URL = "https://www.the-numbers.com/box-office-chart/weekly/{year}/{month:02d}/{day:02d}"

# Requested range:
# start week = Friday 2025-03-07
# end week   = Friday 2026-03-06 (covers through Thursday 2026-03-12)
START_DATE = datetime(2025, 3, 7)
END_DATE = datetime(2026, 3, 6)

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = RAW_DIR / "weekly_box_office_2025_2026.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.the-numbers.com/",
}


def generate_fridays(start_date, end_date):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=7)


def clean_text(value):
    if value is None:
        return ""
    return str(value).replace("\xa0", " ").strip()


def fetch_html(url):
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def parse_week_page(html, week_start, source_url):
    soup = BeautifulSoup(html, "lxml")
    rows = []

    for tr in soup.find_all("tr"):
        cells = [clean_text(cell.get_text(" ", strip=True)) for cell in tr.find_all(["td", "th"])]

        # Valid movie rows confirmed from your debug output:
        # [Rank, Prev, Title, Daily Gross, Weekly Change, Theaters,
        #  Theater Average, Total Gross, Days in Release]
        if len(cells) == 9 and cells[0].isdigit():
            rows.append({
                "Rank": cells[0],
                "Prev": cells[1],
                "Title": cells[2],
                "Daily Gross": cells[3],
                "Weekly Change": cells[4],
                "Theaters": cells[5],
                "Theater Average": cells[6],
                "Total Gross": cells[7],
                "Days in Release": cells[8],
                "week_start": week_start.strftime("%Y-%m-%d"),
                "source_url": source_url,
            })

    return pd.DataFrame(rows)


all_weeks = []
failed_weeks = []

week_dates = list(generate_fridays(START_DATE, END_DATE))
print(f"Total weeks requested: {len(week_dates)}")

for week_start in week_dates:
    url = BASE_URL.format(
        year=week_start.year,
        month=week_start.month,
        day=week_start.day,
    )

    print(f"Reading: {url}")

    try:
        html = fetch_html(url)
        df = parse_week_page(html, week_start, url)

        if df.empty:
            print(f"No usable rows found for {url}")
            failed_weeks.append({
                "week_start": week_start.strftime("%Y-%m-%d"),
                "url": url,
                "reason": "empty parse"
            })
            continue

        all_weeks.append(df)
        print(f"Collected {len(df)} rows for {week_start.strftime('%Y-%m-%d')}")
        time.sleep(1)

    except Exception as e:
        print(f"Failed on {url}: {e}")
        failed_weeks.append({
            "week_start": week_start.strftime("%Y-%m-%d"),
            "url": url,
            "reason": str(e)
        })

if not all_weeks:
    raise ValueError("No weekly rows were collected. Check the page structure or whether the file still contains debug code.")

combined = pd.concat(all_weeks, ignore_index=True)
combined.to_csv(OUTPUT_FILE, index=False)

print("\n--- COLLECTION SUMMARY ---")
print(f"Saved raw data to: {OUTPUT_FILE}")
print(f"Rows collected: {len(combined)}")
print(f"Weeks collected successfully: {combined['week_start'].nunique()} out of {len(week_dates)}")
print(f"Columns collected: {combined.columns.tolist()}")

if failed_weeks:
    failed_df = pd.DataFrame(failed_weeks)
    failed_file = RAW_DIR / "failed_weeks_log.csv"
    failed_df.to_csv(failed_file, index=False)
    print(f"Weeks with errors or empty parses: {len(failed_weeks)}")
    print(f"Saved failed week log to: {failed_file}")
    print(failed_df)
else:
    print("All requested weeks were collected successfully.")