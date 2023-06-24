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
