"""
features/build_features.py
=============================
Orchestrates categories A-G into ONE ROW PER CANDIDATE VESSEL (spec section
10). Input: one SpillRecord + many CandidateVessel objects (+ optional
EnvironmentalRecord). Output: a pandas DataFrame, one row per vessel_id.
"""

from __future__ import annotations

from typing import List, Optional

import pandas as pd

from ..config import FeatureConfig
from ..schemas import CandidateVessel, EnvironmentalRecord, SpillRecord
from .spatial import compute_spatial_features
from .temporal import compute_temporal_features
from .trajectory import compute_trajectory_features
from .behavior import compute_behavior_features
from .gaps import compute_gap_features
from .environmental import compute_environmental_features
from .metadata import compute_metadata_features


def build_feature_row(
    vessel: CandidateVessel,
    spill: SpillRecord,
    config: FeatureConfig,
    environment: Optional[EnvironmentalRecord] = None,
) -> dict:
    row = {"vessel_id": vessel.vessel_id, "spill_id": spill.spill_id}
    row.update(compute_spatial_features(vessel, spill, config))
    row.update(compute_temporal_features(vessel, spill, config))
    row.update(compute_trajectory_features(vessel, spill))
    row.update(compute_behavior_features(vessel, spill, config))
    row.update(compute_gap_features(vessel, spill, config))
    row.update(compute_environmental_features(vessel, spill, environment))
    row.update(compute_metadata_features(vessel))
    row["n_ais_observations"] = len(vessel.observations)
    return row


def build_feature_table(
    candidates: List[CandidateVessel],
    spill: SpillRecord,
    config: FeatureConfig,
    environment: Optional[EnvironmentalRecord] = None,
) -> pd.DataFrame:
    """Turn (one spill + many candidate vessels) into one feature row per
    vessel. Returns an empty-but-correctly-columned DataFrame if there are no
    candidates, so downstream code doesn't need special-case handling."""
    rows = [build_feature_row(v, spill, config, environment) for v in candidates]
    if not rows:
        return pd.DataFrame(
            columns=[
                "vessel_id",
                "spill_id",
                "spatial_min_distance_centroid_km",
                "temporal_abs_time_diff_closest_hr",
                "trajectory_min_distance_km",
                "gap_longest_hr",
            ]
        )
    return pd.DataFrame(rows)
