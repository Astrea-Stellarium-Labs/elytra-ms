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
    players: NoneType
    max_players: int
    minigame_name: NoneType
    minigame_id: NoneType
    minigame_image: NoneType
    active_slot: int
    slots: NoneType
    member: bool
    subscription_refresh_status: NoneType
    club_id: typing.Optional[int] = None
    owner_uuid: typing.Optional[str] = None
    motd: typing.Optional[str] = None


@add_decoder
class MultiRealmResponse(ParsableCamelModel):
    servers: list[FullRealm]


class Player(CamelBaseModel):
    uuid: str
    name: NoneType
    operator: bool
    accepted: bool
    online: bool
    permission: Permission


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
