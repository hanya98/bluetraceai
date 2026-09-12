"""
candidate_filtering.py
========================
Cheap pre-filter applied BEFORE expensive feature engineering: for a given
spill, find every vessel that had at least one AIS ping within a configurable
spatial radius AND configurable temporal window. ALL such vessels are
returned (never just the single closest one) -- narrowing to a "most likely"
vessel is the job of the scoring stage, not the filtering stage.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Dict, List

from .config import CandidateFilterConfig
from .geo_utils import haversine_km
from .schemas import AISObservation, CandidateVessel, SpillRecord, VesselMetadata

logger = logging.getLogger(__name__)


def filter_candidate_vessels(
    spill: SpillRecord,
    observations_by_vessel: Dict[str, List[AISObservation]],
    config: CandidateFilterConfig,
    metadata_by_vessel: Dict[str, VesselMetadata] | None = None,
) -> List[CandidateVessel]:
    """Return every vessel with >= config.min_observations AIS pings that fall
    inside [spill.timestamp - hours_before, spill.timestamp + hours_after] AND
    within config.candidate_radius_km of the spill centroid.

    The candidate's `observations` list is restricted to pings inside the time
    window (this is the slice feature engineering will operate on) but is NOT
    restricted to pings inside the radius -- a vessel that was close at one
    moment but drifted away is still a valid candidate, and its
    outside-radius pings are still useful trajectory/behavior evidence.
    """
    centroid = spill.require_centroid()
    window_start = spill.timestamp_utc - timedelta(hours=config.hours_before)
    window_end = spill.timestamp_utc + timedelta(hours=config.hours_after)
    metadata_by_vessel = metadata_by_vessel or {}

    candidates: List[CandidateVessel] = []

    for vessel_id, obs_list in observations_by_vessel.items():
        in_window = [o for o in obs_list if window_start <= o.timestamp_utc <= window_end]
        if len(in_window) < config.min_observations:
            continue

        close_enough = any(
            haversine_km((o.latitude, o.longitude), centroid) <= config.candidate_radius_km
            for o in in_window
        )
        if not close_enough:
            continue

        candidates.append(
            CandidateVessel(
                vessel_id=vessel_id,
                spill_id=spill.spill_id,
                observations=in_window,
                metadata=metadata_by_vessel.get(vessel_id),
            )
        )

    logger.info(
        "Candidate filtering for spill %s: %d/%d vessels retained "
        "(radius=%.1fkm, window=[-%.1fh, +%.1fh])",
        spill.spill_id,
        len(candidates),
        len(observations_by_vessel),
        config.candidate_radius_km,
        config.hours_before,
        config.hours_after,
    )
    return candidates
