"""
Basic sanity tests for the Model 3 pipeline. Run with: pytest tests/ -q
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta, timezone

from model3.ais_preprocessing import preprocess_ais_records, group_by_vessel
from model3.candidate_filtering import filter_candidate_vessels
from model3.config import Model3Config
from model3.features.build_features import build_feature_table
from model3.pipeline import Model3Pipeline
from model3.schemas import SpillRecord, EnvironmentalRecord


SPILL_TIME = datetime(2024, 6, 1, 12, 0, tzinfo=timezone.utc)
SPILL_LAT, SPILL_LON = 19.05, 72.85  # near Mumbai coast, arbitrary


def make_spill():
    return SpillRecord(
        spill_id="SPILL_TEST_1",
        timestamp_utc=SPILL_TIME,
        centroid=(SPILL_LAT, SPILL_LON),
        area_km2=3.2,
        oil_probability=0.91,
        detection_confidence=0.87,
    )


def make_raw_ais():
    records = []
    # Vessel A: passes very close to spill, right around detection time
    base = SPILL_TIME - timedelta(hours=5)
    for i in range(6):
        records.append(
            {
                "vessel_id": "MMSI_A",
                "timestamp_utc": (base + timedelta(hours=i)).isoformat(),
                "latitude": SPILL_LAT + 0.01 * i,
                "longitude": SPILL_LON + 0.01 * i,
                "speed_knots": 8.0 - i * 0.5,
                "heading_deg": 200,
            }
        )
    # Vessel B: far away the entire time
    for i in range(4):
        records.append(
            {
                "vessel_id": "MMSI_B",
                "timestamp_utc": (SPILL_TIME - timedelta(hours=10 - i * 2)).isoformat(),
                "latitude": SPILL_LAT + 3.0,
                "longitude": SPILL_LON + 3.0,
                "speed_knots": 12.0,
                "heading_deg": 90,
            }
        )
    # Vessel C: bad/dirty data mixed in
    records.append(
        {"vessel_id": "", "timestamp_utc": "not-a-time", "latitude": 999, "longitude": 999}
    )
    records.append(
        {
            "vessel_id": "MMSI_C",
            "timestamp_utc": "bad-timestamp",
            "latitude": SPILL_LAT,
            "longitude": SPILL_LON,
        }
    )
    records.append(
        {
            "vessel_id": "MMSI_C",
            "timestamp_utc": SPILL_TIME.isoformat(),
            "latitude": 200.0,  # invalid lat
            "longitude": SPILL_LON,
        }
    )
    return records


def test_preprocessing_drops_bad_records_and_counts_them():
    obs, report = preprocess_ais_records(make_raw_ais())
    assert report.total_input == len(make_raw_ais())
    assert report.dropped_missing_vessel_id == 1
    assert report.dropped_bad_timestamp == 1
    assert report.dropped_bad_latitude == 1
    assert report.total_output == report.total_input - (
        report.dropped_missing_vessel_id + report.dropped_bad_timestamp + report.dropped_bad_latitude
    )
    # sorted per vessel by time
    a_obs = [o for o in obs if o.vessel_id == "MMSI_A"]
    assert all(a_obs[i].timestamp_utc <= a_obs[i + 1].timestamp_utc for i in range(len(a_obs) - 1))


def test_candidate_filtering_keeps_nearby_drops_far():
    spill = make_spill()
    obs, _ = preprocess_ais_records(make_raw_ais())
    by_vessel = group_by_vessel(obs)
    config = Model3Config().candidate_filter
    candidates = filter_candidate_vessels(spill, by_vessel, config)
    ids = {c.vessel_id for c in candidates}
    assert "MMSI_A" in ids
    assert "MMSI_B" not in ids  # ~470km away, outside default 50km radius


def test_feature_table_has_one_row_per_candidate():
    spill = make_spill()
    obs, _ = preprocess_ais_records(make_raw_ais())
    by_vessel = group_by_vessel(obs)
    cfg = Model3Config()
    candidates = filter_candidate_vessels(spill, by_vessel, cfg.candidate_filter)
    features = build_feature_table(candidates, spill, cfg.features)
    assert len(features) == len(candidates)
    assert "spatial_min_distance_centroid_km" in features.columns
    assert "gap_overlaps_relevant_window" in features.columns


def test_full_pipeline_end_to_end_heuristic_mode():
    spill = make_spill()
    env = EnvironmentalRecord(wind_speed_ms=6.5, wind_direction_deg=210, source="ERA5")
    pipeline = Model3Pipeline(Model3Config())
    result = pipeline.run(spill, make_raw_ais(), environment=env)

    assert result.mode_used == "heuristic"
    assert not result.ranked_candidates.empty
    assert list(result.ranked_candidates["rank"]) == sorted(result.ranked_candidates["rank"])
    top_score = result.ranked_candidates.iloc[0]["candidate_priority_score"]
    assert 0 <= top_score <= 100

    for text in result.ranked_candidates["explanation"]:
        assert "caused the spill" not in text.lower()
        assert "guilty" not in text.lower()

    payload = result.to_api_payload()
    assert payload["spill_id"] == "SPILL_TEST_1"
    assert payload["mode_used"] == "heuristic"
    assert len(payload["candidates"]) == len(result.ranked_candidates)


def test_empty_candidates_does_not_crash():
    spill = make_spill()
    pipeline = Model3Pipeline(Model3Config())
    result = pipeline.run(spill, raw_ais_records=[])
    assert result.ranked_candidates.empty


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
