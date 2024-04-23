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

import typing
from datetime import datetime
from uuid import UUID

from elytra.core import CamelBaseModel, ParsableCamelModel, add_decoder

__all__ = (
    "InboxResponse",
    "MessageContent",
    "MessageContentPart",
    "MessageContentPayload",
    "Message",
    "Conversation",
    "ConversationResponse",
    "Folder",
    "SafetySettings",
)


class MessageContentPart(CamelBaseModel):
    content_type: str
    version: int
    app_uri: typing.Optional[str] = None
    text: typing.Optional[str] = None
    unsuitable_for: typing.Optional[list[typing.Any]] = None
    button_text: typing.Optional[str] = None
    web_uri: typing.Optional[str] = None


class MessageContent(CamelBaseModel):
    parts: list[MessageContentPart]


class MessageContentPayload(CamelBaseModel):
    content: MessageContent

    @property
    def full_content(self) -> str:
        return "".join(part.text for part in self.content.parts if part.text)


class Message(CamelBaseModel):
    timestamp: datetime
    last_update_timestamp: datetime
    type: str
    network_id: str
    conversation_type: str
    conversation_id: UUID
    sender: str
    message_id: str
    clock: str
    is_deleted: bool
    is_server_updated: bool
    owner: typing.Optional[int] = None
    content_payload: typing.Optional[MessageContentPayload] = None


class Conversation(CamelBaseModel):
    timestamp: datetime
    network_id: str
    type: str
    conversation_id: UUID
    voice_id: UUID
    participants: list[str]
    read_horizon: str
    delete_horizon: str
    is_read: bool
    muted: bool
    folder: str
    last_message: Message


@add_decoder
class Folder(ParsableCamelModel):
    folder: str
    total_count: int
    unread_count: int
    conversations: typing.Optional[list[Conversation]] = None


@add_decoder
class ConversationResponse(ParsableCamelModel):
    timestamp: datetime
    network_id: str
    type: str
    conversation_id: UUID
    read_horizon: str
    delete_horizon: str
    is_read: bool
    folder: str
    notification_options: str
    direct_mention_horizon: str
    muted: bool
    voice_id: UUID
    continuation_token: typing.Optional[str] = None
    voice_roster: typing.Optional[list[typing.Any]] = None
    messages: typing.Optional[list[Message]] = None
    participants: typing.Optional[list[str]] = None


class SafetySettings(CamelBaseModel):
    version: int
    primary_inbox_media: str
    primary_inbox_text: str
    primary_inbox_url: str
    secondary_inbox_media: str
    secondary_inbox_text: str
    secondary_inbox_url: str
    can_unobscure: bool


@add_decoder
class InboxResponse(ParsableCamelModel):
    primary: Folder
    folders: list[Folder]
    safety_settings: SafetySettings
