"""
End-to-end demo with synthetic data — run this in Colab to sanity-check the
pipeline before wiring in real AIS/Sentinel-1 outputs.

    python example_run.py
"""
"""
End-to-end demo with synthetic data — run this to sanity-check the pipeline
before wiring in real AIS/Sentinel-1 outputs.

    python example_run.py
"""

from datetime import datetime, timedelta, timezone
import random

from model3 import SpillRecord, EnvironmentalRecord
from model3.pipeline import Model3Pipeline
from model3.config import Model3Config


def make_synthetic_ais(spill_lat, spill_lon, spill_time, n_vessels=6, n_pings=20):
    records = []
    for v in range(n_vessels):
        vessel_id = f"MMSI_{100000 + v}"
        # vessel 0 = clearly implicated (close, aligned heading, near in time)
        # vessel 1 = far away (should rank low)
        # others = random scatter
        if v == 0:
            base_lat, base_lon = spill_lat + 0.3, spill_lon + 0.3
            heading = 225  # heading toward spill (SW)
        elif v == 1:
            base_lat, base_lon = spill_lat + 3.0, spill_lon + 3.0
            heading = 90
        else:
            base_lat = spill_lat + random.uniform(-1, 1)
            base_lon = spill_lon + random.uniform(-1, 1)
            heading = random.uniform(0, 360)

        t0 = spill_time - timedelta(hours=10)
        for i in range(n_pings):
            frac = i / n_pings
            lat = base_lat - frac * (base_lat - spill_lat) * (0.9 if v == 0 else 0.1)
            lon = base_lon - frac * (base_lon - spill_lon) * (0.9 if v == 0 else 0.1)
            # raw_ais_records must be plain dicts -- this is what
            # preprocess_ais_records() in ais_preprocessing.py expects
            records.append({
                "vessel_id": vessel_id,
                "timestamp_utc": (t0 + timedelta(minutes=30 * i)).isoformat(),
                "latitude": lat,
                "longitude": lon,
                "speed_knots": random.uniform(5, 15) if v != 0 else random.uniform(1, 4),
                "heading_deg": heading,
            })
    return records


def main():
    spill_time = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)

    spill = SpillRecord(
        spill_id="SPILL_001",
        timestamp_utc=spill_time,
        centroid=(19.05, 72.85),      # (lat, lon) -- from upstream Model 1 post-processing
        area_km2=12.4,
        drift_direction_deg=210,
        oil_probability=0.87,          # from Model 2
        detection_confidence=0.91,     # from Model 1
    )

    environment = EnvironmentalRecord(
        wind_speed_ms=6.2,
        wind_direction_deg=200,
        source="ERA5",
    )

    ais_records = make_synthetic_ais(spill.centroid[0], spill.centroid[1], spill_time)

    pipeline = Model3Pipeline(Model3Config())
    result = pipeline.run(spill, ais_records, environment=environment)

    print(result.preprocessing_report.summary())
    print(f"Mode used: {result.mode_used} | candidates: {len(result.ranked_candidates)}\n")

    print(result.ranked_candidates[["vessel_id", "rank", "candidate_priority_score"]])
    print()
    print(result.ranked_candidates.iloc[0]["explanation"])

    api_json = result.to_api_payload()
    print("\n--- API payload (first 400 chars) ---")
    import json
    print(json.dumps(api_json, indent=2, default=str)[:400])


if __name__ == "__main__":
    main()