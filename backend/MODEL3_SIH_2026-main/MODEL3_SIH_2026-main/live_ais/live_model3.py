from datetime import datetime, timezone

from model3.pipeline import Model3Pipeline
from model3.config import Model3Config
from model3.schemas import SpillRecord


def run_model3(
    ais_records,
    spill_lat,
    spill_lon,
    spill_time,
):

    spill = SpillRecord(
        spill_id="LIVE_SPILL_001",

        timestamp_utc=spill_time,

        centroid=(
            spill_lat,
            spill_lon,
        ),

        area_km2=None,

        detection_confidence=None,

        oil_probability=None,
    )

    pipeline = Model3Pipeline(
        Model3Config()
    )

    result = pipeline.run(
        spill=spill,
        raw_ais_records=ais_records,
    )

    return result