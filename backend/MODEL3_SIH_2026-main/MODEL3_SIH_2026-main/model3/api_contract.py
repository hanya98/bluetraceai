"""
api_contract.py
=================
JSON-serializable contract that the backend team can rely on, independent of
Model 3's internal implementation.

INPUT CONTRACT (what the backend must send to Model 3):
    {
      "spill": {
        "spill_id": str,
        "timestamp_utc": ISO-8601 str,
        "centroid": [lat, lon] | null,
        "polygon": [[lat, lon], ...] | null,
        "area_km2": float | null,
        "bbox": [min_lat, min_lon, max_lat, max_lon] | null,
        "drift_direction_deg": float | null,
        "drift_speed_kmh": float | null,
        "oil_probability": float | null,     // from Model 2
        "detection_confidence": float | null  // from Model 1
      },
      "ais_records": [ {vessel_id, timestamp_utc, latitude, longitude,
                         speed_knots, heading_deg}, ... ],
      "vessel_metadata": { "<mmsi>": {mmsi, imo, name, flag, vessel_type,
                                       vessel_category}, ... },
      "environment": {wind_speed_ms, wind_direction_deg, source, is_modelled} | null
    }

OUTPUT CONTRACT (what Model 3 returns to the backend):
    {
      "spill_id": str,
      "mode_used": "heuristic" | "ml",
      "preprocessing_summary": str,
      "candidates": [
        {
          "vessel_id": str,
          "rank": int,
          "candidate_priority_score": float,   // 0-100
          "explanation": str,                  // always non-causal phrasing
          "features": { ...all computed feature columns... }
        }, ...
      ]
    }

NOTE: `candidate_priority_score` and `rank` are investigative-priority
signals, not probabilities of guilt, and must be labeled as such by any
frontend consuming this payload.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from .schemas import EnvironmentalRecord, SpillRecord, VesselMetadata

NON_FEATURE_COLUMNS = {"vessel_id", "spill_id", "rank", "candidate_priority_score", "explanation"}


def spill_from_api_payload(payload: Dict[str, Any]) -> SpillRecord:
    centroid = tuple(payload["centroid"]) if payload.get("centroid") else None
    polygon = [tuple(p) for p in payload["polygon"]] if payload.get("polygon") else None
    bbox = tuple(payload["bbox"]) if payload.get("bbox") else None
    return SpillRecord(
        spill_id=payload["spill_id"],
        timestamp_utc=datetime.fromisoformat(payload["timestamp_utc"].replace("Z", "+00:00")),
        centroid=centroid,
        polygon=polygon,
        area_km2=payload.get("area_km2"),
        bbox=bbox,
        drift_direction_deg=payload.get("drift_direction_deg"),
        drift_speed_kmh=payload.get("drift_speed_kmh"),
        oil_probability=payload.get("oil_probability"),
        detection_confidence=payload.get("detection_confidence"),
    )


def vessel_metadata_from_api_payload(payload: Optional[Dict[str, Any]]) -> Dict[str, VesselMetadata]:
    if not payload:
        return {}
    result = {}
    for mmsi, md in payload.items():
        result[mmsi] = VesselMetadata(
            mmsi=mmsi,
            imo=md.get("imo"),
            name=md.get("name"),
            flag=md.get("flag"),
            vessel_type=md.get("vessel_type"),
            vessel_category=md.get("vessel_category"),
        )
    return result


def environment_from_api_payload(payload: Optional[Dict[str, Any]]) -> Optional[EnvironmentalRecord]:
    if not payload:
        return None
    return EnvironmentalRecord(
        wind_speed_ms=payload.get("wind_speed_ms"),
        wind_direction_deg=payload.get("wind_direction_deg"),
        source=payload.get("source", "unknown"),
        is_modelled=payload.get("is_modelled", True),
    )


def _clean_value(v: Any) -> Any:
    if isinstance(v, float) and pd.isna(v):
        return None
    if hasattr(v, "item"):  # numpy scalar
        return v.item()
    return v


def ranked_dataframe_to_api_payload(spill_id: str, ranked: pd.DataFrame, mode_used: str) -> Dict[str, Any]:
    candidates: List[Dict[str, Any]] = []
    for _, row in ranked.iterrows():
        feature_dict = {
            col: _clean_value(row[col]) for col in ranked.columns if col not in NON_FEATURE_COLUMNS
        }
        candidates.append(
            {
                "vessel_id": row["vessel_id"],
                "rank": int(row["rank"]),
                "candidate_priority_score": float(row["candidate_priority_score"]),
                "explanation": row["explanation"],
                "features": feature_dict,
            }
        )
    return {
        "spill_id": spill_id,
        "mode_used": mode_used,
        "candidates": candidates,
    }
