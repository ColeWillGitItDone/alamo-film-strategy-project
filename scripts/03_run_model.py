from pathlib import Path
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

CLEAN_CSV = Path("data/processed/weekly_box_office_cleaned.csv")
OUTPUT_FILE = Path("data/processed/model_predictions.csv")

print(f"Reading cleaned data from: {CLEAN_CSV}")

df = pd.read_csv(CLEAN_CSV)
print(f"Initial row count: {len(df)}")
print("Columns found:")
print(df.columns.tolist())

df = df.sort_values(["movie_title", "week_number"]).copy()

# Create the target: next week's per-theater value for the same movie
df["next_week_per_theater"] = df.groupby("movie_title")["per_theater"].shift(-1)

features = ["per_theater", "theaters", "days_in_release", "is_new_release", "wide_release_flag"]
target = "next_week_per_theater"

# Show missing values before filtering
print("\nMissing values by modeling column before filtering:")
print(df[features + [target]].isna().sum())

# Keep only rows where all model inputs and target are present
model_df = df.dropna(subset=features + [target]).copy()

print(f"\nRows available for modeling after dropping rows with missing features/target: {len(model_df)}")

X = model_df[features]
y = model_df[target]

print("\nFeature preview:")
print(X.head())

model = LinearRegression()
model.fit(X, y)

model_df["predicted_next_week_per_theater"] = model.predict(X)

mae = mean_absolute_error(y, model_df["predicted_next_week_per_theater"])
r2 = r2_score(y, model_df["predicted_next_week_per_theater"])

model_df.to_csv(OUTPUT_FILE, index=False)

print(f"\nSaved predictions to: {OUTPUT_FILE}")
print(f"MAE: {mae:.2f}")
print(f"R^2: {r2:.4f}")
print("\nCoefficients:")
for feature, coef in zip(features, model.coef_):
    print(f"{feature}: {coef:.4f}")

print("\nFirst 5 prediction rows:")
print(model_df.head())