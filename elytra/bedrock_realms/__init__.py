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
    "RealmCountResponse",
    "PendingInvite",
    "PendingInviteResponse",
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

    async def invite_player(
        self, realm_id: str | int, player_xuid: str | int
    ) -> FullRealm:
        return await FullRealm.from_response(
            await self.put(
                f"invites/{realm_id}/invite/update",
                json={"invites": {str(player_xuid): "ADD"}},
            )
        )

    async def fetch_pending_invite_count(self) -> int:
        resp = await self.get("invites/count/pending")
        return int(await resp.aread())

    async def fetch_pending_invites(self) -> PendingInviteResponse:
        return await PendingInviteResponse.from_response(
            await self.get("invites/pending")
        )

    async def accept_invite(self, invitation_id: str) -> None:
        await self.put(f"invites/accept/{invitation_id}")

    async def reject_invite(self, invitation_id: str) -> None:
        await self.put(f"invites/reject/{invitation_id}")

    async def fetch_activities(self) -> ActivityListResponse:
        return await ActivityListResponse.from_response(
            await self.get("activities/live/players")
        )

    async def leave_realm(self, realm_id: int | str) -> None:
        await self.delete(f"invites/{realm_id}")

    async def fetch_realm_count(self) -> RealmCountResponse:
        return await RealmCountResponse.from_response(
            await self.get("clubs/membercount")
        )
