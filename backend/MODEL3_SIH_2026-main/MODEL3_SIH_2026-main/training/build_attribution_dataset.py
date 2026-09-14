import os
import requests
import pandas as pd
from dotenv import load_dotenv


load_dotenv()

TOKEN = os.getenv("GFW_API_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "GFW_API_TOKEN not found in .env"
    )


BASE_URL = "https://gateway.api.globalfishingwatch.org/v3/events"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}


# ============================================================
# GFW EVENT DATASETS
# ============================================================

DATASETS = {
    "loitering":
        "public-global-loitering-events:latest",

    "encounters":
        "public-global-encounters-events:latest",

    "gaps":
        "public-global-gaps-events:latest",

    "port_visits":
        "public-global-port-visits-events:latest",
}


# ============================================================
# GET EVENTS
# ============================================================

def get_events(
    dataset,
    start_date,
    end_date,
    limit=100,
    offset=0,
):

    params = {
        "datasets[0]": dataset,
        "start-date": start_date,
        "end-date": end_date,
        "limit": limit,
        "offset": offset,
    }

    response = requests.get(
        BASE_URL,
        headers=HEADERS,
        params=params,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# NORMALIZE EVENTS
# ============================================================

def normalize_events(data):

    rows = []

    for event in data.get("entries", []):

        vessel = event.get("vessel", {})
        position = event.get("position", {})

        rows.append({

            "event_id":
                event.get("id"),

            "event_type":
                event.get("type"),

            "start":
                event.get("start"),

            "end":
                event.get("end"),

            "latitude":
                position.get("lat"),

            "longitude":
                position.get("lon"),

            "vessel_id":
                vessel.get("id"),

            "mmsi":
                vessel.get("ssvid"),

            "vessel_name":
                vessel.get("name"),

            "vessel_type":
                vessel.get("type"),

            "flag":
                vessel.get("flag"),

        })

    return rows


# ============================================================
# DOWNLOAD ALL EVENTS FOR A PERIOD
# ============================================================

def collect_dataset(
    dataset_name,
    start_date,
    end_date,
    max_pages=10,
):

    dataset = DATASETS[dataset_name]

    all_rows = []

    offset = 0

    for page in range(max_pages):

        print(
            f"[{dataset_name}] "
            f"page={page + 1} "
            f"offset={offset}"
        )

        data = get_events(
            dataset=dataset,
            start_date=start_date,
            end_date=end_date,
            limit=100,
            offset=offset,
        )

        rows = normalize_events(data)

        if not rows:
            break

        all_rows.extend(rows)

        next_offset = data.get(
            "nextOffset"
        )

        if next_offset is None:
            break

        offset = next_offset

    return all_rows


# ============================================================
# MAIN
# ============================================================

def main():

    # Start with a manageable historical period.
    #
    # We will expand this once the pipeline works.
    start_date = "2020-01-01"
    end_date = "2020-12-31"

    output_dir = "training/data"

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    for dataset_name in DATASETS:

        rows = collect_dataset(
            dataset_name,
            start_date,
            end_date,
            max_pages=10,
        )

        df = pd.DataFrame(rows)

        output_file = (
            f"{output_dir}/"
            f"gfw_{dataset_name}_2020.csv"
        )

        df.to_csv(
            output_file,
            index=False
        )

        print()
        print(
            f"Saved {len(df)} rows:"
        )

        print(
            output_file
        )

        print()


if __name__ == "__main__":
    main()