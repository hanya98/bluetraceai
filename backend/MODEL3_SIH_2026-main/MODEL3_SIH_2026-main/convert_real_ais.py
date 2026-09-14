import pandas as pd

INPUT_FILE = r"real_ais\ais.csv"
OUTPUT_FILE = "real_ais_model3.csv"

print("Loading real AIS data...")

df = pd.read_csv(INPUT_FILE)

print(f"Original rows: {len(df)}")

# Convert Zenodo AIS columns to Model 3 schema
converted = pd.DataFrame({
    "vessel_id": df["shipid"],
    "timestamp_utc": df["t"],
    "latitude": df["lat"],
    "longitude": df["lon"],
    "speed_knots": df["speed"],
    "heading_deg": df["heading"],
})

# Remove rows missing the fields Model 3 requires
converted = converted.dropna(
    subset=[
        "vessel_id",
        "timestamp_utc",
        "latitude",
        "longitude",
    ]
)

converted.to_csv(
    OUTPUT_FILE,
    index=False,
)

print(f"Converted rows: {len(converted)}")
print(f"Created: {OUTPUT_FILE}")
print()
print("Columns:")
print(converted.columns.tolist())
print()
print("First 5 rows:")
print(converted.head().to_string(index=False))