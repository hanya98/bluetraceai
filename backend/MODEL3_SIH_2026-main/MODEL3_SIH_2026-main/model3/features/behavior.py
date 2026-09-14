"""
features/behavior.py
======================
Category D: VESSEL BEHAVIOR FEATURES (spec section 9.D).

Requires a minimum number of observations with valid speed to compute
variability statistics; otherwise returns None rather than inventing
behavior from insufficient data (explicit spec requirement).
"""

from __future__ import annotations

import statistics
from typing import Dict, List, Optional

from ..config import FeatureConfig
from ..schemas import AISObservation, CandidateVessel, SpillRecord
from ..geo_utils import haversine_km

MIN_OBS_FOR_VARIABILITY = 2

def compute_behavior_features(
    vessel: CandidateVessel,
    spill: SpillRecord,
    config: FeatureConfig,
) -> Dict[str, Optional[float]]:
    obs = sorted(vessel.observations, key=lambda o: o.timestamp_utc)

    # Only evaluate vessel behavior near the detected spill.
    # This prevents unrelated behavior elsewhere in the trajectory
    # from influencing attribution.
    centroid = spill.require_centroid()

    obs = [
        o
        for o in obs
        if haversine_km(
            (o.latitude, o.longitude),
            centroid
        ) <= config.vicinity_radius_km
    ]
    speeds = [o.speed_knots for o in obs if o.speed_knots is not None]
    headings = [o.heading_deg for o in obs if o.heading_deg is not None]

    result: Dict[str, Optional[float]] = {
        "behavior_mean_speed_knots": None,
        "behavior_max_speed_knots": None,
        "behavior_speed_std_knots": None,
        "behavior_speed_change_knots": None,
        "behavior_heading_variation_deg": None,
        "behavior_is_slowdown": False,
        "behavior_is_loitering": False,
        "behavior_n_speed_obs": len(speeds),
    }

    if speeds:
        result["behavior_mean_speed_knots"] = statistics.mean(speeds)
        result["behavior_max_speed_knots"] = max(speeds)
    if len(speeds) >= MIN_OBS_FOR_VARIABILITY:
        result["behavior_speed_std_knots"] = statistics.pstdev(speeds)
        result["behavior_speed_change_knots"] = speeds[-1] - speeds[0]

    if len(headings) >= MIN_OBS_FOR_VARIABILITY:
        # circular variation approximated via consecutive angular diffs
        diffs = [
            min(abs(headings[i] - headings[i - 1]), 360 - abs(headings[i] - headings[i - 1]))
            for i in range(1, len(headings))
        ]
        result["behavior_heading_variation_deg"] = statistics.mean(diffs)

    result["behavior_is_slowdown"] = _has_slowdown(obs, config)
    result["behavior_is_loitering"] = _has_loitering(obs, config)

    return result


def _has_slowdown(obs: List[AISObservation], config: FeatureConfig) -> bool:
    speeds = [o.speed_knots for o in obs if o.speed_knots is not None]
    if len(speeds) < 2:
        return False
    return any(speeds[i] < speeds[i - 1] - config.loitering_speed_knots for i in range(1, len(speeds)))


def _has_loitering(obs: List[AISObservation], config: FeatureConfig) -> bool:
    """True if the vessel had a *contiguous* run of low-speed pings spanning
    at least `loitering_min_duration_hours`. Requires valid speed AND
    timestamp on each ping in the run."""
    slow_obs = [o for o in obs if o.speed_knots is not None and o.speed_knots <= config.loitering_speed_knots]
    if len(slow_obs) < 2:
        return False
    slow_obs = sorted(slow_obs, key=lambda o: o.timestamp_utc)

    run_start = slow_obs[0].timestamp_utc
    prev_time = slow_obs[0].timestamp_utc
    for o in slow_obs[1:]:
        gap_hr = (o.timestamp_utc - prev_time).total_seconds() / 3600.0
        if gap_hr > config.ais_gap_threshold_hours * 3:
            # treat as a broken run if the gap between "slow" pings is itself
            # large (vessel could have sped up and slowed again elsewhere)
            run_start = o.timestamp_utc
        elif (o.timestamp_utc - run_start).total_seconds() / 3600.0 >= config.loitering_min_duration_hours:
            return True
        prev_time = o.timestamp_utc
    return (prev_time - run_start).total_seconds() / 3600.0 >= config.loitering_min_duration_hours
