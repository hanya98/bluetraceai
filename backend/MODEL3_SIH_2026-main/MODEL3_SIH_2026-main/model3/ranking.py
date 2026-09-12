"""
Turns scored feature rows into the final explainable RankedVessel output
(Section: "explainable output"). Always uses non-causal, evidence-based
language — never asserts a vessel "caused" the spill.
"""

from typing import List, Optional
import pandas as pd

from .schemas import Spill, VesselFeatureRow, RankedVessel


def _standard_caveats(row: pd.Series) -> List[str]:
    caveats = []
    if row.get("significant_gap_overlaps_window"):
        caveats.append(
            "An AIS gap overlaps the spill window. This indicates missing AIS "
            "data only — it is NOT evidence of intentional AIS shutdown."
        )
    if row.get("wind_speed_ms") is not None:
        caveats.append(
            "Wind/drift figures are model estimates (e.g. ERA5/Open-Meteo), "
            "not direct measurements."
        )
    caveats.append(
        "This score is an investigative aid ranking candidate vessels by "
        "evidence strength. It does not establish that this vessel caused "
        "the spill."
    )
    return caveats


def _top_evidence(row: pd.Series, top_k: int = 3) -> List[str]:
    evidence = []
    if row.get("min_distance_km") is not None:
        evidence.append(f"Closest approach to spill: {row['min_distance_km']:.1f} km")
    if row.get("abs_time_diff_closest_hr") is not None:
        evidence.append(f"Closest observation was {row['abs_time_diff_closest_hr']:.1f} h from detection time")
    if row.get("heading_alignment_score") is not None and pd.notna(row.get("heading_alignment_score")):
        evidence.append(f"Heading alignment toward spill: {row['heading_alignment_score']:.2f} (0-1)")
    if row.get("trajectory_intersects_polygon"):
        evidence.append("Vessel trajectory intersects the spill polygon")
    if row.get("loitering_flag"):
        evidence.append("Vessel showed loitering behavior near the spill area")
    if row.get("significant_gap_overlaps_window"):
        evidence.append("A significant AIS gap overlaps the spill detection window")
    return evidence[:top_k] if evidence else ["Ranked primarily on spatial/temporal proximity"]


def build_ranking(scored_df: pd.DataFrame, spill: Spill, score_mode: str,
                   explanations: Optional[List[List[str]]] = None) -> List[RankedVessel]:
    """scored_df must contain 'candidate_priority_score' and vessel_id."""
    if scored_df.empty:
        return []

    ordered = scored_df.sort_values("candidate_priority_score", ascending=False).reset_index(drop=True)
    ranked = []
    for i, row in ordered.iterrows():
        top_evidence = (
            explanations[i] if explanations is not None and i < len(explanations)
            else _top_evidence(row)
        )
        feature_row = VesselFeatureRow(**{
            k: (v if not (isinstance(v, float) and pd.isna(v)) else None)
            for k, v in row.items()
            if k in VesselFeatureRow.__dataclass_fields__
        })
        ranked.append(RankedVessel(
            spill_id=spill.spill_id,
            vessel_id=row["vessel_id"],
            rank=i + 1,
            candidate_priority_score=float(round(row["candidate_priority_score"], 4)),
            score_mode=score_mode,
            top_evidence=top_evidence,
            caveats=_standard_caveats(row),
            feature_row=feature_row,
        ))
    return ranked
