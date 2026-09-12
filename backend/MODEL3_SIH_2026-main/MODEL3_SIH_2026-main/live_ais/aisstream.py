import asyncio
import json
import os

import websockets
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("AISSTREAM_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "AISSTREAM_API_KEY missing from .env"
    )


URL = "wss://stream.aisstream.io/v0/stream"


SUBSCRIPTION = {
    "APIKey": API_KEY,
    "BoundingBoxes": [
        [
            [18.5, 72.0],
            [20.0, 74.0],
        ]
    ],
    "FilterMessageTypes": [
        "PositionReport"
    ],
}


async def main():

    async with websockets.connect(URL) as websocket:

        await websocket.send(
            json.dumps(SUBSCRIPTION)
        )

        print(
            "Listening for live AIS around Mumbai..."
        )

        while True:

            message = await websocket.recv()

            data = json.loads(message)

            msg_type = data.get("MessageType")

            if msg_type != "PositionReport":
                continue

            report = data.get(
                "Message",
                {},
            ).get(
                "PositionReport",
                {},
            )

            output = {
                "vessel_id":
                    str(
                        data.get(
                            "MetaData",
                            {}
                        ).get(
                            "MMSI",
                            ""
                        )
                    ),

                "latitude":
                    report.get("Latitude"),

                "longitude":
                    report.get("Longitude"),

                "speed_knots":
                    report.get("Sog"),

                "heading_deg":
                    report.get("TrueHeading"),

                "timestamp_utc":
                    data.get(
                        "MetaData",
                        {}
                    ).get(
                        "time_utc"
                    ),
            }

            print(output)


if __name__ == "__main__":
    asyncio.run(main())