from datetime import datetime, timezone
import pandas as pd

from model3.pipeline import Model3Pipeline
from model3.config import Model3Config
from model3.schemas import SpillRecord, EnvironmentalRecord


AIS_FILE = "synthetic_ais.csv"


# Load synthetic AIS
df = pd.read_csv(AIS_FILE)

raw_ais_records = df.to_dict(orient="records")


# Synthetic spill information
spill = SpillRecord(
    spill_id="SYNTH_SPILL_001",
    timestamp_utc=datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc),
    centroid=(19.0500, 72.8500),
    area_km2=12.4,
    detection_confidence=0.91,
    oil_probability=None,
)


# Synthetic environmental information
environment = EnvironmentalRecord(
    wind_speed_ms=6.2,
    wind_direction_deg=200.0,
    source="synthetic",
    is_modelled=True,
)


# Create Model 3 pipeline
config = Model3Config()
pipeline = Model3Pipeline(config)


# Run Model 3
result = pipeline.run(
    spill=spill,
    raw_ais_records=raw_ais_records,
    environment=environment,
)


print()
print("=" * 60)
print("MODEL 3 SYNTHETIC RUN")
print("=" * 60)

print()
print("Preprocessing:")
print(result.preprocessing_report.summary())

print()
print("Mode used:")
print(result.mode_used)

print()
print("Number of candidates:")
print(len(result.ranked_candidates))

print()
print("Ranked candidates:")
print(
    result.ranked_candidates[
        ["vessel_id", "rank", "candidate_priority_score"]
    ].to_string(index=False)
)

print()
print("Explanations:")

for _, row in result.ranked_candidates.iterrows():
    print()
    print(f"Vessel: {row['vessel_id']}")
    print(f"Rank: {row['rank']}")
    print(f"Score: {row['candidate_priority_score']:.2f}")
    print(f"Explanation: {row['explanation']}")

print()
print("=" * 60)
print("MODEL 3 RUN COMPLETE")
print("=" * 60)
