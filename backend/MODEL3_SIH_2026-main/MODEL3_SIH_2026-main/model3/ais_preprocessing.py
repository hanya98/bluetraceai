"""
ais_preprocessing.py
=====================
Robust, independently-testable AIS cleaning. Every function here is pure
(input -> output, no hidden state) so it can be unit tested in isolation.

Design rules enforced (per spec):
  - timestamps parsed and normalized to UTC
  - records sorted per-vessel by time
  - invalid lat/lon rejected (not silently coerced)
  - invalid/missing speed & heading handled explicitly (kept as None, not 0)
  - nothing is fabricated
  - every drop is counted and reported via a PreprocessingReport
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union
import logging

from .schemas import AISObservation

logger = logging.getLogger(__name__)


@dataclass
class PreprocessingReport:
    total_input: int = 0
    total_output: int = 0
    dropped_bad_timestamp: int = 0
    dropped_bad_latitude: int = 0
    dropped_bad_longitude: int = 0
    dropped_missing_vessel_id: int = 0
    coerced_bad_speed: int = 0
    coerced_bad_heading: int = 0
    duplicates_removed: int = 0

    def summary(self) -> str:
        return (
            f"AIS preprocessing: {self.total_input} in -> {self.total_output} out "
            f"(dropped: timestamp={self.dropped_bad_timestamp}, "
            f"lat={self.dropped_bad_latitude}, lon={self.dropped_bad_longitude}, "
            f"vessel_id={self.dropped_missing_vessel_id}, "
            f"duplicates={self.duplicates_removed}; "
            f"coerced-to-missing: speed={self.coerced_bad_speed}, "
            f"heading={self.coerced_bad_heading})"
        )


def _parse_timestamp(value: Union[str, datetime, int, float]) -> Optional[datetime]:
    """Parse a timestamp into a UTC-aware datetime. Returns None (never
    raises) on failure so the caller can count/drop it explicitly."""
    try:
        if isinstance(value, datetime):
            dt = value
        elif isinstance(value, (int, float)):
            # assume unix epoch seconds
            dt = datetime.fromtimestamp(float(value), tz=timezone.utc)
        elif isinstance(value, str):
            s = value.strip().replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)
        else:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except (ValueError, TypeError, OverflowError, OSError):
        return None


def _valid_lat(lat: Any) -> bool:
    try:
        return -90.0 <= float(lat) <= 90.0
    except (TypeError, ValueError):
        return False


def _valid_lon(lon: Any) -> bool:
    try:
        return -180.0 <= float(lon) <= 180.0
    except (TypeError, ValueError):
        return False


def _clean_speed(value: Any) -> Optional[float]:
    """Speed must be a finite, non-negative, physically-plausible number
    (knots). Anything else is treated as missing (None) -- NEVER coerced to
    0.0, since 0 is a real, meaningful value (vessel stopped)."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if v != v or v < 0 or v > 60:  # NaN check + implausible max (60 kts)
        return None
    return v


def _clean_heading(value: Any) -> Optional[float]:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if v != v or v < 0 or v > 360:
        return None
    return v % 360.0


def preprocess_ais_records(
    raw_records: List[Dict[str, Any]],
    vessel_id_key: str = "vessel_id",
    timestamp_key: str = "timestamp_utc",
    lat_key: str = "latitude",
    lon_key: str = "longitude",
    speed_key: str = "speed_knots",
    heading_key: str = "heading_deg",
) -> tuple[List[AISObservation], PreprocessingReport]:
    """Clean a list of raw AIS dict records into validated AISObservation
    objects, sorted per-vessel by timestamp. Returns (observations, report).

    Nothing is fabricated: records with unrecoverable identity/position/time
    problems are dropped and counted; speed/heading problems are coerced to
    None (missing) rather than dropping the whole ping, since position and
    time are still usable evidence even without a valid speed/heading.
    """
    report = PreprocessingReport(total_input=len(raw_records))
    cleaned: List[AISObservation] = []
    seen = set()

    for rec in raw_records:
        vessel_id = rec.get(vessel_id_key)
        if vessel_id is None or str(vessel_id).strip() == "":
            report.dropped_missing_vessel_id += 1
            continue
        vessel_id = str(vessel_id).strip()

        ts = _parse_timestamp(rec.get(timestamp_key))
        if ts is None:
            report.dropped_bad_timestamp += 1
            continue

        lat = rec.get(lat_key)
        lon = rec.get(lon_key)
        if not _valid_lat(lat):
            report.dropped_bad_latitude += 1
            continue
        if not _valid_lon(lon):
            report.dropped_bad_longitude += 1
            continue

        raw_speed = rec.get(speed_key)
        speed = _clean_speed(raw_speed) if raw_speed is not None else None
        if raw_speed is not None and speed is None:
            report.coerced_bad_speed += 1

        raw_heading = rec.get(heading_key)
        heading = _clean_heading(raw_heading) if raw_heading is not None else None
        if raw_heading is not None and heading is None:
            report.coerced_bad_heading += 1

        dedup_key = (vessel_id, ts.isoformat(), round(float(lat), 6), round(float(lon), 6))
        if dedup_key in seen:
            report.duplicates_removed += 1
            continue
        seen.add(dedup_key)

        cleaned.append(
            AISObservation(
                vessel_id=vessel_id,
                timestamp_utc=ts,
                latitude=float(lat),
                longitude=float(lon),
                speed_knots=speed,
                heading_deg=heading,
                raw=rec,
            )
        )

    cleaned.sort(key=lambda o: (o.vessel_id, o.timestamp_utc))
    report.total_output = len(cleaned)

    if report.total_output < report.total_input * 0.5:
        logger.warning(
            "More than half of AIS records were dropped during preprocessing. %s",
            report.summary(),
        )
    logger.info(report.summary())

    return cleaned, report


def group_by_vessel(observations: List[AISObservation]) -> Dict[str, List[AISObservation]]:
    """Group already-sorted observations by vessel_id, preserving time order."""
    grouped: Dict[str, List[AISObservation]] = {}
    for obs in observations:
        grouped.setdefault(obs.vessel_id, []).append(obs)
    for v in grouped.values():
        v.sort(key=lambda o: o.timestamp_utc)
    return grouped
