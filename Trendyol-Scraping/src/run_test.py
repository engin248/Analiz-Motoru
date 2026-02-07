
import asyncio
import pandas as pd
import os
import sys
from playwright.async_api import async_playwright
from rich.console import Console

# Path Fix (src içinde olduğumuz için)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importlar (src içindeyken böyle çalışmalı)
try:
    from scrapers.product_scraper import ProductScraper
    from database.db import Database
except ImportError:
    # Eğer src bir paketse
    from src.scrapers.product_scraper import ProductScraper
    from src.database.db import Database

console = Console()

async def run_final_test():
    console.print("[bold blue]🚀 FİNAL TEST BAŞLATILIYOR (SRC İÇİNDEN)[/bold blue]\n")
    
    # 1. Excel'den Linkleri Oku (KÖK DİZİNDEN)
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files = [f for f in os.listdir(root_dir) if f.startswith('linkler_') and f.endswith('.xlsx')]
    if not files:
        console.print("[red]❌ Link dosyası bulunamadı![/red]")
        return
    link_file = os.path.join(root_dir, max(files, key=lambda f: os.path.getctime(os.path.join(root_dir, f))))
    
    console.print(f"[cyan]📂 Link dosyası: {link_file}[/cyan]")
    df = pd.read_excel(link_file)
    links = df['Link'].head(50).tolist()
    
    console.print(f"[green]✅ {len(links)} link yüklendi.[/green]\n")
    
    # DB path
    db_path = f"sqlite:///{os.path.join(root_dir, 'test_final.db')}"
    if os.path.exists(os.path.join(root_dir, 'test_final.db')):
        try: os.remove(os.path.join(root_dir, 'test_final.db'))
        except: pass
        
    db = Database(db_path)
    await db.create_tables()
    
    async with async_playwright() as p:
        # HEADLESS=TRUE (HIZ İÇİN)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        scraper = ProductScraper(page)
        scraper.db = db
        
        results = []
        success = 0
        fail = 0
        
        for i, link in enumerate(links, 1):
            console.print(f"\n[cyan]#{i} Gidiliyor...[/cyan]")
            try:
                data = await scraper.scrape_product(link)
                if data:
                    price = data.get('discounted_price', 0)
                    method = data.get('method', '-')
                    if price > 0:
                        console.print(f"[green]✅ {data.get('product_name','?')[:30]}... : {price} TL ({method})[/green]")
                        success += 1
                        results.append(data)
                    else:
                        console.print(f"[red]❌ Ürün (0 TL): {data.get('product_name','?')[:30]}...[/red]")
                        fail += 1
                else:
                    console.print("[red]❌ Veri Alınamadı[/red]")
                    fail += 1
            except Exception as e:
                console.print(f"[red]❌ Hata: {e}[/red]")
                fail += 1
                
            await asyncio.sleep(1)
            
        await browser.close()
        
    if results:
        out_file = os.path.join(root_dir, "final_results.xlsx")
        pd.DataFrame(results).to_excel(out_file, index=False)
        console.print(f"\n✅ Toplam: {success} Başarılı, {fail} 0 TL Fiyat. Dosya: {out_file}")

if __name__ == "__main__":
    asyncio.run(run_final_test())
