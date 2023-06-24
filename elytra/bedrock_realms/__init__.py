from elytra.const import BEDROCK_REALMS_API_URL, MC_VERSION
from elytra.core import BaseMicrosoftAPI

from .models import *

__all__ = (
    "Permission",
    "State",
    "WorldType",
    "FullRealm",
    "MultiRealmResponse",
    "Player",
    "PartialRealm",
    "ActivityListResponse",
    "BedrockRealmsAPI",
)


class BedrockRealmsAPI(BaseMicrosoftAPI):
    RELYING_PATH: str = BEDROCK_REALMS_API_URL
    BASE_URL: str = BEDROCK_REALMS_API_URL

    @property
    def base_headers(self) -> dict[str, str]:
        return {
            "Authorization": self.auth_mgr.xsts_token.authorization_header_value,
            "Client-Version": MC_VERSION,
            "User-Agent": "MCPE/UWP",
        }

    async def join_realm_from_code(self, code: str) -> FullRealm:
        return await FullRealm.from_response(
            await self.post(f"invites/v1/link/accept/{code}")
        )

    async def fetch_realms(self) -> MultiRealmResponse:
        return await MultiRealmResponse.from_response(await self.get("worlds"))

    async def fetch_activities(self) -> ActivityListResponse:
        return await ActivityListResponse.from_response(
            await self.get("activities/live/players")
        )

    async def leave_realm(self, realm_id: int | str) -> None:
        await self.delete(f"invites/{realm_id}")
