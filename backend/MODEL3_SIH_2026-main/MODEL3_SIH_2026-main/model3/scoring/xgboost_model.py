"""
scoring/xgboost_model.py
==========================
MODE B -- ML model, used ONLY when credible labeled vessel-attribution data
exists (spec explicitly forbids fabricating labels to force this path).

A "label" here means a real, investigator/regulator-confirmed outcome for a
(spill, vessel) pair -- e.g. from a maritime authority's closed-case record,
NOT anything auto-derived from the heuristic score itself (that would just be
the heuristic re-encoded as a model, and would silently launder the
heuristic's assumptions as if they were learned from data).

Colab free-tier T4 friendly: XGBoost here runs on CPU (tabular data, small
row counts per spill -- GPU offers no real benefit and adds fragility on
Colab free tier). If GPU histogram training is ever desired, set
`tree_method="hist", device="cuda"`, but this is NOT required.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

try:
    import xgboost as xgb
except ImportError:  # pragma: no cover
    xgb = None

DEFAULT_NUMERIC_FEATURES: List[str] = [
    "spatial_min_distance_centroid_km",
    "spatial_mean_distance_km",
    "spatial_min_distance_polygon_km",
    "spatial_n_obs_within_radius",
    "temporal_abs_time_diff_closest_hr",
    "temporal_time_diff_last_obs_hr",
    "temporal_time_in_vicinity_hr",
    "temporal_n_obs_in_window",
    "temporal_hours_since_last_near_spill",
    "trajectory_min_distance_km",
    "trajectory_intersects_polygon",
    "trajectory_passes_near_spill",
    "trajectory_heading_alignment_deg",
    "behavior_mean_speed_knots",
    "behavior_max_speed_knots",
    "behavior_speed_std_knots",
    "behavior_speed_change_knots",
    "behavior_heading_variation_deg",
    "behavior_is_slowdown",
    "behavior_is_loitering",
    "gap_longest_hr",
    "gap_near_spill_hr",
    "gap_overlaps_relevant_window",
    "gap_count",
    "env_wind_speed_ms",
    "env_wind_heading_alignment_deg",
    "env_drift_alignment_deg",
    "n_ais_observations",
]


@dataclass
class XGBAttributionModel:
    """Thin, explicit wrapper around an XGBoost classifier for candidate
    attribution scoring. Deliberately does NOT auto-train on import or on
    construction -- training requires the caller to explicitly pass in a
    labeled DataFrame via `fit()`.
    """

    feature_columns: List[str] = field(default_factory=lambda: list(DEFAULT_NUMERIC_FEATURES))
    model: "xgb.XGBClassifier" = None
    params: dict = field(
        default_factory=lambda: dict(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="logloss",
            tree_method="hist",  # CPU histogram method; safe on Colab free tier
            random_state=42,
        )
    )

    def _require_xgb(self):
        if xgb is None:
            raise ImportError(
                "xgboost is not installed. Install with `pip install xgboost` to "
                "use Mode B. Mode A (heuristic) does not require this dependency."
            )

    def _prepare_X(self, df: pd.DataFrame) -> pd.DataFrame:
        X = df.reindex(columns=self.feature_columns)
        # bool -> int, everything else coerced to float; NaN left as NaN
        # (XGBoost natively handles missing values, so we do NOT impute here
        # -- imputing would fabricate evidence for missing AIS/env data).
        for col in X.columns:
            if X[col].dtype == bool:
                X[col] = X[col].astype(float)
        X = X.apply(pd.to_numeric, errors="coerce")
        return X

    def fit(self, labeled_features: pd.DataFrame, label_column: str = "label") -> "XGBAttributionModel":
        """`labeled_features` must contain the feature columns plus a
        `label_column` of REAL, credible ground truth (0/1: vessel confirmed
        NOT linked / confirmed linked by an actual investigation). This
        method does not generate, sample, or infer labels itself."""
        self._require_xgb()
        if label_column not in labeled_features.columns:
            raise ValueError(
                f"'{label_column}' not found in labeled_features. Do not call fit() "
                "without real labels -- see module docstring."
            )
        y = labeled_features[label_column].astype(int)
        if y.nunique() < 2:
            raise ValueError(
                "Labeled data has only one class present. A credible attribution "
                "dataset needs both positive and negative confirmed examples; "
                "refusing to train on a degenerate single-class label set."
            )
        X = self._prepare_X(labeled_features)
        self.model = xgb.XGBClassifier(**self.params)
        self.model.fit(X, y)
        logger.info("XGBoost attribution model trained on %d labeled rows.", len(X))
        return self

    def predict_score(self, features: pd.DataFrame) -> np.ndarray:
        """Return a 0-100 candidate_priority_score per row using the trained
        classifier's positive-class probability."""
        if self.model is None:
            raise RuntimeError(
                "Model has not been trained. Call fit() with real labeled data first, "
                "or use scoring.heuristic.score_candidates_heuristic (Mode A) instead."
            )
        X = self._prepare_X(features)
        proba = self.model.predict_proba(X)[:, 1]
        return np.round(proba * 100.0, 2)

    def feature_importance(self) -> pd.Series:
        if self.model is None:
            raise RuntimeError("Model has not been trained.")
        importances = self.model.feature_importances_
        return pd.Series(importances, index=self.feature_columns).sort_values(ascending=False)

    def save(self, path: str) -> None:
        self._require_xgb()
        if self.model is None:
            raise RuntimeError("Nothing to save -- model has not been trained.")
        self.model.save_model(path)
        meta_path = path + ".features.json"
        with open(meta_path, "w") as f:
            json.dump({"feature_columns": self.feature_columns, "params": self.params}, f, indent=2)
        logger.info("Saved model to %s and feature manifest to %s", path, meta_path)

    @classmethod
    def load(cls, path: str) -> "XGBAttributionModel":
        if xgb is None:
            raise ImportError("xgboost is not installed.")
        meta_path = path + ".features.json"
        with open(meta_path) as f:
            meta = json.load(f)
        instance = cls(feature_columns=meta["feature_columns"], params=meta["params"])
        instance.model = xgb.XGBClassifier(**meta["params"])
        instance.model.load_model(path)
        return instance


def score_candidates_ml(
    features: pd.DataFrame, model: XGBAttributionModel
) -> pd.DataFrame:
    """Mode B scoring: identical output contract to
    scoring.heuristic.score_candidates_heuristic (adds candidate_priority_score
    + rank), but sourced from a trained XGBoost model instead of fixed
    weights."""
    df = features.copy()
    if df.empty:
        df["candidate_priority_score"] = pd.Series(dtype=float)
        df["rank"] = pd.Series(dtype=int)
        return df
    df["candidate_priority_score"] = model.predict_score(df)
    df = df.sort_values("candidate_priority_score", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    return df
