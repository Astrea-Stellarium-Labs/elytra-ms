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

from elytra import BaseMicrosoftAPI
from elytra.const import XBOX_API_RELYING_PARTY

from .club import ClubHandler
from .peoplehub import PeopleHubHandler
from .profile import ProfileHandler
from .rta import RTA
from .social import SocialHandler

__all__ = ("XboxAPI", "RTA")


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
