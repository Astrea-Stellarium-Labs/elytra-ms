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

from elytra.protocols import HandlerProtocol

from .models import *

__all__ = (
    "ClubUserPresence",
    "ClubDeeplinkMetadata",
    "ClubDeeplinks",
    "ClubPresence",
    "ClubType",
    "ProfileMetadata",
    "Profile",
    "TitleDeeplinkMetadata",
    "TitleDeeplinks",
    "Club",
    "ClubResponse",
    "ClubHandler",
)


class ClubHandler(HandlerProtocol):
    async def fetch_club_presence(self, club_id: int | str) -> ClubResponse:
        HEADERS = {"x-xbl-contract-version": "4", "Accept-Language": "en-US"}
        url = (
            f"https://clubhub.xboxlive.com/clubs/Ids({club_id})/decoration/clubpresence"
        )

        return await ClubResponse.from_response(await self.get(url, headers=HEADERS))
