"""
schemas.py
==========
Standardized data contract between:
  - upstream pipeline (Model 1 + Model 2 + backend) -> SpillRecord
  - AIS provider (e.g. Global Fishing Watch) -> AISObservation / VesselMetadata
  - environmental provider (e.g. ERA5 / Open-Meteo) -> EnvironmentalRecord
  - Model 3 internals -> CandidateVessel (one row per candidate, pre-scoring)

Model 3 code must depend ONLY on these dataclasses, never on Model 1/Model 2
internals (no U-Net tensors, no raw SAR pixels, no VV/VH assumptions).

All fields that the upstream pipeline may not yet compute (polygon, drift,
confidence, etc.) are Optional. Do not fabricate them if missing -- every
downstream feature function must degrade gracefully (see features/*.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any


Coordinate = Tuple[float, float]  # (latitude, longitude)


@dataclass
class SpillRecord:
    """Standardized spill object handed to Model 3 by the upstream pipeline.

    NOTE: as of the current Model 1 implementation (grayscale 1-channel
    Attention U-Net with no geospatial post-processing), fields like
    `centroid`, `polygon`, `area_km2`, `bbox`, `acquisition_timestamp_utc`
    and `drift_direction_deg` are NOT yet produced upstream. They are kept
    Optional here on purpose. Model 3 must not crash or fabricate values when
    they are missing -- it should simply skip the features that depend on
    them (see features/spatial.py, trajectory.py).
    """

    spill_id: str
    timestamp_utc: datetime  # detection time (when Model 1/2 flagged the spill)

    centroid: Optional[Coordinate] = None  # (lat, lon)
    polygon: Optional[List[Coordinate]] = None  # ordered ring of (lat, lon)
    area_km2: Optional[float] = None
    bbox: Optional[Tuple[float, float, float, float]] = None  # (min_lat, min_lon, max_lat, max_lon)

    drift_direction_deg: Optional[float] = None  # 0-360, direction spill is estimated to be moving TOWARD
    drift_speed_kmh: Optional[float] = None

    oil_probability: Optional[float] = None  # from Model 2, 0-1
    detection_confidence: Optional[float] = None  # from Model 1, 0-1

    def has_polygon(self) -> bool:
        return bool(self.polygon and len(self.polygon) >= 3)

    def require_centroid(self) -> Coordinate:
        if self.centroid is None:
            raise ValueError(
                f"SpillRecord {self.spill_id} has no centroid. Model 3 requires at "
                "least a centroid (lat, lon) for a spill; the upstream pipeline "
                "must compute this from the Model 1 segmentation mask before "
                "calling Model 3."
            )
        return self.centroid


@dataclass
class VesselMetadata:
    mmsi: str
    imo: Optional[str] = None
    name: Optional[str] = None
    flag: Optional[str] = None
    vessel_type: Optional[str] = None  # e.g. "tanker", "cargo", "fishing"
    vessel_category: Optional[str] = None


@dataclass
class AISObservation:
    """One raw AIS ping. `vessel_id` should be the MMSI (string, preserves
    leading semantics / avoids float precision issues)."""

    vessel_id: str
    timestamp_utc: datetime
    latitude: float
    longitude: float
    speed_knots: Optional[float] = None
    heading_deg: Optional[float] = None  # course over ground, 0-360
    raw: Dict[str, Any] = field(default_factory=dict)  # passthrough for anything else


@dataclass
class EnvironmentalRecord:
    """Modelled environmental data (e.g. ERA5 reanalysis / Open-Meteo
    forecast-archive) matched to the spill's time/location.

    IMPORTANT: this is MODEL / REANALYSIS data, not a direct in-situ
    measurement. Downstream text output must describe it as such (see
    explain.py) rather than implying a sensor recorded it.
    """

    wind_speed_ms: Optional[float] = None
    wind_direction_deg: Optional[float] = None  # direction wind is blowing TOWARD, 0-360
    source: str = "unknown"  # e.g. "ERA5", "open-meteo-ecmwf"
    is_modelled: bool = True


@dataclass
class CandidateVessel:
    """A vessel that survived candidate filtering for a given spill, together
    with its relevant AIS observation slice and metadata. This is the unit
    that feature engineering (features/build_features.py) turns into a
    single feature row."""

    vessel_id: str
    spill_id: str
    observations: List[AISObservation]
    metadata: Optional[VesselMetadata] = None
