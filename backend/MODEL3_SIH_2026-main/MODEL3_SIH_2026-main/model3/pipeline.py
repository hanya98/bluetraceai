"""
pipeline.py
============
End-to-end Model 3 orchestration:

    AIS raw records -> preprocess -> candidate filtering -> feature engineering
    -> scoring (Mode A or Mode B) -> explainability -> ranked output

This is the single entry point the backend team should call.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pandas as pd

from .ais_preprocessing import (
    PreprocessingReport,
    group_by_vessel,
    preprocess_ais_records,
)
from .candidate_filtering import filter_candidate_vessels
from .config import Model3Config
from .explain import explain_table_heuristic, explain_with_shap
from .features.build_features import build_feature_table
from .schemas import EnvironmentalRecord, SpillRecord, VesselMetadata
from .scoring.heuristic import score_candidates_heuristic
from .scoring.xgboost_model import XGBAttributionModel, score_candidates_ml

logger = logging.getLogger(__name__)


@dataclass
class Model3Result:
    spill_id: str
    ranked_candidates: pd.DataFrame  # includes candidate_priority_score, rank, explanation
    preprocessing_report: PreprocessingReport
    mode_used: str

    def to_api_payload(self) -> Dict[str, Any]:
        from .api_contract import ranked_dataframe_to_api_payload

        return ranked_dataframe_to_api_payload(self.spill_id, self.ranked_candidates, self.mode_used)


class Model3Pipeline:
    """Stateful convenience wrapper. Config is the only required state; an
    optional pre-trained XGBAttributionModel enables Mode B."""

    def __init__(self, config: Optional[Model3Config] = None, ml_model: Optional[XGBAttributionModel] = None):
        self.config = config or Model3Config()
        self.ml_model = ml_model
        if self.config.mode == "ml" and self.ml_model is None:
            logger.warning(
                "Model3Config.mode='ml' but no trained ml_model was provided; "
                "falling back to heuristic (Mode A) for this pipeline instance."
            )

    def run(
        self,
        spill: SpillRecord,
        raw_ais_records: List[Dict[str, Any]],
        vessel_metadata: Optional[Dict[str, VesselMetadata]] = None,
        environment: Optional[EnvironmentalRecord] = None,
    ) -> Model3Result:
        observations, report = preprocess_ais_records(raw_ais_records)
        by_vessel = group_by_vessel(observations)

        candidates = filter_candidate_vessels(
            spill=spill,
            observations_by_vessel=by_vessel,
            config=self.config.candidate_filter,
            metadata_by_vessel=vessel_metadata,
        )

        features = build_feature_table(candidates, spill, self.config.features, environment)

        use_ml = self.config.mode == "ml" and self.ml_model is not None and self.ml_model.model is not None
        if use_ml:
            scored = score_candidates_ml(features, self.ml_model)
            scored = explain_with_shap(self.ml_model, features, scored)
            mode_used = "ml"
        else:
            scored = score_candidates_heuristic(features, self.config.scoring)
            scored = explain_table_heuristic(scored)
            mode_used = "heuristic"

        return Model3Result(
            spill_id=spill.spill_id,
            ranked_candidates=scored,
            preprocessing_report=report,
            mode_used=mode_used,
        )
