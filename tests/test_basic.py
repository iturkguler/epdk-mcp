"""Temel testler — parser ve URL fonksiyonları."""

from __future__ import annotations

from datetime import date

import pytest

from epdk_mcp.parsers import (
    extract_dayanak,
    extract_rg,
    extract_sayi_tarih,
    parse_tr_date,
)
from epdk_mcp.urls import KATEGORILER, tahmini_karar_sayisi


class TestParseTrDate:
    def test_dotted(self) -> None:
        assert parse_tr_date("16.10.2025") == date(2025, 10, 16)

    def test_slashed(self) -> None:
        assert parse_tr_date("16/10/2025") == date(2025, 10, 16)

    def test_dashed(self) -> None:
        assert parse_tr_date("16-10-2025") == date(2025, 10, 16)

    def test_invalid(self) -> None:
        assert parse_tr_date("garbage") is None
        assert parse_tr_date("") is None
        assert parse_tr_date("99.99.9999") is None


class TestExtractSayiTarih:
    def test_standart_format(self) -> None:
        text = "EPDK'nın 16/10/2025 tarihli ve 13869 sayılı Kurul Kararı"
        sayi, tarih = extract_sayi_tarih(text)
        assert sayi == 13869
        assert tarih == date(2025, 10, 16)

    def test_alternatif_format(self) -> None:
        text = "13869 sayılı Kurul Kararı 16.10.2025 tarihinde alınmıştır"
        sayi, tarih = extract_sayi_tarih(text)
        assert sayi == 13869
        assert tarih == date(2025, 10, 16)

    def test_sadece_sayi(self) -> None:
        text = "13869 sayılı Kurul Kararı"
        sayi, tarih = extract_sayi_tarih(text)
        assert sayi == 13869
        assert tarih is None

    def test_bos_metin(self) -> None:
        sayi, tarih = extract_sayi_tarih("")
        assert sayi is None
        assert tarih is None


class TestExtractRg:
    def test_kisaltma(self) -> None:
        text = "Resmi Gazete: 18.10.2025 tarihli ve 32750 sayılı"
        rg_tarih, rg_sayi = extract_rg(text)
        assert rg_tarih == date(2025, 10, 18)
        assert rg_sayi == "32750"


class TestExtractDayanak:
    def test_6446(self) -> None:
        text = "6446 sayılı Elektrik Piyasası Kanunu'nun 5 inci maddesi uyarınca..."
        dayanak = extract_dayanak(text)
        assert dayanak == "6446 SK m.5"

    def test_5346(self) -> None:
        text = "5346 sayılı Kanun'un 6 ncı maddesi gereğince..."
        dayanak = extract_dayanak(text)
        assert dayanak == "5346 SK m.6"


class TestKategoriler:
    def test_tum_kategoriler_geçerli_format(self) -> None:
        """Tüm kategoriler beklenen alan yapısına sahip."""
        for k_id, k in KATEGORILER.items():
            assert "ad" in k
            assert "url" in k
            assert "arama_anahtari" in k
            assert "aciklama" in k
            assert isinstance(k_id, str)
            assert k_id == k_id.lower()  # snake-case veya kebab-case

    def test_kritik_kategoriler_var(self) -> None:
        """Büro davaları için en kritik kategoriler tanımlı."""
        kritik = ["lisans", "onlisans", "lisanssiz", "tarife-dagitim", "duy",
                  "yekdem", "depolama", "para-cezasi", "baglanti", "kamulastirma"]
        for k in kritik:
            assert k in KATEGORILER, f"Kritik kategori eksik: {k}"


class TestTahminiSayisi:
    def test_bilinen_nokta(self) -> None:
        """Kalibrasyon noktasındaki ay → o sayıya yakın tahmin."""
        alt, ust, yaklasik = tahmini_karar_sayisi(2025, 10)
        assert yaklasik is not None
        assert 13700 <= yaklasik <= 14000

    def test_ara_deger(self) -> None:
        """İki kalibrasyon noktası arası interpolation."""
        alt, ust, yaklasik = tahmini_karar_sayisi(2024, 6)
        # 2024/03=12524, 2024/12=13115 arası → yaklaşık 12700-12900
        assert yaklasik is not None
        assert 12600 <= yaklasik <= 13000

    def test_ileri_tarih(self) -> None:
        """Son kalibrasyon noktasından sonraki tarih için ekstrapolasyon."""
        alt, ust, yaklasik = tahmini_karar_sayisi(2026, 6)
        assert yaklasik is not None
        # ~92 karar/ay × 8 ay = ~736 fark
        assert yaklasik > 13869


@pytest.mark.skip(reason="Canlı EPDK isteği gerektirir, CI'da skip")
async def test_canli_search_kurul_karari() -> None:
    """Canlı entegrasyon testi (manuel çalıştırma için)."""
    from epdk_mcp.server import search_kurul_karari

    sonuc = await search_kurul_karari(query="depolama", max_results=5)
    assert sonuc.toplam_sonuc >= 0
