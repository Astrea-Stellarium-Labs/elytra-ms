import typing

from elytra.protocols import HandlerProtocol

from .models import *

__all__ = ("ProfileHandler", "ProfileUser", "ProfileResponse", "Setting")


class ProfileHandler(HandlerProtocol):
    async def fetch_profiles(
        self, xuid_list: list[str] | list[int], **kwargs: typing.Any
    ) -> ProfileResponse:
        URL = "https://profile.xboxlive.com/users/batch/profile/settings"
        HEADERS = {"x-xbl-contract-version": "3"}

        post_data = {
            "settings": ["Gamertag"],
            "userIds": xuid_list,
        }
        return await ProfileResponse.from_response(
            await self.post(URL, json=post_data, headers=HEADERS, **kwargs)
        )

    async def fetch_profile_by_xuid(
        self, target_xuid: str | int, **kwargs: typing.Any
    ) -> ProfileResponse:
        HEADERS = {"x-xbl-contract-version": "3"}
        PARAMS = {"settings": "Gamertag"}
        URL = f"https://profile.xboxlive.com/users/xuid({target_xuid})/profile/settings"
        return await ProfileResponse.from_response(
            await self.get(URL, params=PARAMS, headers=HEADERS, **kwargs)
        )

    async def fetch_profile_by_gamertag(
        self, gamertag: str, **kwargs: typing.Any
    ) -> ProfileResponse:
        url = f"https://profile.xboxlive.com/users/gt({gamertag})/profile/settings"
        HEADERS = {"x-xbl-contract-version": "3"}
        PARAMS = {"settings": "Gamertag"}

        return await ProfileResponse.from_response(
            await self.get(url, params=PARAMS, headers=HEADERS, **kwargs)
        )
