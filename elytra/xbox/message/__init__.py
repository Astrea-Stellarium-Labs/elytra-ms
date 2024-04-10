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

import typing

from elytra.protocols import HandlerProtocol

from .models import *

__all__ = (
    "MessageHandler",
    "InboxResponse",
    "MessageContent",
    "MessageContentPart",
    "MessageContentPayload",
    "Message",
    "Conversation",
    "ConversationResponse",
    "Folder",
    "SafetySettings",
)


class MessageHandler(HandlerProtocol):
    async def fetch_inbox(
        self, max_items: int = 100, **kwargs: typing.Any
    ) -> InboxResponse:
        URL = "https://xblmessaging.xboxlive.com/network/Xbox/users/me/inbox"
        HEADERS = {"x-xbl-contract-version": "1"}

        return await InboxResponse.from_response(
            await self.get(
                URL,
                headers=HEADERS,
                params={"maxItems": max_items},
                **kwargs,
            )
        )

    async def fetch_conversation(
        self, xuid: str | int, max_items: int = 100, **kwargs: typing.Any
    ) -> ConversationResponse:
        url = f"https://xblmessaging.xboxlive.com/network/Xbox/users/me/conversations/users/xuid({xuid})"
        HEADERS = {"x-xbl-contract-version": "1"}

        return await ConversationResponse.from_response(
            await self.get(
                url,
                headers=HEADERS,
                params={"maxItems": max_items},
                **kwargs,
            )
        )
