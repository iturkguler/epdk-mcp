"""EPDK sayfa içeriği parser'ları (HTML + PDF)."""

from __future__ import annotations

import io
import logging
import re
from datetime import date, datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from markdownify import markdownify

from .exceptions import EpdkParseError
from .models import KurulKarariOzet, MevzuatOzet, PdfEk
from .urls import BASE_URL

logger = logging.getLogger(__name__)


# ============================================================================
# Tarih ve sayı çıkarımı için regex'ler
# ============================================================================

# "16/10/2025 tarihli ve 13869 sayılı" gibi ifadeler
SAYI_TARIH_PATTERN = re.compile(
    r"(\d{2}[/\.\-]\d{2}[/\.\-]\d{4})\s*tarih(?:li)?\s*ve\s*(\d{4,5})\s*sayılı",
    re.IGNORECASE,
)

# "13869 sayılı Kurul Kararı, 16.10.2025" alternatif format
SAYI_TARIH_PATTERN_ALT = re.compile(
    r"(\d{4,5})\s*sayılı.*?(\d{2}[/\.\-]\d{2}[/\.\-]\d{4})",
    re.IGNORECASE | re.DOTALL,
)

# Dayanak kanun: "6446 sayılı ... X uncu/inci maddesi"
DAYANAK_PATTERN = re.compile(
    r"(\d{4})\s*sayılı.*?(\d+)\s*(?:nci|ncı|uncu|üncü|inci|ıncı)\s*madde",
    re.IGNORECASE | re.DOTALL,
)

# RG: "Resmi Gazete... gg.aa.yyyy ... N sayılı"
RG_PATTERN = re.compile(
    r"(?:RG|Resm[iî] Gazete)[:\s].*?(\d{2}[\.\/\-]\d{2}[\.\/\-]\d{4}).*?(\d{4,6})",
    re.IGNORECASE,
)

# DownloadDocument linkleri
DOWNLOAD_PATTERN = re.compile(
    r"/Detay/DownloadDocument\?id=[^\"'\s>)]+",
    re.IGNORECASE,
)


def parse_tr_date(text: str) -> date | None:
    """'16.10.2025', '16/10/2025', '16-10-2025' formatlarını date'e çevirir."""
    if not text:
        return None
    text = text.strip().replace("/", ".").replace("-", ".")
    try:
        parts = text.split(".")
        if len(parts) != 3:
            return None
        gun, ay, yil = int(parts[0]), int(parts[1]), int(parts[2])
        return date(yil, ay, gun)
    except (ValueError, IndexError):
        return None


def extract_sayi_tarih(text: str) -> tuple[int | None, date | None]:
    """Metinden karar sayısı ve tarihini çıkarır."""
    if not text:
        return None, None

    # Önce "tarihli ve XX sayılı" formatı
    m = SAYI_TARIH_PATTERN.search(text)
    if m:
        return int(m.group(2)), parse_tr_date(m.group(1))

    # Sonra alternatif "XX sayılı ... tarihli" formatı
    m = SAYI_TARIH_PATTERN_ALT.search(text)
    if m:
        return int(m.group(1)), parse_tr_date(m.group(2))

    # Sadece sayı yakalamayı dene
    m = re.search(r"\b(\d{4,5})\s*sayılı", text, re.IGNORECASE)
    sayi = int(m.group(1)) if m else None

    # Sadece tarih yakalamayı dene
    m = re.search(r"(\d{2}[\.\/\-]\d{2}[\.\/\-]\d{4})", text)
    tarih = parse_tr_date(m.group(1)) if m else None

    return sayi, tarih


def extract_rg(text: str) -> tuple[date | None, str | None]:
    """Metinden RG tarih ve sayısını çıkarır."""
    if not text:
        return None, None
    m = RG_PATTERN.search(text)
    if not m:
        return None, None
    return parse_tr_date(m.group(1)), m.group(2)


def extract_dayanak(text: str) -> str | None:
    """'6446 SK m.5' formatında dayanak madde çıkarır."""
    if not text:
        return None
    m = DAYANAK_PATTERN.search(text)
    if not m:
        return None
    return f"{m.group(1)} SK m.{m.group(2)}"


def extract_download_links(html_or_soup: str | BeautifulSoup, base_url: str = BASE_URL) -> list[tuple[str, str]]:
    """HTML'den DownloadDocument linklerini ve etiketlerini çıkarır.

    Returns:
        [(baslik, tam_url), ...]
    """
    if isinstance(html_or_soup, str):
        soup = BeautifulSoup(html_or_soup, "lxml")
    else:
        soup = html_or_soup

    results: list[tuple[str, str]] = []
    seen_urls: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "DownloadDocument" not in href:
            continue
        full_url = urljoin(base_url, href)
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)
        baslik = a.get_text(strip=True) or "Belge"
        results.append((baslik, full_url))

    return results


# ============================================================================
# Liste sayfası parser'ları (kategori sayfasından karar listesi)
# ============================================================================

def parse_kurul_karari_listesi(
    html: str, base_url: str = BASE_URL, kategori: str | None = None
) -> list[KurulKarariOzet]:
    """Bir kategori/liste sayfasındaki Kurul Kararı satırlarını parse eder.

    EPDK liste sayfası tipik yapısı:
        <ul> veya <table> içinde başlık + tarih + link
        Bazen sadece <a> linkler düz liste halinde

    Bu fonksiyon esnek bir yaklaşımla tüm anchor'ları tarar ve karar
    sayısı/tarih ifadesi içeren olanları yakalar.
    """
    soup = BeautifulSoup(html, "lxml")
    sonuclar: list[KurulKarariOzet] = []
    seen_urls: set[str] = set()

    # 1) Ana içerik bölgesi: muhtemelen <main>, <article> veya class="content"
    icerik = (
        soup.find("main")
        or soup.find("article")
        or soup.find(class_=re.compile(r"icerik|content|detay", re.IGNORECASE))
        or soup
    )

    for a in icerik.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(separator=" ", strip=True)
        if not text or len(text) < 5:
            continue

        # Karar göstergesi: "sayılı" veya "Kurul Kararı" geçmeli
        if not ("sayılı" in text.lower() or "kurul kararı" in text.lower() or "karar" in text.lower()):
            # Karar göstergesi yoksa muhtemelen menü linki — atla
            continue

        # DownloadDocument doğrudan linklerini atla (bunlar ek dosya)
        if "DownloadDocument" in href:
            continue

        full_url = urljoin(base_url, href)
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        sayi, tarih = extract_sayi_tarih(text)
        rg_tarih, rg_sayi = extract_rg(text)

        sonuclar.append(
            KurulKarariOzet(
                sayi=sayi,
                tarih=tarih,
                baslik=text[:300],
                url=full_url,
                kategori=kategori,
                rg_tarih=rg_tarih,
                rg_sayi=rg_sayi,
            )
        )

    return sonuclar


def parse_mevzuat_listesi(
    html: str, tur: str = "yonetmelik", base_url: str = BASE_URL
) -> list[MevzuatOzet]:
    """Yönetmelik/Tebliğ listesi sayfasını parse eder."""
    soup = BeautifulSoup(html, "lxml")
    sonuclar: list[MevzuatOzet] = []
    seen_urls: set[str] = set()

    icerik = (
        soup.find("main")
        or soup.find("article")
        or soup.find(class_=re.compile(r"icerik|content|detay", re.IGNORECASE))
        or soup
    )

    for a in icerik.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(separator=" ", strip=True)
        if not text or len(text) < 10:
            continue

        # Tür uyumu için anahtar kelime
        if tur == "yonetmelik" and "yönetmelik" not in text.lower():
            continue
        if tur == "teblig" and "tebliğ" not in text.lower():
            continue

        full_url = urljoin(base_url, href)
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        # Mülga işareti kontrolü
        is_mulga = "mülga" in text.lower() or "(mülga)" in text.lower()
        yururluk = "mulga" if is_mulga else "yururlukte"

        sonuclar.append(
            MevzuatOzet(
                tur=tur,  # type: ignore[arg-type]
                baslik=text[:300],
                url=full_url,
                yururluk=yururluk,  # type: ignore[arg-type]
            )
        )

    return sonuclar


# ============================================================================
# Detay sayfası parser'ları
# ============================================================================

def parse_kurul_karari_detay(html: str, url: str, base_url: str = BASE_URL) -> dict:
    """Bir Kurul Kararı detay sayfasını parse eder.

    Returns dict (KurulKarariDetay'a dönüştürülebilir; pdf metinleri ayrı çekilir).
    """
    soup = BeautifulSoup(html, "lxml")

    # Ana içerik bölgesi
    icerik = (
        soup.find("main")
        or soup.find("article")
        or soup.find(class_=re.compile(r"icerik|content|detay", re.IGNORECASE))
        or soup.find("body")
        or soup
    )

    # Başlık
    h1 = icerik.find(["h1", "h2"])
    baslik = h1.get_text(strip=True) if h1 else "Başlıksız Kurul Kararı"
    if not baslik or len(baslik) < 5:
        # Title tag'inden dene
        title = soup.find("title")
        baslik = title.get_text(strip=True) if title else baslik

    # Tam metni topla (sayı/tarih/dayanak için)
    icerik_text = icerik.get_text(separator=" ", strip=True)

    sayi, tarih = extract_sayi_tarih(icerik_text)
    rg_tarih, rg_sayi = extract_rg(icerik_text)
    dayanak = extract_dayanak(icerik_text)

    # PDF ekleri
    download_links = extract_download_links(soup, base_url)
    pdf_ekler = [
        PdfEk(baslik=baslik_link, url=url_link, metin_markdown=None)
        for baslik_link, url_link in download_links
    ]

    # İçeriği Markdown'a dönüştür
    # Önce gereksiz elementleri at (script, style, nav, footer, header menü vb.)
    if isinstance(icerik, Tag):
        for tag in icerik.find_all(["script", "style", "nav", "footer"]):
            tag.decompose()
        # Menü class'larını da temizle
        for tag in icerik.find_all(class_=re.compile(r"menu|navbar|breadcrumb|footer|header", re.IGNORECASE)):
            tag.decompose()

    icerik_html = str(icerik)
    icerik_markdown = markdownify(icerik_html, heading_style="ATX", strip=["a"])
    # Aşırı boşlukları temizle
    icerik_markdown = re.sub(r"\n{3,}", "\n\n", icerik_markdown).strip()

    return {
        "sayi": sayi,
        "tarih": tarih,
        "baslik": baslik,
        "url": url,
        "rg_tarih": rg_tarih,
        "rg_sayi": rg_sayi,
        "dayanak_kanun_madde": dayanak,
        "icerik_markdown": icerik_markdown,
        "pdf_ekler": pdf_ekler,
    }


def parse_mevzuat_detay(html: str, url: str, tur: str = "yonetmelik") -> dict:
    """Yönetmelik/Tebliğ detay sayfasını parse eder."""
    soup = BeautifulSoup(html, "lxml")

    icerik = (
        soup.find("main")
        or soup.find("article")
        or soup.find(class_=re.compile(r"icerik|content|detay", re.IGNORECASE))
        or soup.find("body")
        or soup
    )

    h1 = icerik.find(["h1", "h2"])
    baslik = h1.get_text(strip=True) if h1 else "Başlıksız Mevzuat"

    icerik_text = icerik.get_text(separator=" ", strip=True)
    rg_tarih, rg_sayi = extract_rg(icerik_text)
    is_mulga = "mülga" in icerik_text.lower()
    yururluk = "mulga" if is_mulga else "yururlukte"

    if isinstance(icerik, Tag):
        for tag in icerik.find_all(["script", "style", "nav", "footer"]):
            tag.decompose()

    icerik_html = str(icerik)
    icerik_markdown = markdownify(icerik_html, heading_style="ATX", strip=["a"])
    icerik_markdown = re.sub(r"\n{3,}", "\n\n", icerik_markdown).strip()

    return {
        "tur": tur,
        "baslik": baslik,
        "url": url,
        "yayim_tarihi": rg_tarih,
        "rg_sayi": rg_sayi,
        "yururluk": yururluk,
        "icerik_markdown": icerik_markdown,
    }


# ============================================================================
# PDF parsing
# ============================================================================

def parse_pdf_metni(pdf_bytes: bytes, max_chars: int = 100000) -> str:
    """PDF byte'larını text'e çevirir (pypdf ile).

    OCR gerekirse ocr.py'deki Mistral fallback kullanılır (opsiyonel).
    """
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise EpdkParseError(f"pypdf yüklü değil: {e}") from e

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        metinler: list[str] = []
        total_chars = 0
        for sayfa in reader.pages:
            metin = sayfa.extract_text() or ""
            metinler.append(metin)
            total_chars += len(metin)
            if total_chars >= max_chars:
                break

        sonuc = "\n\n".join(metinler).strip()

        # Eğer çıkan metin çok kısa veya boş ise taranmış PDF olabilir
        if len(sonuc) < 50:
            logger.warning(
                "PDF metin çıkarımı çok kısa (%d karakter); OCR gerekebilir.",
                len(sonuc),
            )

        return sonuc[:max_chars]
    except Exception as e:
        raise EpdkParseError(f"PDF parse hatası: {e}") from e
