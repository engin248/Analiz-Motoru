
import sys
import os
from sqlalchemy import text
from rich.console import Console
from rich.table import Table
from rich import box

# Paths setup
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
backend_path = os.path.join(parent_dir, 'LangChain_backend')
sys.path.append(backend_path)

# DB Imports
from app.core.database import SessionLocal
from app.models.product import Product
from app.models.daily_metric import DailyMetric

console = Console(width=100)

def show_verification_table():
    db = SessionLocal()
    try:
        # Son taranan 20 ürünü detaylarıyla çek
        results = db.query(DailyMetric, Product)\
            .join(Product, DailyMetric.product_id == Product.id)\
            .order_by(DailyMetric.id.desc())\
            .limit(20)\
            .all()
        
        console.print("\n[bold yellow]SON 20 İŞLENEN ÜRÜN[/bold yellow]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Ad", width=30)
        table.add_column("Fiyat", justify="right")
        table.add_column("Favori", justify="right")
        table.add_column("Sepet", justify="right")
        table.add_column("Puan", justify="center")

        for metric, prod in results:
            name = prod.name[:27] + "..." if prod.name and len(prod.name) > 30 else (prod.name or "-")
            price = f"{metric.discounted_price:.0f} TL"
            fav = f"{metric.favorite_count:,}"
            cart = f"{metric.cart_count:,}"
            rate = f"{metric.avg_rating}"
            
            table.add_row(name, price, fav, cart, rate)
            
        console.print(table)
        console.print(f"\n[green]Toplam {len(results)} kayıt gösteriliyor.[/green]")

    except Exception as e:
        console.print(f"[bold red]❌ Hata:[/bold red] {e}")
    finally:
        db.close()
        


if __name__ == "__main__":
    show_verification_table()
