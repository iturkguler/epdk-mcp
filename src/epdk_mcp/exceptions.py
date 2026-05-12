"""EPDK MCP exception sınıfları."""

from __future__ import annotations


class EpdkMcpError(Exception):
    """EPDK MCP base exception."""


class EpdkHttpError(EpdkMcpError):
    """EPDK web sitesine HTTP isteği başarısız."""

    def __init__(self, message: str, status_code: int | None = None, url: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.url = url


class EpdkParseError(EpdkMcpError):
    """EPDK sayfası beklenen formatta değil; parse hatası."""


class EpdkNotFoundError(EpdkMcpError):
    """Aranan karar/mevzuat bulunamadı."""


class EpdkRateLimitError(EpdkMcpError):
    """EPDK sitesi rate limit; bir süre beklenmesi gerekir."""
