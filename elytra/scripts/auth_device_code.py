"""
MIT License

Copyright (c) 2023-2024 AstreaTSS

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

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
        with anyio.fail_after(data["expires_in"]):
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
