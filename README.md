# EPDK MCP

**Türk Enerji Piyasası Düzenleme Kurumu (EPDK) için Model Context Protocol sunucusu.**

[epdk.gov.tr](https://www.epdk.gov.tr) üzerinden elektrik piyasası mevzuatı ve Kurul Kararlarına programatik erişim sağlar. Claude Desktop, Claude.ai, Cursor, Windsurf veya MCP destekleyen herhangi bir LLM istemcisi ile kullanılabilir.

## Neden EPDK MCP?

[mevzuat-mcp](https://github.com/saidsurucu/mevzuat-mcp) Adalet Bakanlığı mevzuat veritabanına erişim sağlıyor; ancak **EPDK Kurul Kararları orada yok**. EPDK kendi sitesinde 14.000+ Kurul Kararı yayımlıyor (2002'den günümüze) ve bu kararlar elektrik piyasası avukatlığı için kritik. Bu MCP server o boşluğu dolduruyor.

## Özellikler

- 🔍 **Kurul Kararı arama** — sayı, konu, tarih veya anahtar kelime ile
- 📂 **Kategorik tarama** — Tarife, Lisans, Bağlantı, Lisanssız, YEKDEM, DUY, Depolama vb.
- 📄 **Tam metin çıkarımı** — HTML sayfaları + DownloadDocument PDF'leri Markdown'a dönüştürür
- 🗂️ **Yönetmelik & Tebliğ arama** — EPDK sitesindeki ikincil mevzuat
- 🆕 **Son alınan kararlar** — Ana sayfa duyurularından son kararlar
- 📅 **Tarih→sayı kalibrasyon** — Tahminî karar sayısı aralığı hesaplama
- 🤖 **OCR opsiyonel** — Taranmış PDF'ler için Mistral OCR desteği (env var ile)

## Hızlı Kurulum

### Claude Desktop için

`claude_desktop_config.json` dosyasına ekleyin:

```json
{
  "mcpServers": {
    "EPDK MCP": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/iturkguler/epdk-mcp",
        "epdk-mcp"
      ]
    }
  }
}
```

### Yerel geliştirme

```bash
git clone https://github.com/iturkguler/epdk-mcp
cd epdk-mcp
uv pip install -e .
epdk-mcp  # stdio modunda başlar
```

### Mistral OCR (opsiyonel — taranmış PDF'ler için)

```bash
export MISTRAL_API_KEY="your-key-here"
uv pip install -e ".[ocr]"
```

## Sunulan Araçlar (Tools)

### 1. `search_kurul_karari`
EPDK Kurul Kararlarını arar (sayı, konu, tarih, anahtar kelime ile).

**Parametreler:**
- `query` (str, opsiyonel) — Anahtar kelime
- `sayi` (int, opsiyonel) — Karar sayısı (örn. 13869)
- `kategori` (str, opsiyonel) — Konu kategorisi (örn. "tarife", "lisans", "lisanssiz")
- `tarih_baslangic` (str, opsiyonel) — ISO 8601 (YYYY-MM-DD)
- `tarih_bitis` (str, opsiyonel) — ISO 8601
- `max_results` (int, varsayılan 10)

**Örnek:**
```python
search_kurul_karari(query="depolamalı önlisans", tarih_baslangic="2024-01-01")
```

### 2. `get_kurul_karari`
Spesifik bir Kurul Kararının tam metnini Markdown formatında getirir. PDF eki varsa metin çıkarımı yapar.

**Parametreler:**
- `karar_id_or_url` (str) — Karar ID veya tam URL
- `include_pdf_text` (bool, varsayılan True) — PDF eklerin metin içeriği

### 3. `list_kategoriler`
Tüm elektrik piyasası Kurul Kararı kategorilerini listeler.

**Dönüş:** Liste — her biri `{kategori_id, ad, url, aciklama}` formatında.

### 4. `search_yonetmelik`
EPDK yönetmeliklerini başlığa/içeriğe göre arar (EPLY, Lisanssız Yön., DUY, Depolama Yön. vb.).

**Parametreler:**
- `query` (str) — Anahtar kelime
- `title_search` (bool, varsayılan True) — Sadece başlıkta ara

### 5. `search_teblig`
EPDK tebliğlerini arar (Para Cezası Tebliği, Tarife Tebliği, vb.).

### 6. `get_belge`
Verilen URL'deki EPDK belgesini (HTML veya PDF) Markdown olarak getirir. `DownloadDocument?id=...` linklerinde otomatik PDF parse.

### 7. `list_son_kararlar`
EPDK ana sayfasından son alınan kararları listeler (yaklaşık 20 en son).

### 8. `tahmini_karar_sayisi`
Verilen yıl/ay için yaklaşık Kurul Kararı sayı aralığını döner (kalibrasyon tablosu kullanılır).

**Örnek:**
```python
tahmini_karar_sayisi(yil=2024, ay=6)
# → {"alt": 12700, "ust": 12900, "yaklasik": 12800}
```

## Veri Kaynakları

- `https://www.epdk.gov.tr/Detay/Icerik/3-0-39/kurul-kararlari-` — Elektrik Kurul Kararları ana liste
- `https://www.epdk.gov.tr/Detay/Icerik/3-0-0-101/elektrik-piyasasi-kurul-kararlari` — Kategorize liste
- `https://www.epdk.gov.tr/Detay/Icerik/3-0-159-3/yonetmelikler` — Yönetmelikler
- `https://www.epdk.gov.tr/Detay/Icerik/3-0-77-3/tebligler` — Tebliğler
- `https://www.epdk.gov.tr/Detay/Icerik/23-2-3/mevzuat` — Ana mevzuat sayfası

EPDK sitesi resmi API sunmaz; bu MCP sunucusu HTML scraping ile çalışır. Saygılı kullanım için httpx async client'da varsayılan 2 saniye delay vardır.

## Kategori Haritası

| Kategori ID | Konu | Tipik Kararlar |
|---|---|---|
| `tarife-dagitim` | Dağıtım tarifesi | Çeyrek/yıllık tarife |
| `tarife-iletim` | İletim tarifesi (TEİAŞ) | Yıllık iletim |
| `tarife-perakende` | Perakende tarifesi | 3 aylık tarife |
| `tarife-son-kaynak` | Son kaynak tedarik | Aylık tarife |
| `lisans` | Lisans işlemleri | Lisans verme/sona erdirme |
| `onlisans` | Önlisans | Yarışma, ret kararları |
| `lisanssiz` | Lisanssız üretim | Çatı GES, 5 MW |
| `baglanti` | Bağlantı/BBKR | Bölgesel kapasite |
| `duy` | Dengeleme/uzlaştırma | KÜPSM, n katsayı |
| `yekdem` | YEKDEM | Yıllık YEK listesi |
| `depolama` | Depolama (BESS) | Kapasite tahsis |
| `para-cezasi` | İdari para cezası | Yıllık tebliğ |
| `hizmet-kalitesi` | Hizmet kalitesi | Tazminat eşik |
| `kamulastirma` | Kamulaştırma | Bireysel kararlar |
| `osos` | Akıllı sayaç/OSOS | Sayaç değer |
| `bildirim` | Bildirim yükümlülükleri | Tablo değişiklik |

## Mimari

```
epdk-mcp/
├── src/epdk_mcp/
│   ├── server.py          # FastMCP server + tool tanımları
│   ├── client.py          # EPDK async HTTP client
│   ├── parsers.py         # HTML & PDF parse logic
│   ├── urls.py            # URL haritası & kategori şablonları
│   ├── models.py          # Pydantic veri modelleri
│   ├── ocr.py             # Opsiyonel Mistral OCR
│   └── exceptions.py
└── tests/
```

## Bilinen Sınırlamalar

- EPDK sitesi yapısal değişikliğe gidebilir; o durumda `urls.py` ve `parsers.py` güncellenmeli.
- Resmi API olmadığından arama sonuçları HTML parse'a bağlı; bazı eski (2010 öncesi) kararlar yalnızca RG'de bulunabilir.
- Bireysel kararlar (örn. tek şirket için lisans iptali) bazen yalnızca KEP ile tebliğ edilir, EPDK sitesinde yayımlanmaz.
- Site rate limiting yok ama art arda 50+ istek gönderirseniz bloklanabilirsiniz; varsayılan 2s delay var.

## Kardeş Projeler

- [mevzuat-mcp](https://github.com/saidsurucu/mevzuat-mcp) — Adalet Bakanlığı mevzuat sistemi
- [yargi-mcp](https://github.com/saidsurucu/yargi-mcp) — Yargıtay, Danıştay, AYM, BDDK vb.
- [borsa-mcp](https://github.com/saidsurucu/borsa-mcp) — BIST + TCMB EVDS
- [ihale-mcp](https://github.com/saidsurucu/ihale-mcp) — KİK ihaleleri

## Lisans

MIT — Türkgüler | Fırat | Yılmaz Avukatlık Bürosu

## Katkı

PR ve issue açın. Özellikle: yeni kategori URL'leri, EPDK'nın site yapı değişiklikleri için scraper güncellemeleri çok değerlidir.
