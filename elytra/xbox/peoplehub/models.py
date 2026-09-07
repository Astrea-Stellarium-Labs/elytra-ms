"""
MIT License

Copyright (c) 2023-2026 AstreaTSS

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

import typing
from datetime import datetime

from elytra.core import CamelBaseModel, ParsableCamelModel, PascalBaseModel, add_decoder

__all__ = (
    "PeopleSummaryResponse",
    "Suggestion",
    "Recommendation",
    "MultiplayerSummary",
    "RecentPlayer",
    "Follower",
    "PreferredColor",
    "PresenceDetail",
    "TitlePresence",
    "Detail",
    "SocialManager",
    "Avatar",
    "LinkedAccount",
    "Person",
    "RecommendationSummary",
    "FriendFinderState",
    "PeopleHubResponse",
)


class PeopleSummaryResponse(CamelBaseModel):
    target_following_count: int
    target_follower_count: int
    is_caller_following_target: bool
    is_target_following_caller: bool
    has_caller_marked_target_as_favorite: bool
    has_caller_marked_target_as_identity_shared: bool
    legacy_friend_status: str
    available_people_slots: int | None = None
    recent_change_count: int | None = None
    watermark: str | None = None


# microsoft is a great and consistent company
class Suggestion(PascalBaseModel):
    priority: int
    type: str | None = None
    reasons: str | None = None
    title_id: str | None = None


class Recommendation(PascalBaseModel):
    type: str
    reasons: list[str]


class MultiplayerSummary(PascalBaseModel):
    in_multiplayer_session: int
    in_party: int


class RecentPlayer(CamelBaseModel):
    titles: list[str]
    text: str | None = None


class Follower(CamelBaseModel):
    text: str | None = None
    followed_date_time: datetime | None = None


class PreferredColor(CamelBaseModel):
    primary_color: str | None = None
    secondary_color: str | None = None
    tertiary_color: str | None = None


class PresenceDetail(PascalBaseModel):
    is_broadcasting: bool
    device: str
    presence_text: str
    state: str
    title_id: str
    is_primary: bool
    is_game: bool
    title_type: str | None = None
    rich_presence_text: str | None = None


class TitlePresence(PascalBaseModel):
    is_currently_playing: bool
    presence_text: str | None = None
    title_name: str | None = None
    title_id: str | None = None


class Detail(CamelBaseModel):
    account_tier: str
    is_verified: bool
    watermarks: list[str]
    blocked: bool
    mute: bool
    follower_count: int
    following_count: int
    has_game_pass: bool
    bio: str | None = None
    location: str | None = None
    tenure: str | None = None


class SocialManager(CamelBaseModel):
    title_ids: list[str]
    pages: list[str]


class Avatar(CamelBaseModel):
    update_time_offset: datetime | None = None
    spritesheet_metadata: typing.Any | None = None


class LinkedAccount(CamelBaseModel):
    network_name: str
    show_on_profile: bool
    is_family_friendly: bool
    display_name: str | None = None
    deeplink: str | None = None


class Person(CamelBaseModel):
    xuid: str
    is_favorite: bool
    is_following_caller: bool
    is_followed_by_caller: bool
    is_identity_shared: bool
    real_name: str
    display_pic_raw: str
    show_user_as_avatar: str
    gamertag: str
    gamer_score: str
    modern_gamertag: str
    modern_gamertag_suffix: str
    unique_modern_gamertag: str
    xbox_one_rep: str
    presence_state: str
    presence_text: str
    color_theme: str
    preferred_flag: str
    is_broadcasting: bool
    preferred_platforms: list[str]
    is_quarantined: bool
    is_xbox360_gamerpic: bool
    presence_devices: typing.Any | None = None
    is_cloaked: bool | None = None
    added_date_time_utc: datetime | None = None
    display_name: str | None = None
    suggestion: Suggestion | None = None
    recommendation: Recommendation | None = None
    search: typing.Any | None = None
    title_history: typing.Any | None = None
    multiplayer_summary: MultiplayerSummary | None = None
    recent_player: RecentPlayer | None = None
    follower: Follower | None = None
    preferred_color: PreferredColor | None = None
    presence_details: list[PresenceDetail] | None = None
    title_presence: TitlePresence | None = None
    title_summaries: typing.Any | None = None
    presence_title_ids: list[str] | None = None
    detail: Detail | None = None
    community_manager_titles: typing.Any | None = None
    social_manager: SocialManager | None = None
    broadcast: list[typing.Any] | None = None
    tournament_summary: typing.Any | None = None
    avatar: Avatar | None = None
    linked_accounts: list[LinkedAccount] | None = None
    last_seen_date_time_utc: datetime | None = None


class RecommendationSummary(CamelBaseModel):
    friend_of_friend: int
    facebook_friend: int
    phone_contact: int
    follower: int
    VIP: int
    steam_friend: int
    promote_suggestions: bool


class FriendFinderState(CamelBaseModel):
    facebook_opt_in_status: str
    facebook_token_status: str
    phone_opt_in_status: str
    phone_token_status: str
    steam_opt_in_status: str
    steam_token_status: str
    discord_opt_in_status: str
    discord_token_status: str
    instagram_opt_in_status: str
    instagram_token_status: str
    mixer_opt_in_status: str
    mixer_token_status: str
    reddit_opt_in_status: str
    reddit_token_status: str
    twitch_opt_in_status: str
    twitch_token_status: str
    twitter_opt_in_status: str
    twitter_token_status: str
    you_tube_opt_in_status: str
    you_tube_token_status: str


@add_decoder
class PeopleHubResponse(ParsableCamelModel):
    people: list[Person]
    recommendation_summary: RecommendationSummary | None = None
    friend_finder_state: FriendFinderState | None = None
    account_link_details: list[LinkedAccount] | None = None
