"""
config.py
=========
All "arbitrary" scientific/operational thresholds live HERE, in one place,
with documented justification, so nothing is silently hardcoded inside the
feature/candidate-filtering logic. Change these without touching core code.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CandidateFilterConfig:
    """Controls which vessels are even considered for a given spill."""

    # Radius (km) around the spill centroid/polygon within which an AIS ping
    # counts as "near" the spill for the purpose of *initial candidate selection*.
    # 50 km is a common first-pass radius used in maritime pollution-response
    # literature for coastal/shelf spills observed by SAR; widen for open ocean.
    candidate_radius_km: float = 50.0

    # Time window (hours) around the spill detection timestamp within which an
    # AIS observation is considered relevant. Sentinel-1 revisit + oil drift
    # + reporting latency commonly justify a window of +/- 24h; default is
    # asymmetric (looks further back than forward, since spills are usually
    # investigated after the fact and the causal event, if any, precedes
    # detection).
    hours_before: float = 48.0
    hours_after: float = 12.0

    # Minimum number of AIS pings a vessel needs within the window to be kept
    # as a candidate at all (avoids single stray/erroneous pings driving a
    # ranking). Set to 1 to disable this filter.
    min_observations: int = 1


@dataclass
class FeatureConfig:
    # Radius (km) used for the "observations within radius" spatial feature
    # and for the "time spent within spill vicinity" temporal feature. This is
    # intentionally allowed to differ from candidate_radius_km (a tighter,
    # more evidentiary radius) -- default ties them together for simplicity.
    vicinity_radius_km: float = 20.0

    # Speed (knots) below which a vessel is considered "slowed/loitering" for
    # the stop/slowdown behavioral indicator. 2 knots is a standard maritime
    # "dead slow / stopped" threshold used in AIS behavior-analysis literature.
    loitering_speed_knots: float = 2.0

    # Minimum duration (hours) below loitering_speed_knots, within the
    # candidate window, required to flag the loitering indicator.
    loitering_min_duration_hours: float = 1.0

    # Gap (hours) between consecutive AIS pings from the same vessel that is
    # considered a reportable "AIS gap". 1 hour is conservative relative to
    # typical AIS reporting intervals (seconds-to-minutes while underway);
    # tune upward for sparse satellite-AIS coverage areas.
    ais_gap_threshold_hours: float = 1.0

    # Heading alignment is expressed as the absolute angular difference (deg)
    # between vessel heading/course and the bearing from vessel to spill (or
    # the estimated drift direction). No implicit threshold is applied here --
    # this is a continuous feature, not a boolean, to avoid a hidden
    # guilt threshold.


@dataclass
class ScoringConfig:
    """Weights for the Mode A heuristic baseline score (0-100 scale).

    These weights are a starting point, not a validated model. They MUST be
    documented and MUST be tunable; do not treat the resulting score as a
    calibrated probability of causation. Weights are normalized internally so
    they need not sum to 1.
    """

    weight_spatial: float = 0.35
    weight_temporal: float = 0.25
    weight_trajectory: float = 0.20
    weight_behavior: float = 0.10
    weight_ais_gap: float = 0.05
    weight_environmental: float = 0.05

    # Distance (km) beyond which spatial evidence contributes ~0 to the score.
    # Chosen equal to candidate_radius_km by default so scoring is consistent
    # with the filtering stage; override independently if desired.
    spatial_decay_km: float = 50.0

    # Time difference (hours) beyond which temporal evidence contributes ~0.
    temporal_decay_hours: float = 48.0


@dataclass
class Model3Config:
    candidate_filter: CandidateFilterConfig = field(default_factory=CandidateFilterConfig)
    features: FeatureConfig = field(default_factory=FeatureConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)

    # Mode A ("heuristic") always runs and always produces a ranking, even
    # with zero labeled training data. Mode B ("ml") is only used when a
    # trained XGBoost model artifact is supplied -- it is never auto-trained
    # on fabricated labels.
    mode: str = "heuristic"  # "heuristic" | "ml"

    random_seed: int = 42
