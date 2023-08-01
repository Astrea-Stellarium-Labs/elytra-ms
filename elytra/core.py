import asyncio
import datetime
import functools
import typing

import aiohttp
import aiohttp_retry
import msgspec
import typing_extensions as typing_ext
from aiohttp import ClientResponse

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


class BetterResponse(aiohttp.ClientResponse):
    def raise_for_status(self) -> None:
        # i just dont want the resp to close lol
        if not self.ok:
            # reason should always be not None for a started response
            assert self.reason is not None  # noqa: S101
            raise aiohttp.ClientResponseError(
                self.request_info,
                self.history,
                status=self.status,
                message=self.reason,
                headers=self.headers,
            )


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


class ParsableBase:
    if typing.TYPE_CHECKING:
        _decoder: msgspec.json.Decoder[typing_ext.Self]

    @classmethod
    def from_data(cls, obj: dict) -> typing_ext.Self:
        return cls(**obj)

    @classmethod
    def from_bytes(cls, obj: bytes) -> typing_ext.Self:
        return cls._decoder.decode(obj)  # type: ignore

    @classmethod
    async def from_response(cls, resp: aiohttp.ClientResponse) -> typing_ext.Self:
        return cls.from_bytes(await resp.read())


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
    refresh_token: typing.Optional[str]
    user_id: str
    issued: datetime.datetime = msgspec.field(default_factory=utc_now)

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

    session: aiohttp_retry.RetryClient
    client_id: str
    client_secret: str
    relying_party: str

    oauth: OAuth2TokenResponse
    user_token: XAUResponse
    xsts_token: XSTSResponse

    def __init__(
        self,
        session: aiohttp_retry.RetryClient,
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
        session: aiohttp_retry.RetryClient,
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
        session: aiohttp_retry.RetryClient,
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
        session: aiohttp_retry.RetryClient,
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
        await self.session.close()


class MicrosoftAPIException(Exception):
    def __init__(self, resp: aiohttp.ClientResponse, error: Exception) -> None:
        self.resp = resp
        self.error = error

        super().__init__(
            "An error occured when trying to access this resource: code"
            f" {resp.status}.\nError: {error}"
        )


try:
    import orjson

    def _dumps_wrapper(obj: typing.Any) -> str:
        return orjson.dumps(obj).decode("utf-8")

except ImportError:
    encoder = msgspec.json.Encoder()

    def _dumps_wrapper(obj: typing.Any) -> str:
        return encoder.encode(obj).decode("utf-8")


class CustomRetry(aiohttp_retry.JitterRetry):
    def get_timeout(
        self, attempt: int, response: ClientResponse | None = None
    ) -> float:
        if not response:
            return super().get_timeout(attempt, response)

        if not response.ok and response.headers.get("Retry-After"):
            timeout = self._start_timeout
            self._start_timeout = 0.5
            result = super().get_timeout(attempt, response)
            self._start_timeout = timeout
            return result

        return super().get_timeout(attempt, response)


async def evaluate_response_callback(
    auth_mgr: AuthenticationManager, resp: aiohttp.ClientResponse
) -> bool:
    if resp.status == 401:
        await auth_mgr.refresh_tokens(force_refresh=True)
        return False

    if not resp.ok and (retry_after := resp.headers.get("Retry-After")):
        await asyncio.sleep(float(retry_after))
        return False
    return True


class BaseMicrosoftAPI(HandlerProtocol):
    RELYING_PATH: str = "http://xboxlive.com"
    BASE_URL: str = ""

    session: aiohttp_retry.RetryClient
    auth_mgr: AuthenticationManager

    def __init__(
        self, session: aiohttp_retry.RetryClient, auth_mgr: AuthenticationManager
    ) -> None:
        self.session = session
        self.auth_mgr = auth_mgr

    @classmethod
    async def from_oauth(
        cls, client_id: str, client_secret: str, oauth: OAuth2TokenResponse
    ) -> typing_ext.Self:
        session = aiohttp_retry.RetryClient(
            retry_options=CustomRetry(
                attempts=3,
                start_timeout=0.1,
                random_interval_size=0.35,
            ),
            response_class=BetterResponse,
            json_serialize=_dumps_wrapper,
        )
        auth_mgr = await AuthenticationManager.from_ouath(
            session, client_id, client_secret, cls.RELYING_PATH, oauth
        )
        session._retry_options.evaluate_response_callback = functools.partial(
            evaluate_response_callback, auth_mgr
        )
        return cls(session, auth_mgr)

    @classmethod
    async def from_data(
        cls, client_id: str, client_secret: str, oauth_data: dict
    ) -> typing_ext.Self:
        session = aiohttp_retry.RetryClient(
            retry_options=CustomRetry(
                attempts=3,
                start_timeout=0.1,
                random_interval_size=0.35,
            ),
            response_class=BetterResponse,
            json_serialize=_dumps_wrapper,
        )
        auth_mgr = await AuthenticationManager.from_data(
            session, client_id, client_secret, cls.RELYING_PATH, oauth_data
        )
        session._retry_options.evaluate_response_callback = functools.partial(
            evaluate_response_callback, auth_mgr
        )
        return cls(session, auth_mgr)

    @classmethod
    async def from_file(
        cls, client_id: str, client_secret: str, oauth_path: str = "oauth.json"
    ) -> typing_ext.Self:
        session = aiohttp_retry.RetryClient(
            retry_options=CustomRetry(
                attempts=3,
                start_timeout=0.1,
                random_interval_size=0.35,
            ),
            response_class=BetterResponse,
            json_serialize=_dumps_wrapper,
        )
        auth_mgr = await AuthenticationManager.from_file(
            session, client_id, client_secret, cls.RELYING_PATH, oauth_path
        )
        session._retry_options.evaluate_response_callback = functools.partial(
            evaluate_response_callback, auth_mgr
        )
        return cls(session, auth_mgr)

    @property
    def base_headers(self) -> dict[str, str]:
        return {"Authorization": self.auth_mgr.xsts_token.authorization_header_value}

    async def close(self) -> None:
        await self.session.close()

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
    ) -> aiohttp.ClientResponse:
        if not headers:
            headers = {}
        if not params:
            params = {}

        # refresh token as needed
        await self.auth_mgr.refresh_tokens(force_refresh=force_refresh)

        req_kwargs = {
            "method": method,
            "url": f"{self.BASE_URL}{url}",
            "headers": headers | self.base_headers,
            "json": json,
            "data": data,
            "params": params,
        } | kwargs
        if dont_handle_ratelimit:
            req_kwargs["retry_options"] = aiohttp_retry.JitterRetry(
                random_interval_size=0.2
            )

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
    ) -> aiohttp.ClientResponse:
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
    ) -> aiohttp.ClientResponse:
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
    ) -> aiohttp.ClientResponse:
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
    ) -> aiohttp.ClientResponse:
        return await self.request(
            "DELETE",
            url,
            json=json,
            data=data,
            params=params,
            headers=headers,
            **kwargs,
        )
