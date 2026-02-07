# Trendyol Scraping System

Trendyol'dan ürün ve kategori verilerini çeken, PostgreSQL veritabanına kaydeden scraping sistemi.

## 🚀 Kurulum

### 1. Python Sanal Ortamı Oluştur

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 2. Bağımlılıkları Yükle

```bash
pip install -r requirements.txt
```

### 3. Playwright Tarayıcılarını Yükle

```bash
playwright install chromium
```

### 4. Ortam Değişkenlerini Ayarla

```bash
copy .env.example .env
# .env dosyasını düzenle ve PostgreSQL bilgilerini gir
```

### 5. Veritabanını Oluştur

```bash
# PostgreSQL'de veritabanı oluştur
# psql -U postgres -c "CREATE DATABASE trendyol_scraping;"

# Tabloları oluştur
python main.py init
```

## 📖 Kullanım

### İnteraktif Mod

```bash
python main.py
```

### CLI Komutları

```bash
# Veritabanı oluştur
python main.py init

# Bağlantı testi
python main.py test

# Kategori tara (3 sayfa)
python main.py category "https://www.trendyol.com/sr?q=kadin+elbise" 3

# Tek ürün tara
python main.py product "https://www.trendyol.com/xxmagaza/urun-adi-p-123456789"

# İstatistikler
python main.py stats
```

## 📁 Proje Yapısı

```
Trendyol-Scraping/
├── main.py                 # Ana uygulama
├── requirements.txt        # Bağımlılıklar
├── .env.example           # Örnek ortam değişkenleri
├── .gitignore
├── README.md
└── src/
    ├── __init__.py
    ├── database.py        # PostgreSQL bağlantısı
    ├── models.py          # SQLAlchemy modelleri
    ├── scrapers/
    │   ├── __init__.py
    │   ├── category_scraper.py  # Kategori tarayıcı
    │   └── product_scraper.py   # Ürün detay tarayıcı
    └── services/
        ├── __init__.py
        └── data_service.py      # Veritabanı işlemleri
```

## 📊 Veritabanı Şeması

### products
- Temel ürün bilgileri (isim, satıcı, fiyat, URL, kategori)

### product_metrics
- Etkileşim verileri (rating, favori, sepet sayısı)
- Tarihsel takip için ayrı tablo

### product_attributes
- Ürün özellikleri (beden, renk, kumaş tipi vb.)

### scraping_logs
- Tarama işlem logları

## 🔧 Konfigürasyon (.env)

```env
# Veritabanı
DATABASE_URL=postgresql://postgres:password@localhost:5432/trendyol_scraping
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trendyol_scraping
DB_USER=postgres
DB_PASSWORD=your_password

# Scraping
HEADLESS=true
SLOW_MO=100
REQUEST_DELAY=2
```

## ⚠️ Önemli Notlar

1. **Rate Limiting**: Trendyol'un engellemesini önlemek için istekler arası bekleme süresi eklenmiştir.
2. **Headless Mod**: Test için `headless=False` kullanabilirsiniz.
3. **Veritabanı**: PostgreSQL'in çalışır durumda olduğundan emin olun.

## 📝 Lisans

MIT
