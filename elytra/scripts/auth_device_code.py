import argparse
import asyncio
import os

import aiohttp
import msgspec


async def async_main() -> None:
    parser = argparse.ArgumentParser(description="Authenticate into Microsoft's APIs.")
    parser.add_argument(
        "--file",
        "-f",
        default="oauth.json",
        help="Filepath to put output of program. Default: 'oauth.json'.",
    )
    parser.add_argument(
        "--client-id",
        "-cid",
        default=os.environ.get("CLIENT_ID"),
        help="OAuth2 client ID.",
    )
    args = parser.parse_args()

    if not args.client_id:
        raise ValueError(
            "You must provide a client ID either via the CLI or environment variables."
        )

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://login.microsoftonline.com/consumers/oauth2/v2.0/devicecode",
            data={
                "client_id": args.client_id,
                "scope": "Xboxlive.signin Xboxlive.offline_access",
            },
        ) as r:
            data = await r.json()
            if not r.ok:
                print(data)  # noqa: T201
                return

        success_response: dict | None = None

        print(data["message"])  # noqa: T201

        async with asyncio.Timeout(data["expires_in"]):
            while True:
                await asyncio.sleep(data["interval"])
                async with session.post(
                    "https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
                    data={
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                        "client_id": args.client_id,
                        "device_code": data["device_code"],
                    },
                ) as r:
                    resp_json = await r.json()
                    if error := resp_json.get("error"):
                        if error in {
                            "authorization_declined",
                            "expired_token",
                            "bad_verification_code",
                        }:
                            break
                    else:
                        success_response = resp_json
                        break

        if not success_response:
            print("Authentication failed.")  # noqa: T201
            return

        with open(args.file, "wb") as f:
            f.write(msgspec.json.encode(success_response))

        print("Authentication successful!")  # noqa: T201


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
