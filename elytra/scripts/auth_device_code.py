import argparse
import os

import anyio
import httpx
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

    session = httpx.AsyncClient()

    r = await session.post(
        "https://login.microsoftonline.com/consumers/oauth2/v2.0/devicecode",
        data={
            "client_id": args.client_id,
            "scope": "Xboxlive.signin Xboxlive.offline_access",
        },
    )
    data = await r.json()
    if r.is_error:
        print(data)  # noqa: T201
        return

    success_response: dict | None = None

    print(data["message"])  # noqa: T201

    try:
        async with anyio.fail_after(data["expires_in"]):
            while True:
                await anyio.sleep(data["interval"])
                r = await session.post(
                    "https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
                    data={
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                        "client_id": args.client_id,
                        "device_code": data["device_code"],
                    },
                )
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
    except TimeoutError:
        print("Authentication timed out.")  # noqa: T201
        return

    if not success_response:
        print("Authentication failed.")  # noqa: T201
        return

    with open(args.file, "wb") as f:
        f.write(msgspec.json.encode(success_response))

    print("Authentication successful!")  # noqa: T201


def main() -> None:
    anyio.run(async_main)


if __name__ == "__main__":
    main()
