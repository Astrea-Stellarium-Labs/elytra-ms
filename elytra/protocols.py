import typing

import httpx


class HandlerProtocol(typing.Protocol):
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
        **kwargs: typing.Any,
    ) -> httpx.Response: ...

    async def get(
        self,
        url: str,
        json: typing.Any = None,
        data: typing.Optional[dict] = None,
        params: typing.Optional[dict] = None,
        headers: typing.Optional[dict] = None,
        **kwargs: typing.Any,
    ) -> httpx.Response: ...

    async def post(
        self,
        url: str,
        json: typing.Any = None,
        data: typing.Optional[dict] = None,
        params: typing.Optional[dict] = None,
        headers: typing.Optional[dict] = None,
        **kwargs: typing.Any,
    ) -> httpx.Response: ...

    async def put(
        self,
        url: str,
        json: typing.Any = None,
        data: typing.Optional[dict] = None,
        params: typing.Optional[dict] = None,
        headers: typing.Optional[dict] = None,
        **kwargs: typing.Any,
    ) -> httpx.Response: ...

    async def delete(
        self,
        url: str,
        json: typing.Any = None,
        data: typing.Optional[dict] = None,
        params: typing.Optional[dict] = None,
        headers: typing.Optional[dict] = None,
        **kwargs: typing.Any,
    ) -> httpx.Response: ...
