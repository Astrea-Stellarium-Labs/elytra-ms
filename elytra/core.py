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
import functools
import typing

import httpx
import msgspec
import typing_extensions as typing_ext

from elytra import retry_transport
from elytra.protocols import HandlerProtocol

__all__ = (
    "BaseModel",
    "CamelBaseModel",
    "PascalBaseModel",
    "ParsableModel",
    "ParsableCamelModel",
    "ParsablePascalModel",
    "add_decoder",
    "OAuth2TokenResponse",
    "AuthenticationManager",
    "MicrosoftAPIException",
    "BaseMicrosoftAPI",
)


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


class ParsableBase:
    if typing.TYPE_CHECKING:
        _decoder: msgspec.json.Decoder[typing_ext.Self]
        _encoded_fields: frozenset[str]

    @classmethod
    def from_data(cls, obj: dict) -> typing_ext.Self:
        if not hasattr(cls, "_encoded_fields"):
            cls._encoded_fields = frozenset(
                f.encode_name for f in msgspec.structs.fields(cls)
            )

        filted_dict = {k: v for k, v in obj.items() if k in cls._encoded_fields}
        return cls(**filted_dict)

    @classmethod
    def from_bytes(cls, obj: bytes) -> typing_ext.Self:
        return cls._decoder.decode(obj)  # type: ignore

    @classmethod
    async def from_response(cls, resp: httpx.Response) -> typing_ext.Self:
        return cls.from_bytes(await resp.aread())


class ParsableModel(msgspec.Struct, ParsableBase, kw_only=True):
    pass


class ParsableCamelModel(msgspec.Struct, ParsableBase, rename="camel", kw_only=True):
    pass


class ParsablePascalModel(msgspec.Struct, ParsableBase, rename="pascal", kw_only=True):
    pass


PM = typing.TypeVar("PM", bound=type[ParsableBase])


def add_decoder(cls: PM) -> PM:
    cls._decoder = msgspec.json.Decoder(cls)
    return cls


class BaseModel(msgspec.Struct, kw_only=True):
    pass


class CamelBaseModel(msgspec.Struct, rename="camel", kw_only=True):
    pass


class PascalBaseModel(msgspec.Struct, rename="pascal", kw_only=True):
    pass


@add_decoder
class OAuth2TokenResponse(ParsableModel):
    token_type: str
    expires_in: int
    scope: str
    access_token: str
    issued: datetime.datetime = msgspec.field(default_factory=utc_now)
    user_id: typing.Optional[str] = None
    refresh_token: typing.Optional[str] = None

    def is_valid(self) -> bool:
        return (self.issued + datetime.timedelta(seconds=self.expires_in)) > utc_now()

    @classmethod
    def from_file(cls, path: str) -> typing_ext.Self:
        with open(path, "rb") as f:
            return cls.from_bytes(f.read())


class XTokenResponse(ParsablePascalModel):
    issue_instant: datetime.datetime
    not_after: datetime.datetime
    token: str

    def is_valid(self) -> bool:
        return self.not_after > utc_now()


class DisplayClaims(BaseModel):
    xui: list[dict[str, str]]


@add_decoder
class XAUResponse(XTokenResponse):
    display_claims: DisplayClaims


@add_decoder
class XSTSResponse(XTokenResponse):
    display_claims: DisplayClaims

    @property
    def xuid(self) -> str:
        return self.display_claims.xui[0]["xid"]

    @property
    def userhash(self) -> str:
        return self.display_claims.xui[0]["uhs"]

    @property
    def gamertag(self) -> str:
        return self.display_claims.xui[0]["gtg"]

    @property
    def age_group(self) -> str:
        return self.display_claims.xui[0]["agg"]

    @property
    def privileges(self) -> str:
        return self.display_claims.xui[0]["prv"]

    @property
    def user_privileges(self) -> str:
        return self.display_claims.xui[0]["usr"]

    @property
    def authorization_header_value(self) -> str:
        return f"XBL3.0 x={self.userhash};{self.token}"


class AuthenticationManager:
    __slots__ = (
        "session",
        "client_id",
        "client_secret",
        "relying_party",
        "oauth",
        "user_token",
        "xsts_token",
    )

    session: httpx.AsyncClient
    client_id: str
    client_secret: str
    relying_party: str

    oauth: OAuth2TokenResponse
    user_token: XAUResponse
    xsts_token: XSTSResponse

    def __init__(
        self,
        session: httpx.AsyncClient,
        client_id: str,
        client_secret: str,
        relying_party: str,
    ) -> None:
        self.session = session
        self.client_id = client_id
        self.client_secret = client_secret
        self.relying_party = relying_party

        self.oauth = None  # type: ignore
        self.user_token = None  # type: ignore
        self.xsts_token = None  # type: ignore

    @classmethod
    async def from_ouath(
        cls,
        session: httpx.AsyncClient,
        client_id: str,
        client_secret: str,
        relying_party: str,
        oauth: OAuth2TokenResponse,
    ) -> typing_ext.Self:
        self = cls(session, client_id, client_secret, relying_party)
        self.oauth = oauth
        await self.refresh_tokens()
        return self

    @classmethod
    async def from_data(
        cls,
        session: httpx.AsyncClient,
        client_id: str,
        client_secret: str,
        relying_party: str,
        oauth_data: dict,
    ) -> typing_ext.Self:
        self = cls(session, client_id, client_secret, relying_party)
        self.oauth = OAuth2TokenResponse.from_data(oauth_data)
        await self.refresh_tokens()
        return self

    @classmethod
    async def from_file(
        cls,
        session: httpx.AsyncClient,
        client_id: str,
        client_secret: str,
        relying_party: str,
        oauth_path: str,
    ) -> typing_ext.Self:
        self = cls(session, client_id, client_secret, relying_party)
        self.oauth = OAuth2TokenResponse.from_file(oauth_path)
        await self.refresh_tokens()
        return self

    async def _oauth2_token_request(self, data: dict) -> OAuth2TokenResponse:
        """Execute token requests."""
        data["client_id"] = self.client_id
        if self.client_secret:
            data["client_secret"] = self.client_secret
        resp = await self.session.post(
            "https://login.live.com/oauth20_token.srf", data=data
        )
        resp.raise_for_status()
        return await OAuth2TokenResponse.from_response(resp)

    async def request_oauth_token(
        self, authorization_code: str, redirect_uri: str
    ) -> OAuth2TokenResponse:
        """Request OAuth2 token."""
        return await self._oauth2_token_request(
            {
                "grant_type": "authorization_code",
                "code": authorization_code,
                "scope": "Xboxlive.signin Xboxlive.offline_access",
                "redirect_uri": redirect_uri,
            }
        )

    async def refresh_oauth_token(self) -> OAuth2TokenResponse:
        """Refresh OAuth2 token."""
        if not self.oauth.refresh_token:
            raise ValueError("No refresh token present.")

        return await self._oauth2_token_request(
            {
                "grant_type": "refresh_token",
                "scope": "Xboxlive.signin Xboxlive.offline_access",
                "refresh_token": self.oauth.refresh_token,
            },
        )

    async def request_user_token(
        self,
        relying_party: str = "http://auth.xboxlive.com",
        use_compact_ticket: bool = False,
    ) -> XAUResponse:
        """Authenticate via access token and receive user token."""
        url = "https://user.auth.xboxlive.com/user/authenticate"
        headers = {"x-xbl-contract-version": "1"}
        data = {
            "RelyingParty": relying_party,
            "TokenType": "JWT",
            "Properties": {
                "AuthMethod": "RPS",
                "SiteName": "user.auth.xboxlive.com",
                "RpsTicket": (
                    self.oauth.access_token
                    if use_compact_ticket
                    else f"d={self.oauth.access_token}"
                ),
            },
        }

        resp = await self.session.post(url, json=data, headers=headers)
        resp.raise_for_status()
        return await XAUResponse.from_response(resp)

    async def request_xsts_token(
        self,
    ) -> XSTSResponse:
        """Authorize via user token and receive final X token."""
        url = "https://xsts.auth.xboxlive.com/xsts/authorize"
        headers = {"x-xbl-contract-version": "1"}
        data = {
            "RelyingParty": self.relying_party,
            "TokenType": "JWT",
            "Properties": {
                "UserTokens": [self.user_token.token],
                "SandboxId": "RETAIL",
            },
        }

        resp = await self.session.post(url, json=data, headers=headers)
        resp.raise_for_status()
        return await XSTSResponse.from_response(resp)

    async def refresh_tokens(self, force_refresh: bool = False) -> None:
        """Refresh all tokens."""
        if force_refresh:
            self.oauth = await self.refresh_oauth_token()
            self.user_token = await self.request_user_token()
            self.xsts_token = await self.request_xsts_token()
        else:
            if not (self.oauth and self.oauth.is_valid()):
                self.oauth = await self.refresh_oauth_token()
            if not (self.user_token and self.user_token.is_valid()):
                self.user_token = await self.request_user_token()
            if not (self.xsts_token and self.xsts_token.is_valid()):
                self.xsts_token = await self.request_xsts_token()

    async def close(self) -> None:
        await self.session.aclose()


class MicrosoftAPIException(Exception):
    def __init__(self, resp: httpx.Response, error: Exception) -> None:
        self.resp = resp
        self.error = error

        super().__init__(
            "An error occured when trying to access this resource: code"
            f" {resp.status_code}.\nError: {error}"
        )


try:
    import orjson

    def _dumps_wrapper(obj: typing.Any) -> bytes:
        return orjson.dumps(obj)

except ImportError:
    encoder = msgspec.json.Encoder()

    def _dumps_wrapper(obj: typing.Any) -> bytes:
        return encoder.encode(obj)


async def should_retry(
    auth_mgr: AuthenticationManager, response: httpx.Response
) -> bool:
    if not response.is_error:
        return False

    if response.status_code == 401:
        await auth_mgr.refresh_tokens(force_refresh=True)
        return True

    return True


class BaseMicrosoftAPI(HandlerProtocol):
    RELYING_PATH: str = "http://xboxlive.com"
    BASE_URL: str = ""

    session: httpx.AsyncClient
    auth_mgr: AuthenticationManager

    def __init__(
        self, session: httpx.AsyncClient, auth_mgr: AuthenticationManager
    ) -> None:
        self.session = session
        self.auth_mgr = auth_mgr

    @classmethod
    async def from_oauth(
        cls, client_id: str, client_secret: str, oauth: OAuth2TokenResponse
    ) -> typing_ext.Self:
        transport = retry_transport.RetryTransport(
            wrapped_transport=httpx.AsyncHTTPTransport(http2=True, retries=2),
            jitter_ratio=0.3,
        )
        session = httpx.AsyncClient(transport=transport)
        auth_mgr = await AuthenticationManager.from_ouath(
            session, client_id, client_secret, cls.RELYING_PATH, oauth
        )

        session._transport._should_retry_async = functools.partial(should_retry, auth_mgr)  # type: ignore
        return cls(session, auth_mgr)

    @classmethod
    async def from_data(
        cls, client_id: str, client_secret: str, oauth_data: dict
    ) -> typing_ext.Self:
        transport = retry_transport.RetryTransport(
            wrapped_transport=httpx.AsyncHTTPTransport(http2=True, retries=2),
            jitter_ratio=0.3,
        )
        session = httpx.AsyncClient(transport=transport)
        auth_mgr = await AuthenticationManager.from_data(
            session, client_id, client_secret, cls.RELYING_PATH, oauth_data
        )

        session._transport._should_retry_async = functools.partial(should_retry, auth_mgr)  # type: ignore
        return cls(session, auth_mgr)

    @classmethod
    async def from_file(
        cls, client_id: str, client_secret: str, oauth_path: str = "oauth.json"
    ) -> typing_ext.Self:
        transport = retry_transport.RetryTransport(
            wrapped_transport=httpx.AsyncHTTPTransport(http2=True, retries=2),
            jitter_ratio=0.3,
        )
        session = httpx.AsyncClient(transport=transport)
        auth_mgr = await AuthenticationManager.from_file(
            session, client_id, client_secret, cls.RELYING_PATH, oauth_path
        )

        session._transport._should_retry_async = functools.partial(should_retry, auth_mgr)  # type: ignore
        return cls(session, auth_mgr)

    @property
    def base_headers(self) -> dict[str, str]:
        return {"Authorization": self.auth_mgr.xsts_token.authorization_header_value}

    async def close(self) -> None:
        await self.session.aclose()

    async def request(
        self,
        method: str,
        url: str,
        json: typing.Any = None,
        data: typing.Optional[dict] = None,
        params: typing.Optional[dict] = None,
        headers: typing.Optional[dict] = None,
        *,
        force_refresh: bool = False,
        dont_handle_ratelimit: bool = False,
        **kwargs: typing.Any,
    ) -> httpx.Response:
        if not headers:
            headers = {}
        if not params:
            params = {}

        # refresh token as needed
        await self.auth_mgr.refresh_tokens(force_refresh=force_refresh)

        if json:
            if data:
                raise ValueError("Cannot use both json and data.")

            kwargs["content"] = _dumps_wrapper(json)
            headers["Content-Type"] = "application/json"

        req_kwargs = {
            "method": method,
            "url": f"{self.BASE_URL}{url}",
            "headers": headers | self.base_headers,
            "data": data,
            "params": params,
        } | kwargs

        if dont_handle_ratelimit:
            req_kwargs["extensions"] = {"dont_handle_ratelimit": True}

        resp = await self.session.request(**req_kwargs)

        try:
            resp.raise_for_status()
            return resp
        except Exception as e:
            raise MicrosoftAPIException(resp, e) from e

    async def get(
        self,
        url: str,
        json: typing.Any = None,
        data: typing.Optional[dict] = None,
        params: typing.Optional[dict] = None,
        headers: typing.Optional[dict] = None,
        **kwargs: typing.Any,
    ) -> httpx.Response:
        return await self.request(
            "GET",
            url,
            json=json,
            data=data,
            params=params,
            headers=headers,
            **kwargs,
        )

    async def post(
        self,
        url: str,
        json: typing.Any = None,
        data: typing.Optional[dict] = None,
        params: typing.Optional[dict] = None,
        headers: typing.Optional[dict] = None,
        **kwargs: typing.Any,
    ) -> httpx.Response:
        return await self.request(
            "POST",
            url,
            json=json,
            data=data,
            params=params,
            headers=headers,
            **kwargs,
        )

    async def put(
        self,
        url: str,
        json: typing.Any = None,
        data: typing.Optional[dict] = None,
        params: typing.Optional[dict] = None,
        headers: typing.Optional[dict] = None,
        **kwargs: typing.Any,
    ) -> httpx.Response:
        return await self.request(
            "PUT",
            url,
            json=json,
            data=data,
            params=params,
            headers=headers,
            **kwargs,
        )

    async def delete(
        self,
        url: str,
        json: typing.Any = None,
        data: typing.Optional[dict] = None,
        params: typing.Optional[dict] = None,
        headers: typing.Optional[dict] = None,
        **kwargs: typing.Any,
    ) -> httpx.Response:
        return await self.request(
            "DELETE",
            url,
            json=json,
            data=data,
            params=params,
            headers=headers,
            **kwargs,
        )
