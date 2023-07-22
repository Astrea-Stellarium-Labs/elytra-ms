from elytra import BaseMicrosoftAPI
from elytra.const import XBOX_API_RELYING_PARTY

from .club import ClubHandler
from .peoplehub import PeopleHubHandler
from .profile import ProfileHandler
from .rta import RTAHandler

__all__ = ("XboxAPI",)


class XboxAPI(
    BaseMicrosoftAPI, ProfileHandler, PeopleHubHandler, ClubHandler, RTAHandler
):
    RELYING_PARTY: str = XBOX_API_RELYING_PARTY
