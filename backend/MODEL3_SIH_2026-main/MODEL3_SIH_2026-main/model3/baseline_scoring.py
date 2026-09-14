"""
MODE A — Heuristic baseline evidence score.

Works with zero labeled training data. Combines normalized sub-scores from
each evidence category into a single "candidate_priority_score" in [0, 1].
This is NOT a probability of guilt — it is a weighted evidence heuristic,
useful as a cold-start ranking until labeled data justifies Mode B.
"""

from typing import Dict
import numpy as np
import pandas as pd

from .config import Model3Config


def _normalize_inverse(value: float, scale: float) -> float:
    """Map a 'smaller is more suspicious' value to [0,1], 1 = most suspicious.
    scale is the distance/time at which the score decays to ~0.37 (1/e)."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return 0.0
    return float(np.exp(-value / scale))


def _spatial_subscore(row: pd.Series, config: Model3Config) -> float:
    return _normalize_inverse(row.get("min_distance_km"), scale=config.candidate_radius_km / 3)


def _temporal_subscore(row: pd.Series, config: Model3Config) -> float:
    return _normalize_inverse(row.get("abs_time_diff_closest_hr"), scale=config.temporal_window_hours / 3)


def _trajectory_subscore(row: pd.Series) -> float:
    score = 0.0
    weight_sum = 0.0
    if row.get("heading_alignment_score") is not None and not pd.isna(row.get("heading_alignment_score")):
        score += max(0.0, row["heading_alignment_score"]) * 0.6
        weight_sum += 0.6
    if row.get("trajectory_intersects_polygon"):
        score += 1.0 * 0.4
        weight_sum += 0.4
    return score / weight_sum if weight_sum > 0 else 0.0


def _ais_gap_subscore(row: pd.Series) -> float:
    """AIS gap contributes MILDLY — it is context, never proof of guilt."""
    if row.get("significant_gap_overlaps_window"):
        return 0.6  # capped well below 1.0 intentionally
    if (row.get("longest_ais_gap_hr") or 0) > 0:
        return 0.2
    return 0.0


def _environment_subscore(row: pd.Series) -> float:
    if row.get("drift_alignment_score") is not None and not pd.isna(row.get("drift_alignment_score")):
        return max(0.0, row["drift_alignment_score"])
    return 0.0  # missing wind data -> neutral, does not penalize the vessel


def compute_baseline_scores(feature_df: pd.DataFrame, config: Model3Config) -> pd.DataFrame:
    """Adds 'candidate_priority_score' and per-category subscores to feature_df."""
    if feature_df.empty:
        return feature_df

    w = config.baseline_weights
    out = feature_df.copy()
    out["_sub_spatial"] = out.apply(lambda r: _spatial_subscore(r, config), axis=1)
    out["_sub_temporal"] = out.apply(lambda r: _temporal_subscore(r, config), axis=1)
    out["_sub_trajectory"] = out.apply(_trajectory_subscore, axis=1)
    out["_sub_ais_gap"] = out.apply(_ais_gap_subscore, axis=1)
    out["_sub_environment"] = out.apply(_environment_subscore, axis=1)

    out["candidate_priority_score"] = (
        w["spatial"] * out["_sub_spatial"] +
        w["temporal"] * out["_sub_temporal"] +
        w["trajectory"] * out["_sub_trajectory"] +
        w["ais_gap"] * out["_sub_ais_gap"] +
        w["environment"] * out["_sub_environment"]
    ).clip(0, 1)

    return out
