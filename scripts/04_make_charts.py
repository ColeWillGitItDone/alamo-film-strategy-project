from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

CLEAN_CSV = Path("data/processed/weekly_box_office_cleaned.csv")
PREDICTIONS_CSV = Path("data/processed/model_predictions.csv")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"Reading cleaned data from: {CLEAN_CSV}")
print(f"Reading prediction data from: {PREDICTIONS_CSV}")

df = pd.read_csv(CLEAN_CSV)
pred_df = pd.read_csv(PREDICTIONS_CSV)

print(f"Cleaned rows: {len(df)}")
print(f"Prediction rows: {len(pred_df)}")

# -----------------------------
# Chart 1: Average per-theater by week
# -----------------------------
weekly_avg = df.groupby("week_start", as_index=False)["per_theater"].mean()
weekly_avg["week_start"] = pd.to_datetime(weekly_avg["week_start"])

print(f"Weekly average rows: {len(weekly_avg)}")

plt.figure(figsize=(12, 6))
plt.plot(weekly_avg["week_start"], weekly_avg["per_theater"])

# Show fewer x-axis labels so they are readable
tick_positions = weekly_avg["week_start"][::4]
plt.xticks(tick_positions, rotation=45)

plt.title("Average Per-Theater Performance by Week")
plt.xlabel("Week Start")
plt.ylabel("Average Per-Theater")
plt.tight_layout()

chart1 = OUTPUT_DIR / "01_avg_per_theater_by_week.png"
plt.savefig(chart1, dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved chart: {chart1}")

# -----------------------------
# Chart 2: Top titles by per-theater decline
# -----------------------------
decline_df = pred_df.copy()
decline_df = decline_df[
    decline_df["per_theater"].notna() &
    decline_df["next_week_per_theater"].notna() &
    (decline_df["per_theater"] != 0)
].copy()

decline_df["pct_decline"] = (
    (decline_df["next_week_per_theater"] - decline_df["per_theater"]) / decline_df["per_theater"]
)

# Show more titles so the chart has more visual spread
top_declines = decline_df.nsmallest(15, "pct_decline").copy()

print(f"Top decline rows: {len(top_declines)}")

plt.figure(figsize=(12, 7))
plt.bar(top_declines["movie_title"], top_declines["pct_decline"])
plt.xticks(rotation=45, ha="right")
plt.title("Top 15 Titles by Per-Theater Decline")
plt.xlabel("Movie Title")
plt.ylabel("Pct Decline")

# Zoom the y-axis slightly around the actual range for better visual separation
y_max = top_declines["pct_decline"].max()
plt.ylim(-1.0, y_max + 0.05)

plt.tight_layout()

chart2 = OUTPUT_DIR / "02_top_titles_by_decline.png"
plt.savefig(chart2, dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved chart: {chart2}")

# -----------------------------
# Chart 3: Predicted vs actual
# -----------------------------
plot_df = pred_df.dropna(subset=["next_week_per_theater", "predicted_next_week_per_theater"]).copy()

print(f"Prediction scatter rows: {len(plot_df)}")

plt.figure(figsize=(8, 6))
plt.scatter(plot_df["next_week_per_theater"], plot_df["predicted_next_week_per_theater"])
plt.title("Predicted vs Actual Next-Week Per-Theater")
plt.xlabel("Actual Next-Week Per-Theater")
plt.ylabel("Predicted Next-Week Per-Theater")
plt.tight_layout()

chart3 = OUTPUT_DIR / "03_predicted_vs_actual.png"
plt.savefig(chart3, dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved chart: {chart3}")

print("\nAll charts saved successfully.")
print("Output folder contents:")
for file in sorted(OUTPUT_DIR.glob("*")):
    print(f"- {file.name}")