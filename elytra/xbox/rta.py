import asyncio
import functools
import traceback
import typing
from enum import IntEnum

import aiohttp
import typing_extensions as typing_ext

try:
    import orjson

    def _loads_wrapper(json_input: str | bytes) -> typing.Any:
        return orjson.loads(json_input)

except ImportError:
    import msgspec

    decoder = msgspec.json.Decoder()

    def _loads_wrapper(json_input: str | bytes) -> typing.Any:
        return decoder.decode(json_input)


class RTAType(IntEnum):
    SUBSCRIBE = 1
    UNSUBSCRIBE = 2
    EVENT = 3
    RSYNC = 4


class RTA:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._rta_session: aiohttp.ClientSession = session
        self._rta_ws: aiohttp.ClientWebSocketResponse = None  # type: ignore
        self._rta_receive_task: asyncio.Task | None = None
        self.last_sequence_number = 0
        self.endpoint_maps: dict[
            int, typing.Callable[[aiohttp.WSMessage], typing.Awaitable[typing.Any]]
        ] = {}
        self.subscribe_listeners: dict[
            int, typing.Callable[[aiohttp.WSMessage], typing.Awaitable[typing.Any]]
        ] = {}

    @classmethod
    async def establish(cls, base_headers: dict[str, str]) -> typing_ext.Self:
        session = aiohttp.ClientSession(headers=base_headers)
        rta = cls(session)
        await rta._connect()
        return rta

    async def _connect(self) -> None:
        self._rta_ws = await self._rta_session.ws_connect(
            "wss://rta.xboxlive.com/connect"
        )
        self._rta_receive_task = asyncio.create_task(self._receive())

    async def _receive(self) -> None:
        while True:
            msg = await self._rta_ws.receive()
            data: list[typing.Any] = msg.json(loads=_loads_wrapper)

            try:
                match msg.type:
                    case aiohttp.WSMsgType.TEXT:
                        if data[0] == RTAType.SUBSCRIBE:
                            await self.subscribe_listeners[data[1]](msg)
                        elif data[0] == RTAType.EVENT:
                            await self.endpoint_maps[data[1]](msg)
                    case aiohttp.WSMsgType.CLOSED:
                        break
                    case aiohttp.WSMsgType.ERROR:
                        break
                    case _:
                        raise ValueError(f"Invalid RTA: {msg}")
            except Exception as e:
                traceback.print_exception(e)

    async def close(self) -> None:
        if self._rta_receive_task:
            self._rta_receive_task.cancel()
        await self._rta_ws.close()
        await self._rta_session.close()

    async def subscribe(
        self,
        url: str,
        dispatch_handler: typing.Callable[
            [aiohttp.WSMessage], typing.Awaitable[typing.Any]
        ],
    ) -> None:
        self.last_sequence_number += 1
        to_send = f'[{RTAType.SUBSCRIBE},{self.last_sequence_number},"{url}"]'

        future = asyncio.Future()

        self.subscribe_listeners[self.last_sequence_number] = functools.partial(
            self._subscribe_handle, dispatch_handler, future
        )
        await self._rta_ws.send_str(to_send)

        await future

    async def unsubscribe(self, subscription_id: int) -> None:
        self.last_sequence_number += 1
        to_send = (
            f"[{RTAType.UNSUBSCRIBE},{self.last_sequence_number}, {subscription_id}]"
        )
        await self._rta_ws.send_str(to_send)
        self.endpoint_maps.pop(subscription_id, None)

    async def _subscribe_handle(
        self,
        new_dispatch_handle: typing.Callable[
            [aiohttp.WSMessage], typing.Awaitable[typing.Any]
        ],
        future: asyncio.Future,
        msg: aiohttp.WSMessage,
    ) -> None:
        data: list[typing.Any] = msg.json(loads=_loads_wrapper)

        if len(data) != 5:
            if len(data) == 4:
                future.set_exception(ValueError(f"Invalid RTA: {data[3]}"))
            else:
                future.set_exception(ValueError(f"Invalid RTA: {data}"))

        self.endpoint_maps[data[3]] = new_dispatch_handle
        self.subscribe_listeners.pop(data[1], None)

        future.set_result(None)
