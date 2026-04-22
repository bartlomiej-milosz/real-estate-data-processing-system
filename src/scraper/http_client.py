import logging
from typing import Optional

import requests

from .config import HEADERS

logger = logging.getLogger(__name__)


class HttpClient:
    """Thin wrapper around requests.Session with consistent headers and logging."""

    def __init__(self, base_headers: Optional[dict[str, str]] = None) -> None:
        self.session = requests.Session()
        self.session.headers.update(base_headers or HEADERS)

    def get(self, url: str) -> Optional[str]:
        """Return decoded response body or None on failure."""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            response.encoding = "utf-8"
            return response.text
        except requests.RequestException as e:
            logger.error(f"HTTP request failed for {url}: {e}")
            return None

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
