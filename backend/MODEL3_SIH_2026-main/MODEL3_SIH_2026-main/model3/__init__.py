"""
Model 3 -- AIS-based Candidate Vessel Attribution / Ranking
=============================================================

SIH26143 -- AI Oil Spill Detection & Vessel Attribution

This package implements ONLY Model 3 of the 3-model pipeline:

    Sentinel-1 SAR -> Model 1 (Attention U-Net segmentation)
                    -> Model 2 (CNN oil vs look-alike classifier)
                    -> Model 3 (THIS PACKAGE: AIS-based candidate vessel ranking)

SCIENTIFIC / ETHICAL FRAMING (read before touching this code)
---------------------------------------------------------------
Model 3 never asserts causality or guilt. It produces a `candidate_priority_score`
and a ranked list of candidate vessels supported by spatial, temporal,
trajectory, behavioral, AIS-gap and environmental evidence. Every output must be
read as "ranked candidates for human investigation", never as proof that a
vessel caused a spill. See model3/explain.py for the enforced output phrasing.

This package does NOT touch raw Sentinel-1 pixels and does NOT depend on the
internal architecture of Model 1 or Model 2. It consumes a standardized
`SpillRecord` object (see schemas.py / api_contract.py) that the upstream
pipeline/backend is responsible for producing.
"""

from .schemas import (
    SpillRecord,
    AISObservation,
    VesselMetadata,
    EnvironmentalRecord,
    CandidateVessel,
)

__all__ = [
    "SpillRecord",
    "AISObservation",
    "VesselMetadata",
    "EnvironmentalRecord",
    "CandidateVessel",
]

__version__ = "0.1.0"
