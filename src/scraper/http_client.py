import asyncio
import logging
from typing import Optional

import httpx
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from ..config import settings
from .config import HEADERS

logger = logging.getLogger(__name__)


class TransientHttpError(httpx.HTTPError):
    """5xx or 429 — worth retrying."""


def _is_transient(response: httpx.Response) -> bool:
    return response.status_code >= 500 or response.status_code == 429


class AsyncHttpClient:
    """Async httpx client with concurrency limit, retries, and per-request timeout."""

    def __init__(
        self,
        base_headers: Optional[dict[str, str]] = None,
        max_attempts: int | None = None,
        max_concurrent: int | None = None,
        timeout: float | None = None,
    ) -> None:
        self._headers = base_headers or HEADERS
        self._max_attempts = max_attempts or settings.http_max_attempts
        self._semaphore = asyncio.Semaphore(
            max_concurrent or settings.http_max_concurrent
        )
        self._client = httpx.AsyncClient(
            headers=self._headers,
            timeout=timeout or settings.http_timeout_seconds,
            follow_redirects=True,
        )

    async def get(self, url: str) -> Optional[str]:
        """Return decoded response body or None on permanent failure."""
        try:
            return await self._get_with_retry(url)
        except httpx.HTTPError as e:
            logger.error(f"HTTP request failed for {url}: {e}")
            return None

    async def _get_with_retry(self, url: str) -> str:
        retrying = retry(
            reraise=True,
            stop=stop_after_attempt(self._max_attempts),
            wait=wait_exponential_jitter(initial=1, max=30, jitter=2),
            retry=retry_if_exception_type(
                (TransientHttpError, httpx.ConnectError, httpx.TimeoutException)
            ),
            before_sleep=before_sleep_log(logger, logging.WARNING),
        )
        wrapped = retrying(self._do_get)
        return await wrapped(url)

    async def _do_get(self, url: str) -> str:
        async with self._semaphore:
            response = await self._client.get(url)
        if _is_transient(response):
            raise TransientHttpError(
                f"transient status {response.status_code} for {url}"
            )
        response.raise_for_status()
        return response.text

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncHttpClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()
