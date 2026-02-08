
import sys
import os
import time
from datetime import datetime, timedelta
from sqlalchemy import text
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.align import Align
from rich.text import Text

# Paths setup
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
backend_path = os.path.join(parent_dir, 'LangChain_backend')
sys.path.append(backend_path)

# DB Imports
from app.core.database import SessionLocal
from app.models.product import Product
from app.models.daily_metric import DailyMetric

console = Console()

def get_db_stats():
    db = SessionLocal()
    try:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 1. Toplam Ürün Sayısı
        total_products = db.query(Product).count()
        
        # 2. Bugün Eklenen (Yeni Ürün)
        today_new_products = db.query(Product).filter(Product.first_seen_at >= today_start).count()
        
        # 3. Bugün İşlenen (Scraped)
        # last_scraped_at bugüne ait olanlar
        today_scraped = db.query(Product).filter(Product.last_scraped_at >= today_start).count()
        
        # 4. Eksik Veriler (Link var ama detay yok)
        # last_scraped_at NULL veya bugün değil
        pending_scrape = db.query(Product).filter(
            (Product.last_scraped_at < today_start) | (Product.last_scraped_at == None)
        ).count()
        
        # 5. Kategorilere Göre En Pahalı/Ucuz (Basit Analiz)
        # Sadece bugün güncellenenlerden örnek alalım
        expensive_sample = db.query(DailyMetric).filter(DailyMetric.recorded_at >= today_start).order_by(DailyMetric.discounted_price.desc()).first()
        cheap_sample = db.query(DailyMetric).filter(DailyMetric.recorded_at >= today_start).order_by(DailyMetric.discounted_price.asc()).first()
        
        # 6. Son Logları Çek (YENİ)
        from src.models_log import SystemLog
        recent_logs = db.query(SystemLog).order_by(SystemLog.id.desc()).limit(5).all()

        return {
            "total": total_products,
            "today_new": today_new_products,
            "today_scraped": today_scraped,
            "pending": pending_scrape,
            "expensive": expensive_sample,
            "cheap": cheap_sample,
            "recent_logs": recent_logs, # Eklendi
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
    except Exception as e:
        console.print(f"[red]DB Bağlantı Hatası: {e}[/red]")
        return None
    finally:
        db.close()

def generate_dashboard(stats):
    if not stats:
        return Panel(Text("Veri Alınamadı!", style="bold red"))

    # --- ANA TABLO ---
    table = Table(title="🤖 ANALİZ MOTORU - CANLI TAKİP EKRANI", style="cyan", border_style="bright_blue", width=70)
    
    table.add_column("Metrik", style="white", justify="left")
    table.add_column("Değer", style="bold yellow", justify="right")
    table.add_column("Durum", style="italic green", justify="center")

    # Satırlar
    table.add_row("📦 Toplam Ürün Havuzu", f"{stats['total']:,}", "✅ Aktif")
    table.add_row("🌾 Bugün Eklenen (Yeni Link)", f"+{stats['today_new']}", "🆕 Taze")
    table.add_row("🏭 Bugün İşlenen (Detay)", f"{stats['today_scraped']}", "⚙️ Çalışıyor" if stats['today_scraped'] > 0 else "💤 Beklemede")
    table.add_row("⏳ Sırada Bekleyen (İşlenecek)", f"{stats['pending']}", "⚠️ Darboğaz" if stats['pending'] > 1000 else "Normal")

    # --- ALT BİLGİ PANELİ ---
    info_text = Text()
    info_text.append(f"\nSon Güncelleme: {stats['timestamp']}\n", style="dim white")
    
    if stats['expensive']:
        p = stats['expensive']
        info_text.append(f"💎 Günün En Pahalı Ürünü: {p.discounted_price} TL (ID: {p.product_id})\n", style="bold magenta")
    
    if stats['cheap']:
        p = stats['cheap']
        info_text.append(f"🏷️ Günün En Ucuz Ürünü: {p.discounted_price} TL (ID: {p.product_id})\n", style="bold green")

    # --- LOG PANELİ (YENİ) ---
    log_text = Text()
    if stats.get('recent_logs'):
        for log in stats['recent_logs']:
            icon = "✅" if log.level == "INFO" else "❌"
            time_str = log.timestamp.strftime("%H:%M:%S")
            log_text.append(f"{time_str} {icon} [{log.bot_name}] {log.message}\n", style="green" if log.level=="INFO" else "bold red")
    else:
        log_text.append("Henüz log kaydı yok...", style="dim")

    # Birleştirme (3 Panel)
    layout = Layout()
    layout.split_column(
        Layout(Align.center(table), size=10),
        Layout(Panel(info_text, title="📊 Anlık Piyasa Özeti", border_style="green"), size=8),
        Layout(Panel(log_text, title="📜 Canlı Log Akışı", border_style="yellow"), size=10) # Log Paneli
    )
    
    return layout

if __name__ == "__main__":
    console.print("[bold yellow]🚀 Dashboard Başlatılıyor... (Çıkış için Ctrl+C)[/bold yellow]")
    
    with Live(generate_dashboard(get_db_stats()), refresh_per_second=1) as live:
        while True:
            try:
                stats = get_db_stats()
                live.update(generate_dashboard(stats))
                time.sleep(5) # 5 saniyede bir yenile
            except KeyboardInterrupt:
                console.print("\n[bold red]🛑 Dashboard Kapatıldı.[/bold red]")
                break
