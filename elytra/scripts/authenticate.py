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
import contextlib
import os
from email.utils import formatdate
from urllib.parse import parse_qsl, urlencode

import anyio
import httpx
import msgspec
from anyio.abc import SocketStream

from elytra import AuthenticationManager

code: str = ""


def generate_authorization_url(client_id: str, redirect_uri: str) -> str:
    """Generate Windows Live Authorization URL."""
    query_params = {
        "client_id": client_id,
        "response_type": "code",
        "approval_prompt": "auto",
        "scope": "Xboxlive.signin Xboxlive.offline_access",
        "redirect_uri": redirect_uri,
    }

    return f"https://login.live.com/oauth20_authorize.srf?{urlencode(query_params)}"


async def respond_to_request(client: SocketStream, response_status: str) -> None:
    resp = (
        f"HTTP/1.1 {response_status}\r\nDate: {formatdate(usegmt=True)}\r\nServer:"
        " elytra-ms\r\n\r\n"
    )
    await client.send(resp.encode())


async def respond_with_text(
    client: SocketStream, response_status: str, text: str
) -> None:
    resp = (
        f"HTTP/1.1 {response_status}\r\nContent-Type: text/plain;"
        f" charset=utf-8\r\nContent-Length: {len(text)}\r\nDate:"
        f" {formatdate(usegmt=True)}\r\nServer: elytra-ms\r\n\r\n{text}"
    )
    await client.send(resp.encode())


async def handle_microsoft(client: SocketStream) -> None:
    global code

    async with client:
        raw_data = await client.receive()

        try:
            data = raw_data.decode()
        except UnicodeDecodeError:
            return await respond_to_request(client, "400 Bad Request")

        if not data.startswith("GET /auth/callback?code="):
            return await respond_to_request(client, "400 Bad Request")

        first_couple_of_entries = data.split(maxsplit=2)

        url_ish = first_couple_of_entries[1]
        query_string = url_ish.split("?", 1)[1]
        query_dict = dict(parse_qsl(query_string))

        if query_dict.get("error"):
            await respond_with_text(
                client,
                "400 Bad Request",
                f"Error: {query_dict.get('error_description')}",
            )
        elif gotten_code := query_dict.get("code"):
            code = gotten_code
            await respond_with_text(
                client,
                "200 OK",
                "Success! You may now close this tab and go back to the terminal.",
            )
        else:
            await respond_with_text(
                client, "400 Bad Request", "Error: No code was provided."
            )

        await client.aclose()
        raise anyio.EndOfStream


async def async_main() -> None:
    global code

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
    parser.add_argument(
        "--client-secret",
        default=os.environ.get("CLIENT_SECRET"),
        help="OAuth2 client secret.",
    )
    args = parser.parse_args()

    if not (args.client_id and args.client_secret):
        raise ValueError(
            "You must provide a client ID and secret either via the CLI or environment"
            " variables."
        )

    redirect_uri = "http://localhost:8080/auth/callback"

    print(  # noqa: T201
        f"Please visit {generate_authorization_url(args.client_id, redirect_uri)} to"
        " authenticate."
    )

    listener = await anyio.create_tcp_listener(local_host="localhost", local_port=8080)

    with contextlib.suppress(anyio.EndOfStream):
        await listener.serve(handle_microsoft)

    if not code:
        print("Authentication failed.")  # noqa: T201
        return

    auth_mgr = AuthenticationManager(
        httpx.AsyncClient(http2=True),
        args.client_id,
        args.client_secret,
        "http://xboxlive.com",
    )
    oauth = await auth_mgr.request_oauth_token(code, redirect_uri)
    with open(args.file, mode="wb") as f:
        f.write(msgspec.json.encode(oauth))

    await auth_mgr.close()
    print("Authentication successful!")  # noqa: T201


def main() -> None:
    anyio.run(async_main)


if __name__ == "__main__":
    main()
