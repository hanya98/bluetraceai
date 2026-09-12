import json
from gfw_client import get_events


START_DATE = "2024-01-01"
END_DATE = "2024-12-31"

EVENTS = {
    "loitering": "public-global-loitering-events:latest",
    "gaps": "public-global-gaps-events:latest",
    "port_visits": "public-global-port-visits-events:latest",
    "encounters": "public-global-encounters-events:latest",
}


def download_event_type(name, dataset):

    print()
    print("=" * 60)
    print("Downloading:", name)
    print("=" * 60)

    all_entries = []
    offset = 0
    limit = 100

    while True:

        result = get_events(
            dataset=dataset,
            start_date=START_DATE,
            end_date=END_DATE,
            limit=limit,
            offset=offset,
        )

        entries = result.get("entries", [])

        print(
            f"offset={offset} "
            f"received={len(entries)} "
            f"total={result.get('total')}"
        )

        all_entries.extend(entries)

        if not entries:
            break

        next_offset = result.get("nextOffset")

        if next_offset is None:
            break

        offset = next_offset

        if len(all_entries) >= 5000:
            print("Stopping at 5000 events for this prototype.")
            break

    output = f"{name}_events.json"

    with open(output, "w", encoding="utf-8") as f:
        json.dump(
            all_entries,
            f,
            indent=2,
        )

    print("Saved:", output)
    print("Events:", len(all_entries))


for name, dataset in EVENTS.items():
    download_event_type(name, dataset)