"""
features/gaps.py
==================
Category E: AIS GAP FEATURES (spec section 9.E).

CRITICAL FRAMING (enforced here and re-enforced in explain.py):
An AIS gap means only "no AIS data was received for this interval". It does
NOT mean the vessel intentionally disabled its transponder, and it does NOT
by itself imply wrongdoing. This module produces a numeric feature only; it
must never be converted into a boolean "guilty" flag anywhere downstream.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Dict, List, Optional

from ..config import FeatureConfig
from ..schemas import AISObservation, CandidateVessel, SpillRecord


def compute_gap_features(
    vessel: CandidateVessel, spill: SpillRecord, config: FeatureConfig
) -> Dict[str, Optional[float]]:
    obs = sorted(vessel.observations, key=lambda o: o.timestamp_utc)

    if len(obs) < 2:
        return {
            "gap_longest_hr": None,
            "gap_near_spill_hr": 0.0,
            "gap_overlaps_relevant_window": False,
            "gap_count": 0,
        }

    gaps = []  # (start, end, duration_hr)
    for prev, cur in zip(obs, obs[1:]):
        duration_hr = (cur.timestamp_utc - prev.timestamp_utc).total_seconds() / 3600.0
        if duration_hr >= config.ais_gap_threshold_hours:
            gaps.append((prev.timestamp_utc, cur.timestamp_utc, duration_hr))

    longest = max((g[2] for g in gaps), default=None)

    # a gap "near the spill" = one whose interval overlaps [-6h, +6h] around
    # spill detection time; 6h is a documented default proximity window for
    # this specific sub-feature, independent of the broader candidate window.
    proximity_start = spill.timestamp_utc - timedelta(hours=6)
    proximity_end = spill.timestamp_utc + timedelta(hours=6)
    near_spill_duration = sum(
        g[2] for g in gaps if not (g[1] < proximity_start or g[0] > proximity_end)
    )
    overlaps_relevant_window = any(
        not (g[1] < proximity_start or g[0] > proximity_end) for g in gaps
    )

    return {
        "gap_longest_hr": longest,
        "gap_near_spill_hr": near_spill_duration,
        "gap_overlaps_relevant_window": bool(overlaps_relevant_window),
        "gap_count": len(gaps),
    }
