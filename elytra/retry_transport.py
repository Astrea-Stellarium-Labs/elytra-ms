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

import random
import time
from collections.abc import Callable, Coroutine, Iterable, Mapping
from datetime import datetime
from functools import partial
from http import HTTPStatus
from typing import Any, Union

import anyio
import httpx
from dateutil.parser import isoparse


# Adapted from https://github.com/encode/httpx/issues/108#issuecomment-1434439481
class RetryTransport(httpx.AsyncBaseTransport, httpx.BaseTransport):
    """
    A custom HTTP transport that automatically retries requests using an exponential backoff strategy
    for specific HTTP status codes and request methods.

    Args:
        wrapped_transport (Union[httpx.BaseTransport, httpx.AsyncBaseTransport]): The underlying HTTP transport
            to wrap and use for making requests.
        max_attempts (int, optional): The maximum number of times to retry a request before giving up. Defaults to 10.
        max_backoff_wait (float, optional): The maximum time to wait between retries in seconds. Defaults to 60.
        backoff_factor (float, optional): The factor by which the wait time increases with each retry attempt.
            Defaults to 0.1.
        jitter_ratio (float, optional): The amount of jitter to add to the backoff time. Jitter is a random
            value added to the backoff time to avoid a "thundering herd" effect. The value should be between 0 and 0.5.
            Defaults to 0.1.
        respect_retry_after_header (bool, optional): Whether to respect the Retry-After header in HTTP responses
            when deciding how long to wait before retrying. Defaults to True.
        retryable_methods (Iterable[str], optional): The HTTP methods that can be retried. Defaults to
            ["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE"].
        retry_status_codes (Iterable[int], optional): The HTTP status codes that can be retried. Defaults to
            [429, 502, 503, 504].

    Attributes:
        _wrapped_transport (Union[httpx.BaseTransport, httpx.AsyncBaseTransport]): The underlying HTTP transport
            being wrapped.
        _max_attempts (int): The maximum number of times to retry a request.
        _backoff_factor (float): The factor by which the wait time increases with each retry attempt.
        _respect_retry_after_header (bool): Whether to respect the Retry-After header in HTTP responses.
        _retryable_methods (frozenset): The HTTP methods that can be retried.
        _retry_status_codes (frozenset): The HTTP status codes that can be retried.
        _jitter_ratio (float): The amount of jitter to add to the backoff time.
        _max_backoff_wait (float): The maximum time to wait between retries in seconds.

    """

    RETRYABLE_METHODS = frozenset(["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE"])
    RETRYABLE_STATUS_CODES = frozenset(
        [
            HTTPStatus.TOO_MANY_REQUESTS,
            HTTPStatus.BAD_GATEWAY,
            HTTPStatus.SERVICE_UNAVAILABLE,
            HTTPStatus.GATEWAY_TIMEOUT,
        ]
    )
    MAX_BACKOFF_WAIT = 30

    def __init__(
        self,
        wrapped_transport: Union[httpx.BaseTransport, httpx.AsyncBaseTransport],
        max_attempts: int = 3,
        max_backoff_wait: float = MAX_BACKOFF_WAIT,
        backoff_factor: float = 0.1,
        jitter_ratio: float = 0.1,
        respect_retry_after_header: bool = True,
        retryable_methods: Iterable[str] | None = None,
        retry_status_codes: Iterable[int] | None = None,
        logger: Any | None = None,
    ) -> None:
        """
        Initializes the instance of RetryTransport class with the given parameters.

        Args:
            wrapped_transport (Union[httpx.BaseTransport, httpx.AsyncBaseTransport]):
                The transport layer that will be wrapped and retried upon failure.
            max_attempts (int, optional):
                The maximum number of times the request can be retried in case of failure.
                Defaults to 3.
            max_backoff_wait (float, optional):
                The maximum amount of time (in seconds) to wait before retrying a request.
                Defaults to 30.
            backoff_factor (float, optional):
                The factor by which the waiting time will be multiplied in each retry attempt.
                Defaults to 0.1.
            jitter_ratio (float, optional):
                The ratio of randomness added to the waiting time to prevent simultaneous retries.
                Should be between 0 and 0.5. Defaults to 0.1.
            respect_retry_after_header (bool, optional):
                A flag to indicate if the Retry-After header should be respected.
                If True, the waiting time specified in Retry-After header is used for the waiting time.
                Defaults to True.
            retryable_methods (Iterable[str], optional):
                The HTTP methods that can be retried. Defaults to ['HEAD', 'GET', 'PUT', 'DELETE', 'OPTIONS', 'TRACE'].
            retry_status_codes (Iterable[int], optional):
                The HTTP status codes that can be retried.
                Defaults to [429, 502, 503, 504].
            logger (Any): The logger to use for logging retries.
        """
        self._wrapped_transport = wrapped_transport
        if jitter_ratio < 0 or jitter_ratio > 0.5:
            raise ValueError(
                f"Jitter ratio should be between 0 and 0.5, actual {jitter_ratio}"
            )

        self._max_attempts = max_attempts
        self._backoff_factor = backoff_factor
        self._respect_retry_after_header = respect_retry_after_header
        self._retryable_methods = (
            frozenset(retryable_methods)
            if retryable_methods
            else self.RETRYABLE_METHODS
        )
        self._retry_status_codes = (
            frozenset(retry_status_codes)
            if retry_status_codes
            else self.RETRYABLE_STATUS_CODES
        )
        self._jitter_ratio = jitter_ratio
        self._max_backoff_wait = max_backoff_wait
        self._logger = logger

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        """
        Sends an HTTP request, possibly with retries.

        Args:
            request (httpx.Request): The request to send.

        Returns:
            httpx.Response: The response received.

        """
        transport: httpx.BaseTransport = self._wrapped_transport  # type: ignore
        if request.method in self._retryable_methods:
            send_method = partial(transport.handle_request)
            response = self._retry_operation(request, send_method)
        else:
            response = transport.handle_request(request)
        return response

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """Sends an HTTP request, possibly with retries.

        Args:
            request: The request to perform.

        Returns:
            The response.

        """
        transport: httpx.AsyncBaseTransport = self._wrapped_transport  # type: ignore
        if self._is_retryable_method(request):
            send_method = partial(transport.handle_async_request)
            response = await self._retry_operation_async(request, send_method)
        else:
            response = await transport.handle_async_request(request)
        return response

    async def aclose(self) -> None:
        """
        Closes the underlying HTTP transport, terminating all outstanding connections and rejecting any further
        requests.

        This should be called before the object is dereferenced, to ensure that connections are properly cleaned up.
        """
        transport: httpx.AsyncBaseTransport = self._wrapped_transport  # type: ignore
        await transport.aclose()

    def close(self) -> None:
        """
        Closes the underlying HTTP transport, terminating all outstanding connections and rejecting any further
        requests.

        This should be called before the object is dereferenced, to ensure that connections are properly cleaned up.
        """
        transport: httpx.BaseTransport = self._wrapped_transport  # type: ignore
        transport.close()

    def _is_retryable_method(self, request: httpx.Request) -> bool:
        return request.method in self._retryable_methods

    def _should_retry(self, response: httpx.Response) -> bool:
        return response.status_code in self._retry_status_codes

    def _log_failure(
        self,
        request: httpx.Request,
        sleep_time: float,
        response: httpx.Response | None,
        error: Exception | None,
    ) -> None:
        if self._logger and response:
            self._logger.warning(
                f"Request {request.method} {request.url} failed with status code:"
                f" {response.status_code}, retrying in {sleep_time} seconds."  # noqa: F821
            )
        elif self._logger and error:
            self._logger.warning(
                f"Request {request.method} {request.url} failed with exception:"
                f" {type(error).__name__} - {str(error) or 'No error message'},"
                f" retrying in {sleep_time} seconds."
            )

    async def _should_retry_async(self, response: httpx.Response) -> bool:
        return response.status_code in self._retry_status_codes

    def _calculate_sleep(
        self, attempts_made: int, headers: Union[httpx.Headers, Mapping[str, str]]
    ) -> float:
        # Retry-After
        # The Retry-After response HTTP header indicates how long the user agent should wait before
        # making a follow-up request. There are three main cases this header is used:
        # - When sent with a 503 (Service Unavailable) response, this indicates how long the service
        #   is expected to be unavailable.
        # - When sent with a 429 (Too Many Requests) response, this indicates how long to wait before
        #   making a new request.
        # - When sent with a redirect response, such as 301 (Moved Permanently), this indicates the
        #   minimum time that the user agent is asked to wait before issuing the redirected request.
        retry_after_header = (headers.get("Retry-After") or "").strip()
        if self._respect_retry_after_header and retry_after_header:
            if retry_after_header.isdigit():
                return float(retry_after_header)

            try:
                parsed_date = isoparse(
                    retry_after_header
                ).astimezone()  # converts to local time
                diff = (parsed_date - datetime.now().astimezone()).total_seconds()
                if diff > 0:
                    return min(diff, self._max_backoff_wait)
            except ValueError:
                pass

        backoff = self._backoff_factor * (2 ** (attempts_made - 1))
        jitter = (backoff * self._jitter_ratio) * random.choice([1, -1])  # noqa: S311
        total_backoff = backoff + jitter
        return min(total_backoff, self._max_backoff_wait)

    async def _retry_operation_async(
        self,
        request: httpx.Request,
        send_method: Callable[..., Coroutine[Any, Any, httpx.Response]],
    ) -> httpx.Response:
        remaining_attempts = self._max_attempts
        attempts_made = 0
        response: httpx.Response | None = None
        error: Exception | None = None

        while True:
            if attempts_made > 0:
                sleep_time = self._calculate_sleep(
                    attempts_made, response.headers if response else {}
                )
                self._log_failure(request, sleep_time, response, error)
                await anyio.sleep(sleep_time)

            error = None
            response = None
            try:
                response = await send_method(request)
                response.request = request
                if remaining_attempts < 1 or not (
                    await self._should_retry_async(response)
                ):
                    return response
                await response.aclose()
            except httpx.HTTPError as e:
                error = e
                if remaining_attempts < 1:
                    raise
            attempts_made += 1
            remaining_attempts -= 1

    def _retry_operation(
        self,
        request: httpx.Request,
        send_method: Callable[..., httpx.Response],
    ) -> httpx.Response:
        remaining_attempts = self._max_attempts
        attempts_made = 0
        response: httpx.Response | None = None
        error: Exception | None = None
        while True:
            if attempts_made > 0:
                sleep_time = self._calculate_sleep(
                    attempts_made, response.headers if response else {}
                )
                self._log_failure(request, sleep_time, response, error)
                time.sleep(sleep_time)

            error = None
            response = None
            try:
                response = send_method(request)
                response.request = request
                if remaining_attempts < 1 or not self._should_retry(response):
                    return response
                response.close()
            except httpx.HTTPError as e:
                error = e
                if remaining_attempts < 1:
                    raise
            attempts_made += 1
            remaining_attempts -= 1
