import os
import json
import re
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GFW_API_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "GFW_API_TOKEN is missing from .env"
    )

URL = "https://gateway.api.globalfishingwatch.org/v3/vessels/search"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json",
}

CASES = [
    ("ALFA_1_2012", "ALFA I", "2012-03-05"),
    ("AGIA_ZONI_II_2017", "AGIA ZONI II", "2017-09-10"),
    ("BOW_JUBAIL_2018", "BOW JUBAIL", "2018-06-23"),
    ("GOLDEN_RAY_2019", "GOLDEN RAY", "2019-09-08"),
    ("MARINE_HONOUR_2024", "MARINE HONOUR", "2024-06-14"),
    ("SILVER_2013", "SILVER", "2013-12-23"),
]


def normalize(value):

    if value is None:
        return ""

    value = str(value).upper()

    value = re.sub(
        r"[^A-Z0-9 ]+",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


def search_vessel(name):

    params = [
        ("query", name),
        (
            "datasets[0]",
            "public-global-vessel-identity:latest"
        ),
        ("limit", "20"),

    ]

    print("\n" + "=" * 70)
    print("SEARCH:", name)
    print("=" * 70)

    response = requests.get(
        URL,
        headers=HEADERS,
        params=params,
        timeout=60,
    )

    print(
        "HTTP STATUS:",
        response.status_code
    )

    print(
        "REQUEST URL:",
        response.url
    )

    if response.status_code != 200:

        print("\nERROR RESPONSE:")
        print(response.text[:5000])

        return []

    data = response.json()

    print(
        "\nTotal results:",
        data.get("total")
    )

    entries = data.get(
        "entries",
        []
    )

    print(
        "Returned entries:",
        len(entries)
    )

    results = []

    target = normalize(name)

    for entry_index, entry in enumerate(entries):

        registry_info = entry.get(
            "registryInfo",
            []
        )

        self_reported_info = entry.get(
            "selfReportedInfo",
            []
        )

        combined_info = entry.get(
            "combinedSourcesInfo",
            []
        )

        # --------------------------------------------------
        # Registry identities
        # --------------------------------------------------

        for registry in registry_info:

            shipname = (
                registry.get("shipname")
                or registry.get("nShipname")
                or ""
            )

            vessel_id = registry.get("id")

            if vessel_id:

                results.append({
                    "vessel_id": vessel_id,
                    "shipname": shipname,
                    "mmsi": registry.get("ssvid"),
                    "imo": registry.get("imo"),
                    "source": "registryInfo",
                    "exact_name": (
                        normalize(shipname) == target
                    ),
                    "entry_index": entry_index,
                })

        # --------------------------------------------------
        # AIS self-reported identities
        # --------------------------------------------------

        for self_info in self_reported_info:

            shipname = (
                self_info.get("shipname")
                or self_info.get("nShipname")
                or ""
            )

            vessel_id = self_info.get("id")

            if vessel_id:

                results.append({
                    "vessel_id": vessel_id,
                    "shipname": shipname,
                    "mmsi": self_info.get("ssvid"),
                    "imo": self_info.get("imo"),
                    "source": "selfReportedInfo",
                    "exact_name": (
                        normalize(shipname) == target
                    ),
                    "entry_index": entry_index,
                })

    # ------------------------------------------------------
    # Deduplicate
    # ------------------------------------------------------

    unique = {}

    for result in results:

        key = (
            result["vessel_id"],
            result["mmsi"],
            result["imo"],
        )

        unique[key] = result

    results = list(unique.values())

    # Exact name first
    results.sort(
        key=lambda x: x["exact_name"],
        reverse=True
    )

    # ------------------------------------------------------
    # Print matches
    # ------------------------------------------------------

    if not results:

        print(
            "\nNO VESSEL IDENTITIES EXTRACTED."
        )

        # Very useful diagnostic
        if entries:

            print(
                "\nFIRST RAW ENTRY:"
            )

            print(
                json.dumps(
                    entries[0],
                    indent=2
                )[:12000]
            )

        return []

    print(
        "\nExtracted vessel identities:"
    )

    for i, result in enumerate(
        results[:20],
        start=1
    ):

        print(
            f"{i:2}. "
            f"{result['shipname']} | "
            f"id={result['vessel_id']} | "
            f"MMSI={result['mmsi']} | "
            f"IMO={result['imo']} | "
            f"source={result['source']} | "
            f"exact={result['exact_name']}"
        )

    return results


def main():

    print("=" * 70)
    print("GLOBAL FISHING WATCH VESSEL RESOLUTION")
    print("=" * 70)

    rows = []

    for spill_id, vessel_name, date in CASES:

        matches = search_vessel(
            vessel_name
        )

        if matches:

            best = matches[0]

            rows.append({
                "spill_id": spill_id,
                "vessel_name": vessel_name,
                "date": date,
                "gfw_vessel_id": best["vessel_id"],
                "gfw_name": best["shipname"],
                "mmsi": best["mmsi"],
                "imo": best["imo"],
                "source": best["source"],
                "exact_name": best["exact_name"],
                "gfw_resolved": True,
            })

        else:

            rows.append({
                "spill_id": spill_id,
                "vessel_name": vessel_name,
                "date": date,
                "gfw_vessel_id": None,
                "gfw_name": None,
                "mmsi": None,
                "imo": None,
                "source": None,
                "exact_name": False,
                "gfw_resolved": False,
            })

    df = pd.DataFrame(rows)

    output = (
        "training/data/"
        "gfw_vessel_resolution.csv"
    )

    df.to_csv(
        output,
        index=False
    )

    print("\n")
    print("=" * 70)
    print("FINAL TABLE")
    print("=" * 70)

    print(
        df.to_string(index=False)
    )

    print(
        "\nResolved:",
        int(df["gfw_resolved"].sum()),
        "/",
        len(df)
    )

    print(
        "\nSaved:",
        output
    )


if __name__ == "__main__":
    main()