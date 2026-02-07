# 🤖 TRENDYOL TREND TAKİP & SCRAPING BOTU - ÖZELLİKLER

## 📋 GENEL BAKIŞ

**Amaç:** Trendyol'dan günlük otomatik veri toplama ve trend analizi  
**Hedef:** 30-40 kategori, günlük 120,000+ ürün verisi  
**Kullanım:** E-ticaret trend takibi, piyasa araştırması, fiyat izleme, rekabet analizi

---

## 🔥 ANA ÖZELLİKLER

### **1. AKILLI LİNK TOPLAMA SİSTEMİ**

#### **Otomatik Kategori Yönetimi**
- ✅ 30 kadın giyim kategorisi (tayt, elbise, etek, bluz, pantolon, mont, kazak, jean vb.)
- ✅ JSON tabanlı merkezi kategori yönetimi
- ✅ Her kategori için özelleştirilebilir sayfa limiti (100-200 sayfa)
- ✅ Öncelik bazlı işleme (high/medium/low)
- ✅ Kategori aktif/pasif kontrol (tek tıkla aç/kapat)

#### **Hızlı ve Güvenilir Toplama**
- ✅ Headless browser modu (2x daha hızlı)
- ✅ Optimize edilmiş bekleme süreleri (%40 azaltılmış)
- ✅ 1 kategori (200 sayfa) = ~10-15 dakika
- ✅ Günlük kapasite: 30 kategori × 4,800 link = **144,000 link**

#### **Anti-Ban Koruması**
- ✅ İnsan taklidi (rastgele bekleme süreleri)
- ✅ Otomatik session yenileme (her 20 sayfada)
- ✅ Redirect tespiti ve otomatik düzeltme
- ✅ Duplicate link tespiti (aynı linkler atlanır)
- ✅ Stealth mode (WebDriver maskeleme, fingerprint spoofing)
- ✅ Gerçek tarayıcı profili (cookie/state yönetimi)

#### **Akıllı Hata Yönetimi**
- ✅ 3 katmanlı retry logic
- ✅ URL bazlı yönlendirme kontrolü
- ✅ HTML içerik bazlı doğrulama
- ✅ Tuzak sayfa tespiti (bot önleme sistemlerini geçer)
- ✅ Otomatik oturum yenileme

---

### **2. GELİŞMİŞ ÜRÜN DETAY SCRAPING**

#### **Hybrid Veri Toplama Sistemi**
Tek bir ürün için **3 farklı kaynaktan** veri toplar:

**A. API Interception (En Garantili)**
- Trendyol'un kendi API'lerini dinler
- Product details API
- Social proof API (favori, görüntüleme)
- Review summary API (puan, yorum sayısı)

**B. HTML/DOM Parsing**
- CSS selector bazlı veri çekme
- JavaScript ile runtime veri okuma
- Dinamik fiyat tespiti

**C. Schema.org Verisi**
- JSON-LD structured data
- SEO verilerinden bilgi çıkarma

#### **Gelişmiş Fiyat Motoru**
Trendyol'un karmaşık fiyatlandırma yapısını doğru okur:

- ✅ **Kampanya fiyatları** (Sepette %15, Trendyol Plus)
- ✅ **İndirimli fiyatlar** (düşen/orijinal fiyat ayrımı)
- ✅ **Tek fiyatlı ürünler** (indirim yok)
- ✅ **Renk/beden varyanlarında** fiyat doğruluğu
- ✅ **Dinamik fiyat değişimlerini** yakalama

**Fiyat Doğrulama Sistemi:**
```
Stratejik Sıralama:
1. Kampanya fiyatı ara (Sepette, Plus)
2. Standart indirimli fiyat kontrol et
3. Regex ile tüm fiyatları bul (fallback)
4. Validation: 0 < fiyat < 50,000 TL
```

#### **Toplanan Veriler**
Her ürün için:
```
✅ Ürün Bilgileri:
   - Trendyol ID
   - Ürün adı
   - Marka
   - Satıcı
   - Kategori
   - Resimler (3 adet)
   - Ürün özellikleri (beden, renk, kumaş vb.)

✅ Fiyat Bilgileri:
   - İndirimli fiyat
   - Orijinal fiyat
   - Kampanya fiyatı (varsa)
   - Fiyat tespit yöntemi (şeffaflık)

✅ Sosyal Kanıt Metrikleri:
   - Yıldız puanı
   - Yorum sayısı
   - Favori sayısı
   - Sepete eklenme sayısı
   - Görüntülenme sayısı

✅ Tarihsel Veri:
   - Scraping tarihi
   - Kategori sıralaması
   - Ürünün ilk görülme tarihi
```

---

### **3. YORUM TOPLAMA SİSTEMİ**

- ✅ Ürün yorumlarını otomatik toplar
- ✅ Limit belirlenebilir (örn: ilk 50 yorum)
- ✅ Yorum metni, puan, tarih bilgileri
- ✅ Infinite scroll desteği (sayfayı kaydırarak tüm yorumları toplar)
- ✅ AI ile yorum analizi için hazır (sentiment analysis yapılabilir)

---

### **4. VERİTABANI ve RAPORLAMA**

#### **Çoklu Veritabanı Desteği**
- ✅ SQLite (test/lokal çalışma)
- ✅ PostgreSQL (production/çoklu VPS)
- ✅ Otomatik tablo oluşturma
- ✅ İlişkisel veri modeli

**Tablolar:**
```
products               → Ana ürün bilgileri
product_metrics        → Metrikler (puan, favori, sepet)
product_attributes     → Özellikler (beden, renk)
product_price_history  → Fiyat geçmişi
product_reviews        → Yorumlar
scraping_logs          → İşlem logları
```

#### **Excel Export**
- ✅ Tek tıkla Excel'e aktarma
- ✅ Tarih bazlı dosya isimlendirme
- ✅ Tüm kolonlar anlamlı başlıklar
- ✅ Örnek: `linkler_kadin_tayt_2026-02-07.xlsx`

#### **Raporlama Sistemi**
- ✅ Günlük harvest raporu (başarılı/başarısız kategoriler)
- ✅ VPS bazlı plan oluşturma
- ✅ Progress tracking (gerçek zamanlı ilerleme göstergesi)
- ✅ Hata logları ve detaylı hata raporları

---

### **5. ÖLÇEKLEME ve DAĞITIK MİMARİ**

#### **Multi-VPS Desteği**
- ✅ Her VPS kendi kategori grubunu işler
- ✅ Paralel çalışma (3 VPS = 3x hız)
- ✅ Merkezi kategori yönetimi (tek JSON dosyası)
- ✅ VPS'lere otomatik kategori dağılımı

**Örnek Senaryo:**
```
VPS 1: 10 kategori → 48,000 link/gün
VPS 2: 10 kategori → 40,800 link/gün  
VPS 3: 10 kategori → 36,000 link/gün
-----------------------------------------
TOPLAM: 30 kategori → 124,800 link/gün
```

#### **Proxy Stratejisi (Smart Kullanım)**
**Maliyet Optimizasyonu:**
```
Link Toplama → PROXYSİZ (güvenli, maliyet $0)
Ürün Detay   → PROXY'Lİ (ISP proxy, $50-70/ay)
```

**Proxy Özellikleri:**
- ✅ Otomatik rotasyon (her 200 istek)
- ✅ Sticky session (30 dakika-1 saat)
- ✅ Hata durumunda acil rotasyon
- ✅ ISP proxy recommendation (residential gibi görünür)

---

### **6. TREND TAKİP SİSTEMİ** (Gelişmiş)

#### **Günlük Snapshot**
- ✅ Her ürün için günlük fiyat/metrik kaydı
- ✅ Tarih bazlı karşılaştırma
- ✅ Veritabanında tarihsel data

#### **Trend Hesaplama Formülü**
```python
trend_score = (
    (favori_artış_7gün × 0.30) +      # Popülerlik
    (sepet_artış_7gün × 0.40) +       # Satın alma niyeti
    (yorum_hızı × 0.20) +             # Sosyal kanıt
    (fiyat_düşüş_oranı × 0.10)        # Fiyat çekiciliği
)
```

#### **Trend Metrikleri**
- ✅ Trending ürün tespiti (sıcak ürünler)
- ✅ Fiyat trendi (yükseliş/düşüş/stabil)
- ✅ Popülerlik trendi
- ✅ 7 günlük hızlanma (momentum)
- ✅ Kategori içi sıralama değişimi

---

## 🚀 PERFORMANS ve KAPASİTE

### **Teknik Özellikler**
```
Platform:        Python 3.8+
Browser Engine:  Playwright (Chromium)
Mode:            Headless (görsel mod kapalı)
RAM Kullanımı:   ~300-400 MB/bot
CPU:             2 vCPU yeterli
İşletim Sistemi: Windows/Linux/MacOS
```

### **Hız Metrikleri**
```
Link Toplama:
- 1 sayfa     = 2-3 saniye
- 100 sayfa   = ~5-8 dakika
- 200 sayfa   = ~10-15 dakika
- 1 kategori  = 4,800 link (~15 dk)

Ürün Detay:
- 1 ürün      = 3-4 saniye
- 1,000 ürün  = ~50-60 dakika
- 10,000 ürün = ~10-12 saat

Günlük Kapasite:
- 3 VPS       = 120,000-150,000 ürün/gün
- 5 VPS       = 200,000-250,000 ürün/gün
```

### **Maliyet Analizi**
```
SENARYO 1: $74/ay (Dengeli)
├─ 3 VPS @ $8      = $24
├─ ISP Proxy 20GB  = $50
└─ Kapasite        = ~120K ürün/gün

SENARYO 2: $150/ay (Premium)
├─ 5 VPS @ $10     = $50
├─ ISP Proxy 30GB  = $100
└─ Kapasite        = ~250K ürün/gün
```

---

## 🛠️ TEKNOLOJİ STACK

### **Core**
- **Python 3.8+** - Ana programlama dili
- **Playwright** - Browser automation (Selenium'dan hızlı)
- **BeautifulSoup4** - HTML parsing
- **asyncio** - Asenkron işlemler (paralel çalışma)

### **Database**
- **SQLAlchemy** - ORM (veritabanı yönetimi)
- **PostgreSQL** - Production veritabanı
- **SQLite** - Lokal test/geliştirme

### **Data Processing**
- **Pandas** - Excel export, data manipulation
- **Rich** - Terminal görselleştirme (progress bar, renkli çıktılar)

### **Utilities**
- **python-dotenv** - Ortam değişkenleri (.env)
- **tenacity** - Retry logic
- **aiohttp/httpx** - Async HTTP requests

---

## 🎯 KULLANIM SENARYOLARI

### **1. E-Ticaret Girişimcisi**
**Kullanım:**
- Trend olan ürünleri tespit et
- Hangi kategoriler yükselişte
- Fiyat stratejisi belirle
- Rakip analizi

**Örnek:** "Kadın tayt kategorisinde son 7 günde en çok favoriye eklenen ürünler hangileri?"

### **2. Dropshipping İşletmesi**
**Kullanım:**
- Satış potansiyeli yüksek ürünler
- Fiyat değişimlerini takip et
- Stok durumu analizi (yorumlara göre)
- Tedarikçi araştırması

**Örnek:** "500 TL altı, 1000+ favorisi olan elbiseler"

### **3. Pazar Araştırma/Analiz Firması**
**Kullanım:**
- Kategori raporları
- Marka performans analizi
- Fiyat endeksi (ortalama fiyatlar)
- Sezonsal trend tespiti

**Örnek:** "Kadın giyimde son 30 günlük ortalama fiyat değişimi nedir?"

### **4. Marka/Üretici**
**Kullanım:**
- Rakip fiyat takibi
- Kendi ürünlerinin market pozisyonu
- Müşteri yorumları analizi
- Kampanya etkisi ölçümü

**Örnek:** "Markamızın ürünleri rakiplere göre nasıl performans gösteriyor?"

---

## 🔐 GÜVENLİK ve GİZLİLİK

### **Anti-Bot Bypass Teknikleri**
- ✅ WebDriver işaretlerini maskeleme
- ✅ Chrome runtime mocking
- ✅ WebGL fingerprint spoofing
- ✅ Plugin/language mocking
- ✅ Gerçek kullanıcı user-agent
- ✅ Ekran boyutu tutarlılığı

### **Veri Güvenliği**
- ✅ .env dosyası ile hassas bilgi yönetimi
- ✅ .gitignore ile kredilerin korunması
- ✅ Cookie/state yönetimi
- ✅ Proxy credential encryption

---

## 📊 ÇIKTI ÖRNEKLERİ

### **Link Excel Dosyası**
```
linkler_kadin_tayt_2026-02-07.xlsx

Link                              | Sayfa | Sıralama | Tarama Tarihi
----------------------------------|-------|----------|---------------
https://trendyol.com/xx-p-123456  | 1     | 1        | 2026-02-07 02:00
https://trendyol.com/yy-p-789012  | 1     | 2        | 2026-02-07 02:00
```

### **Ürün Detay Excel**
```
trendyol_products.xlsx

Ürün Adı          | Marka    | Fiyat | Orjinal | Puan | Favori | Tarih
------------------|----------|-------|---------|------|--------|-------
Slim Fit Tayt     | Nike     | 199   | 299     | 4.5  | 1200   | 2026-02-07
Yüksek Bel Tayt   | Adidas   | 249   | 0       | 4.8  | 3400   | 2026-02-07
```

---

## 🏆 REKABET AVANTAJLARI

### **Neden Bu Bot Özel?**

1. **Hybrid Veri Toplama**  
   Diğer scraper'lar sadece HTML okur → Bu bot API + HTML + Schema kullanır (3x güvenilir)

2. **Akıllı Fiyat Motoru**  
   Trendyol'un karmaşık fiyat yapısını doğru okur (Sepette, Plus, kampanyalar)

3. **Self-Healing (Kendini Onarma)**  
   Bot tespiti algılar → Otomatik session yeniler → Devam eder

4. **Ölçeklenebilir Mimari**  
   1 VPS'de 40K ürün → 3 VPS'de 120K ürün → 10 VPS'de 400K ürün

5. **Maliyet Optimizasyonu**  
   Proxysiz link toplama + Proxy'li ürün detay = %60 maliyet tasarrufu

6. **Tam Otomatik**  
   Kategori ekle → Bırak çalışsın → Excel al → Analiz et

---

## 📦 TESLİMAT PAKETİ

### **Kurulu Sistem İçerir:**
```
✅ Kaynak kod (Python)
✅ Veritabanı şeması
✅ 30 hazır kategori (JSON)
✅ Kurulum kılavuzu
✅ Kullanım dökümanı
✅ VPS deployment scriptleri
✅ Cron job örnekleri (otomatik çalışma)
✅ Troubleshooting rehberi
✅ 30 gün teknik destek
```

### **Opsiyonel Eklentiler:**
```
⚡ Telegram/Discord bot (günlük raporlar)
⚡ Web dashboard (Grafana/Superset)
⚡ REST API (kendi yazılımınızla entegre)
⚡ AI trend analiz modülü (ML predictions)
⚡ Özel kategori/marka filtreleme
```

---

## 🎓 ÖĞRENME EĞRİSİ

### **Temel Kullanım** (30 dakika)
- Kategori ekleme/çıkarma
- Link toplama çalıştırma
- Excel export alma

### **Orta Seviye** (2-3 saat)
- VPS kurulumu
- Proxy entegrasyonu
- Ürün detay scraping
- Veritabanı kurulumu

### **İleri Seviye** (1-2 gün)
- Multi-VPS orchestration
- Özel rapor oluşturma
- API geliştirme
- Trend analiz algoritmaları

---

## 💼 FİYATLANDIRMA ÖNERİLERİ

### **Ürün Olarak Satış:**
```
PAKET 1: Temel (Kod + Döküman)
Fiyat: $500-800
İçerik: Kaynak kod, kurulum, temel destek

PAKET 2: Premium (Kurulu Sistem)
Fiyat: $1,200-1,800
İçerik: VPS kurulu, çalışır halde, 3 aylık destek

PAKET 3: Enterprise (Özelleştirilmiş)
Fiyat: $2,500-4,000
İçerik: Özel kategoriler, dashboard, API, tam destek
```

### **Hizmet Olarak (SaaS):**
```
PLAN 1: Starter ($99/ay)
- 10 kategori
- 40K ürün/gün
- Excel export

PLAN 2: Pro ($249/ay)
- 30 kategori
- 120K ürün/gün
- Excel + API

PLAN 3: Enterprise ($499/ay)
- Sınırsız kategori
- 250K+ ürün/gün
- Tam özelleştirme
```

---

## 📞 DESTEK ve GÜNCELLEMELER

### **İlk 30 Gün:**
- ✅ Email/Telegram desteği
- ✅ Kurulum yardımı
- ✅ Bug fix garantisi

### **Uzun Vadeli:**
- ✅ Trendyol değişikliklerine uyum
- ✅ Yeni özellik ekleme (ücretli)
- ✅ Performans optimizasyonları

---

## 🎉 ÖZET

**Tek Satırda:**  
*"Trendyol'dan günde 120K+ ürün verisi toplayan, trend analizi yapan, self-healing, multi-VPS destekli, maliyet optimize edilmiş scraping botu."*

**Satış Cümlesi:**  
*"Trendyol'daki trendleri kaçırmayın! Bu bot sayesinde hangi ürünlerin yükselişte olduğunu, fiyat değişimlerini ve rakip stratejilerini günlük otomatik olarak takip edebilirsiniz. E-ticaret işinizi veriye dayalı kararlarla büyütün!"*

---

**Versiyon:** 1.0  
**Son Güncelleme:** 2026-02-07  
**Geliştirici Notu:** Bu bot sürekli geliştirilmektedir. Yeni özellikler ve optimizasyonlar düzenli olarak eklenmektedir.
