
from sqlalchemy import text
from src.database import SessionLocal

def analyze():
    db = SessionLocal()
    try:
        print("\n🔎 DETAYLI VERİ ANALİZİ BAŞLIYOR...\n")
        
        # 1. Toplam Ürün (Link Havuzu)
        total = db.execute(text("SELECT COUNT(*) FROM products")).scalar()
        print(f"📦 Toplam Ürün (Link): {total}")
        
        # 2. Detayı Çekilmiş (Fiyatı Olanlar) - Daily Metrics tablosunda kaydı olanlar
        # Not: DailyMetric tablosunda discount_price > 0 olanlar başarılıdır.
        scraped = db.execute(text("SELECT COUNT(DISTINCT product_id) FROM daily_metrics WHERE discounted_price > 0")).scalar()
        print(f"✅ Başarıyla Kazınan (Detaylı): {scraped}")
        
        # 3. Henüz Kazınmamış (Link Var, Detay Yok)
        pending = total - scraped
        print(f"⏳ Sırada Bekleyen: {pending}")
        
        # 4. Hatalı Veri Var mı? (Fiyatı 0 olanlar)
        zeros = db.execute(text("SELECT COUNT(*) FROM daily_metrics WHERE discounted_price = 0")).scalar()
        if zeros > 0:
            print(f"⚠️ DİKKAT: {zeros} ürünün fiyatı 0 TL olarak çekilmiş! (Hata olabilir)")
        else:
            print("✨ Mükemmel: Fiyatı 0 TL olan bozuk veri yok.")
            
        print("\n--- ÖRNEK VERİLER (Son 5 Kazınan) ---")
        rr = db.execute(text("""
            SELECT p.name, d.discounted_price, d.avg_rating, d.rating_count 
            FROM daily_metrics d 
            JOIN products p ON d.product_id = p.id 
            WHERE d.discounted_price > 0
            ORDER BY d.recorded_at DESC LIMIT 5
        """)).fetchall()
        
        for r in rr:
            p_name = r[0] if r[0] else "İsimsiz Ürün"
            print(f"🔹 {p_name[:40]}... | {r[1]} TL | ⭐{r[2]} ({r[3]} yorum)")
            
    finally:
        db.close()

if __name__ == "__main__":
    analyze()
