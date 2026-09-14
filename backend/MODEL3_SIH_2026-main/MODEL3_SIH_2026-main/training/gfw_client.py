import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GFW_API_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "GFW_API_TOKEN not found. Put it in .env"
    )

BASE_URL = "https://gateway.api.globalfishingwatch.org/v3"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json",
}


def gfw_get(endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"

    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=60,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"GFW API error {response.status_code}: "
            f"{response.text[:1000]}"
        )

    return response.json()


def search_vessel(query):
    return gfw_get(
        "vessels/search",
        params={
            "query": query,
            "datasets[0]": "public-global-vessel-identity:latest",
        },
    )


def get_vessel(vessel_id):
    return gfw_get(
        f"vessels/{vessel_id}",
        params={
            "dataset": "public-global-vessel-identity:latest",
        },
    )


def get_events(
    dataset,
    start_date,
    end_date,
    limit=100,
    offset=0,
):
    return gfw_get(
        "events",
        params={
            "datasets[0]": dataset,
            "start-date": start_date,
            "end-date": end_date,
            "limit": limit,
            "offset": offset,
        },
    )