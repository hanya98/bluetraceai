"""
features/temporal.py
======================
Category B: TEMPORAL FEATURES (spec section 9.B). All datetimes are assumed
already normalized to UTC by ais_preprocessing.py.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Dict, Optional

from ..config import FeatureConfig
from ..geo_utils import haversine_km
from ..schemas import CandidateVessel, SpillRecord


def compute_temporal_features(
    vessel: CandidateVessel, spill: SpillRecord, config: FeatureConfig
) -> Dict[str, Optional[float]]:
    obs = vessel.observations
    if not obs:
        return {
            "temporal_abs_time_diff_closest_hr": None,
            "temporal_time_diff_last_obs_hr": None,
            "temporal_time_in_vicinity_hr": None,
            "temporal_n_obs_in_window": 0,
            "temporal_hours_since_last_near_spill": None,
        }

    centroid = spill.require_centroid()
    spill_time = spill.timestamp_utc

    # observation spatially closest to the spill
    closest_obs = min(obs, key=lambda o: haversine_km((o.latitude, o.longitude), centroid))
    abs_time_diff_closest_hr = abs((closest_obs.timestamp_utc - spill_time).total_seconds()) / 3600.0

    last_obs = max(obs, key=lambda o: o.timestamp_utc)
    time_diff_last_hr = (last_obs.timestamp_utc - spill_time).total_seconds() / 3600.0

    # time spent within `vicinity_radius_km` of the spill: approximated as the
    # sum of time gaps *between consecutive in-vicinity pings* (does not
    # extrapolate beyond observed data -- a lone in-vicinity ping contributes
    # 0 duration, which is conservative/documented behavior).
    in_vicinity = sorted(
        (o for o in obs if haversine_km((o.latitude, o.longitude), centroid) <= config.vicinity_radius_km),
        key=lambda o: o.timestamp_utc,
    )
    time_in_vicinity_hr = 0.0
    for prev, cur in zip(in_vicinity, in_vicinity[1:]):
        time_in_vicinity_hr += (cur.timestamp_utc - prev.timestamp_utc).total_seconds() / 3600.0

    hours_since_last_near_spill: Optional[float] = None
    if in_vicinity:
        last_near = max(in_vicinity, key=lambda o: o.timestamp_utc)
        hours_since_last_near_spill = (spill_time - last_near.timestamp_utc).total_seconds() / 3600.0

    return {
        "temporal_abs_time_diff_closest_hr": abs_time_diff_closest_hr,
        "temporal_time_diff_last_obs_hr": time_diff_last_hr,
        "temporal_time_in_vicinity_hr": time_in_vicinity_hr,
        "temporal_n_obs_in_window": len(obs),
        "temporal_hours_since_last_near_spill": hours_since_last_near_spill,
    }
