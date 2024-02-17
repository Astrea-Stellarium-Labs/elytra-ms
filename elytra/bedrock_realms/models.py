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

import datetime
import typing
from enum import Enum
from types import NoneType

import msgspec

from elytra.core import CamelBaseModel, ParsableCamelModel, add_decoder

__all__ = (
    "Permission",
    "State",
    "WorldType",
    "FullRealm",
    "MultiRealmResponse",
    "Player",
    "PartialRealm",
    "ActivityListResponse",
    "PendingInvite",
    "PendingInviteResponse",
    "RealmCountResponse",
)


class Permission(Enum):
    VISITOR = "VISITOR"
    MEMBER = "MEMBER"
    OPERATOR = "OPERATOR"


class State(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"


class WorldType(Enum):
    NORMAL = "NORMAL"


class Player(CamelBaseModel):
    uuid: str
    name: NoneType
    operator: bool
    accepted: bool
    online: bool
    permission: Permission


@add_decoder
class FullRealm(ParsableCamelModel):
    id: int
    remote_subscription_id: str
    owner: typing.Optional[str]
    name: str
    default_permission: Permission
    state: State
    days_left: int
    expired: bool
    expired_trial: bool
    grace_period: bool
    world_type: WorldType
    max_players: int
    minigame_name: NoneType
    minigame_id: NoneType
    minigame_image: NoneType
    active_slot: int
    member: bool
    subscription_refresh_status: NoneType
    owner_uuid: str = msgspec.field(name="ownerUUID")
    slots: typing.Optional[typing.Any] = None
    players: typing.Optional[list[Player]] = None
    club_id: typing.Optional[int] = None
    motd: typing.Optional[str] = None


@add_decoder
class MultiRealmResponse(ParsableCamelModel):
    servers: list[FullRealm]


class PartialRealm(CamelBaseModel):
    id: int
    players: list[Player]
    full: bool


@add_decoder
class ActivityListResponse(ParsableCamelModel):
    servers: list[PartialRealm]


class PendingInvite(CamelBaseModel):
    invitation_id: str  # not the realm id, funny enough
    world_name: str
    world_description: str
    world_owner_name: str
    world_owner_uuid: str
    date_timestamp: int = msgspec.field(name="date")

    @property
    def date(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self.date_timestamp, tz=datetime.UTC)


@add_decoder
class PendingInviteResponse(ParsableCamelModel):
    invites: list[PendingInvite]


@add_decoder
class RealmCountResponse(ParsableCamelModel):
    realm_count: int = msgspec.field(name="memberCount")
    realm_limit: int = msgspec.field(name="memberLimit")
    over_limit: bool
