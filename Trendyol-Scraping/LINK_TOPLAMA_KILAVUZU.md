# 🚀 Trendyol Scraping System - Link Toplama Kılavuzu

## 📖 YENİ SİSTEM YAPISI

### **1. Kategori Yönetim Sistemi**

Artık tüm kategoriler `categories.json` dosyasında merkezi olarak yönetiliyor.

```json
{
  "categories": [
    {
      "id": 1,
      "name": "Kadın Elbise",
      "keyword": "kadın elbise",
      "max_pages": 200,
      "vps_id": 1,
      "priority": "high",
      "enabled": true
    }
  ]
}
```

### **2. Günlük Link Toplama (Otomatik)**

**Komut:**
```bash
# Tüm kategoriler için plan göster (test)
python daily_harvester.py --dry-run

# VPS 1 kategorileri için link topla
python daily_harvester.py --vps-id 1

# VPS 2 kategorileri için plan göster
python daily_harvester.py --vps-id 2 --dry-run
```

**Ne yapar?**
- `categories.json` dosyasından kategorileri okur
- Belirtilen VPS'e ait kategorileri sırayla işler
- Her kategori için `harvest_links.py` mantığını çalıştırır
- **PROXYSİZ çalışır** (maliyet tasarrufu)
- Progress bar ile ilerlemeyi gösterir
- Başarılı/başarısız kategorileri raporlar

---

## 🎯 $50-75 BÜTÇE İLE KAPASİTE

### **Günlük Kapasite:**
```
10 kategori/VPS × 200 sayfa × 24 ürün = 48,000 link/VPS
3 VPS × 48,000 = 144,000 link/gün

Kategorilere göre değişir:
- Popüler kategoriler: 200 sayfa (4,800 link)
- Orta kategoriler: 150 sayfa (3,600 link)
- Niş kategoriler: 100 sayfa (2,400 link)

Toplam: 30-40 kategori/gün mümkün ✅
```

### **Maliyet Dağılımı:**
```
3 VPS @ $8/ay        = $24/ay
ISP Proxy (~20 GB)   = $50/ay
---------------------------------
TOPLAM               = $74/ay
```

---

## 📋 KULLANIM SENARYOLARI

### **Senaryo 1: Test Çalışması (Tek Kategori)**
```bash
# Eski yöntem (manuel):
python harvest_links.py  # "tayt" kelimesi için 200 sayfa

# Yeni yöntem: categories.json'dan ID=2 (Kadın Tayt)
# Önce dry-run ile test et
python daily_harvester.py --vps-id 1 --dry-run
```

### **Senaryo 2: Günlük Tam Çalışma (VPS 1)**
```bash
# Aktivasyon
venv\Scripts\activate

# VPS 1'in tüm kategorilerini topla
python daily_harvester.py --vps-id 1

# Çıktı:
# - linkler_kadin_elbise_2026-02-07.xlsx
# - linkler_kadin_tayt_2026-02-07.xlsx
# - linkler_kadin_bluz_2026-02-07.xlsx
# - daily_harvest_report_20260207_0215.txt
```

### **Senaryo 3: Tüm VPS'leri Simüle Et (Lokal Test)**
```bash
# Tüm kategorileri (3 VPS'in hepsini) sırayla çalıştır
python daily_harvester.py

# ⚠️ DİKKAT: Bu 30-40 kategori demek = 8-12 saat sürer!
```

---

## 🗂️ ÇIKTI DOSYALARI

### **Link Excel Dosyaları:**
```
linkler_{keyword}_{tarih}.xlsx
├── Link
├── Sayfa
├── Sıralama
└── Tarama Tarihi
```

### **Harvest Raporu:**
```
daily_harvest_report_20260207_0215.txt
├── Başarılı kategoriler
├── Başarısız kategoriler
└── Özet istatistikler
```

### **VPS Planı:**
```bash
# VPS 1 için günlük plan oluştur
python src/utils/category_manager.py

# Çıktı: vps1_daily_plan.txt
```

---

## ⚙️ KATEGORİ EKLEME/DÜZENLEME

### **Yeni Kategori Eklemek:**

1. `categories.json` dosyasını aç
2. En alta yeni kategori ekle:

```json
{
  "id": 11,
  "name": "Spor Tayt",
  "keyword": "spor tayt",
  "max_pages": 150,
  "vps_id": 2,
  "priority": "medium",
  "enabled": true
}
```

3. **ID'lerin unique olduğundan emin ol!**

### **Kategori Devre Dışı Bırakmak:**
```json
{
  "id": 9,
  "name": "Kozmetik",
  "enabled": false  // ⬅️ Bu kategori atlanacak
}
```

### **VPS Dağılımını Değiştirmek:**
```json
// VPS 1'den VPS 3'e taşı
{
  "id": 4,
  "vps_id": 3  // ⬅️ Değişti (1 → 3)
}
```

---

## 📊 PERFORMANS TAHMİNİ

### **Link Toplama Süresi:**
| Kategori Boyutu | Sayfa | Tahmini Süre |
|----------------|-------|-------------|
| Küçük          | 100   | ~5-8 dakika |
| Orta           | 150   | ~8-12 dakika|
| Büyük          | 200   | ~10-15 dakika|

**Toplam (VPS 1, 4 kategori):**
```
4 kategori × 12 dakika = ~48 dakika/VPS
3 VPS paralel = Aynı anda 48 dakika
```

### **Günlük Workflow:**
```
02:00 - Link toplama başlar (her VPS kendi kategorileri)
03:00 - Link toplama biter
03:30 - Excel dosyaları hazır
04:00 - Ürün detay scraping başlar (PROXY'Lİ)
20:00 - Ürün scraping biter
22:00 - Günlük rapor gönderilir
```

---

## 🔧 GELİŞTİRME PLANI (Sonraki Adımlar)

### **Faz 1: Proxy Entegrasyonu** ✅ (Sonraki)
- `src/utils/proxy_manager.py` yazılacak
- Ürün detay scraping'e proxy eklenecek
- Link toplama proxysiz kalacak

### **Faz 2: Merkezi Veritabanı**
- PostgreSQL kurulumu
- Link deduplication
- Tarihsel takip

### **Faz 3: VPS Deployment**
- Docker container
- Cron job kurulumu
- Monitoring dashboard

### **Faz 4: Trend Analizi**
- Günlük snapshot karşılaştırma
- Trend score hesaplama
- Top 100 trending ürünler

---

## 🤝 DESTEK

**Test için:**
```bash
# Kategori listesini göster
python src/utils/category_manager.py

# 1 kategori ile test (dry-run)
python daily_harvester.py --vps-id 1 --dry-run
```

**Sorun mu var?** README'nin devamında troubleshooting bölümü eklenecek.
