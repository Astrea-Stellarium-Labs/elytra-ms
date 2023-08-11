import typing

from elytra.protocols import HandlerProtocol

__all__ = ("SocialHandler",)


class SocialHandler(HandlerProtocol):
    @typing.overload
    async def add_friend(self, *, xuid: str | int, **kwargs: typing.Any) -> None:
        ...

    @typing.overload
    async def add_friend(self, *, gamertag: str, **kwargs: typing.Any) -> None:
        ...

    async def add_friend(
        self,
        *,
        xuid: str | int | None = None,
        gamertag: str | None = None,
        **kwargs: typing.Any,
    ) -> None:
        if not xuid and not gamertag:
            raise ValueError("Either an xuid or gamertag must be provided.")
        elif xuid and gamertag:
            raise ValueError("Only one of xuid or gamertag may be provided.")

        identifier = f"xuid({xuid})" if xuid else f"gt({gamertag})"
        url = f"https://social.xboxlive.com/users/me/people/{identifier}"
        HEADERS = {"x-xbl-contract-version": "2"}
        await self.put(url, headers=HEADERS, **kwargs)

    @typing.overload
    async def remove_friend(self, *, xuid: str | int, **kwargs: typing.Any) -> None:
        ...

    @typing.overload
    async def remove_friend(self, *, gamertag: str, **kwargs: typing.Any) -> None:
        ...

    async def remove_friend(
        self,
        *,
        xuid: str | int | None = None,
        gamertag: str | None = None,
        **kwargs: typing.Any,
    ) -> None:
        if not xuid and not gamertag:
            raise ValueError("Either an xuid or gamertag must be provided.")
        elif xuid and gamertag:
            raise ValueError("Only one of xuid or gamertag may be provided.")

        identifier = f"xuid({xuid})" if xuid else f"gt({gamertag})"
        url = f"https://social.xboxlive.com/users/me/people/{identifier}"
        HEADERS = {"x-xbl-contract-version": "2"}
        await self.delete(url, headers=HEADERS, **kwargs)
