
import sys
import os
import pandas as pd
from datetime import datetime

# Paths setup
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
backend_path = os.path.join(parent_dir, 'LangChain_backend')
sys.path.append(backend_path)

# DB Imports
from app.core.database import SessionLocal
from app.models.product import Product
from app.models.daily_metric import DailyMetric
from rich.console import Console

console = Console()

def export_full_data():
    db = SessionLocal()
    console.print("[yellow]🔄 Veriler veritabanından çekiliyor...[/yellow]")
    
    try:
        # Tüm detayları çekiyoruz
        results = db.query(DailyMetric, Product)\
            .join(Product, DailyMetric.product_id == Product.id)\
            .order_by(DailyMetric.sales_rank.asc().nullslast())\
            .all()
            
        data = []
        for metric, prod in results:
            # --- TÜM METRİKLER ---
            row = {
                'ID': metric.id,
                'Sıralama (Rank)': metric.sales_rank, # Yeni eklenen kritik metrik! 🎯
                'Ürün Adı': prod.name,
                'Marka': prod.brand,
                'Fiyat (İndirimli)': metric.discounted_price,
                'Fiyat (Orijinal)': metric.price,
                'İndirim (%)': metric.discount_rate,
                'Puan (1-5)': metric.avg_rating,
                'Yorum Sayısı': metric.rating_count,
                'Favori Sayısı': metric.favorite_count,
                'Sepetteki Kişi': metric.cart_count,
                'Görüntülenme (24s)': metric.view_count,
                'Ürün Linki': prod.url,
                'Resim Linki': prod.image_url,
                'Tarih': metric.recorded_at.strftime("%Y-%m-%d %H:%M:%S") if metric.recorded_at else "-"
            }
            data.append(row)
            
        if not data:
            console.print("[red]❌ Gösterilecek veri bulunamadı![/red]")
            return

        # DataFrame Oluştur
        df = pd.DataFrame(data)
        
        # Dosya Adı
        filename = f"Analiz_Raporu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # Excel'e Yaz
        console.print(f"[cyan]💾 Excel oluşturuluyor: {filename}[/cyan]")
        df.to_excel(filename, index=False)
        
        console.print(f"[bold green]✅ BAŞARILI: Tüm veriler (Linkler dahil) {filename} dosyasına kaydedildi![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]❌ Hata:[/bold red] {e}")
    finally:
        db.close()

if __name__ == "__main__":
    export_full_data()
