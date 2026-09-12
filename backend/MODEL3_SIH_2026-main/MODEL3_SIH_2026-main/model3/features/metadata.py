"""
features/metadata.py
======================
Category G: VESSEL METADATA FEATURES (spec section 9.G).

Kept deliberately thin: metadata is exposed as categorical context, NOT
scored with strong weight (see config.ScoringConfig / scoring/heuristic.py --
there is intentionally no `weight_metadata`), per spec requirement that
vessel type must not dominate direct spatial/temporal evidence without
validation.
"""

from __future__ import annotations

from typing import Dict, Optional

from ..schemas import CandidateVessel


def compute_metadata_features(vessel: CandidateVessel) -> Dict[str, Optional[str]]:
    md = vessel.metadata
    if md is None:
        return {
            "meta_vessel_type": None,
            "meta_vessel_category": None,
            "meta_flag": None,
            "meta_imo": None,
            "meta_name": None,
        }
    return {
        "meta_vessel_type": md.vessel_type,
        "meta_vessel_category": md.vessel_category,
        "meta_flag": md.flag,
        "meta_imo": md.imo,
        "meta_name": md.name,
    }
