from elytra.core import CamelBaseModel, ParsableCamelModel, add_decoder

__all__ = ("Setting", "ProfileUser", "ProfileResponse")


class Setting(CamelBaseModel):
    id: str
    value: str


class ProfileUser(CamelBaseModel):
    id: str
    host_id: str
    settings: list[Setting]
    is_sponsored_user: bool


@add_decoder
class ProfileResponse(ParsableCamelModel):
    profile_users: list[ProfileUser]
