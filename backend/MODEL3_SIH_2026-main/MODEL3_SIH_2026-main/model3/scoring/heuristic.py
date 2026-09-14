"""
scoring/heuristic.py
======================
MODE A -- heuristic baseline. Works with zero labeled training data. Produces
a `candidate_priority_score` (0-100, higher = more evidence worth
investigating) for every candidate row from build_feature_table().

This is a transparent, documented weighted combination -- NOT a calibrated
probability. It exists so the system produces a usable ranking on day one and
so Mode B (XGBoost) has a sane fallback whenever labels aren't available.
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np
import pandas as pd

from ..config import ScoringConfig


def _decay_score(value: Optional[float], decay: float) -> float:
    """Map a "smaller is more suspicious" quantity to a 0-1 score using
    exponential decay: 1.0 at value=0, ~0.37 at value=decay, ->0 as value
    grows. Missing values score 0 (no evidence contributed), NOT 0.5 --
    absence of evidence should not be treated as neutral-positive evidence."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return 0.0
    return float(math.exp(-max(value, 0.0) / max(decay, 1e-9)))


def _bool_score(value) -> float:
    if value is None:
        return 0.0
    return 1.0 if bool(value) else 0.0


def _alignment_score(diff_deg: Optional[float]) -> float:
    """0-180 degree difference -> 1.0 (perfectly aligned) .. 0.0 (opposite)."""
    if diff_deg is None or (isinstance(diff_deg, float) and math.isnan(diff_deg)):
        return 0.0
    return float(max(0.0, 1.0 - diff_deg / 180.0))


def score_row(row: pd.Series, config: ScoringConfig) -> float:
    """
    Transparent heuristic candidate-priority score.

    Higher score means stronger evidence for investigation.
    This is NOT a probability and does NOT establish causation.
    """

    spatial = _decay_score(
        row.get("spatial_min_distance_centroid_km"),
        config.spatial_decay_km,
    )

    temporal = _decay_score(
        row.get("temporal_abs_time_diff_closest_hr"),
        config.temporal_decay_hours,
    )

    # Trajectory evidence.
    trajectory_components = [
        _bool_score(
            row.get("trajectory_intersects_polygon")
        ),
        _bool_score(
            row.get("trajectory_passes_near_spill")
        ),
    ]

    heading_alignment = row.get(
        "trajectory_heading_alignment_deg"
    )

    if (
        heading_alignment is not None
        and not (
            isinstance(heading_alignment, float)
            and math.isnan(heading_alignment)
        )
    ):
        trajectory_components.append(
            _alignment_score(heading_alignment)
        )

    trajectory = float(
        np.mean(trajectory_components)
    ) if trajectory_components else 0.0

    trajectory = float(
        np.mean(trajectory_components)
    )

    # Behavior evidence.
    behavior_components = [
        _bool_score(
            row.get("behavior_is_loitering")
        ),
        _bool_score(
            row.get("behavior_is_slowdown")
        ),
    ]

    behavior = float(
        np.mean(behavior_components)
    )

    # AIS gaps remain deliberately weak.
    ais_gap = _bool_score(
        row.get("gap_overlaps_relevant_window")
    )

    # Environmental evidence.
    env_components = []

    wind_alignment = row.get(
        "env_wind_heading_alignment_deg"
    )

    drift_alignment = row.get(
        "env_drift_alignment_deg"
    )

    if wind_alignment is not None:
        env_components.append(
            _alignment_score(wind_alignment)
        )

    if drift_alignment is not None:
        env_components.append(
            _alignment_score(drift_alignment)
        )

    environmental = (
        float(np.mean(env_components))
        if env_components
        else 0.0
    )

    # Explicit weights.
    weights = {
        "spatial": config.weight_spatial,
        "temporal": config.weight_temporal,
        "trajectory": config.weight_trajectory,
        "behavior": config.weight_behavior,
        "ais_gap": config.weight_ais_gap,
        "environmental": config.weight_environmental,
    }

    total_weight = sum(weights.values()) or 1.0

    weighted_sum = (
        spatial * weights["spatial"]
        + temporal * weights["temporal"]
        + trajectory * weights["trajectory"]
        + behavior * weights["behavior"]
        + ais_gap * weights["ais_gap"]
        + environmental * weights["environmental"]
    )

    normalized = weighted_sum / total_weight

    return round(
        normalized * 100.0,
        2,
    )

def score_candidates_heuristic(features: pd.DataFrame, config: ScoringConfig) -> pd.DataFrame:
    """Add `candidate_priority_score` and `rank` columns to a feature table
    produced by build_feature_table(). Does not mutate the input in place."""
    df = features.copy()
    if df.empty:
        df["candidate_priority_score"] = pd.Series(dtype=float)
        df["rank"] = pd.Series(dtype=int)
        return df

    df["candidate_priority_score"] = df.apply(lambda r: score_row(r, config), axis=1)
    df = df.sort_values("candidate_priority_score", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    return df
