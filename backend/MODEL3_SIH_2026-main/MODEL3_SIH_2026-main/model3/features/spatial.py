"""
features/spatial.py
=====================
Category A: SPATIAL FEATURES (see spec section 9.A).
"""

from __future__ import annotations

import math
from typing import Dict, Optional

from ..config import FeatureConfig
from ..geo_utils import haversine_km, min_distance_to_polygon_km
from ..schemas import CandidateVessel, SpillRecord


def compute_spatial_features(
    vessel: CandidateVessel, spill: SpillRecord, config: FeatureConfig
) -> Dict[str, Optional[float]]:
    obs = vessel.observations
    centroid = spill.require_centroid()

    if not obs:
        return {
            "spatial_min_distance_centroid_km": None,
            "spatial_distance_at_closest_ais_km": None,
            "spatial_mean_distance_km": None,
            "spatial_min_distance_polygon_km": None,
            "spatial_n_obs_within_radius": 0,
        }

    distances = [haversine_km((o.latitude, o.longitude), centroid) for o in obs]
    min_dist = min(distances)
    mean_dist = sum(distances) / len(distances)

    # "distance at closest AIS observation" == the minimum distance itself,
    # by definition, when "closest" is defined spatially. We keep both fields
    # per the spec (they are the same value here; kept separate so a future
    # change to "closest in TIME" for the second field doesn't require a
    # schema change).
    distance_at_closest = min_dist

    polygon_dist = None
    if spill.has_polygon():
        polygon_dist = min(
            min_distance_to_polygon_km((o.latitude, o.longitude), spill.polygon)
            for o in obs
        )

    n_within_radius = sum(1 for d in distances if d <= config.vicinity_radius_km)

    return {
        "spatial_min_distance_centroid_km": min_dist,
        "spatial_distance_at_closest_ais_km": distance_at_closest,
        "spatial_mean_distance_km": mean_dist,
        "spatial_min_distance_polygon_km": polygon_dist,
        "spatial_n_obs_within_radius": n_within_radius,
    }
