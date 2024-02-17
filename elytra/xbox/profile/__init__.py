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

__all__ = ("ProfileHandler", "ProfileUser", "ProfileResponse", "Setting")


class ProfileHandler(HandlerProtocol):
    async def fetch_profiles(
        self, xuid_list: list[str] | list[int], **kwargs: typing.Any
    ) -> ProfileResponse:
        URL = "https://profile.xboxlive.com/users/batch/profile/settings"
        HEADERS = {"x-xbl-contract-version": "3"}

        post_data = {
            "settings": ["Gamertag"],
            "userIds": xuid_list,
        }
        return await ProfileResponse.from_response(
            await self.post(URL, json=post_data, headers=HEADERS, **kwargs)
        )

    async def fetch_profile_by_xuid(
        self, target_xuid: str | int, **kwargs: typing.Any
    ) -> ProfileResponse:
        HEADERS = {"x-xbl-contract-version": "3"}
        PARAMS = {"settings": "Gamertag"}
        URL = f"https://profile.xboxlive.com/users/xuid({target_xuid})/profile/settings"
        return await ProfileResponse.from_response(
            await self.get(URL, params=PARAMS, headers=HEADERS, **kwargs)
        )

    async def fetch_profile_by_gamertag(
        self, gamertag: str, **kwargs: typing.Any
    ) -> ProfileResponse:
        url = f"https://profile.xboxlive.com/users/gt({gamertag})/profile/settings"
        HEADERS = {"x-xbl-contract-version": "3"}
        PARAMS = {"settings": "Gamertag"}

        return await ProfileResponse.from_response(
            await self.get(url, params=PARAMS, headers=HEADERS, **kwargs)
        )
