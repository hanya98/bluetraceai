import os
import json
import time
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GFW_API_TOKEN")

if not TOKEN:
    raise RuntimeError("GFW_API_TOKEN is missing from .env")

URL = "https://gateway.api.globalfishingwatch.org/v3/events"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json",
}


# ============================================================
# KNOWN SPILL CASES
# ============================================================

CASES = [
    {
        "spill_id": "ALFA_1_2012",
        "vessel_name": "ALFA I",
        "date": "2012-03-05",
        "latitude": 38.016,
        "longitude": 23.530,
    },
    {
        "spill_id": "AGIA_ZONI_II_2017",
        "vessel_name": "AGIA ZONI II",
        "date": "2017-09-10",
        "latitude": 37.955,
        "longitude": 23.545,
    },
    {
        "spill_id": "BOW_JUBAIL_2018",
        "vessel_name": "BOW JUBAIL",
        "date": "2018-06-23",
        "latitude": 51.900,
        "longitude": 4.400,
    },
    {
        "spill_id": "GOLDEN_RAY_2019",
        "vessel_name": "GOLDEN RAY",
        "date": "2019-09-08",
        "latitude": 31.130,
        "longitude": -81.500,
    },
    {
        "spill_id": "MARINE_HONOUR_2024",
        "vessel_name": "MARINE HONOUR",
        "date": "2024-06-14",
        "latitude": 1.280,
        "longitude": 103.750,
    },
]


# ============================================================
# SETTINGS
# ============================================================

RADIUS_KM = 20

DAYS_BEFORE = 2
DAYS_AFTER = 2

EVENT_DATASETS = [
    ("loitering", "public-global-loitering-events:latest"),
    ("encounter", "public-global-encounters-events:latest"),
    ("gap", "public-global-gaps-events:latest"),
    ("port_visit", "public-global-port-visits-events:latest"),
    ("fishing", "public-global-fishing-events:latest"),
]


# ============================================================
# GEOJSON CIRCLE
# ============================================================

def make_circle_polygon(lat, lon, radius_km=20, points=72):

    import math

    coords = []

    lat_delta = radius_km / 111.0

    lon_delta = radius_km / (
        111.0 * math.cos(math.radians(lat))
    )

    for i in range(points + 1):

        angle = 2 * math.pi * i / points

        p_lat = lat + lat_delta * math.sin(angle)
        p_lon = lon + lon_delta * math.cos(angle)

        coords.append([p_lon, p_lat])

    return {
        "type": "Polygon",
        "coordinates": [coords],
    }


# ============================================================
# DATE WINDOW
# ============================================================

def get_dates(date_string):

    date = pd.Timestamp(date_string, tz="UTC")

    start = (
        date - pd.Timedelta(days=DAYS_BEFORE)
    ).strftime("%Y-%m-%d")

    end = (
        date + pd.Timedelta(days=DAYS_AFTER + 1)
    ).strftime("%Y-%m-%d")

    return start, end


# ============================================================
# ACTUAL EVENT OVERLAP CHECK
# ============================================================

def event_overlaps_window(
    event,
    start_date,
    end_date,
):

    start = event.get("start")
    end = event.get("end")

    if not start:
        return False

    try:
        event_start = pd.Timestamp(start, tz="UTC")

        if end:
            event_end = pd.Timestamp(end, tz="UTC")
        else:
            event_end = event_start

        window_start = pd.Timestamp(
            start_date,
            tz="UTC"
        )

        window_end = pd.Timestamp(
            end_date,
            tz="UTC"
        )

        return (
            event_start < window_end
            and event_end >= window_start
        )

    except Exception:
        return False


# ============================================================
# FETCH EVENTS
# ============================================================

def fetch_events(spill, event_name, dataset):

    start_date, end_date = get_dates(
        spill["date"]
    )

    geometry = make_circle_polygon(
        spill["latitude"],
        spill["longitude"],
        RADIUS_KM,
    )

    print()
    print("=" * 75)
    print(
        f"{spill['spill_id']} | {event_name}"
    )
    print(
        f"Requested window: "
        f"{start_date} -> {end_date}"
    )
    print("=" * 75)

    all_events = []

    offset = 0
    limit = 100

    while True:

        params = {
            "offset": offset,
            "limit": limit,
        }

        body = {
            "datasets": [dataset],
            "startDate": start_date,
            "endDate": end_date,
            "geometry": geometry,
        }

        # ----------------------------------------------------
        # RETRY NETWORK ERRORS
        # ----------------------------------------------------

        response = None

        for attempt in range(3):

            try:

                response = requests.post(
                    URL,
                    headers=HEADERS,
                    params=params,
                    json=body,
                    timeout=120,
                )

                break

            except requests.RequestException as e:

                print(
                    f"Network error "
                    f"(attempt {attempt + 1}/3): {e}"
                )

                if attempt < 2:
                    time.sleep(5)

        if response is None:
            print("Skipping this event type.")
            break

        # ----------------------------------------------------
        # GFW POST RETURNS 201 AS WELL AS 200
        # ----------------------------------------------------

        print(
            f"HTTP {response.status_code} | "
            f"offset={offset}"
        )

        if response.status_code not in (200, 201):

            print(
                response.text[:5000]
            )

            break

        try:
            data = response.json()

        except Exception:

            print(
                "Could not decode JSON:"
            )

            print(
                response.text[:5000]
            )

            break

        entries = data.get(
            "entries",
            []
        )

        total = data.get(
            "total",
            0
        )

        next_offset = data.get(
            "nextOffset"
        )

        print(
            f"returned={len(entries)} "
            f"total={total} "
            f"nextOffset={next_offset}"
        )

        # ----------------------------------------------------
        # FILTER EVENTS BY THEIR ACTUAL TIMESTAMP
        # ----------------------------------------------------

        valid_entries = []

        for event in entries:

            if event_overlaps_window(
                event,
                start_date,
                end_date,
            ):

                valid_entries.append(
                    event
                )

        print(
            f"actual date-overlap events="
            f"{len(valid_entries)}"
        )

        all_events.extend(
            valid_entries
        )

        # ----------------------------------------------------
        # PAGINATION
        # ----------------------------------------------------

        if not entries:
            break

        if next_offset is None:
            break

        if next_offset >= total:
            break

        offset = next_offset

        # Avoid hammering API.
        time.sleep(0.5)

    return all_events


# ============================================================
# FLATTEN
# ============================================================

def flatten_event(
    event,
    spill,
    event_name,
):

    vessel = event.get(
        "vessel",
        {}
    )

    position = event.get(
        "position",
        {}
    )

    return {
        "spill_id":
            spill["spill_id"],

        "known_spill_vessel":
            spill["vessel_name"],

        "spill_date":
            spill["date"],

        "spill_latitude":
            spill["latitude"],

        "spill_longitude":
            spill["longitude"],

        "event_type":
            event_name,

        "event_id":
            event.get("id"),

        "event_start":
            event.get("start"),

        "event_end":
            event.get("end"),

        "event_latitude":
            position.get("lat"),

        "event_longitude":
            position.get("lon"),

        "gfw_vessel_id":
            vessel.get("id"),

        "vessel_name":
            vessel.get("name"),

        "mmsi":
            vessel.get("ssvid"),

        "vessel_type":
            vessel.get("type"),

        "flag":
            vessel.get("flag"),

        "raw_event":
            json.dumps(event),
    }


# ============================================================
# MAIN
# ============================================================

def main():

    output_dir = (
        "training/data/"
        "gfw_spatial_candidates"
    )

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    rows = []

    for spill in CASES:

        for event_name, dataset in EVENT_DATASETS:

            events = fetch_events(
                spill,
                event_name,
                dataset,
            )

            print(
                f"Collected valid "
                f"{event_name} events: "
                f"{len(events)}"
            )

            for event in events:

                rows.append(
                    flatten_event(
                        event,
                        spill,
                        event_name,
                    )
                )

    df = pd.DataFrame(rows)

    output = (
        output_dir +
        "/spatial_gfw_events.csv"
    )

    df.to_csv(
        output,
        index=False
    )

    print()
    print("=" * 75)
    print("SPATIAL GFW SEARCH COMPLETE")
    print("=" * 75)

    print(
        "Total event rows:",
        len(df)
    )

    if not df.empty:

        print()
        print(
            "Unique GFW vessels:",
            df["gfw_vessel_id"].nunique()
        )

        print()
        print("Events by type:")

        print(
            df["event_type"]
            .value_counts()
            .to_string()
        )

        print()
        print("Vessels by spill:")

        print(
            df.groupby(
                "spill_id"
            )["gfw_vessel_id"]
            .nunique()
            .to_string()
        )

        print()
        print("Sample candidates:")

        print(
            df[
                [
                    "spill_id",
                    "event_type",
                    "vessel_name",
                    "mmsi",
                    "gfw_vessel_id",
                    "event_start",
                ]
            ]
            .head(50)
            .to_string(index=False)
        )

    print()
    print("Saved:")
    print(output)


if __name__ == "__main__":
    main()