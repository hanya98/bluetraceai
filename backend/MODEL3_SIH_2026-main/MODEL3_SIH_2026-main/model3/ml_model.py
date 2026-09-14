"""
MODE B — XGBoost attribution model.

Only trains when credible labeled data exists (Section 3: "Do NOT create
fake labels just to make XGBoost train"). Labels must come from real
investigative outcomes (e.g. confirmed responsible vessel / cleared vessel
from a maritime authority's report) — never synthesized here.
"""

from typing import List, Optional, Tuple
import numpy as np
import pandas as pd

from .config import Model3Config

FEATURE_COLUMNS = [
    "min_distance_km", "distance_at_closest_obs_km", "mean_distance_km",
    "min_distance_to_polygon_km", "n_obs_within_radius",
    "abs_time_diff_closest_hr", "time_diff_last_obs_hr",
    "time_spent_near_spill_hr", "n_obs_within_window", "time_since_last_near_spill_hr",
    "min_trajectory_distance_km", "bearing_vessel_to_spill_deg",
    "vessel_heading_deg", "heading_alignment_score",
    "mean_speed_knots", "max_speed_knots", "speed_std_knots", "speed_change_knots",
    "heading_variation_deg",
    "longest_ais_gap_hr", "ais_gap_near_spill_hr", "n_ais_gaps",
    "wind_speed_ms", "wind_direction_deg", "wind_vessel_heading_diff_deg",
    "drift_alignment_score",
]

BOOL_COLUMNS = [
    "trajectory_intersects_polygon", "stop_or_slowdown_flag", "loitering_flag",
    "significant_gap_overlaps_window",
]


class InsufficientLabeledDataError(Exception):
    pass


def _prepare_X(df: pd.DataFrame) -> pd.DataFrame:
    X = df.copy()
    for col in FEATURE_COLUMNS:
        if col not in X.columns:
            X[col] = np.nan
    for col in BOOL_COLUMNS:
        if col not in X.columns:
            X[col] = np.nan
        X[col] = X[col].map({True: 1.0, False: 0.0}).astype(float)
    return X[FEATURE_COLUMNS + BOOL_COLUMNS]


class XGBAttributionModel:
    """Thin wrapper around xgboost.XGBClassifier with the project's
    guardrails (min labeled examples, explicit missing-value handling)."""

    def __init__(self, config: Model3Config):
        self.config = config
        self.model = None
        self._is_trained = False

    def fit(self, feature_df: pd.DataFrame, labels: pd.Series):
        """labels: 1 = confirmed/likely responsible vessel per real
        investigative record, 0 = cleared/not implicated. NEVER pass
        synthetic labels."""
        if len(feature_df) != len(labels):
            raise ValueError("feature_df and labels must be the same length")
        n_labeled = int(labels.notna().sum())
        if n_labeled < self.config.min_labeled_examples_to_train:
            raise InsufficientLabeledDataError(
                f"Only {n_labeled} labeled examples available; need at least "
                f"{self.config.min_labeled_examples_to_train}. Falling back to "
                f"Mode A (heuristic baseline) is recommended instead of training."
            )
        try:
            import xgboost as xgb
        except ImportError as e:
            raise ImportError(
                "xgboost is required for Mode B. pip install xgboost"
            ) from e

        mask = labels.notna()
        X = _prepare_X(feature_df.loc[mask])
        y = labels.loc[mask].astype(int)

        self.model = xgb.XGBClassifier(**self.config.xgb_params)
        self.model.fit(X, y)
        self._is_trained = True
        self._feature_names = list(X.columns)
        return self

    def predict_scores(self, feature_df: pd.DataFrame) -> np.ndarray:
        if not self._is_trained:
            raise RuntimeError("Model not trained. Call fit() first, or use Mode A.")
        X = _prepare_X(feature_df)
        return self.model.predict_proba(X)[:, 1]

    def explain(self, feature_df: pd.DataFrame, top_k: int = 3) -> List[List[str]]:
        """Return top_k human-readable evidence strings per row using SHAP
        if available, falling back to feature_importances_ otherwise."""
        X = _prepare_X(feature_df)
        try:
            import shap
            explainer = shap.TreeExplainer(self.model)
            shap_values = explainer.shap_values(X)
            explanations = []
            for i in range(len(X)):
                row_shap = shap_values[i]
                order = np.argsort(-np.abs(row_shap))[:top_k]
                explanations.append([
                    f"{X.columns[j]} = {X.iloc[i][X.columns[j]]:.2f} "
                    f"({'raised' if row_shap[j] > 0 else 'lowered'} the score)"
                    for j in order
                ])
            return explanations
        except ImportError:
            importances = self.model.feature_importances_
            order = np.argsort(-importances)[:top_k]
            generic = [f"{X.columns[j]} (globally important feature)" for j in order]
            return [generic for _ in range(len(X))]
