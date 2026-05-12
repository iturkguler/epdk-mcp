"""EPDK web sitesi için async client (Playwright tabanlı — JS-SPA desteği)."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from .exceptions import EpdkHttpError, EpdkRateLimitError

logger = logging.getLogger(__name__)


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}

DEFAULT_TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0)
DEFAULT_DELAY_SECONDS = 1.5
PLAYWRIGHT_WAIT_MS = 3000   # JS render için bekleme süresi (ms)
PLAYWRIGHT_TIMEOUT_MS = 30000


class EpdkClient:
    """epdk.gov.tr için async istemci.

    HTML sayfaları: Playwright (headless Chromium) ile JS render sonrası çeker.
    PDF dosyaları: httpx ile doğrudan indirir.
    """

    def __init__(
        self,
        *,
        delay_seconds: float = DEFAULT_DELAY_SECONDS,
        timeout: httpx.Timeout | None = None,
        max_retries: int = 3,
    ) -> None:
        self.delay_seconds = delay_seconds
        self.timeout = timeout or DEFAULT_TIMEOUT
        self.max_retries = max_retries
        self._last_request_at: float = 0.0

        # Playwright nesneleri — context manager ile yönetilir
        self._playwright: Any = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    @staticmethod
    def _install_chromium() -> None:
        """Chromium binary yoksa kurar (ilk çalıştırmada)."""
        import subprocess, sys
        logger.info("Playwright Chromium kurulumu başlatılıyor...")
        try:
            subprocess.run(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                check=True, capture_output=True,
            )
            logger.info("Playwright Chromium kuruldu.")
        except subprocess.CalledProcessError as e:
            logger.warning("Chromium kurulum hatası: %s", e.stderr.decode()[:200])

    async def __aenter__(self) -> EpdkClient:
        self._playwright = await async_playwright().start()
        try:
            self._browser = await self._playwright.chromium.launch(headless=True)
        except Exception:
            # Binary yok — kur ve tekrar dene
            await asyncio.get_event_loop().run_in_executor(None, self._install_chromium)
            self._browser = await self._playwright.chromium.launch(headless=True)
        self._context = await self._browser.new_context(
            user_agent=DEFAULT_HEADERS["User-Agent"],
            locale="tr-TR",
            extra_http_headers={"Accept-Language": DEFAULT_HEADERS["Accept-Language"]},
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def _respect_rate_limit(self) -> None:
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_at
        if elapsed < self.delay_seconds:
            await asyncio.sleep(self.delay_seconds - elapsed)
        self._last_request_at = asyncio.get_event_loop().time()

    async def get_html(self, url: str) -> str:
        """Playwright ile sayfayı render edip HTML döndürür.

        JS yüklenmesini bekler; içerik dolana kadar ek bekleme yapar.
        """
        if self._context is None:
            raise RuntimeError("EpdkClient context manager içinde kullanılmalıdır.")

        await self._respect_rate_limit()

        page: Page | None = None
        last_exc: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                page = await self._context.new_page()

                # Gereksiz kaynakları engelle (hız için)
                await page.route(
                    "**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf,otf}",
                    lambda route: route.abort(),
                )

                response = await page.goto(
                    url,
                    wait_until="networkidle",
                    timeout=PLAYWRIGHT_TIMEOUT_MS,
                )

                if response and response.status == 429:
                    raise EpdkRateLimitError(f"EPDK sitesi rate limit (429) — {url}")

                if response and response.status >= 400:
                    raise EpdkHttpError(
                        f"HTTP {response.status}: {url}",
                        status_code=response.status,
                        url=url,
                    )

                # JS render'ın tamamlanması için kısa bekleme
                await page.wait_for_timeout(PLAYWRIGHT_WAIT_MS)

                html = await page.content()
                await page.close()
                page = None
                return html

            except (EpdkRateLimitError, EpdkHttpError):
                raise
            except Exception as e:
                last_exc = EpdkHttpError(f"Playwright hatası: {url} ({e})", url=url)
                if page:
                    try:
                        await page.close()
                    except Exception:
                        pass
                    page = None
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2.0 * (attempt + 1))
                    continue
                raise last_exc from e

        if last_exc:
            raise last_exc
        raise EpdkHttpError(f"Beklenmedik hata: {url}", url=url)

    async def get_pdf_bytes(self, url: str) -> bytes:
        """PDF byte içeriği döndürür (httpx ile — Playwright gerekmez)."""
        await self._respect_rate_limit()

        async with httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            timeout=self.timeout,
            follow_redirects=True,
        ) as client:
            last_exc: Exception | None = None
            for attempt in range(self.max_retries):
                try:
                    response = await client.get(url)
                    if response.status_code == 429:
                        raise EpdkRateLimitError(f"Rate limit: {url}")
                    response.raise_for_status()
                    return response.content
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

            if last_exc:
                raise last_exc
            raise EpdkHttpError(f"Beklenmedik PDF hatası: {url}", url=url)
