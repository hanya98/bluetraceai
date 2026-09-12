import csv
from datetime import datetime, timedelta, timezone

OUTPUT = "synthetic_ais.csv"

spill_time = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)

rows = []

# V001 - strongest candidate
v001 = [
    (19.200, 73.020, 10.0, 225.0),
    (19.140, 72.950, 9.0, 225.0),
    (19.080, 72.880, 4.0, 225.0),
    (19.055, 72.852, 1.5, 225.0),
    (19.052, 72.851, 1.0, 225.0),
]

for i, (lat, lon, sog, heading) in enumerate(v001):
    timestamp = spill_time - timedelta(hours=8) + timedelta(hours=2*i)

    rows.append([
        "V001",
        timestamp.isoformat().replace("+00:00", "Z"),
        lat,
        lon,
        sog,
        heading,
    ])


# V002 - close to spill but moving east
v002 = [
    (19.020, 72.780, 8.0, 90.0),
    (19.020, 72.800, 8.0, 90.0),
    (19.020, 72.820, 8.0, 90.0),
    (19.020, 72.840, 8.0, 90.0),
    (19.020, 72.860, 8.0, 90.0),
]

for i, (lat, lon, sog, heading) in enumerate(v002):
    timestamp = spill_time - timedelta(hours=8) + timedelta(hours=2*i)

    rows.append([
        "V002",
        timestamp.isoformat().replace("+00:00", "Z"),
        lat,
        lon,
        sog,
        heading,
    ])


# V003 - was nearby but much earlier
v003 = [
    (19.100, 72.950, 12.0, 180.0),
    (19.100, 72.960, 12.0, 180.0),
    (19.100, 72.970, 12.0, 180.0),
]

for i, (lat, lon, sog, heading) in enumerate(v003):
    timestamp = spill_time - timedelta(hours=40) + timedelta(hours=2*i)

    rows.append([
        "V003",
        timestamp.isoformat().replace("+00:00", "Z"),
        lat,
        lon,
        sog,
        heading,
    ])


# V004 - deliberately far away
for i in range(4):
    timestamp = spill_time - timedelta(hours=4) + timedelta(hours=i)

    rows.append([
        "V004",
        timestamp.isoformat().replace("+00:00", "Z"),
        20.200,
        74.200,
        12.0,
        270.0,
    ])


# V005 - close and slow
v005 = [
    (19.000, 72.900, 1.0, 315.0),
    (19.010, 72.890, 1.0, 315.0),
    (19.020, 72.880, 1.0, 315.0),
    (19.030, 72.870, 1.0, 315.0),
    (19.040, 72.860, 1.0, 315.0),
]

for i, (lat, lon, sog, heading) in enumerate(v005):
    timestamp = spill_time - timedelta(hours=6) + timedelta(hours=i)

    rows.append([
        "V005",
        timestamp.isoformat().replace("+00:00", "Z"),
        lat,
        lon,
        sog,
        heading,
    ])


# Write CSV
with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    writer.writerow([
        "vessel_id",
        "timestamp_utc",
        "latitude",
        "longitude",
        "speed_knots",
        "heading_deg",
    ])

    writer.writerows(rows)

print(f"Created {OUTPUT}")
print(f"Total AIS observations: {len(rows)}")
