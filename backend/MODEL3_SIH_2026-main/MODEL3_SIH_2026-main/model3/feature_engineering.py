"""
Feature engineering (Section 9) — the core of Model 3.

Converts (one spill + many AIS tracks) -> (one VesselFeatureRow per
candidate vessel). Each category (spatial / temporal / trajectory /
behavior / AIS-gap / environment / metadata) is implemented as its own
function so it stays independently testable and swappable.
"""

from typing import Optional, Dict, List
import math
import numpy as np
import pandas as pd

from .schemas import Spill, VesselFeatureRow
from .config import Model3Config
from .geo_utils import (
    haversine_km, bearing_deg, angular_diff_deg,
    point_to_polygon_min_distance_km, segment_intersects_polygon,
)


def _spatial_features(vessel_df: pd.DataFrame, spill: Spill, config: Model3Config) -> Dict:
    dists = vessel_df["distance_to_spill_km"].values
    closest_idx = int(np.argmin(dists))
    min_distance_km = float(dists[closest_idx])
    mean_distance_km = float(np.mean(dists))
    n_obs_within_radius = int((dists <= config.candidate_radius_km).sum())

    min_distance_to_polygon_km = None
    if spill.spill_polygon:
        polygon_dists = [
            point_to_polygon_min_distance_km(row.latitude, row.longitude, spill.spill_polygon)
            for row in vessel_df.itertuples()
        ]
        polygon_dists = [d for d in polygon_dists if d is not None]
        if polygon_dists:
            min_distance_to_polygon_km = float(min(polygon_dists))

    return {
        "min_distance_km": min_distance_km,
        "distance_at_closest_obs_km": min_distance_km,  # same observation by definition
        "mean_distance_km": mean_distance_km,
        "min_distance_to_polygon_km": min_distance_to_polygon_km,
        "n_obs_within_radius": n_obs_within_radius,
        "_closest_idx": closest_idx,  # internal, stripped before output
    }


def _temporal_features(vessel_df: pd.DataFrame, spill: Spill, config: Model3Config,
                        closest_idx: int) -> Dict:
    spill_time = pd.Timestamp(spill.timestamp_utc)
    if spill_time.tzinfo is None:
        spill_time = spill_time.tz_localize("UTC")

    times = vessel_df["timestamp_utc"]
    closest_obs_time = times.iloc[closest_idx]
    abs_time_diff_closest_hr = abs((closest_obs_time - spill_time).total_seconds()) / 3600.0

    last_obs_time = times.iloc[-1]
    time_diff_last_obs_hr = abs((last_obs_time - spill_time).total_seconds()) / 3600.0

    near_mask = vessel_df["distance_to_spill_km"] <= config.near_spill_radius_km
    n_obs_within_window = int(len(vessel_df))

    time_spent_near_spill_hr = 0.0
    if near_mask.sum() >= 2:
        near_times = times[near_mask].sort_values()
        # Approximate dwell time as span between first and last "near" ping.
        time_spent_near_spill_hr = (near_times.iloc[-1] - near_times.iloc[0]).total_seconds() / 3600.0

    time_since_last_near_spill_hr = None
    if near_mask.any():
        last_near_time = times[near_mask].max()
        time_since_last_near_spill_hr = (spill_time - last_near_time).total_seconds() / 3600.0

    return {
        "abs_time_diff_closest_hr": float(abs_time_diff_closest_hr),
        "time_diff_last_obs_hr": float(time_diff_last_obs_hr),
        "time_spent_near_spill_hr": float(time_spent_near_spill_hr),
        "n_obs_within_window": n_obs_within_window,
        "time_since_last_near_spill_hr": (
            float(time_since_last_near_spill_hr) if time_since_last_near_spill_hr is not None else None
        ),
    }


def _trajectory_features(vessel_df: pd.DataFrame, spill: Spill, closest_idx: int) -> Dict:
    closest_row = vessel_df.iloc[closest_idx]
    bearing_to_spill = bearing_deg(closest_row["latitude"], closest_row["longitude"],
                                    spill.latitude, spill.longitude)

    vessel_heading = closest_row.get("heading_deg", None)
    vessel_speed = closest_row.get("speed_knots", None)

    # Heading is not reliable evidence when a vessel is essentially stationary.
    # AIS heading may be stale/arbitrary while a vessel is stopped or loitering.
    if (
        vessel_heading is not None
        and not pd.isna(vessel_heading)
        and vessel_speed is not None
        and not pd.isna(vessel_speed)
        and float(vessel_speed) >= 2.0
    ):
        alignment_diff = angular_diff_deg(
            vessel_heading,
            bearing_to_spill,
        )
        heading_alignment_score = 1.0 - (
            alignment_diff / 180.0
        )
    else:
        vessel_heading = None
        heading_alignment_score = None

    min_trajectory_distance_km = float(vessel_df["distance_to_spill_km"].min())

    trajectory_intersects_polygon = None
    if spill.spill_polygon and len(vessel_df) >= 2:
        intersects = False
        coords = list(zip(vessel_df["latitude"], vessel_df["longitude"]))
        for i in range(len(coords) - 1):
            if segment_intersects_polygon(coords[i], coords[i + 1], spill.spill_polygon):
                intersects = True
                break
        trajectory_intersects_polygon = intersects

    return {
        "min_trajectory_distance_km": min_trajectory_distance_km,
        "trajectory_intersects_polygon": trajectory_intersects_polygon,
        "bearing_vessel_to_spill_deg": float(bearing_to_spill),
        "vessel_heading_deg": float(vessel_heading) if vessel_heading is not None else None,
        "heading_alignment_score": (
            float(heading_alignment_score) if heading_alignment_score is not None else None
        ),
    }


def _behavior_features(
    vessel_df: pd.DataFrame,
    spill: Spill,
    config: Model3Config,
) -> Dict:
    """
    Calculate vessel behavior primarily around the spill event.

    This avoids allowing an unrelated low-speed period elsewhere in a
    long AIS track to dominate the attribution score.
    """

    vessel_df = vessel_df.sort_values("timestamp_utc").reset_index(drop=True)

    spill_time = pd.Timestamp(spill.timestamp_utc)
    if spill_time.tzinfo is None:
        spill_time = spill_time.tz_localize("UTC")

    # Focus behavior analysis on observations reasonably close to the spill.
    near_mask = (
        vessel_df["distance_to_spill_km"]
        <= config.near_spill_radius_km
    )

    near_df = vessel_df.loc[near_mask].copy()

    # If there are no nearby observations, behavior provides no evidence.
    if near_df.empty:
        return {
            "mean_speed_knots": None,
            "max_speed_knots": None,
            "speed_std_knots": None,
            "speed_change_knots": None,
            "heading_variation_deg": None,
            "stop_or_slowdown_flag": None,
            "loitering_flag": None,
        }

    speeds = near_df["speed_knots"].dropna()
    headings = near_df["heading_deg"].dropna()

    if speeds.empty:
        return {
            "mean_speed_knots": None,
            "max_speed_knots": None,
            "speed_std_knots": None,
            "speed_change_knots": None,
            "heading_variation_deg": None,
            "stop_or_slowdown_flag": None,
            "loitering_flag": None,
        }

    mean_speed = float(speeds.mean())
    max_speed = float(speeds.max())

    speed_std = float(speeds.std()) if len(speeds) > 1 else 0.0

    speed_change = None
    if len(speeds) >= 2:
        speed_change = float(speeds.iloc[-1] - speeds.iloc[0])

    heading_variation = None
    if len(headings) > 1:
        heading_variation = float(headings.max() - headings.min())

    # Low-speed evidence must occur near the spill.
    stop_or_slowdown = bool(
        (speeds < config.loitering_speed_threshold_knots).any()
    )

    # Require the low-speed period to persist near the spill.
    loitering = False

    below_thresh = (
        near_df["speed_knots"]
        < config.loitering_speed_threshold_knots
    )

    if below_thresh.any():
        slow_times = near_df.loc[
            below_thresh,
            "timestamp_utc"
        ].sort_values()

        if len(slow_times) >= 2:
            span_hr = (
                slow_times.iloc[-1] - slow_times.iloc[0]
            ).total_seconds() / 3600.0

            loitering = (
                span_hr >= config.loitering_min_duration_hours
            )

    return {
        "mean_speed_knots": mean_speed,
        "max_speed_knots": max_speed,
        "speed_std_knots": speed_std,
        "speed_change_knots": speed_change,
        "heading_variation_deg": heading_variation,
        "stop_or_slowdown_flag": stop_or_slowdown,
        "loitering_flag": loitering,
    }

def _ais_gap_features(vessel_df: pd.DataFrame, spill: Spill, config: Model3Config) -> Dict:
    """AIS gaps are purely descriptive of missing data density. They are
    NEVER treated as evidence of intentional shutdown (Section 9E)."""
    times = vessel_df["timestamp_utc"].sort_values().reset_index(drop=True)
    if len(times) < 2:
        return {
            "longest_ais_gap_hr": None,
            "ais_gap_near_spill_hr": None,
            "significant_gap_overlaps_window": None,
            "n_ais_gaps": 0,
        }

    gaps_hr = (times.diff().dropna().dt.total_seconds() / 3600.0)
    min_gap_hr = config.ais_gap_minimum_minutes / 60.0
    sig_gap_hr = config.significant_ais_gap_minutes / 60.0

    real_gaps = gaps_hr[gaps_hr >= min_gap_hr]
    longest_gap_hr = float(real_gaps.max()) if not real_gaps.empty else 0.0
    n_gaps = int((real_gaps >= min_gap_hr).sum())

    spill_time = pd.Timestamp(spill.timestamp_utc)
    if spill_time.tzinfo is None:
        spill_time = spill_time.tz_localize("UTC")

    ais_gap_near_spill_hr = 0.0
    significant_overlap = False
    for i in range(1, len(times)):
        gap = gaps_hr.iloc[i - 1]
        if gap < min_gap_hr:
            continue
        gap_start, gap_end = times.iloc[i - 1], times.iloc[i]
        if gap_start <= spill_time <= gap_end:
            ais_gap_near_spill_hr = float(gap)
            significant_overlap = gap >= sig_gap_hr

    return {
        "longest_ais_gap_hr": longest_gap_hr,
        "ais_gap_near_spill_hr": ais_gap_near_spill_hr,
        "significant_gap_overlaps_window": significant_overlap,
        "n_ais_gaps": n_gaps,
    }


def _environment_features(vessel_df: pd.DataFrame, spill: Spill, closest_idx: int) -> Dict:
    """Optional — degrades gracefully to None if wind data absent.
    NOTE: wind values are model estimates (ERA5/Open-Meteo), not direct
    measurements — surface that caveat wherever this feature is reported."""
    wind_speed = getattr(spill, "wind_speed_ms", None)
    wind_dir = getattr(spill, "wind_direction_deg", None)

    if wind_speed is None and wind_dir is None:
        return {
            "wind_speed_ms": None, "wind_direction_deg": None,
            "wind_vessel_heading_diff_deg": None, "drift_alignment_score": None,
        }

    closest_row = vessel_df.iloc[closest_idx]
    heading = closest_row.get("heading_deg", None)
    wind_vessel_diff = None
    if wind_dir is not None and heading is not None and not pd.isna(heading):
        wind_vessel_diff = angular_diff_deg(heading, wind_dir)

    drift_alignment_score = None
    if spill.spill_drift_direction_deg is not None and heading is not None and not pd.isna(heading):
        diff = angular_diff_deg(heading, spill.spill_drift_direction_deg)
        drift_alignment_score = 1.0 - (diff / 180.0)

    return {
        "wind_speed_ms": wind_speed,
        "wind_direction_deg": wind_dir,
        "wind_vessel_heading_diff_deg": wind_vessel_diff,
        "drift_alignment_score": drift_alignment_score,
    }


def build_feature_row(vessel_id: str, vessel_df: pd.DataFrame, spill: Spill,
                       config: Model3Config) -> VesselFeatureRow:
    """Build the single feature row for one candidate vessel against one spill."""
    vessel_df = vessel_df.sort_values("timestamp_utc").reset_index(drop=True)

    spatial = _spatial_features(vessel_df, spill, config)
    closest_idx = spatial.pop("_closest_idx")
    temporal = _temporal_features(vessel_df, spill, config, closest_idx)
    trajectory = _trajectory_features(vessel_df, spill, closest_idx)
    behavior = _behavior_features(vessel_df, spill, config)
    gaps = _ais_gap_features(vessel_df, spill, config)
    environment = _environment_features(vessel_df, spill, closest_idx)

    vessel_type = None
    if "vessel_type" in vessel_df.columns:
        non_null = vessel_df["vessel_type"].dropna()
        vessel_type = non_null.iloc[0] if not non_null.empty else None

    fields = {**spatial, **temporal, **trajectory, **behavior, **gaps, **environment}
    return VesselFeatureRow(vessel_id=vessel_id, spill_id=spill.spill_id,
                             vessel_type=vessel_type, **fields)


def build_feature_table(candidate_ais_df: pd.DataFrame, spill: Spill,
                         config: Model3Config) -> List[VesselFeatureRow]:
    """One spill + many AIS tracks -> one VesselFeatureRow per candidate vessel."""
    rows = []
    for vessel_id, vessel_df in candidate_ais_df.groupby("vessel_id"):
        rows.append(build_feature_row(vessel_id, vessel_df, spill, config))
    return rows


def feature_rows_to_dataframe(rows: List[VesselFeatureRow]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([r.as_dict() for r in rows])
