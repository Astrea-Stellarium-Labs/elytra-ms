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

__all__ = ("SocialHandler",)


class SocialHandler(HandlerProtocol):
    @typing.overload
    async def add_friend(self, *, xuid: str | int, **kwargs: typing.Any) -> None: ...

    @typing.overload
    async def add_friend(self, *, gamertag: str, **kwargs: typing.Any) -> None: ...

    async def add_friend(
        self,
        *,
        xuid: str | int | None = None,
        gamertag: str | None = None,
        **kwargs: typing.Any,
    ) -> None:
        if not xuid and not gamertag:
            raise ValueError("Either an xuid or gamertag must be provided.")
        elif xuid and gamertag:
            raise ValueError("Only one of xuid or gamertag may be provided.")

        identifier = f"xuid({xuid})" if xuid else f"gt({gamertag})"
        url = f"https://social.xboxlive.com/users/me/people/{identifier}"
        HEADERS = {"x-xbl-contract-version": "2"}
        await self.put(url, headers=HEADERS, **kwargs)

    @typing.overload
    async def remove_friend(self, *, xuid: str | int, **kwargs: typing.Any) -> None: ...

    @typing.overload
    async def remove_friend(self, *, gamertag: str, **kwargs: typing.Any) -> None: ...

    async def remove_friend(
        self,
        *,
        xuid: str | int | None = None,
        gamertag: str | None = None,
        **kwargs: typing.Any,
    ) -> None:
        if not xuid and not gamertag:
            raise ValueError("Either an xuid or gamertag must be provided.")
        elif xuid and gamertag:
            raise ValueError("Only one of xuid or gamertag may be provided.")

        identifier = f"xuid({xuid})" if xuid else f"gt({gamertag})"
        url = f"https://social.xboxlive.com/users/me/people/{identifier}"
        HEADERS = {"x-xbl-contract-version": "2"}
        await self.delete(url, headers=HEADERS, **kwargs)
