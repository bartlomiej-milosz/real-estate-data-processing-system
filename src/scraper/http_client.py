import logging
from typing import Optional

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from .config import HEADERS

logger = logging.getLogger(__name__)


class TransientHttpError(requests.RequestException):
    """5xx or 429 — worth retrying."""


def _is_transient(response: requests.Response) -> bool:
    return response.status_code >= 500 or response.status_code == 429


class HttpClient:
    """requests.Session wrapper with consistent headers and bounded retries."""

    def __init__(
        self,
        base_headers: Optional[dict[str, str]] = None,
        max_attempts: int = 4,
    ) -> None:
        self.session = requests.Session()
        self.session.headers.update(base_headers or HEADERS)
        self._max_attempts = max_attempts

    def get(self, url: str) -> Optional[str]:
        """Return decoded response body or None on permanent failure."""
        try:
            return self._get_with_retry(url)
        except (requests.RequestException, TransientHttpError) as e:
            logger.error(f"HTTP request failed for {url}: {e}")
            return None

    def _get_with_retry(self, url: str) -> str:
        retrying = retry(
            reraise=True,
            stop=stop_after_attempt(self._max_attempts),
            wait=wait_exponential_jitter(initial=1, max=30, jitter=2),
            retry=retry_if_exception_type(
                (TransientHttpError, requests.ConnectionError, requests.Timeout)
            ),
            before_sleep=before_sleep_log(logger, logging.WARNING),
        )
        return retrying(self._do_get)(url)

    def _do_get(self, url: str) -> str:
        response = self.session.get(url, timeout=30)
        if _is_transient(response):
            raise TransientHttpError(
                f"transient status {response.status_code} for {url}"
            )
        response.raise_for_status()
        response.encoding = "utf-8"
        return response.text

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
