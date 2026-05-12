"""EPDK MCP FastMCP server."""

from __future__ import annotations

import logging
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from .client import EpdkClient
from .exceptions import EpdkMcpError, EpdkNotFoundError
from .models import (
    AramaSonucu,
    Kategori,
    KurulKarariDetay,
    KurulKarariOzet,
    MevzuatDetay,
    MevzuatOzet,
    PdfEk,
    SayiTahmini,
)
from .parsers import (
    parse_fast_access_models,
    parse_kurul_karari_detay,
    parse_kurul_karari_listesi,
    parse_mevzuat_detay,
    parse_mevzuat_listesi,
    parse_pdf_metni,
)
from .urls import (
    ANA_URLLER,
    KATEGORILER,
    YONETMELIK_TAM_AD,
    tahmini_karar_sayisi as _tahmini_karar_sayisi,
)

logger = logging.getLogger(__name__)


mcp = FastMCP(
    name="EPDK MCP",
    instructions=(
        "Türk Enerji Piyasası Düzenleme Kurumu (EPDK) elektrik piyasası mevzuatı "
        "ve Kurul Kararları için MCP server. epdk.gov.tr üzerinden canlı arama "
        "ve içerik çekme yapar. 2002'den günümüze tüm Kurul Kararlarını kapsar."
    ),
)


# ============================================================================
# Tool 1: list_kategoriler
# ============================================================================

@mcp.tool()
async def list_kategoriler() -> list[Kategori]:
    """EPDK elektrik piyasası Kurul Kararı kategorilerini listeler.

    Returns:
        Tarife, Lisans, Bağlantı, Lisanssız, YEKDEM, DUY, Depolama vb.
        kategorilerin tam listesi.
    """
    return [
        Kategori(
            kategori_id=kategori_id,
            ad=k["ad"],
            url=k["url"],
            arama_anahtari=k["arama_anahtari"],
            aciklama=k["aciklama"],
        )
        for kategori_id, k in KATEGORILER.items()
    ]


# ============================================================================
# Tool 2: search_kurul_karari
# ============================================================================

@mcp.tool()
async def search_kurul_karari(
    query: Annotated[
        str | None,
        Field(description="Anahtar kelime (örn. 'depolamalı önlisans', 'lisans iptal')"),
    ] = None,
    sayi: Annotated[
        int | None,
        Field(description="Karar sayısı (örn. 13869). Verilirse doğrudan o karara odaklanır."),
    ] = None,
    kategori: Annotated[
        str | None,
        Field(
            description=(
                "Kategori ID. Geçerli değerler: tarife-dagitim, tarife-iletim, "
                "tarife-perakende, tarife-son-kaynak, lisans, onlisans, lisanssiz, "
                "baglanti, duy, yekdem, depolama, para-cezasi, hizmet-kalitesi, "
                "kamulastirma, osos, bildirim, lisans-bedeli, siber-guvenlik. "
                "Tam liste için list_kategoriler() çağırın."
            ),
        ),
    ] = None,
    max_results: Annotated[
        int,
        Field(description="Maksimum sonuç sayısı (1-50)", ge=1, le=50),
    ] = 10,
) -> AramaSonucu:
    """EPDK elektrik piyasası Kurul Kararlarını arar.

    Üç arama modu:
    1. **Sayı** ile: `sayi=13869` → o spesifik karara odaklanır
    2. **Kategori** ile: `kategori="tarife-dagitim"` → kategori sayfasındaki kararlar
    3. **Query** ile: `query="depolamalı önlisans"` → kategoriler arası anahtar kelime taraması

    Combineler de mümkündür (örn. kategori + query birlikte).
    """
    notlar: list[str] = []
    sonuclar: list[KurulKarariOzet] = []

    async with EpdkClient() as client:
        # Tüm kararları GetFastAccessList API ile çek (Playwright + browser context)
        liste_url = ANA_URLLER["kurul_kararlari_eski"]

        # Mod 1: Sayı verildi → tüm listeyi çek, sayıya göre filtrele
        if sayi is not None:
            models = await client.get_fast_access_data(liste_url)
            tum_kararlar = parse_fast_access_models(models)
            for k in tum_kararlar:
                if k.sayi == sayi:
                    sonuclar.append(k)
            if not sonuclar:
                notlar.append(
                    f"{sayi} sayılı karar EPDK listesinde bulunamadı. "
                    "Karar çok eski olabilir (liste son kararları gösteriyor) "
                    "veya sayı farklı bir formatta olabilir. "
                    "Doğrudan https://www.epdk.gov.tr üzerinden arama yapabilirsiniz."
                )

        # Mod 2: Kategori verildi → aynı liste URL'inden çek (kategori mevcutsa)
        elif kategori is not None:
            if kategori not in KATEGORILER:
                notlar.append(
                    f"Bilinmeyen kategori: '{kategori}'. "
                    f"Geçerli kategoriler: {', '.join(sorted(KATEGORILER.keys()))}"
                )
            else:
                models = await client.get_fast_access_data(liste_url)
                tum_kararlar = parse_fast_access_models(models, kategori=kategori)
                query_lower = query.lower() if query else None
                # Kategori anahtar kelimesiyle filtrele
                arama_anahtari = KATEGORILER[kategori]["arama_anahtari"].lower()
                sonuclar = [
                    k for k in tum_kararlar
                    if any(
                        kw in k.baslik.lower()
                        for kw in arama_anahtari.split()
                        if len(kw) > 3
                    )
                ]
                if query_lower:
                    sonuclar = [s for s in sonuclar if query_lower in s.baslik.lower()]
                if not sonuclar:
                    # Keyword filtresi çok kısıtlayıcı olabilir — query varsa direkt uygula
                    if query_lower:
                        sonuclar = [k for k in tum_kararlar if query_lower in k.baslik.lower()]
                    else:
                        sonuclar = tum_kararlar
                    notlar.append(
                        f"'{kategori}' kategorisi için anahtar kelime eşleşmesi bulunamadı; "
                        "tüm liste döndürülüyor."
                    )

        # Mod 3: Sadece query verildi → liste genelinde arama
        elif query is not None:
            models = await client.get_fast_access_data(liste_url)
            tum_kararlar = parse_fast_access_models(models)
            query_lower = query.lower()
            sonuclar = [k for k in tum_kararlar if query_lower in k.baslik.lower()]
            if not sonuclar:
                notlar.append(
                    "Anahtar kelime eşleşmesi bulunamadı. "
                    "Karar başlıklarında Türkçe karakter ve kısaltmaya dikkat edin. "
                    "Farklı terimle tekrar deneyin veya kategori parametresi kullanın."
                )

        # Hiç parametre yok → son kararları döndür
        else:
            models = await client.get_fast_access_data(liste_url)
            sonuclar = parse_fast_access_models(models)
            notlar.append(
                "Filtre verilmedi; EPDK kurul kararları listesi döndürülüyor."
            )

    sonuclar = sonuclar[:max_results]
    return AramaSonucu(
        sorgu=query or (f"sayı={sayi}" if sayi else (kategori or "")),
        toplam_sonuc=len(sonuclar),
        sonuclar=sonuclar,
        notlar=notlar,
    )


# ============================================================================
# Tool 3: get_kurul_karari
# ============================================================================

@mcp.tool()
async def get_kurul_karari(
    karar_url: Annotated[
        str,
        Field(
            description=(
                "Karar detay sayfası URL'i (https://www.epdk.gov.tr/... ile başlar). "
                "search_kurul_karari sonuçlarından alınır."
            )
        ),
    ],
    include_pdf_text: Annotated[
        bool,
        Field(description="PDF eklerin metin içeriği çıkarılsın mı"),
    ] = True,
    max_pdf_chars: Annotated[
        int,
        Field(
            description="Her PDF için maksimum karakter (büyük PDF'lerde kesim için)",
            ge=1000,
            le=200000,
        ),
    ] = 50000,
) -> KurulKarariDetay:
    """Bir Kurul Kararının tam metnini Markdown formatında getirir.

    İçerik:
    - HTML sayfa metni (Markdown'a dönüştürülmüş)
    - Karar sayısı, tarih, dayanak kanun maddesi
    - PDF ekler (varsa, metin içeriği `include_pdf_text=True` ise çıkarılır)
    - RG yayım bilgisi (varsa)
    """
    if not karar_url.startswith("http"):
        raise ValueError(f"karar_url tam URL olmalı: {karar_url}")

    async with EpdkClient() as client:
        # DownloadDocument URL'leri direkt PDF'dir
        if "DownloadDocument" in karar_url:
            pdf_bytes = await client.get_pdf_bytes(karar_url)
            metin = parse_pdf_metni(pdf_bytes, max_chars=max_pdf_chars)
            # PDF metninden meta bilgi çıkar
            from .parsers import extract_sayi_tarih, extract_rg, extract_dayanak
            sayi, tarih = extract_sayi_tarih(metin)
            rg_tarih, rg_sayi = extract_rg(metin)
            dayanak = extract_dayanak(metin)
            # Başlık: ilk anlamlı satır
            baslik_satir = next(
                (ln.strip() for ln in metin.split("\n") if len(ln.strip()) > 20), "Kurul Kararı"
            )
            return KurulKarariDetay(
                sayi=sayi,
                tarih=tarih,
                baslik=baslik_satir[:200],
                url=karar_url,
                rg_tarih=rg_tarih,
                rg_sayi=rg_sayi,
                dayanak_kanun_madde=dayanak,
                icerik_markdown=metin,
                pdf_ekler=[PdfEk(baslik="Karar PDF", url=karar_url, metin_markdown=metin)],
            )

        # HTML sayfa (eski tip URL)
        html = await client.get_html(karar_url)
        detay_dict = parse_kurul_karari_detay(html, karar_url)

        # PDF metin çıkarımı
        if include_pdf_text and detay_dict["pdf_ekler"]:
            for pdf_ek in detay_dict["pdf_ekler"]:
                try:
                    pdf_bytes = await client.get_pdf_bytes(pdf_ek.url)
                    metin = parse_pdf_metni(pdf_bytes, max_chars=max_pdf_chars)
                    pdf_ek.metin_markdown = metin
                except Exception as e:
                    logger.warning("PDF parse başarısız %s: %s", pdf_ek.url, e)
                    pdf_ek.metin_markdown = f"[PDF çıkarımı başarısız: {e}]"

        return KurulKarariDetay(**detay_dict)


# ============================================================================
# Tool 4: search_yonetmelik
# ============================================================================

@mcp.tool()
async def search_yonetmelik(
    query: Annotated[
        str,
        Field(description="Anahtar kelime (yönetmelik başlığı veya konusu)"),
    ],
    max_results: Annotated[
        int,
        Field(description="Maksimum sonuç", ge=1, le=50),
    ] = 20,
    sadece_yururlukte: Annotated[
        bool,
        Field(description="Sadece yürürlükteki yönetmelikleri döndür (mülga olanları hariç tut)"),
    ] = True,
) -> AramaSonucu:
    """EPDK elektrik piyasası yönetmeliklerini arar.

    Kapsam: EPLY, Lisanssız Yön., DUY, Depolama Yön., Bağlantı Yön., Hizmet Kalitesi Yön. vb.
    Mülga olanlar varsayılan olarak filtrelenir.
    """
    async with EpdkClient() as client:
        html = await client.get_html(ANA_URLLER["elektrik_yonetmelikler"])
        tum_yonetmelikler = parse_mevzuat_listesi(html, tur="yonetmelik")

    query_lower = query.lower()
    sonuclar = [
        y for y in tum_yonetmelikler
        if query_lower in y.baslik.lower()
    ]

    if sadece_yururlukte:
        sonuclar = [y for y in sonuclar if y.yururluk != "mulga"]

    sonuclar = sonuclar[:max_results]

    notlar: list[str] = []
    # Eğer arama "EPLY" gibi kısaltma ise, tam adı hatırlat
    for kisaltma, tam_ad in YONETMELIK_TAM_AD.items():
        if kisaltma.lower() == query_lower:
            notlar.append(
                f"'{kisaltma}' kısaltması '{tam_ad}' anlamına gelir. "
                f"Eğer sonuç boş ise tam adla tekrar arayın."
            )
            break

    return AramaSonucu(
        sorgu=query,
        toplam_sonuc=len(sonuclar),
        sonuclar=sonuclar,
        notlar=notlar,
    )


# ============================================================================
# Tool 5: search_teblig
# ============================================================================

@mcp.tool()
async def search_teblig(
    query: Annotated[
        str,
        Field(description="Anahtar kelime"),
    ],
    max_results: Annotated[
        int,
        Field(description="Maksimum sonuç", ge=1, le=50),
    ] = 20,
    sadece_yururlukte: Annotated[
        bool,
        Field(description="Sadece yürürlükteki tebliğler"),
    ] = True,
) -> AramaSonucu:
    """EPDK elektrik piyasası tebliğlerini arar.

    Kapsam: Para Cezası Tebliği, Tarife Tebliğleri, Bağlantı Bedeli Tebliği,
    Lisanssız Tebliği, Sayaç Tebliği vb.
    """
    async with EpdkClient() as client:
        html = await client.get_html(ANA_URLLER["elektrik_tebligler"])
        tum_tebligler = parse_mevzuat_listesi(html, tur="teblig")

    query_lower = query.lower()
    sonuclar = [t for t in tum_tebligler if query_lower in t.baslik.lower()]

    if sadece_yururlukte:
        sonuclar = [t for t in sonuclar if t.yururluk != "mulga"]

    sonuclar = sonuclar[:max_results]

    return AramaSonucu(
        sorgu=query,
        toplam_sonuc=len(sonuclar),
        sonuclar=sonuclar,
    )


# ============================================================================
# Tool 6: get_belge
# ============================================================================

@mcp.tool()
async def get_belge(
    url: Annotated[
        str,
        Field(
            description=(
                "EPDK belgesi URL'i. /Detay/Icerik/... veya "
                "/Detay/DownloadDocument?id=... formatında."
            )
        ),
    ],
    max_pdf_chars: Annotated[
        int,
        Field(description="PDF için maksimum karakter", ge=1000, le=200000),
    ] = 50000,
) -> MevzuatDetay:
    """Verilen URL'deki EPDK belgesini (HTML sayfa veya PDF) Markdown olarak getirir.

    - HTML sayfası ise: BeautifulSoup ile temizlenip markdownify ile dönüştürülür
    - DownloadDocument PDF linki ise: pypdf ile metin çıkarımı yapılır
    """
    if not url.startswith("http"):
        raise ValueError(f"url tam URL olmalı: {url}")

    async with EpdkClient() as client:
        # PDF mi HTML mi?
        if "DownloadDocument" in url:
            pdf_bytes = await client.get_pdf_bytes(url)
            metin = parse_pdf_metni(pdf_bytes, max_chars=max_pdf_chars)
            return MevzuatDetay(
                tur="diger",
                baslik=f"EPDK Belgesi ({url.rsplit('=', 1)[-1][:20]})",
                url=url,
                yururluk="bilinmiyor",
                icerik_markdown=metin,
            )
        else:
            html = await client.get_html(url)
            detay_dict = parse_mevzuat_detay(html, url, tur="diger")
            return MevzuatDetay(**detay_dict)


# ============================================================================
# Tool 7: list_son_kararlar
# ============================================================================

@mcp.tool()
async def list_son_kararlar(
    adet: Annotated[
        int,
        Field(description="Maksimum karar sayısı", ge=1, le=50),
    ] = 20,
) -> AramaSonucu:
    """EPDK ana sayfasından son alınan kararları ve duyuruları listeler.

    Not: EPDK ana sayfası tüm sektörleri (elektrik + doğal gaz + petrol + LPG) içerir;
    filtreleme yapılmaz. Sadece elektrik için search_kurul_karari kullanın.
    """
    async with EpdkClient() as client:
        models = await client.get_fast_access_data(ANA_URLLER["kurul_kararlari_eski"])
        tum_sonuclar = parse_fast_access_models(models)

    # Tarihe göre sırala (en yeni önce)
    tum_sonuclar.sort(key=lambda k: k.tarih or __import__("datetime").date.min, reverse=True)
    sonuclar = tum_sonuclar[:adet]

    return AramaSonucu(
        sorgu="son_kararlar",
        toplam_sonuc=len(sonuclar),
        sonuclar=sonuclar,
        notlar=[
            "EPDK kurul kararları listesinden alınmıştır; "
            "elektrik piyasası kategorilerini kapsar."
        ],
    )


# ============================================================================
# Tool 8: tahmini_karar_sayisi
# ============================================================================

@mcp.tool()
async def tahmini_karar_sayisi(
    yil: Annotated[int, Field(description="Yıl (örn. 2024)", ge=2002, le=2030)],
    ay: Annotated[int, Field(description="Ay (1-12)", ge=1, le=12)],
) -> SayiTahmini:
    """Verilen yıl/ay için yaklaşık Kurul Kararı sayı aralığını döner.

    Kalibrasyon noktaları:
    - 2019/09 → 8845
    - 2021/11 → 10543
    - 2022/08 → 11157
    - 2023/01 → 11607
    - 2023/12 → 12286
    - 2024/12 → 13115
    - 2025/08 → 13721
    - 2025/10 → 13869

    Linear interpolation ile ara değer tahmin edilir.
    Yıllık ortalama ~1100 karar alınır.
    """
    alt, ust, yaklasik = _tahmini_karar_sayisi(yil, ay)
    return SayiTahmini(
        yil=yil,
        ay=ay,
        alt_sinir=alt,
        ust_sinir=ust,
        yaklasik=yaklasik,
    )


# ============================================================================
# Entry point
# ============================================================================

def run() -> None:
    """Stdio modunda MCP server'ı başlat."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    mcp.run()


if __name__ == "__main__":
    run()
