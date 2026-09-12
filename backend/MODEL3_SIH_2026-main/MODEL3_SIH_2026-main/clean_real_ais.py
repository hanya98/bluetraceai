import pandas as pd

INPUT_FILE = "real_ais_model3.csv"
OUTPUT_FILE = "real_ais_clean.csv"

print("Loading AIS data...")

df = pd.read_csv(INPUT_FILE)

print(f"Original rows: {len(df)}")

# Convert numeric fields
for col in ["latitude", "longitude", "speed_knots", "heading_deg"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Remove impossible geographic coordinates
df = df[
    (df["latitude"] >= -90) &
    (df["latitude"] <= 90) &
    (df["longitude"] >= -180) &
    (df["longitude"] <= 180)
]

# The dataset contains 0,0 position records.
# Remove them because 0,0 is not part of the Piraeus study area.
df = df[
    ~((df["latitude"] == 0) & (df["longitude"] == 0))
]

# Remove rows missing required Model 3 fields
df = df.dropna(
    subset=[
        "vessel_id",
        "timestamp_utc",
        "latitude",
        "longitude",
    ]
)

# Sort chronologically
df["timestamp_utc"] = pd.to_datetime(
    df["timestamp_utc"],
    utc=True,
)

df = df.sort_values(
    ["vessel_id", "timestamp_utc"]
)

df.to_csv(
    OUTPUT_FILE,
    index=False,
)

print(f"Clean rows: {len(df)}")
print(f"Removed rows: {371585 - len(df)}")
print(f"Unique vessels: {df['vessel_id'].nunique()}")
print(f"Created: {OUTPUT_FILE}")

print()
print("Clean geographic range:")
print("Latitude:", df["latitude"].min(), "to", df["latitude"].max())
print("Longitude:", df["longitude"].min(), "to", df["longitude"].max())