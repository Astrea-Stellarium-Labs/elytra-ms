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
    "PeopleSummaryResponse",
    "Suggestion",
    "Recommendation",
    "MultiplayerSummary",
    "RecentPlayer",
    "Follower",
    "PreferredColor",
    "PresenceDetail",
    "TitlePresence",
    "Detail",
    "SocialManager",
    "Avatar",
    "LinkedAccount",
    "Person",
    "RecommendationSummary",
    "FriendFinderState",
    "PeopleHubResponse",
    "PeopleHubHandler",
)


class PeopleHubHandler(HandlerProtocol):
    async def fetch_people_batch(
        self,
        xuid_list: list[str] | list[int],
        *,
        decoration: str = "presencedetail",
        **kwargs: typing.Any,
    ) -> PeopleHubResponse:
        HEADERS = {"x-xbl-contract-version": "3", "Accept-Language": "en-US"}
        URL = f"https://peoplehub.xboxlive.com/users/me/people/batch/decoration/{decoration}"
        return await PeopleHubResponse.from_response(
            await self.post(
                URL,
                headers=HEADERS,
                json={"xuids": xuid_list},
                **kwargs,
            )
        )
