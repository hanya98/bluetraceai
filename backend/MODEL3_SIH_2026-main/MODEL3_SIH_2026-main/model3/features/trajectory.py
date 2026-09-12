"""
features/trajectory.py
========================
Category C: TRAJECTORY FEATURES (spec section 9.C).

Falls back gracefully to centroid-based geometry when spill.polygon is
unavailable (current Model 1 does not yet produce a polygon).
"""

from __future__ import annotations

import math
from typing import Dict, Optional
from ..geo_utils import (
    angular_diff_deg,
    bearing_deg,
    haversine_km,
    point_in_polygon,
    min_distance_to_polygon_km,
)
from ..schemas import CandidateVessel, SpillRecord


def compute_trajectory_features(vessel: CandidateVessel, spill: SpillRecord) -> Dict[str, Optional[float]]:
    obs = sorted(vessel.observations, key=lambda o: o.timestamp_utc)
    centroid = spill.require_centroid()

    if not obs:
        return {
            "trajectory_min_distance_km": None,
            "trajectory_intersects_polygon": False,
            "trajectory_passes_near_spill": False,
            "trajectory_approach_bearing_deg": None,
            "trajectory_last_heading_deg": None,
            "trajectory_bearing_to_spill_deg": None,
            "trajectory_heading_alignment_deg": None,
            "trajectory_used_polygon": False,
        }

    use_polygon = spill.has_polygon()

    if use_polygon:
        min_dist = min(
            min_distance_to_polygon_km((o.latitude, o.longitude), spill.polygon) for o in obs
        )
        intersects = any(point_in_polygon((o.latitude, o.longitude), spill.polygon) for o in obs)
    else:
        min_dist = min(haversine_km((o.latitude, o.longitude), centroid) for o in obs)
        intersects = False  # cannot assess polygon intersection without a polygon

    # "passes near spill": any ping strictly closer than the vessel's own mean
    # distance -- i.e. the trajectory has a discernible approach, not just
    # noise around a constant distance. Documented heuristic, not a fixed
    # absolute threshold (that lives in FeatureConfig.vicinity_radius_km and
    # is applied at the scoring stage instead).
    distances = [haversine_km((o.latitude, o.longitude), centroid) for o in obs]
    mean_distance = sum(distances) / len(distances)
    passes_near = min(distances) < mean_distance

    # approach bearing: bearing of travel from the vessel's first to last
    # position in the window (direction the vessel was heading, empirically).
    first_pos = (obs[0].latitude, obs[0].longitude)
    last_pos = (obs[-1].latitude, obs[-1].longitude)
    approach_bearing = bearing_deg(first_pos, last_pos) if first_pos != last_pos else None


    last_heading = obs[-1].heading_deg  # reported AIS heading/course, if present

    # Treat NaN as missing, not as a valid heading.
    if last_heading is not None:
        try:
            if math.isnan(float(last_heading)):
                last_heading = None
        except (TypeError, ValueError):
            last_heading = None

    bearing_to_spill = bearing_deg(last_pos, centroid)

    heading_alignment: Optional[float] = None

    if last_heading is not None:
        heading_alignment = angular_diff_deg(
            last_heading,
            bearing_to_spill
        )
    elif approach_bearing is not None:
        # Fall back to trajectory-derived bearing when AIS heading is missing.
        heading_alignment = angular_diff_deg(
            approach_bearing,
            bearing_to_spill
        )
    return {
        "trajectory_min_distance_km": min_dist,
        "trajectory_intersects_polygon": bool(intersects),
        "trajectory_passes_near_spill": bool(passes_near),
        "trajectory_approach_bearing_deg": approach_bearing,
        "trajectory_last_heading_deg": last_heading,
        "trajectory_bearing_to_spill_deg": bearing_to_spill,
        "trajectory_heading_alignment_deg": heading_alignment,
        "trajectory_used_polygon": use_polygon,
    }
