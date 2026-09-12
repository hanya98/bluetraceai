# Model 3 — AIS-based Candidate Vessel Attribution / Ranking

**SIH26143 — AI Oil Spill Detection & Vessel Attribution**

This is Model 3 of the 3-model pipeline:

```
Sentinel-1 SAR → Model 1 (Attention U-Net segmentation)
               → Model 2 (CNN oil vs look-alike classifier)
               → Model 3 (THIS REPO: AIS-based candidate vessel ranking)
```

## What this is (and isn't)

Model 3 **ranks candidate vessels** near a detected spill using AIS,
spatial/temporal/trajectory/behavioral evidence, AIS-gap information, and
optional wind/drift data. It outputs a `candidate_priority_score` (0–100) and
a human-readable, non-causal explanation per vessel.

**It never claims a vessel caused a spill or is guilty.** Every explanation
string is checked against a banned-phrase guard (`explain.py`) before being
returned. Treat the output as an *investigative lead*, not a verdict.

It does **not** touch raw Sentinel-1 pixels and does **not** depend on the
internal architecture of Model 1 (Attention U-Net) or Model 2 (CNN). It
consumes a standardized `SpillRecord` — see `model3/api_contract.py` for the
exact JSON contract the backend team should use.

## Current integration note (Model 1 status)

The current Model 1 implementation is a **1-channel grayscale** Attention
U-Net (`AttentionUNet(in_channels=1, out_channels=1, base_channels=32)`) that
outputs a `(batch, 1, 256, 256)` probability map, thresholded to a binary
mask. It does **not yet** compute centroid / polygon / area_km² / bbox /
geospatial timestamp / drift direction.

**Model 3 requires at minimum a spill `centroid` (lat, lon).** Everything
else (`polygon`, `drift_direction_deg`, `oil_probability`, etc.) is optional
and every feature module degrades gracefully when a field is missing (see
each `features/*.py` docstring for its documented fallback behavior). The
upstream pipeline/backend — not Model 3 — is responsible for turning the
Model 1 pixel mask into geospatial fields.

## Two operating modes

- **Mode A — heuristic baseline** (`model3/scoring/heuristic.py`): a
  transparent, documented, weighted combination of evidence categories.
  Requires **zero labeled data**. This is the default and always works.
- **Mode B — XGBoost** (`model3/scoring/xgboost_model.py`): used only when
  you have **real, investigator-confirmed** (spill, vessel) labels. It will
  refuse to train (`ValueError`) if given a single-class or fabricated label
  set. Never auto-trains on the heuristic's own output.

Both modes share the same feature table and the same output contract
(`candidate_priority_score`, `rank`, `explanation`), so the backend never
needs to know which mode produced a given result (it's echoed as
`mode_used`).

## Package layout

```
model3/
  schemas.py            # SpillRecord, AISObservation, VesselMetadata, EnvironmentalRecord, CandidateVessel
  config.py              # ALL thresholds, documented, in one place
  geo_utils.py            # haversine distance, bearing, point-in-polygon (no naive lat/lon Euclidean math)
  ais_preprocessing.py    # cleaning, UTC normalization, validation, drop-reporting
  candidate_filtering.py  # spatial radius + temporal window pre-filter (returns ALL candidates)
  features/
    spatial.py            # category A
    temporal.py           # category B
    trajectory.py         # category C (graceful polygon → centroid fallback)
    behavior.py           # category D
    gaps.py               # category E (AIS gap ≠ guilt, enforced)
    environmental.py       # category F (wind/drift, optional)
    metadata.py            # category G (deliberately low-weight)
    build_features.py      # assembles one row per candidate vessel
  scoring/
    heuristic.py           # Mode A
    xgboost_model.py        # Mode B
  explain.py               # non-causal explanation generation + banned-phrase guard
  pipeline.py              # Model3Pipeline — the single entry point
  api_contract.py          # JSON in/out contract for the backend team
tests/
  test_pipeline.py         # end-to-end + unit sanity tests
```

## Quick start

```python
from datetime import datetime, timezone
from model3.config import Model3Config
from model3.pipeline import Model3Pipeline
from model3.schemas import SpillRecord, EnvironmentalRecord

spill = SpillRecord(
    spill_id="SPILL_001",
    timestamp_utc=datetime(2024, 6, 1, 12, 0, tzinfo=timezone.utc),
    centroid=(19.05, 72.85),          # from upstream Model 1 post-processing
    oil_probability=0.91,              # from Model 2
)

raw_ais_records = [
    {"vessel_id": "412345678", "timestamp_utc": "2024-06-01T07:00:00Z",
     "latitude": 19.03, "longitude": 72.83, "speed_knots": 8.0, "heading_deg": 205},
    # ... more AIS pings, any vessels, any distance -- filtering happens internally
]

pipeline = Model3Pipeline(Model3Config())
result = pipeline.run(spill, raw_ais_records, environment=EnvironmentalRecord(
    wind_speed_ms=6.5, wind_direction_deg=210, source="ERA5"))

print(result.ranked_candidates[["vessel_id", "rank", "candidate_priority_score"]])
print(result.ranked_candidates.iloc[0]["explanation"])

api_json = result.to_api_payload()   # hand this straight to the backend
```

### Enabling Mode B (once you have credible labels)

```python
from model3.scoring.xgboost_model import XGBAttributionModel

model = XGBAttributionModel()
model.fit(labeled_feature_dataframe, label_column="label")  # REAL labels only
model.save("model3_xgb.json")

config = Model3Config(mode="ml")
pipeline = Model3Pipeline(config, ml_model=model)
```

## Colab (free-tier T4) notes

- Model 3 is tabular (pandas/XGBoost), not deep learning — it runs entirely
  on CPU and needs no GPU. The T4 is irrelevant to this stage; it matters for
  Models 1/2, not Model 3.
- `xgboost` defaults to `tree_method="hist"` (CPU) in this repo, since a T4
  offers no benefit for the small per-spill row counts here.
- Install once per Colab session: `!pip install -q xgboost shap` (both
  optional; the heuristic baseline needs only pandas/numpy, which Colab
  ships by default).

## Running tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Data source references used to define this contract

- Copernicus Sentinel-1 STAC / GRD docs (Model 1's input, referenced for
  context only — Model 3 does not call these):
  https://documentation.dataspace.copernicus.eu/APIs/STAC.html ,
  https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/S1GRD.html
- Global Fishing Watch AIS Events API (recommended AIS source):
  https://api-doc.globalfishingwatch.org/our-apis/documentation/docs/v3/events/get-all-events
  — see also the **data caveats** page before treating AIS gaps as meaningful:
  https://api-doc.globalfishingwatch.org/our-apis/documentation/docs/v3/general-api-doc/data-caveats
- ERA5 reanalysis / Open-Meteo (environmental/wind, modelled not measured):
  https://www.ecmwf.int/en/forecasts/datasets/era5-hourly-time-series-data-single-levels-1940-present ,
  https://open-meteo.com/en/docs/ecmwf-api

## Explicit non-goals of this repo

- Does not fetch or process Sentinel-1 imagery.
- Does not implement or depend on the Attention U-Net or CNN classifier.
- Does not fabricate vessel-attribution training labels.
- Does not claim causality — every text output is guarded against
  causal/guilt phrasing (`model3/explain.py::_assert_non_causal`).
