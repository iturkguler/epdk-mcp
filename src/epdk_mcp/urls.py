"""EPDK web sitesi URL haritası ve kategori şablonları."""

from __future__ import annotations

BASE_URL = "https://www.epdk.gov.tr"

# ============================================================================
# Ana giriş noktaları
# ============================================================================

ANA_URLLER = {
    "ana_sayfa": f"{BASE_URL}/",
    "elektrik_mevzuat_ana": f"{BASE_URL}/Detay/Icerik/23-2-3/mevzuat",
    "elektrik_yonetmelikler": f"{BASE_URL}/Detay/Icerik/3-0-159-3/yonetmelikler",
    "elektrik_tebligler": f"{BASE_URL}/Detay/Icerik/3-0-77-3/tebligler",
    "elektrik_diger_mevzuat": f"{BASE_URL}/detay/icerik/3-0-0-62/elektrik-piyasasi-diger-mevzuatlar",
    "kurul_kararlari_eski": f"{BASE_URL}/Detay/Icerik/3-0-39/kurul-kararlari-",
    "kurul_kararlari_yeni": f"{BASE_URL}/Detay/Icerik/3-0-39-3/kurul-kararlari-",
    "kurul_kararlari_kategorize": f"{BASE_URL}/Detay/Icerik/3-0-0-101/elektrik-piyasasi-kurul-kararlari",
    "bakanlar_kurulu_kararlari": f"{BASE_URL}/Detay/Icerik/3-0-0-2255/bakanlar-kurulu-kararlari",
    "kamulastirma_kurul_kararlari": f"{BASE_URL}/Detay/Icerik/3-0-194/kurul-kararlari",
    "lisans_bedelleri": f"{BASE_URL}/Detay/Icerik/21-9/lisans-bedelleri",
    "elektrik_tarifeler": f"{BASE_URL}/Detay/Icerik/3-0-1-3/elektriktarifeler",
    "elektrik_lisanslar": f"{BASE_URL}/Detay/Icerik/3-0-0-140/elektrik-lisanslar",
    "kamulastirma_mevzuat": f"{BASE_URL}/Detay/Icerik/23-2-1026/mevzuat",
}


# ============================================================================
# Kategori → konu/aramayı kolaylaştırıcı anahtar kelimeler
# ============================================================================

# Her kategori şu yapıdadır:
# {
#     "kategori_id": {
#         "ad": "Kullanıcıya gösterilecek isim",
#         "url": "Sayfa URL'i (varsa)",
#         "arama_anahtari": "Web search query'sinde kullanılacak terim",
#         "aciklama": "Kısa açıklama"
#     }
# }

KATEGORILER: dict[str, dict[str, str]] = {
    "tarife-dagitim": {
        "ad": "Dağıtım Tarifesi",
        "url": f"{BASE_URL}/Detay/Icerik/3-0-1-3/elektriktarifeler",
        "arama_anahtari": "dağıtım tarifesi gelir gereksinimi",
        "aciklama": "Dağıtım lisansı sahipleri tarafından uygulanacak tarifeler",
    },
    "tarife-iletim": {
        "ad": "İletim Tarifesi",
        "url": "",
        "arama_anahtari": "iletim tarifesi TEİAŞ sistem kullanım",
        "aciklama": "TEİAŞ iletim sistemi gelir gereksinimi ve tarifeler",
    },
    "tarife-perakende": {
        "ad": "Perakende Tarifesi",
        "url": "",
        "arama_anahtari": "perakende tarifesi görevli tedarik",
        "aciklama": "Görevli tedarik şirketi perakende tarifeleri",
    },
    "tarife-son-kaynak": {
        "ad": "Son Kaynak Tedarik Tarifesi",
        "url": "",
        "arama_anahtari": "son kaynak tedarik tarifesi",
        "aciklama": "Tedarikçisi olmayan tüketiciler için son kaynak tarifesi",
    },
    "lisans": {
        "ad": "Lisans İşlemleri",
        "url": f"{BASE_URL}/Detay/Icerik/3-0-0-140/elektrik-lisanslar",
        "arama_anahtari": "lisans sona erdirme iptal tadil",
        "aciklama": "Üretim, dağıtım, tedarik, OSB, ihracat-ithalat lisansları",
    },
    "onlisans": {
        "ad": "Önlisans / Yarışma",
        "url": "",
        "arama_anahtari": "önlisans yarışma aynı bölge kaynak",
        "aciklama": "Önlisans verme, yarışma süreçleri, ret kararları",
    },
    "lisanssiz": {
        "ad": "Lisanssız Elektrik Üretim",
        "url": "",
        "arama_anahtari": "lisanssız elektrik üretim çatı GES mahsuplaşma",
        "aciklama": "5 MW altı, çatı GES, mahsuplaşma rejimi",
    },
    "baglanti": {
        "ad": "Bağlantı ve Sistem Kullanım",
        "url": "",
        "arama_anahtari": "bağlantı sistem kullanım enterkonneksiyon BBKR",
        "aciklama": "Bağlantı anlaşmaları, BBKR, hat katılım bedeli",
    },
    "duy": {
        "ad": "Dengeleme ve Uzlaştırma (DUY)",
        "url": "",
        "arama_anahtari": "dengeleme uzlaştırma KÜPSM n katsayısı",
        "aciklama": "DUY uygulama kararları, kategoriler, katsayılar",
    },
    "yekdem": {
        "ad": "YEKDEM",
        "url": "",
        "arama_anahtari": "YEKDEM yerli katkı yenilenebilir destek",
        "aciklama": "Yenilenebilir Enerji Destekleme Mekanizması",
    },
    "depolama": {
        "ad": "Depolama (BESS)",
        "url": "",
        "arama_anahtari": "depolama BESS batarya önlisans kapasite",
        "aciklama": "Elektrik depolama tesisleri, BESS önlisansı",
    },
    "para-cezasi": {
        "ad": "İdari Para Cezası",
        "url": "",
        "arama_anahtari": "para cezası 16. madde tebliği",
        "aciklama": "6446 SK m.16 kapsamında uygulanacak idari para cezaları",
    },
    "hizmet-kalitesi": {
        "ad": "Hizmet Kalitesi",
        "url": "",
        "arama_anahtari": "hizmet kalitesi tazminat kesinti süre",
        "aciklama": "Dağıtım hizmet kalitesi, tazminat eşikleri",
    },
    "kamulastirma": {
        "ad": "Kamulaştırma",
        "url": f"{BASE_URL}/Detay/Icerik/3-0-194/kurul-kararlari",
        "arama_anahtari": "kamulaştırma taşınmaz temini",
        "aciklama": "EPDK kamu yararı kararları, acele kamulaştırma",
    },
    "osos": {
        "ad": "OSOS / Akıllı Sayaç",
        "url": "",
        "arama_anahtari": "OSOS akıllı sayaç otomatik okuma",
        "aciklama": "Otomatik sayaç okuma sistemleri kapsamı",
    },
    "bildirim": {
        "ad": "Bildirim Yükümlülükleri",
        "url": "",
        "arama_anahtari": "bildirim yükümlülük tabloları",
        "aciklama": "Lisans sahiplerinin EPDK'ya yapacağı bildirimler",
    },
    "lisans-bedeli": {
        "ad": "Lisans Bedelleri",
        "url": f"{BASE_URL}/Detay/Icerik/21-9/lisans-bedelleri",
        "arama_anahtari": "lisans bedeli katılma payı",
        "aciklama": "Yıllık lisans bedelleri ve katılma payları",
    },
    "siber-guvenlik": {
        "ad": "Siber Güvenlik",
        "url": "",
        "arama_anahtari": "siber güvenlik yetkinlik denetçi firma",
        "aciklama": "Enerji sektörü siber güvenlik denetimi",
    },
}


# ============================================================================
# Yönetmelik kısaltma → tam ad (arama destekleyici)
# ============================================================================

YONETMELIK_TAM_AD: dict[str, str] = {
    "EPLY": "Elektrik Piyasası Lisans Yönetmeliği",
    "Lisanssız": "Elektrik Piyasasında Lisanssız Elektrik Üretim Yönetmeliği",
    "DUY": "Elektrik Piyasası Dengeleme ve Uzlaştırma Yönetmeliği",
    "Depolama": "Elektrik Piyasasında Depolama Faaliyetleri Yönetmeliği",
    "Yarışma": "Rüzgar veya Güneş Enerjisine Dayalı Üretim Tesisi Kurmak Üzere Yapılan Önlisans Başvurularına İlişkin Yarışma Yönetmeliği",
    "HK": "Elektrik Dağıtımı ve Perakende Satışına İlişkin Hizmet Kalitesi Yönetmeliği",
    "Bağlantı": "Elektrik Piyasası Bağlantı ve Sistem Kullanım Yönetmeliği",
    "Şebeke": "Elektrik Piyasası Şebeke Yönetmeliği",
    "Ölçüm": "Elektrik Piyasası Ölçüm Sistemleri Yönetmeliği",
    "Tüketici": "Elektrik Piyasası Tüketici Hizmetleri Yönetmeliği",
    "Toplayıcılık": "Elektrik Piyasasında Toplayıcılık Faaliyeti Yönetmeliği",
    "Devir": "Elektrik Piyasası Tadilat ve İletim Faaliyeti ile Vazgeçilen Faaliyetlerin Devrine İlişkin Yönetmelik",
    "Denetim": "Elektrik Piyasasında Yapılacak Denetimler ile Ön Araştırma ve Soruşturmalarda Takip Edilecek Usul ve Esaslar Hakkında Yönetmelik",
    "Taşınmaz": "Taşınmaz Temini İşlemleri Hakkında Yönetmelik",
    "YEK": "Yenilenebilir Enerji Kaynaklarının Belgelendirilmesi ve Desteklenmesine İlişkin Yönetmelik",
    "Yerli Aksam": "Yenilenebilir Enerji Kaynaklarından Elektrik Enerjisi Üreten Tesislerde Kullanılan Yerli Aksamın Desteklenmesi Hakkında Yönetmelik",
    "OSB": "Organize Sanayi Bölgelerinin ve Endüstri Bölgelerinin Elektrik Piyasası Faaliyetlerine İlişkin Yönetmelik",
}


# ============================================================================
# Tarih → Karar Sayısı Kalibrasyon Noktaları
# ============================================================================
# Kaynak: epdk.gov.tr'de gözlemlenen kararlar.
# Yeni karar tespit edildikçe güncellenmesi gereken liste.

SAYI_KALIBRASYONU: dict[tuple[int, int], int] = {
    (2019, 9):  8845,
    (2021, 11): 10543,
    (2022, 3):  10842,
    (2022, 8):  11119,
    (2022, 9):  11157,
    (2023, 1):  11607,
    (2023, 12): 12286,
    (2024, 3):  12524,
    (2024, 12): 13115,
    (2025, 8):  13721,
    (2025, 10): 13869,
}


# ============================================================================
# DownloadDocument URL şablonu
# ============================================================================

DOWNLOAD_DOCUMENT_BASE = f"{BASE_URL}/Detay/DownloadDocument"


def build_download_url(document_id: str) -> str:
    """DownloadDocument URL'i oluşturur (id base64 encoded olabilir)."""
    return f"{DOWNLOAD_DOCUMENT_BASE}?id={document_id}"


def tahmini_karar_sayisi(yil: int, ay: int) -> tuple[int | None, int | None, int | None]:
    """
    Verilen yıl/ay için yaklaşık karar sayı aralığı tahmin eder.
    Linear interpolation between calibration points.

    Returns:
        (alt_sinir, ust_sinir, yaklasik) — None döndürebilir veri yetersizse
    """
    if not SAYI_KALIBRASYONU:
        return None, None, None

    nokta_list = sorted(SAYI_KALIBRASYONU.items())
    sorgu_ay = yil * 12 + ay

    onceki: tuple[tuple[int, int], int] | None = None
    sonraki: tuple[tuple[int, int], int] | None = None

    for (y, a), sayi in nokta_list:
        nokta_ay = y * 12 + a
        if nokta_ay <= sorgu_ay:
            onceki = ((y, a), sayi)
        elif sonraki is None:
            sonraki = ((y, a), sayi)
            break

    if onceki and sonraki:
        (y1, a1), s1 = onceki
        (y2, a2), s2 = sonraki
        ay_fark_toplam = (y2 - y1) * 12 + (a2 - a1)
        ay_fark_sorgu = (yil - y1) * 12 + (ay - a1)
        if ay_fark_toplam > 0:
            yaklasik = s1 + int((s2 - s1) * ay_fark_sorgu / ay_fark_toplam)
        else:
            yaklasik = s1
    elif onceki:
        (y1, a1), s1 = onceki
        ay_fark = (yil - y1) * 12 + (ay - a1)
        yaklasik = s1 + int(92 * ay_fark)  # yaklaşık ~92 karar/ay
    elif sonraki:
        (y2, a2), s2 = sonraki
        ay_fark = (y2 - yil) * 12 + (a2 - ay)
        yaklasik = s2 - int(92 * ay_fark)
    else:
        return None, None, None

    return yaklasik - 100, yaklasik + 100, yaklasik
