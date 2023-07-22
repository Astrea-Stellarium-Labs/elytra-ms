import asyncio
import typing

import aiohttp
import aiohttp_retry


class RTAHandler:
    session: aiohttp_retry.RetryClient

    async def _rta_start(
        self,
        url: str,
        dispatch_handler: typing.Callable[
            [aiohttp.WSMessage], typing.Awaitable[typing.Any]
        ],
    ) -> None:
        async with self.session._client.ws_connect(
            "wss://rta.xboxlive.com/connect"
        ) as ws:
            to_send = f'[1,1,"{url}"]'
            await ws.send_str(to_send)

            async for msg in ws:
                await dispatch_handler(msg)

    async def rta(
        self,
        url: str,
        dispatch_handler: typing.Callable[
            [aiohttp.WSMessage], typing.Awaitable[typing.Any]
        ],
    ) -> None:
        asyncio.create_task(self._rta_start(url, dispatch_handler))
