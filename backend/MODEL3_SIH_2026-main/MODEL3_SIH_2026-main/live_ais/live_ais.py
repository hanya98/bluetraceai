
import asyncio
import json
import os

import websockets
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("AISSTREAM_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "AISSTREAM_API_KEY not found in .env"
    )


URL = "wss://stream.aisstream.io/v0/stream"


# Mumbai / Arabian Sea
SUBSCRIPTION = {
    "APIKey": API_KEY,

    "BoundingBoxes": [
        [
            [25.835, -80.208],
            [25.603, -79.879],
        ]
    ],

    "FilterMessageTypes": [
        "PositionReport"
    ],
}


async def main():

    print("=" * 60)
    print("AISSTREAM DIAGNOSTIC")
    print("=" * 60)

    print("Connecting...")

    async with websockets.connect(
        URL,
        compression="deflate",
        ping_interval=20,
        ping_timeout=20,
    ) as websocket:

        print("WebSocket connected.")

        await websocket.send(
            json.dumps(SUBSCRIPTION)
        )

        print("Subscription sent.")
        print()
        print("Waiting for AIS messages...")
        print("Bounding box:")
        print("LAT 18.0 → 20.5")
        print("LON 71.0 → 74.5")
        print()
        print("Press CTRL+C to stop.")
        print("=" * 60)

        count = 0

        while True:

            raw = await websocket.recv()

            # Decode binary WebSocket frames
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")

            data = json.loads(raw)

            count += 1

            message_type = data.get(
                "MessageType",
                "UNKNOWN"
            )

            print()
            print(
                f"MESSAGE #{count}"
            )

            print(
                f"MessageType = {message_type}"
            )

            # ------------------------------------------------
            # Subscription confirmation
            # ------------------------------------------------

            if message_type == "SubscriptionConfirmation":

                print(
                    "✓ AISStream accepted the subscription."
                )

                print(
                    json.dumps(
                        data,
                        indent=2
                    )
                )

                continue

            # ------------------------------------------------
            # Position report
            # ------------------------------------------------

            if message_type == "PositionReport":

                metadata = data.get(
                    "MetaData",
                    {}
                )

                report = data.get(
                    "Message",
                    {}
                ).get(
                    "PositionReport",
                    {}
                )

                print(
                    "🚢 VESSEL RECEIVED"
                )

                print(
                    "MMSI:",
                    metadata.get("MMSI")
                )

                print(
                    "Ship:",
                    metadata.get("ShipName")
                )

                print(
                    "Latitude:",
                    metadata.get("Latitude")
                )

                print(
                    "Longitude:",
                    metadata.get("Longitude")
                )

                print(
                    "Speed:",
                    report.get("Sog")
                )

                print(
                    "Heading:",
                    report.get("TrueHeading")
                )

                continue

            # ------------------------------------------------
            # Anything else
            # ------------------------------------------------

            print(
                "Other AIS message:"
            )

            print(
                json.dumps(
                    data,
                    indent=2
                )[:2000]
            )


if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        print()
        print("Stopped.")

