from datetime import datetime, timezone
import pandas as pd

from model3.pipeline import Model3Pipeline
from model3.config import Model3Config
from model3.schemas import SpillRecord


AIS_FILE = "real_ais_clean.csv"

# Real AIS dataset
df = pd.read_csv(AIS_FILE)

# Convert to the format expected by Model 3
raw_ais_records = df.to_dict(orient="records")

# Hypothetical spill based on a REAL AIS observation
spill = SpillRecord(
    spill_id="REAL_AIS_TEST_001",
    timestamp_utc=datetime(
        2020, 3, 1, 14, 20, 13,
        tzinfo=timezone.utc
    ),
    centroid=(37.949963333333336, 23.604381666666665),
    area_km2=5.0,
    detection_confidence=0.90,
    oil_probability=None,
)

# Create Model 3
config = Model3Config()
pipeline = Model3Pipeline(config)

# Run Model 3
print("Loading and processing real AIS...")
print(f"Total AIS records supplied: {len(raw_ais_records)}")

result = pipeline.run(
    spill=spill,
    raw_ais_records=raw_ais_records,
)

print()
print("=" * 70)
print("MODEL 3 - REAL AIS TEST")
print("=" * 70)

print()
print("Spill ID:")
print(spill.spill_id)

print()
print("Hypothetical spill location:")
print(spill.centroid)

print()
print("Hypothetical spill time:")
print(spill.timestamp_utc)

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

if len(result.ranked_candidates) > 0:
    
    print(
        result.ranked_candidates[
            [
                "vessel_id",
                "rank",
                "candidate_priority_score",
            ]
        ].head(20).to_string(index=False)
    )
print()
print("=" * 70)
print("ORIGINAL TEST VESSEL")
print("=" * 70)

test_vessel = "86dbf2ec-a3df-462a-9343-7e78adbd43da"

test_result = result.ranked_candidates[
    result.ranked_candidates["vessel_id"] == test_vessel
]

if len(test_result) > 0:
    print(test_result.to_string(index=False))
else:
    print("Original test vessel was not included as a candidate.")
"""
    print()
    print("Explanations:")

    for _, row in result.ranked_candidates.iterrows():
        print()
        print(f"Vessel: {row['vessel_id']}")
        print(f"Rank: {row['rank']}")
        print(f"Score: {row['candidate_priority_score']:.2f}")
        print(f"Explanation: {row['explanation']}")
    """
print()
print("TOP 5 EXPLANATIONS")

for _, row in result.ranked_candidates.head(5).iterrows():
    print()
    print(f"Vessel: {row['vessel_id']}")
    print(f"Rank: {row['rank']}")
    print(f"Score: {row['candidate_priority_score']:.2f}")
    print(f"Explanation: {row['explanation']}")

else:
    print("No candidate vessels found.")

print()
print("=" * 70)
print("REAL AIS MODEL 3 TEST COMPLETE")
print("=" * 70)