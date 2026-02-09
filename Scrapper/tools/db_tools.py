"""
Database Tools - Unified module for all DB-related operations
Updated for Product + DailyMetric model (Actual Schema)
"""

from sqlalchemy import text
from rich.console import Console
from rich.table import Table
from datetime import datetime
import pandas as pd

from src.database import DatabaseManager
from src.config import load_config

console = Console()


def get_db_manager():
    """Get database manager with config"""
    config = load_config()
    platform_config = config.platforms.get('trendyol')
    if not platform_config:
        raise Exception("Trendyol config not found")
    return DatabaseManager(
        connection_url=platform_config.database.connection_url,
        platform='trendyol'
    )


def analyze():
    """Veri analizi - istatistikleri gösterir"""
    db = get_db_manager()
    session = db.get_session()
    
    console.print("\n[bold cyan]🔎 VERİ ANALİZİ[/bold cyan]\n")
    
    try:
        # Toplam ürün
        total_products = session.execute(text("SELECT COUNT(*) FROM products")).scalar()
        console.print(f"📦 Toplam Ürün: {total_products}")
        
        # Toplam metrik
        total_metrics = session.execute(text("SELECT COUNT(*) FROM daily_metrics")).scalar()
        console.print(f"📊 Toplam Metrik Kayıt: {total_metrics}")
        
        # Bugünkü kayıtlar - Fix: Use quotes for date column and handle time component
        today_metrics = session.execute(text("""
            SELECT COUNT(*) FROM daily_metrics 
            WHERE CAST("date" AS DATE) = CURRENT_DATE
        """)).scalar()
        console.print(f"📆 Bugün Eklenen: {today_metrics}")
        
        # En popüler 5 ürün (son metriğe göre)
        console.print("\n[bold yellow]🏆 En Popüler 5 Ürün[/bold yellow]")
        top = session.execute(text("""
            SELECT p.name, dm.discounted_price, dm.favorite_count, dm.avg_rating
            FROM products p
            JOIN daily_metrics dm ON dm.product_id = p.id
            WHERE dm.id IN (
                SELECT MAX(id) FROM daily_metrics GROUP BY product_id
            )
            ORDER BY dm.favorite_count DESC NULLS LAST
            LIMIT 5
        """)).fetchall()
        
        for r in top:
            name = (r[0] or "İsimsiz")[:35]
            console.print(f"  ❤️ {r[2] or 0:,} | {r[1] or 0:.0f} TL | ⭐{r[3] or 0:.1f} | {name}")
            
    except Exception as e:
        console.print(f"[red]❌ Hata: {e}[/red]")
    finally:
        db.close()


def check(limit: int = 20):
    """Son taranan ürünleri kontrol et"""
    db = get_db_manager()
    session = db.get_session()
    
    console.print(f"\n[bold cyan]📋 SON {limit} METRİK[/bold cyan]\n")
    
    try:
        results = session.execute(text(f"""
            SELECT p.name, dm.discounted_price, dm.favorite_count, dm.cart_count, dm.avg_rating, dm."date"
            FROM daily_metrics dm
            JOIN products p ON p.id = dm.product_id
            ORDER BY dm."date" DESC 
            LIMIT {limit}
        """)).fetchall()
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Ürün Adı", width=30)
        table.add_column("Fiyat", justify="right")
        table.add_column("❤️", justify="right")
        table.add_column("🛒", justify="right")
        table.add_column("⭐", justify="center")
        table.add_column("Tarih", justify="right")
        
        for r in results:
            name = (r[0] or "-")[:27] + "..." if len(r[0] or "") > 30 else (r[0] or "-")
            date_str = r[5].strftime("%d/%m %H:%M") if r[5] else "-"
            table.add_row(
                name,
                f"{r[1]:.0f} TL" if r[1] else "-",
                f"{r[2]:,}" if r[2] else "-",
                f"{r[3]:,}" if r[3] else "-",
                f"{r[4]:.1f}" if r[4] else "-",
                date_str
            )
        
        console.print(table)
        console.print(f"[dim]Toplam {len(results)} kayıt gösteriliyor.[/dim]")
        
    except Exception as e:
        console.print(f"[red]❌ Hata: {e}[/red]")
    finally:
        db.close()


def export(filename: str = None):
    """Tüm verileri Excel'e aktar (son metriklerle)"""
    db = get_db_manager()
    session = db.get_session()
    
    if not filename:
        filename = f"rapor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    console.print(f"\n[cyan]💾 Veriler dışa aktarılıyor: {filename}[/cyan]\n")
    
    try:
        results = session.execute(text("""
            SELECT p.url, p.brand, p.name, 
                   dm.discounted_price, dm.price, dm.discount_rate,
                   dm.avg_rating, dm.rating_count, dm.favorite_count,
                   dm.cart_count, dm.clicks_24h, dm."date"
            FROM products p
            JOIN daily_metrics dm ON dm.product_id = p.id
            WHERE dm.id IN (
                SELECT MAX(id) FROM daily_metrics GROUP BY product_id
            )
            ORDER BY dm.favorite_count DESC NULLS LAST
        """)).fetchall()
        
        data = []
        for r in results:
            data.append({
                'URL': r[0],
                'Marka': r[1],
                'Ürün Adı': r[2],
                'Fiyat': r[3],
                'Eski Fiyat': r[4],
                'İndirim %': r[5],
                'Puan': r[6],
                'Yorum': r[7],
                'Favori': r[8],
                'Sepet': r[9],
                'Görüntüleme': r[10],
                'Son Güncelleme': r[11]
            })
        
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False)
        
        console.print(f"[bold green]✅ {len(data)} ürün {filename} dosyasına kaydedildi![/bold green]")
        
    except Exception as e:
        console.print(f"[red]❌ Hata: {e}[/red]")
    finally:
        db.close()

def reset():
    """Veritabanını sıfırla (DİKKAT!)"""
    db = get_db_manager()
    session = db.get_session()
    
    confirm = input("⚠️  TÜM VERİLER SİLİNECEK! Emin misiniz? (evet/hayır): ")
    if confirm.lower() != 'evet':
        console.print("[yellow]İşlem iptal edildi.[/yellow]")
        return
    
    try:
        session.execute(text("TRUNCATE TABLE daily_metrics RESTART IDENTITY CASCADE"))
        session.execute(text("TRUNCATE TABLE products RESTART IDENTITY CASCADE"))
        session.commit()
        console.print("[bold green]✅ Veritabanı temizlendi![/bold green]")
        
    except Exception as e:
        console.print(f"[red]❌ Hata: {e}[/red]")
    finally:
        db.close()


def stats():
    """Hızlı istatistikler"""
    db = get_db_manager()
    session = db.get_session()
    
    try:
        products = session.execute(text("SELECT COUNT(*) FROM products")).scalar()
        metrics = session.execute(text("SELECT COUNT(*) FROM daily_metrics")).scalar()
        avg_price = session.execute(text("""
            SELECT AVG(discounted_price) FROM daily_metrics 
            WHERE id IN (SELECT MAX(id) FROM daily_metrics GROUP BY product_id)
            AND discounted_price > 0
        """)).scalar()
        
        console.print(f"\n📊 Ürün: {products} | Metrik: {metrics} | Ort. Fiyat: {avg_price or 0:.0f} TL\n")
        
    except Exception as e:
        console.print(f"[red]❌ Hata: {e}[/red]")
    finally:
        db.close()


def history(url: str):
    """Bir ürünün fiyat geçmişini göster"""
    db = get_db_manager()
    session = db.get_session()
    
    console.print(f"\n[bold cyan]📈 FİYAT GEÇMİŞİ[/bold cyan]\n")
    
    try:
        results = session.execute(text("""
            SELECT p.name, dm.discounted_price, dm.favorite_count, dm."date"
            FROM products p
            JOIN daily_metrics dm ON dm.product_id = p.id
            WHERE p.url = :url
            ORDER BY dm."date" DESC
            LIMIT 30
        """), {"url": url}).fetchall()
        
        if not results:
            console.print(f"[yellow]⚠️ Ürün bulunamadı: {url}[/yellow]")
            return
        
        console.print(f"[bold]{results[0][0]}[/bold]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Tarih", justify="right")
        table.add_column("Fiyat", justify="right")
        table.add_column("❤️ Favori", justify="right")
        
        for r in results:
            date_str = r[3].strftime("%d/%m/%Y %H:%M") if r[3] else "-"
            table.add_row(
                date_str,
                f"{r[1]:.0f} TL" if r[1] else "-",
                f"{r[2]:,}" if r[2] else "-"
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]❌ Hata: {e}[/red]")
    finally:
        db.close()
