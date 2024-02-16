import functools
import traceback
import typing
from concurrent.futures import Future
from enum import IntEnum

import anyio
import httpx
import httpx_ws
import typing_extensions as typing_ext
from anyio.abc import TaskGroup

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
    def __init__(self, session: httpx.AsyncClient) -> None:
        raise NotImplementedError("RTA is not implemented with httpx yet.")

        self._rta_session: httpx.AsyncClient = session
        self._rta_ws: httpx_ws.AsyncWebSocketSession = None  # type: ignore
        self._rta_receive_tg: TaskGroup | None = None
        self.last_sequence_number = 0
        self.endpoint_maps: dict[
            int, typing.Callable[[list[typing.Any]], typing.Awaitable[typing.Any]]
        ] = {}
        self.subscribe_listeners: dict[
            int, typing.Callable[[list[typing.Any]], typing.Awaitable[typing.Any]]
        ] = {}

    @classmethod
    async def establish(cls, base_headers: dict[str, str]) -> typing_ext.Self:
        session = httpx.AsyncClient(headers=base_headers)
        rta = cls(session)
        await rta._connect()
        return rta

    async def _connect(self) -> None:
        self._rta_ws = await httpx_ws.aconnect_ws(
            "https://rta.xboxlive.com/connect", self._rta_session
        ).__aenter__()
        self._rta_receive_tg = await anyio.create_task_group().__aenter__()
        self._rta_receive_tg.start_soon(self._receive)

    async def _receive(self) -> None:
        while True:
            try:
                msg = await self._rta_ws.receive_text()
            except httpx_ws.WebSocketDisconnect:
                break
            except httpx_ws.WebSocketInvalidTypeReceived as e:
                raise ValueError("Invalid RTA") from e
            except httpx_ws.HTTPXWSException:
                break

            data: list[typing.Any] = _loads_wrapper(msg)

            try:
                if data[0] == RTAType.SUBSCRIBE:
                    await self.subscribe_listeners[data[1]](data)
                elif data[0] == RTAType.EVENT:
                    await self.endpoint_maps[data[1]](data)
            except Exception as e:
                traceback.print_exception(e)

    async def close(self) -> None:
        if self._rta_receive_tg:
            await self._rta_receive_tg.__aexit__(None, None, None)
        await self._rta_ws.close()
        await self._rta_session.aclose()

    async def subscribe(
        self,
        url: str,
        dispatch_handler: typing.Callable[
            [list[typing.Any]], typing.Awaitable[typing.Any]
        ],
    ) -> None:
        self.last_sequence_number += 1
        to_send = f'[{RTAType.SUBSCRIBE},{self.last_sequence_number},"{url}"]'

        future = Future()

        self.subscribe_listeners[self.last_sequence_number] = functools.partial(
            self._subscribe_handle, dispatch_handler, future
        )
        await self._rta_ws.send_text(to_send)

        future.result()

    async def unsubscribe(self, subscription_id: int) -> None:
        self.last_sequence_number += 1
        to_send = (
            f"[{RTAType.UNSUBSCRIBE},{self.last_sequence_number}, {subscription_id}]"
        )
        await self._rta_ws.send_text(to_send)
        self.endpoint_maps.pop(subscription_id, None)

    async def _subscribe_handle(
        self,
        new_dispatch_handle: typing.Callable[
            [list[typing.Any]], typing.Awaitable[typing.Any]
        ],
        future: Future,
        data: list[typing.Any],
    ) -> None:
        if len(data) != 5:
            if len(data) == 4:
                future.set_exception(ValueError(f"Invalid RTA: {data[3]}"))
            else:
                future.set_exception(ValueError(f"Invalid RTA: {data}"))

        self.endpoint_maps[data[3]] = new_dispatch_handle
        self.subscribe_listeners.pop(data[1], None)

        future.set_result(None)
