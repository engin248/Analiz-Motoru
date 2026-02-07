
import sys
import os
from sqlalchemy import text

# Paths setup
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
backend_path = os.path.join(parent_dir, 'LangChain_backend')
sys.path.append(backend_path)

# DB Imports
from app.core.database import SessionLocal
from rich.console import Console

console = Console()

def clear_database():
    db = SessionLocal()
    try:
        console.print("[bold red]⚠️  TÜM VERİLER SİLİNİYOR...[/bold red]")
        
        # Önce bağımlı tabloyu (metrics) sonra ana tabloyu (products) sil
        db.execute(text("TRUNCATE TABLE daily_metrics RESTART IDENTITY CASCADE;"))
        db.execute(text("TRUNCATE TABLE products RESTART IDENTITY CASCADE;"))
        
        db.commit()
        console.print("[bold green]✅ Veritabanı başarıyla temizlendi (Pırıl pırıl)! ✨[/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]❌ Silme Hatası:[/bold red] {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    permission = input("Tüm verileri silmek istediğinize emin misiniz? (E/H): ")
    if permission.lower() == 'e':
        clear_database()
    else:
        print("İşlem iptal edildi.")
