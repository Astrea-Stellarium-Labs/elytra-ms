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
