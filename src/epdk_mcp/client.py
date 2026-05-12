"""EPDK web sitesi için async HTTP client."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from .exceptions import EpdkHttpError, EpdkRateLimitError

logger = logging.getLogger(__name__)


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; EpdkMCP/0.1; "
        "+https://github.com/legalenerji/epdk-mcp)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}

DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0)
DEFAULT_DELAY_SECONDS = 1.5  # nezaket için art arda isteklerde gecikme


class EpdkClient:
    """epdk.gov.tr için async HTTP istemci.

    Sayfa fetch + PDF download + rate limiting (nazik).
    """

    def __init__(
        self,
        *,
        delay_seconds: float = DEFAULT_DELAY_SECONDS,
        timeout: httpx.Timeout | None = None,
        headers: dict[str, str] | None = None,
        max_retries: int = 3,
    ) -> None:
        self.delay_seconds = delay_seconds
        self.timeout = timeout or DEFAULT_TIMEOUT
        self.headers = headers or DEFAULT_HEADERS
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None
        self._last_request_at: float = 0.0

    async def __aenter__(self) -> EpdkClient:
        self._client = httpx.AsyncClient(
            headers=self.headers,
            timeout=self.timeout,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers=self.headers,
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client

    async def _respect_rate_limit(self) -> None:
        """Son isteğin üzerinden delay_seconds geçmemişse bekle."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_at
        if elapsed < self.delay_seconds:
            await asyncio.sleep(self.delay_seconds - elapsed)
        self._last_request_at = asyncio.get_event_loop().time()

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        """GET isteği; rate limiting + retry uygular."""
        client = await self._ensure_client()
        await self._respect_rate_limit()

        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                response = await client.get(url, **kwargs)
                if response.status_code == 429:
                    raise EpdkRateLimitError(
                        f"EPDK sitesi rate limit (429) — {url}"
                    )
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                last_exc = EpdkHttpError(
                    f"HTTP {e.response.status_code}: {url}",
                    status_code=e.response.status_code,
                    url=url,
                )
                if e.response.status_code in (500, 502, 503, 504) and attempt < self.max_retries - 1:
                    await asyncio.sleep(2.0 * (attempt + 1))
                    continue
                raise last_exc from e
            except httpx.RequestError as e:
                last_exc = EpdkHttpError(f"İstek hatası: {url} ({e})", url=url)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2.0 * (attempt + 1))
                    continue
                raise last_exc from e

        # Buraya gelinmemeli ama tip güvenliği için
        if last_exc:
            raise last_exc
        raise EpdkHttpError(f"Beklenmedik hata: {url}", url=url)

    async def get_html(self, url: str) -> str:
        """HTML sayfasını metin olarak döndürür."""
        response = await self.get(url)
        return response.text

    async def get_pdf_bytes(self, url: str) -> bytes:
        """PDF byte içeriği döndürür."""
        response = await self.get(url)
        return response.content
