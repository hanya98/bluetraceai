import os
import json
import math
import time
import requests
import pandas as pd

from dotenv import load_dotenv

from spill_cases import SPILL_CASES


# ============================================================
# SETUP
# ============================================================

load_dotenv()

TOKEN = os.getenv("GFW_API_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "GFW_API_TOKEN not found in .env"
    )


BASE_URL = (
    "https://gateway.api.globalfishingwatch.org"
)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}


# ============================================================
# SETTINGS
# ============================================================

RADIUS_KM = 50

HOURS_BEFORE = 48
HOURS_AFTER = 12

VESSEL_DATASET = (
    "public-global-vessel-identity:latest"
)

PRESENCE_DATASET = (
    "public-global-presence:latest"
)


# ============================================================
# GENERIC GET
# ============================================================

def gfw_get(path, params):

    url = BASE_URL + path

    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=120,
    )

    if not response.ok:

        print()
        print("GFW ERROR")
        print(response.status_code)
        print(response.text[:3000])

        response.raise_for_status()

    return response.json()


# ============================================================
# GENERIC POST
# ============================================================

def gfw_post(path, params, body):

    url = BASE_URL + path

    response = requests.post(
        url,
        headers=HEADERS,
        params=params,
        json=body,
        timeout=120,
    )

    if not response.ok:

        print()
        print("GFW ERROR")
        print(response.status_code)
        print(response.text[:3000])

        response.raise_for_status()

    return response.json()


# ============================================================
# SEARCH VESSEL
# ============================================================

def search_vessel(name):

    params = [
        (
            "query",
            name,
        ),

        (
            "datasets[0]",
            VESSEL_DATASET,
        ),

        (
            "includes[0]",
            "MATCH_CRITERIA",
        ),

        (
            "limit",
            "20",
        ),
    ]

    return gfw_get(
        "/v3/vessels/search",
        params,
    )


# ============================================================
# EXTRACT IDS FROM SEARCH
# ============================================================

def extract_vessel_ids(data):

    vessel_ids = set()

    for entry in data.get(
        "entries",
        []
    ):

        # ----------------------------------------------------
        # AIS self-reported identities
        # ----------------------------------------------------

        self_reported = entry.get(
            "selfReportedInfo",
            []
        )

        if isinstance(
            self_reported,
            list
        ):

            for vessel in self_reported:

                vessel_id = vessel.get(
                    "id"
                )

                if vessel_id:
                    vessel_ids.add(
                        vessel_id
                    )

        # ----------------------------------------------------
        # Registry identities
        # ----------------------------------------------------

        registry_info = entry.get(
            "registryInfo",
            []
        )

        if isinstance(
            registry_info,
            list
        ):

            for vessel in registry_info:

                vessel_id = vessel.get(
                    "id"
                )

                if vessel_id:
                    vessel_ids.add(
                        vessel_id
                    )

    return vessel_ids


# ============================================================
# PRINT SEARCH RESULTS
# ============================================================

def show_vessel_matches(
    vessel_name,
    data,
):

    print()
    print(
        f"GFW matches for: {vessel_name}"
    )

    entries = data.get(
        "entries",
        []
    )

    if not entries:

        print(
            "  NO MATCHES"
        )

        return

    for i, entry in enumerate(
        entries,
        start=1
    ):

        print(
            f"\n  Match {i}"
        )

        registry = entry.get(
            "registryInfo",
            []
        )

        for vessel in registry:

            print(
                "    Registry:",
                vessel.get(
                    "shipname"
                ),
                "| IMO:",
                vessel.get(
                    "imo"
                ),
                "| MMSI:",
                vessel.get(
                    "ssvid"
                ),
                "| ID:",
                vessel.get(
                    "id"
                ),
            )

        self_reported = entry.get(
            "selfReportedInfo",
            []
        )

        if isinstance(
            self_reported,
            list
        ):

            for vessel in self_reported:

                print(
                    "    AIS:",
                    vessel.get(
                        "shipname"
                    ),
                    "| IMO:",
                    vessel.get(
                        "imo"
                    ),
                    "| MMSI:",
                    vessel.get(
                        "ssvid"
                    ),
                    "| ID:",
                    vessel.get(
                        "id"
                    ),
                )


# ============================================================
# CIRCLE GEOJSON
# ============================================================

def make_circle(
    latitude,
    longitude,
    radius_km,
    points=48,
):

    coords = []

    lat_radius = (
        radius_km / 111.0
    )

    cos_lat = math.cos(
        math.radians(latitude)
    )

    # Avoid division by zero
    if abs(cos_lat) < 1e-8:
        cos_lat = 1e-8

    lon_radius = (
        radius_km /
        (111.0 * cos_lat)
    )

    for i in range(
        points + 1
    ):

        angle = (
            2 *
            math.pi *
            i /
            points
        )

        lat = (
            latitude +
            lat_radius *
            math.sin(angle)
        )

        lon = (
            longitude +
            lon_radius *
            math.cos(angle)
        )

        coords.append(
            [lon, lat]
        )

    return {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                coords
            ],
        },
    }


# ============================================================
# QUERY GFW PRESENCE
# ============================================================

def query_presence(case):

    spill_time = pd.Timestamp(
        case["date"],
        tz="UTC"
    )

    start = (
        spill_time -
        pd.Timedelta(
            hours=HOURS_BEFORE
        )
    )

    end = (
        spill_time +
        pd.Timedelta(
            hours=HOURS_AFTER
        )
    )

    date_range = (
        start.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        +
        ","
        +
        end.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    )

    params = [

        (
            "spatial-resolution",
            "HIGH",
        ),

        (
            "temporal-resolution",
            "HOURLY",
        ),

        (
            "group-by",
            "VESSEL_ID",
        ),

        (
            "datasets[0]",
            PRESENCE_DATASET,
        ),

        (
            "date-range",
            date_range,
        ),

        (
            "format",
            "JSON",
        ),

        (
            "spatial-aggregation",
            "false",
        ),
    ]

    geojson = make_circle(
        case["latitude"],
        case["longitude"],
        RADIUS_KM,
    )

    body = {
        "geojson": geojson
    }

    print()
    print(
        "Querying GFW historical AIS..."
    )

    print(
        "  Date:",
        date_range
    )

    print(
        "  Center:",
        case["latitude"],
        case["longitude"]
    )

    print(
        "  Radius:",
        RADIUS_KM,
        "km"
    )

    return gfw_post(
        "/v3/4wings/report",
        params,
        body,
    )


# ============================================================
# FLATTEN PRESENCE
# ============================================================

def flatten_presence(data):

    rows = []

    entries = data.get(
        "entries",
        []
    )

    # GFW 4Wings responses can have
    # slightly different structures.
    # We recursively inspect the response
    # for dictionaries containing vessel IDs.

    def walk(obj):

        if isinstance(
            obj,
            dict
        ):

            # Candidate record
            if (
                obj.get("vesselId")
                or obj.get("vessel_id")
                or obj.get("ssvid")
                or obj.get("mmsi")
            ):

                rows.append({
                    "vessel_id":
                        obj.get(
                            "vesselId",
                            obj.get(
                                "vessel_id"
                            )
                        ),

                    "mmsi":
                        obj.get(
                            "mmsi",
                            obj.get(
                                "ssvid"
                            )
                        ),

                    "ship_name":
                        obj.get(
                            "shipName",
                            obj.get(
                                "shipname"
                            )
                        ),

                    "imo":
                        obj.get(
                            "imo"
                        ),

                    "flag":
                        obj.get(
                            "flag"
                        ),

                    "vessel_type":
                        obj.get(
                            "vesselType",
                            obj.get(
                                "shiptype"
                            )
                        ),

                    "date":
                        obj.get(
                            "date"
                        ),

                    "latitude":
                        obj.get(
                            "lat",
                            obj.get(
                                "latitude"
                            )
                        ),

                    "longitude":
                        obj.get(
                            "lon",
                            obj.get(
                                "longitude"
                            )
                        ),

                    "hours":
                        obj.get(
                            "hours"
                        ),

                    "entry_timestamp":
                        obj.get(
                            "entryTimestamp"
                        ),

                    "exit_timestamp":
                        obj.get(
                            "exitTimestamp"
                        ),
                })

            else:

                for value in obj.values():
                    walk(value)

        elif isinstance(
            obj,
            list
        ):

            for item in obj:
                walk(item)

    walk(data)

    return rows


# ============================================================
# BUILD ONE SPILL CASE
# ============================================================

def build_case(case):

    print()
    print("=" * 70)
    print(
        case["spill_id"]
    )
    print(
        case["vessel_name"]
    )
    print(
        case["date"]
    )
    print("=" * 70)

    # --------------------------------------------------------
    # 1. Search documented vessel
    # --------------------------------------------------------

    vessel_search = search_vessel(
        case["vessel_name"]
    )

    show_vessel_matches(
        case["vessel_name"],
        vessel_search,
    )

    target_ids = extract_vessel_ids(
        vessel_search
    )

    print()

    print(
        "Resolved GFW vessel IDs:"
    )

    for vessel_id in target_ids:

        print(
            " ",
            vessel_id
        )

    # --------------------------------------------------------
    # 2. Query historical AIS presence
    # --------------------------------------------------------

    presence = query_presence(
        case
    )

    rows = flatten_presence(
        presence
    )

    print()

    print(
        "AIS candidate rows:",
        len(rows)
    )

    # --------------------------------------------------------
    # 3. Add spill metadata
    # --------------------------------------------------------

    output = []

    for row in rows:

        vessel_id = row.get(
            "vessel_id"
        )

        label = int(
            vessel_id in target_ids
        )

        row.update({

            "spill_id":
                case["spill_id"],

            "spill_date":
                case["date"],

            "spill_latitude":
                case["latitude"],

            "spill_longitude":
                case["longitude"],

            "documented_vessel":
                case["vessel_name"],

            "location":
                case["location"],

            "source":
                case["source"],

            "label":
                label,

            "label_source":
                "ITOPF_public_case",

        })

        output.append(
            row
        )

    return output


# ============================================================
# MAIN
# ============================================================

def main():

    os.makedirs(
        "training/data",
        exist_ok=True
    )

    all_rows = []

    for case in SPILL_CASES:

        try:

            rows = build_case(
                case
            )

            all_rows.extend(
                rows
            )

        except Exception as e:

            print()
            print(
                "FAILED:",
                case["spill_id"]
            )

            print(
                repr(e)
            )

        # Small pause between cases
        time.sleep(2)

    if not all_rows:

        raise RuntimeError(
            "No data collected."
        )

    df = pd.DataFrame(
        all_rows
    )

    output_file = (
        "training/data/"
        "genuine_attribution_dataset.csv"
    )

    df.to_csv(
        output_file,
        index=False
    )

    print()
    print("=" * 70)
    print(
        "DATASET COMPLETE"
    )
    print("=" * 70)

    print(
        "Rows:",
        len(df)
    )

    print(
        "Spills:",
        df["spill_id"].nunique()
    )

    print(
        "Positive rows:",
        int(
            df["label"].sum()
        )
    )

    print(
        "Negative rows:",
        int(
            (df["label"] == 0).sum()
        )
    )

    print()

    print(
        df.groupby(
            "spill_id"
        )["label"].agg(
            [
                "count",
                "sum",
            ]
        )
    )

    print()

    print(
        "Saved:",
        output_file
    )


if __name__ == "__main__":
    main()