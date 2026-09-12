import requests


STAC_URL = (
    "https://stac.dataspace.copernicus.eu"
    "/v1/search"
)


def search_sentinel1(
    min_lon,
    min_lat,
    max_lon,
    max_lat,
    start_datetime,
    end_datetime,
):

    payload = {
        "collections": [
            "sentinel-1-grd"
        ],

        "bbox": [
            min_lon,
            min_lat,
            max_lon,
            max_lat,
        ],

        "datetime": (
            f"{start_datetime}/"
            f"{end_datetime}"
        ),

        "limit": 10,
    }

    response = requests.post(
        STAC_URL,
        json=payload,
        timeout=60,
    )

    response.raise_for_status()

    return response.json()


if __name__ == "__main__":

    result = search_sentinel1(
        min_lon=72.5,
        min_lat=18.5,
        max_lon=73.5,
        max_lat=19.5,
        start_datetime="2025-01-01T00:00:00Z",
        end_datetime="2025-01-31T23:59:59Z",
    )

    features = result.get(
        "features",
        []
    )

    print(
        "Sentinel-1 scenes:",
        len(features),
    )

    for item in features:

        print()
        print("ID:", item.get("id"))
        print(
            "Datetime:",
            item.get(
                "properties",
                {}
            ).get(
                "datetime"
            )
        )

        print(
            "BBox:",
            item.get("bbox")
        )

        print(
            "Geometry:",
            item.get("geometry")
        )