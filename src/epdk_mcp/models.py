"""Pydantic veri modelleri."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class KurulKarariOzet(BaseModel):
    """Bir Kurul Kararı arama sonucu özeti (liste için)."""

    sayi: int | None = Field(None, description="Karar sayısı (örn. 13869)")
    tarih: date | None = Field(None, description="Karar tarihi (YYYY-MM-DD)")
    baslik: str = Field(..., description="Karar başlığı / konu özeti")
    url: str = Field(..., description="Karar detay sayfası URL'i")
    kategori: str | None = Field(None, description="Kategori ID (varsa)")
    rg_tarih: date | None = Field(None, description="Resmi Gazete yayım tarihi (varsa)")
    rg_sayi: str | None = Field(None, description="Resmi Gazete sayısı (varsa)")


class KurulKarariDetay(BaseModel):
    """Kurul Kararı tam detay."""

    sayi: int | None = None
    tarih: date | None = None
    baslik: str
    url: str
    kategori: str | None = None
    rg_tarih: date | None = None
    rg_sayi: str | None = None
    dayanak_kanun_madde: str | None = Field(
        None, description="Dayanılan kanun maddesi (örn. '6446 SK m.5')"
    )
    icerik_markdown: str = Field(..., description="Karar metni Markdown formatında")
    pdf_ekler: list[PdfEk] = Field(
        default_factory=list, description="PDF ek dosyalar (DownloadDocument linkleri)"
    )


class PdfEk(BaseModel):
    """Bir Kurul Kararına ek PDF dosyası."""

    baslik: str
    url: str
    metin_markdown: str | None = Field(None, description="PDF metni (parse edildiyse)")


class MevzuatOzet(BaseModel):
    """Yönetmelik / Tebliğ özeti."""

    tur: Literal["yonetmelik", "teblig", "usul_esas", "diger"]
    baslik: str
    url: str
    yayim_tarihi: date | None = None
    rg_sayi: str | None = None
    yururluk: Literal["yururlukte", "mulga", "kismi_mulga", "bilinmiyor"] = "bilinmiyor"
    son_degisiklik: date | None = None


class MevzuatDetay(BaseModel):
    """Tam mevzuat detay."""

    tur: Literal["yonetmelik", "teblig", "usul_esas", "diger"]
    baslik: str
    url: str
    yayim_tarihi: date | None = None
    rg_sayi: str | None = None
    yururluk: Literal["yururlukte", "mulga", "kismi_mulga", "bilinmiyor"] = "bilinmiyor"
    son_degisiklik: date | None = None
    icerik_markdown: str


class Kategori(BaseModel):
    """Kurul Kararı kategorisi."""

    kategori_id: str
    ad: str
    url: str
    arama_anahtari: str
    aciklama: str


class SayiTahmini(BaseModel):
    """Tarih → karar sayısı tahmini."""

    yil: int
    ay: int
    alt_sinir: int | None
    ust_sinir: int | None
    yaklasik: int | None
    kalibrasyon_kaynagi: str = Field(
        default="Linear interpolation between known calibration points",
        description="Tahmin yöntemi",
    )


class AramaSonucu(BaseModel):
    """Genel arama sonucu wrapper."""

    sorgu: str | None = None
    toplam_sonuc: int
    sonuclar: list[KurulKarariOzet] | list[MevzuatOzet]
    notlar: list[str] = Field(default_factory=list, description="Arama notları/uyarıları")
