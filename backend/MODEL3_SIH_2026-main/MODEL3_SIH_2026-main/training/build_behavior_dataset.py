import json
import math
import pandas as pd


def load_events(path):

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_event_features(event):

    vessel = event.get("vessel", {})
    position = event.get("position", {})
    distances = event.get("distances", {})

    def number(x):
        try:
            value = float(x)
            if math.isfinite(value):
                return value
        except (TypeError, ValueError):
            pass
        return None

    return {
        "vessel_id": vessel.get("id"),
        "mmsi": vessel.get("ssvid"),
        "vessel_name": vessel.get("name"),

        "latitude": number(position.get("lat")),
        "longitude": number(position.get("lon")),

        "start_distance_from_port_km":
            number(distances.get("startDistanceFromPortKm")),

        "end_distance_from_port_km":
            number(distances.get("endDistanceFromPortKm")),

        "start_distance_from_shore_km":
            number(distances.get("startDistanceFromShoreKm")),

        "end_distance_from_shore_km":
            number(distances.get("endDistanceFromShoreKm")),

        "start": event.get("start"),
        "end": event.get("end"),

        "event_type": event.get("type"),

        "label": 1,
    }


events = load_events("loitering_events.json")

rows = [
    extract_event_features(event)
    for event in events
]

df = pd.DataFrame(rows)

df = df.dropna(
    subset=[
        "latitude",
        "longitude",
    ]
)

print(df.head())
print()
print("Rows:", len(df))
print("Columns:", list(df.columns))

df.to_csv(
    "real_behavior_positive.csv",
    index=False,
)

print("Saved real_behavior_positive.csv")