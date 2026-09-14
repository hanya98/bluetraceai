"""
explain.py
===========
Human-readable, non-causal explanations for a ranked candidate list.

HARD RULE enforced throughout this module: never produce a sentence that
asserts a vessel caused/is guilty of a spill. Always phrase output as
ranked, evidence-based candidacy for investigation.

Supports:
  - Mode A: reason strings generated directly from the interpretable
    heuristic feature contributions.
  - Mode B: SHAP-based per-row explanations when a trained XGBoost model is
    available (falls back to a plain feature-value summary if `shap` is not
    installed, so this never hard-fails the pipeline).
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

try:
    import shap  # optional dependency
except ImportError:  # pragma: no cover
    shap = None


BANNED_PHRASES = [
    "caused the spill",
    "is guilty",
    "responsible for the spill",
    "confirmed to have",
]


def _assert_non_causal(text: str) -> str:
    lowered = text.lower()
    for phrase in BANNED_PHRASES:
        if phrase in lowered:
            raise ValueError(
                f"Generated explanation text contains a causal/guilt assertion "
                f"('{phrase}'), which violates Model 3's non-causal output policy: {text!r}"
            )
    return text


def _fmt(value, unit: str = "", digits: int = 1) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "unavailable"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        return f"{round(float(value), digits)}{unit}"
    return str(value)


def explain_row_heuristic(row: pd.Series) -> str:
    """Build a plain-English, evidence-listing sentence for one ranked
    candidate row. Explicitly non-causal phrasing."""
    parts = []

    dist = row.get("spatial_min_distance_centroid_km")
    if dist is not None and not pd.isna(dist):
        parts.append(f"closest AIS position {_fmt(dist, ' km')} from the spill centroid")

    tdiff = row.get("temporal_abs_time_diff_closest_hr")
    if tdiff is not None and not pd.isna(tdiff):
        parts.append(f"{_fmt(tdiff, ' hr')} time difference from spill detection")

    if row.get("trajectory_intersects_polygon"):
        parts.append("AIS trajectory intersects the estimated spill polygon")
    elif row.get("trajectory_passes_near_spill"):
        parts.append("trajectory passes closer to the spill than its average distance")

    align = row.get("trajectory_heading_alignment_deg")
    if align is not None and not pd.isna(align) and align <= 45:
        parts.append(f"heading aligned within {_fmt(align, ' deg')} of the bearing to the spill")

    if row.get("behavior_is_loitering"):
        parts.append("a sustained low-speed / loitering period was observed nearby")

    if row.get("gap_overlaps_relevant_window"):
        parts.append(
            "an AIS reporting gap overlaps the relevant time window "
            "(this indicates missing AIS data only, not confirmed transponder shutdown)"
        )

    evidence = "; ".join(parts) if parts else "limited distinguishing evidence in the available AIS data"

    score = row.get("candidate_priority_score")
    rank = row.get("rank")
    vessel_id = row.get("vessel_id")

    text = (
        f"Vessel {vessel_id} is ranked #{int(rank) if rank is not None else '?'} "
        f"with a candidate priority score of {_fmt(score)}/100, based on: {evidence}. "
        "This is a ranked candidate for further investigation, not a determination "
        "of fault or causation."
    )
    return _assert_non_causal(text)


def explain_table_heuristic(scored: pd.DataFrame) -> pd.DataFrame:
    df = scored.copy()
    if df.empty:
        df["explanation"] = pd.Series(dtype=str)
        return df
    df["explanation"] = df.apply(explain_row_heuristic, axis=1)
    return df


def explain_with_shap(
    model,  # XGBAttributionModel
    features: pd.DataFrame,
    scored: pd.DataFrame,
    top_k: int = 3,
) -> pd.DataFrame:
    """Mode B explanation: attach top-k SHAP-driving features per row as a
    non-causal explanation string. Falls back to explain_table_heuristic-style
    generic phrasing (without SHAP internals) if `shap` isn't installed --
    never raises just because the optional dependency is missing."""
    df = scored.copy()

    if shap is None or model.model is None:
        logger.warning("shap not installed or model not trained; using generic explanation fallback.")
        df["explanation"] = df.apply(
            lambda r: _assert_non_causal(
                f"Vessel {r.get('vessel_id')} ranked #{int(r.get('rank'))} "
                f"(candidate priority score {_fmt(r.get('candidate_priority_score'))}/100) "
                "by the trained attribution model. This is a ranked candidate for "
                "investigation, not a determination of causation."
            ),
            axis=1,
        )
        return df

    X = model._prepare_X(features)
    explainer = shap.TreeExplainer(model.model)
    shap_values = explainer.shap_values(X)

    explanations = []
    for i in range(len(X)):
        row_shap = pd.Series(shap_values[i], index=X.columns)
        top_features = row_shap.abs().sort_values(ascending=False).head(top_k).index.tolist()
        contributions = []
        for feat in top_features:
            direction = "increased" if row_shap[feat] > 0 else "decreased"
            val = X.iloc[i][feat]
            contributions.append(f"{feat}={_fmt(val)} ({direction} the score)")
        vessel_id = scored.iloc[i].get("vessel_id")
        rank = scored.iloc[i].get("rank")
        score = scored.iloc[i].get("candidate_priority_score")
        text = (
            f"Vessel {vessel_id} is ranked #{int(rank)} with a candidate priority "
            f"score of {_fmt(score)}/100. Top contributing evidence: "
            f"{'; '.join(contributions)}. This ranking reflects statistical "
            "association with the AIS/spill evidence used to train the model, "
            "not a determination of fault or causation."
        )
        explanations.append(_assert_non_causal(text))

    df["explanation"] = explanations
    return df
