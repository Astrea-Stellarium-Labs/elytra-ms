from elytra import BaseMicrosoftAPI
from elytra.const import XBOX_API_RELYING_PARTY

from .club import ClubHandler
from .peoplehub import PeopleHubHandler
from .profile import ProfileHandler
from .rta import RTA
from .social import SocialHandler

__all__ = ("XboxAPI",)


class XboxAPI(
    BaseMicrosoftAPI,
    ProfileHandler,
    PeopleHubHandler,
    ClubHandler,
    SocialHandler,
):
    RELYING_PARTY: str = XBOX_API_RELYING_PARTY

    async def establish_rta(self) -> RTA:
        return await RTA.establish(self.base_headers)
