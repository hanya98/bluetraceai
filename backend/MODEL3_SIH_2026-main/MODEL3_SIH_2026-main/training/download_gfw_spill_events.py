import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GFW_API_TOKEN")

if not TOKEN:
    raise RuntimeError("GFW_API_TOKEN is missing from .env")

BASE_URL = "https://gateway.api.globalfishingwatch.org/v3/events"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json",
}


# ---------------------------------------------------------
# IMPORTANT:
# These are the GFW vessel identities we resolved.
# SILVER is intentionally excluded for now because
# multiple vessels have that name.
# ---------------------------------------------------------

CASES = [
    {
        "spill_id": "ALFA_1_2012",
        "vessel_name": "ALFA I",
        "gfw_vessel_id": "33a246117-766c-8053-6014-9ea7c44b3497",
        "mmsi": "239346000",
        "imo": "7037208",
        "spill_date": "2012-03-05",
    },
    {
        "spill_id": "AGIA_ZONI_II_2017",
        "vessel_name": "AGIA ZONI II",
        "gfw_vessel_id": "0ff743922-22ed-359b-ed67-91e47c93c74b",
        "mmsi": "240783000",
        "imo": "7126152",
        "spill_date": "2017-09-10",
    },
    {
        "spill_id": "BOW_JUBAIL_2018",
        "vessel_name": "BOW JUBAIL",
        "gfw_vessel_id": "bff96da87-7946-2c10-7531-1d53792e2cbe",
        "mmsi": "259757000",
        "imo": "9087025",
        "spill_date": "2018-06-23",
    },
    {
        "spill_id": "GOLDEN_RAY_2019",
        "vessel_name": "GOLDEN RAY",
        "gfw_vessel_id": "5cb3ca5c53578544f481682f3b339244",
        "mmsi": "235098004",
        "imo": "8540812",
        "spill_date": "2019-09-08",
    },
    {
        "spill_id": "MARINE_HONOUR_2024",
        "vessel_name": "MARINE HONOUR",
        "gfw_vessel_id": "7926d4c6fe7f9c2cdeee0dbbc8714685",
        "mmsi": "565574000",
        "imo": "9422811",
        "spill_date": "2024-06-14",
    },
]


EVENT_DATASETS = {
    "loitering": "public-global-loitering-events:latest",
    "encounters": "public-global-encounters-events:latest",
    "gaps": "public-global-gaps-events:latest",
    "port_visits": "public-global-port-visits-events:latest",
    "fishing": "public-global-fishing-events:latest",
}


def date_range(spill_date):
    """
    Fetch a reasonably wide historical window around the spill.

    We use 30 days before -> 30 days after initially.
    This is deliberately wider than the attribution window so
    we don't accidentally throw away useful GFW behavior.
    """

    date = pd.Timestamp(spill_date, tz="UTC")

    start = (date - pd.Timedelta(days=30)).strftime("%Y-%m-%d")
    end = (date + pd.Timedelta(days=31)).strftime("%Y-%m-%d")

    return start, end


def fetch_events(vessel, event_name, dataset):
    start_date, end_date = date_range(vessel["spill_date"])

    print()
    print("=" * 75)
    print(
        f"{vessel['spill_id']} | "
        f"{vessel['vessel_name']} | "
        f"{event_name}"
    )
    print("=" * 75)

    all_entries = []
    offset = 0
    limit = 100

    while True:

        params = [
            ("vessels[0]", vessel["gfw_vessel_id"]),
            ("datasets[0]", dataset),
            ("start-date", start_date),
            ("end-date", end_date),
            ("limit", str(limit)),
            ("offset", str(offset)),
        ]

        response = requests.get(
            BASE_URL,
            headers=HEADERS,
            params=params,
            timeout=60,
        )

        print(
            f"HTTP={response.status_code} "
            f"offset={offset}"
        )

        if response.status_code != 200:
            print(response.text[:5000])
            break

        data = response.json()

        entries = data.get("entries", [])

        all_entries.extend(entries)

        total = data.get("total", 0)
        next_offset = data.get("nextOffset")

        print(
            f"returned={len(entries)} "
            f"total={total} "
            f"nextOffset={next_offset}"
        )

        if not entries:
            break

        if next_offset is None:
            break

        if next_offset >= total:
            break

        offset = next_offset

    return all_entries


def flatten_event(event, vessel, event_name):

    position = event.get("position", {})
    vessel_info = event.get("vessel", {})

    return {
        "spill_id": vessel["spill_id"],
        "vessel_name": vessel["vessel_name"],
        "gfw_vessel_id": vessel["gfw_vessel_id"],
        "mmsi": vessel["mmsi"],
        "imo": vessel["imo"],

        "spill_date": vessel["spill_date"],

        "event_type": event_name,

        "event_id": event.get("id"),

        "start": event.get("start"),
        "end": event.get("end"),

        "latitude": position.get("lat"),
        "longitude": position.get("lon"),

        "vessel_event_name": vessel_info.get("name"),
        "vessel_event_mmsi": vessel_info.get("ssvid"),

        "raw_event": str(event),
    }


def main():

    output_dir = "training/data/gfw_spill_events"
    os.makedirs(output_dir, exist_ok=True)

    all_rows = []

    for vessel in CASES:

        for event_name, dataset in EVENT_DATASETS.items():

            events = fetch_events(
                vessel,
                event_name,
                dataset,
            )

            print(
                f"Collected {len(events)} {event_name} events"
            )

            for event in events:

                all_rows.append(
                    flatten_event(
                        event,
                        vessel,
                        event_name,
                    )
                )

    df = pd.DataFrame(all_rows)

    output = os.path.join(
        output_dir,
        "gfw_spill_events.csv",
    )

    df.to_csv(output, index=False)

    print()
    print("=" * 75)
    print("GFW EVENT DOWNLOAD COMPLETE")
    print("=" * 75)

    print("Rows:", len(df))

    if not df.empty:

        print()
        print("Events by type:")

        print(
            df["event_type"]
            .value_counts()
            .to_string()
        )

        print()
        print("Events by spill:")

        print(
            df.groupby(
                ["spill_id", "event_type"]
            )
            .size()
            .to_string()
        )

    print()
    print("Saved:")
    print(output)


if __name__ == "__main__":
    main()