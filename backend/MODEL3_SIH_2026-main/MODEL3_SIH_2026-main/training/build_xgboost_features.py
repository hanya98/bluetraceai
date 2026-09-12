from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "genuine_attribution_dataset.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "xgboost_features.csv"
)


# ============================================================
# GEO HELPERS
# ============================================================

def haversine_km(lat1, lon1, lat2, lon2):

    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)

    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1)
        * np.cos(lat2)
        * np.sin(dlon / 2) ** 2
    )

    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


# ============================================================
# MAIN FEATURE BUILDING
# ============================================================

def build_features(df):

    print("\nBuilding vessel-level features...")

    # --------------------------------------------------------
    # Convert date columns
    # --------------------------------------------------------

    df["date"] = pd.to_datetime(
        df["date"],
        utc=True,
        errors="coerce"
    )

    df["spill_date"] = pd.to_datetime(
        df["spill_date"],
        utc=True,
        errors="coerce"
    )

    # --------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------

    numeric_columns = [
        "latitude",
        "longitude",
        "spill_latitude",
        "spill_longitude",
        "hours",
        "label",
    ]

    for col in numeric_columns:

        if col in df.columns:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    # --------------------------------------------------------
    # Remove unusable rows
    # --------------------------------------------------------

    required = [
        "spill_id",
        "vessel_id",
        "date",
        "spill_date",
        "latitude",
        "longitude",
        "spill_latitude",
        "spill_longitude",
    ]

    df = df.dropna(
        subset=required
    ).copy()

    print(
        f"Valid rows after cleaning: {len(df):,}"
    )

    # ========================================================
    # ROW-LEVEL FEATURES
    # ========================================================

    # --------------------------------------------------------
    # Distance to spill
    # --------------------------------------------------------

    df["distance_km"] = haversine_km(
        df["latitude"],
        df["longitude"],
        df["spill_latitude"],
        df["spill_longitude"],
    )

    # --------------------------------------------------------
    # Time difference from spill
    # --------------------------------------------------------

    df["time_diff_hours"] = (
        (
            df["date"]
            - df["spill_date"]
        )
        .dt.total_seconds()
        / 3600.0
    )

    df["abs_time_diff_hours"] = (
        df["time_diff_hours"].abs()
    )

    # ========================================================
    # SPATIAL FEATURES
    # ========================================================

    df["within_5km"] = (
        df["distance_km"] <= 5
    ).astype(int)

    df["within_10km"] = (
        df["distance_km"] <= 10
    ).astype(int)

    df["within_20km"] = (
        df["distance_km"] <= 20
    ).astype(int)

    df["within_50km"] = (
        df["distance_km"] <= 50
    ).astype(int)

    # ========================================================
    # TEMPORAL FEATURES
    # ========================================================

    df["within_48h_before"] = (
        (df["time_diff_hours"] >= -48)
        & (df["time_diff_hours"] <= 0)
    ).astype(int)

    df["within_12h_after"] = (
        (df["time_diff_hours"] > 0)
        & (df["time_diff_hours"] <= 12)
    ).astype(int)

    df["within_event_window"] = (
        (df["time_diff_hours"] >= -48)
        & (df["time_diff_hours"] <= 12)
    ).astype(int)

    # ========================================================
    # GROUP BY SPILL + VESSEL
    # ========================================================

    group_cols = [
        "spill_id",
        "vessel_id"
    ]

    groups = df.groupby(
        group_cols,
        sort=False
    )

    print(
        f"Candidate spill-vessel groups: "
        f"{len(groups):,}"
    )

    rows = []

    # ========================================================
    # AGGREGATE
    # ========================================================

    for index, ((spill_id, vessel_id), g) in enumerate(
        groups,
        start=1
    ):

        row = {
            "spill_id": spill_id,
            "vessel_id": vessel_id,
        }

        # ----------------------------------------------------
        # LABEL
        # ----------------------------------------------------

        row["label"] = int(
            pd.to_numeric(
                g["label"],
                errors="coerce"
            )
            .fillna(0)
            .max()
        )

        # ----------------------------------------------------
        # Basic observation information
        # ----------------------------------------------------

        row["observation_count"] = len(g)

        # ----------------------------------------------------
        # Spatial
        # ----------------------------------------------------

        row["min_distance_km"] = (
            g["distance_km"].min()
        )

        row["mean_distance_km"] = (
            g["distance_km"].mean()
        )

        row["median_distance_km"] = (
            g["distance_km"].median()
        )

        row["within_5km_count"] = (
            g["within_5km"].sum()
        )

        row["within_10km_count"] = (
            g["within_10km"].sum()
        )

        row["within_20km_count"] = (
            g["within_20km"].sum()
        )

        row["within_50km_count"] = (
            g["within_50km"].sum()
        )

        row["within_10km_fraction"] = (
            g["within_10km"].mean()
        )

        row["within_20km_fraction"] = (
            g["within_20km"].mean()
        )

        row["within_50km_fraction"] = (
            g["within_50km"].mean()
        )

        # ----------------------------------------------------
        # Temporal
        # ----------------------------------------------------

        row["min_abs_time_diff_hours"] = (
            g["abs_time_diff_hours"].min()
        )

        row["mean_abs_time_diff_hours"] = (
            g["abs_time_diff_hours"].mean()
        )

        row["before_48h_count"] = (
            g["within_48h_before"].sum()
        )

        row["after_12h_count"] = (
            g["within_12h_after"].sum()
        )

        row["event_window_count"] = (
            g["within_event_window"].sum()
        )

        row["event_window_fraction"] = (
            g["within_event_window"].mean()
        )

        # ----------------------------------------------------
        # Track duration
        # ----------------------------------------------------

        first_time = g["date"].min()
        last_time = g["date"].max()

        row["track_duration_hours"] = (
            last_time - first_time
        ).total_seconds() / 3600.0

        # ----------------------------------------------------
        # Speed
        #
        # IMPORTANT:
        # This GFW 4Wings dataset does not necessarily contain
        # raw AIS speed/heading. Therefore we don't fabricate
        # those features.
        # ----------------------------------------------------

        # ----------------------------------------------------
        # First / last position
        # ----------------------------------------------------

        first_idx = g["date"].idxmin()
        last_idx = g["date"].idxmax()

        first_distance = g.loc[
            first_idx,
            "distance_km"
        ]

        last_distance = g.loc[
            last_idx,
            "distance_km"
        ]

        row["first_distance_km"] = (
            first_distance
        )

        row["last_distance_km"] = (
            last_distance
        )

        row["distance_change_km"] = (
            last_distance
            - first_distance
        )

        # ----------------------------------------------------
        # GFW event features
        #
        # The genuine attribution dataset may contain these
        # aggregated event counts. If not present, use 0.
        # ----------------------------------------------------

        event_columns = [
            "loitering_events",
            "encounter_events",
            "gap_events",
            "port_visit_events",
            "fishing_events",
        ]

        for col in event_columns:

            if col in g.columns:

                values = pd.to_numeric(
                    g[col],
                    errors="coerce"
                ).fillna(0)

                row[col] = values.sum()

            else:

                row[col] = 0

        rows.append(row)

        if index % 5000 == 0:

            print(
                f"  processed "
                f"{index:,}/{len(groups):,}"
            )

    # ========================================================
    # CREATE DATAFRAME
    # ========================================================

    features = pd.DataFrame(rows)

    # --------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------

    features = features.replace(
        [np.inf, -np.inf],
        np.nan
    )

    features = features.sort_values(
        [
            "spill_id",
            "label",
            "vessel_id"
        ],
        ascending=[
            True,
            False,
            True
        ]
    ).reset_index(drop=True)

    # ========================================================
    # SAVE
    # ========================================================

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    features.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ========================================================
    # REPORT
    # ========================================================

    print("\n" + "=" * 65)
    print("XGBOOST FEATURE DATASET COMPLETE")
    print("=" * 65)

    print(
        f"\nOutput file:\n{OUTPUT_FILE}"
    )

    print(
        f"\nRows: {len(features):,}"
    )

    print(
        f"Columns: {len(features.columns)}"
    )

    print("\nLabel distribution:")

    print(
        features["label"].value_counts()
    )

    print(
        "\nPositive candidates by spill:"
    )

    print(
        features
        .groupby("spill_id")["label"]
        .agg(["count", "sum"])
    )

    print("\nFeature columns:")

    for column in features.columns:

        print(
            f"  {column}"
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"\nInput file not found:\n"
            f"{INPUT_FILE}\n\n"
            "Run first:\n"
            "python training\\"
            "build_genuine_attribution_dataset.py"
        )

    print(
        f"Reading:\n{INPUT_FILE}"
    )

    df = pd.read_csv(
        INPUT_FILE
    )

    print(
        f"\nInput rows: {len(df):,}"
    )

    print(
        f"Input columns: {len(df.columns)}"
    )

    print(
        "\nColumns:"
    )

    print(
        df.columns.tolist()
    )

    build_features(df)