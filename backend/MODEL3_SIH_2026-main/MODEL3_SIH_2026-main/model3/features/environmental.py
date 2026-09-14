"""
features/environmental.py
============================
Category F: ENVIRONMENTAL FEATURES (spec section 9.F).

`EnvironmentalRecord` is expected to come from a modelled/reanalysis source
(ERA5, Open-Meteo-ECMWF) -- never presented downstream as a direct
measurement (see EnvironmentalRecord.is_modelled and explain.py).

Gracefully returns all-None features (never raises) when environmental data
is unavailable, per spec: wind fields are optional and their absence must not
break the pipeline.
"""

from __future__ import annotations

from typing import Dict, Optional

from ..geo_utils import angular_diff_deg
from ..schemas import CandidateVessel, EnvironmentalRecord, SpillRecord


def compute_environmental_features(
    vessel: CandidateVessel,
    spill: SpillRecord,
    environment: Optional[EnvironmentalRecord],
) -> Dict[str, Optional[float]]:
    result: Dict[str, Optional[float]] = {
        "env_wind_speed_ms": None,
        "env_wind_direction_deg": None,
        "env_wind_source": None,
        "env_wind_is_modelled": None,
        "env_wind_heading_alignment_deg": None,
        "env_drift_alignment_deg": None,
    }

    if environment is None:
        return result

    result["env_wind_speed_ms"] = environment.wind_speed_ms
    result["env_wind_direction_deg"] = environment.wind_direction_deg
    result["env_wind_source"] = environment.source
    result["env_wind_is_modelled"] = environment.is_modelled

    obs = sorted(vessel.observations, key=lambda o: o.timestamp_utc)
    last_heading = next((o.heading_deg for o in reversed(obs) if o.heading_deg is not None), None)

    if last_heading is not None and environment.wind_direction_deg is not None:
        result["env_wind_heading_alignment_deg"] = angular_diff_deg(
            last_heading, environment.wind_direction_deg
        )

    if last_heading is not None and spill.drift_direction_deg is not None:
        result["env_drift_alignment_deg"] = angular_diff_deg(
            last_heading, spill.drift_direction_deg
        )

    return result
