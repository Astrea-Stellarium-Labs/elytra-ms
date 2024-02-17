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

import contextlib
import functools
import inspect
import secrets
import traceback
import typing
from enum import IntEnum

import anyio
from anyio.streams.stapled import StapledObjectStream
from anyio.streams.tls import TLSStream
from websockets.client import ClientProtocol
from websockets.frames import Frame, Opcode
from websockets.uri import parse_uri

__all__ = ("RTAType", "RTA")

try:
    import orjson

    def _loads_wrapper(json_input: str | bytes) -> typing.Any:
        return orjson.loads(json_input)

except ImportError:
    import msgspec

    decoder = msgspec.json.Decoder()

    def _loads_wrapper(json_input: str | bytes) -> typing.Any:
        return decoder.decode(json_input)


def _generate_id() -> bytes:
    return secrets.token_bytes()


class RTAType(IntEnum):
    SUBSCRIBE = 1
    UNSUBSCRIBE = 2
    EVENT = 3
    RSYNC = 4


PING_INTERVAL = 20.0
PING_TIMEOUT = 20.0


class RTA:
    def __init__(self, headers: dict | None = None) -> None:
        self._uri = parse_uri("wss://rta.xboxlive.com/connect")
        self._headers = headers or {}
        self._protocol = ClientProtocol(self._uri)
        self._stream: TLSStream | None = None

        self._tg = anyio.create_task_group()
        self._exit_stack = contextlib.AsyncExitStack()

        self._last_sequence_number = 0
        self._endpoint_maps: dict[
            int, typing.Callable[[list[typing.Any]], typing.Awaitable[typing.Any]]
        ] = {}
        self._subscribe_listeners: dict[
            int, typing.Callable[[list[typing.Any]], typing.Awaitable[typing.Any]]
        ] = {}
        self._stapled_stream_set: set[StapledObjectStream] = set()

        self._ping_tasks: dict[bytes, anyio.Event] = {}

    @classmethod
    async def establish(cls, headers: dict | None = None) -> typing.Self:
        self = cls(headers=headers)
        await self.connect()
        return self

    async def connect(self) -> None:
        self._stream = await anyio.connect_tcp(
            self._uri.host, self._uri.port, tls=True, tls_standard_compatible=False
        )

        request = self._protocol.connect()
        request.headers.update(self._headers)
        self._protocol.send_request(request)

        for data in self._protocol.data_to_send():
            await self._stream.send(data)

        try:
            data = await self._stream.receive()
        except anyio.EndOfStream:
            self._protocol.receive_eof()
            for data in self._protocol.data_to_send():
                await self._stream.send(data)

            raise ConnectionError("Connection closed.") from None

        self._protocol.receive_data(data)

        if self._protocol.handshake_exc is not None:
            raise self._protocol.handshake_exc

        await self._exit_stack.enter_async_context(self._tg)
        self._tg.start_soon(self._receive)
        self._tg.start_soon(self._send_ping)

    async def _receive(self) -> None:
        if not self._stream:
            raise ConnectionError("Stream hasn't been started yet.")

        try:
            while True:
                try:
                    data = await self._stream.receive()
                except anyio.EndOfStream:
                    self._protocol.receive_eof()
                    for data in self._protocol.data_to_send():
                        await self._stream.send(data)

                    await self.close()
                    raise ConnectionError("Received EOF.") from None
                except anyio.ClosedResourceError:
                    return

                self._protocol.receive_data(data)

                if self._protocol.handshake_exc is not None:
                    await self.close()
                    raise self._protocol.handshake_exc

                events = self._protocol.events_received()

                for event in events:
                    if isinstance(event, Frame):
                        if event.opcode == Opcode.CLOSE:
                            await self.close()
                            return

                        if event.opcode == Opcode.PING:
                            self._protocol.send_pong(event.data)
                            for data in self._protocol.data_to_send():
                                await self._stream.send(data)

                        elif (
                            event.opcode == Opcode.PONG
                            and bytes(event.data) in self._ping_tasks
                        ):
                            self._ping_tasks[bytes(event.data)].set()

                        elif event.opcode in {Opcode.BINARY, Opcode.TEXT}:
                            await self._handle_data(event.data)

        except anyio.get_cancelled_exc_class():
            return

        except Exception as e:
            traceback.print_exception(e)
            raise e

    async def _send_ping(self) -> None:
        if not self._stream:
            raise ConnectionError("Stream hasn't been started yet.")

        try:
            while True:
                await anyio.sleep(PING_INTERVAL)

                ping_id = _generate_id()
                self._ping_tasks[ping_id] = anyio.Event()

                self._protocol.send_ping(ping_id)
                for data in self._protocol.data_to_send():
                    await self._stream.send(data)

                with anyio.fail_after(PING_TIMEOUT):
                    await self._ping_tasks[ping_id].wait()
                    self._ping_tasks.pop(ping_id)

        except TimeoutError:
            print("Ping timeout.")  # noqa: T201
            await self.close()

        except anyio.get_cancelled_exc_class():
            return

        except Exception as e:
            traceback.print_exception(e)
            raise e

    async def _send_str(self, data: str) -> None:
        if not self._stream:
            raise ConnectionError("Connection closed.")

        self._protocol.send_text(data.encode())
        for data_to_send in self._protocol.data_to_send():
            await self._stream.send(data_to_send)

    async def _handle_data(self, data: bytes) -> None:
        if not self._stream:
            raise ConnectionError("Connection closed.")

        parsed_data: list[typing.Any] = _loads_wrapper(data)

        if parsed_data[0] == RTAType.SUBSCRIBE:
            await self._subscribe_listeners[parsed_data[1]](parsed_data)
        elif parsed_data[0] == RTAType.EVENT:
            self._tg.start_soon(self._endpoint_maps[parsed_data[1]], parsed_data)

    async def subscribe(
        self,
        url: str,
        dispatch_handler: typing.Callable[
            [list[typing.Any]], typing.Awaitable[typing.Any]
        ],
    ) -> None:
        if not inspect.iscoroutinefunction(dispatch_handler):
            raise ValueError("dispatch_handler must be a coroutine function.")

        url = url.removesuffix("/")
        self._last_sequence_number += 1
        to_send = f'[{RTAType.SUBSCRIBE},{self._last_sequence_number},"{url}"]'

        stapled_stream = StapledObjectStream(*anyio.create_memory_object_stream())

        self._subscribe_listeners[self._last_sequence_number] = functools.partial(
            self._subscribe_handle, dispatch_handler, stapled_stream
        )
        await self._send_str(to_send)

        self._stapled_stream_set.add(stapled_stream)

        try:
            data = await stapled_stream.receive()
        except (anyio.ClosedResourceError, anyio.EndOfStream):
            return

        self._stapled_stream_set.discard(stapled_stream)

        if isinstance(data, Exception):
            raise data

    async def unsubscribe(self, subscription_id: int) -> None:
        self._last_sequence_number += 1
        to_send = (
            f"[{RTAType.UNSUBSCRIBE},{self._last_sequence_number}, {subscription_id}]"
        )
        await self._send_str(to_send)
        self._endpoint_maps.pop(subscription_id, None)

    async def _subscribe_handle(
        self,
        new_dispatch_handle: typing.Callable[
            [list[typing.Any]], typing.Awaitable[typing.Any]
        ],
        stapled_stream: StapledObjectStream,
        data: list[typing.Any],
    ) -> None:
        if len(data) != 5:
            if len(data) == 4:
                await stapled_stream.send(ValueError(f"Invalid RTA: {data[3]}"))
            else:
                await stapled_stream.send(ValueError(f"Invalid RTA: {data}"))
            return

        self._endpoint_maps[data[3]] = new_dispatch_handle
        self._subscribe_listeners.pop(data[1], None)

        await stapled_stream.send(None)

    async def close(self) -> None:
        if self._stream is not None:
            await self._stream.aclose()
            self._stream = None

        for stream in self._stapled_stream_set:
            await stream.aclose()

        self._tg.cancel_scope.cancel()
        await self._exit_stack.aclose()
