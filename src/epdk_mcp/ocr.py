"""Opsiyonel Mistral OCR — taranmış PDF'lerden metin çıkarımı için.

Kullanım: MISTRAL_API_KEY environment variable set edildiyse otomatik fallback.
Kurulum: pip install epdk-mcp[ocr]
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def mistral_ocr_available() -> bool:
    """Mistral OCR kullanılabilir mi (paket + API key kontrol)."""
    if not os.getenv("MISTRAL_API_KEY"):
        return False
    try:
        import mistralai  # noqa: F401
        return True
    except ImportError:
        return False


async def ocr_pdf_with_mistral(pdf_bytes: bytes) -> str:
    """Mistral OCR ile PDF'i text'e çevir.

    Çağıran kod önce mistral_ocr_available() ile kontrol etmeli.
    """
    if not mistral_ocr_available():
        raise RuntimeError(
            "Mistral OCR mevcut değil. "
            "MISTRAL_API_KEY env var set edin ve `pip install epdk-mcp[ocr]` yapın."
        )

    try:
        from mistralai import Mistral
    except ImportError as e:
        raise RuntimeError(f"mistralai paketi yüklü değil: {e}") from e

    api_key = os.getenv("MISTRAL_API_KEY")
    client = Mistral(api_key=api_key)

    # Mistral OCR API'ye PDF gönder
    # NOT: Mistral OCR API spec'i değişebilir; bu fonksiyon başlangıç noktasıdır.
    # Güncel API için: https://docs.mistral.ai/capabilities/document/
    import base64

    pdf_b64 = base64.b64encode(pdf_bytes).decode("ascii")

    try:
        response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_base64",
                "document_base64": pdf_b64,
            },
        )
        # Tüm sayfaların metnini birleştir
        sayfa_metinleri = []
        for page in response.pages:
            sayfa_metinleri.append(page.markdown)
        return "\n\n".join(sayfa_metinleri)
    except Exception as e:
        logger.exception("Mistral OCR hatası")
        raise RuntimeError(f"Mistral OCR API hatası: {e}") from e
