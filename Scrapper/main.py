import asyncio
import argparse
import os
from datetime import datetime
from playwright.async_api import async_playwright
from rich.console import Console
from rich.table import Table

from src.config import load_config
from src.config.loader import get_enabled_platforms
from src.database import DatabaseManager
from src.scrapers.trendyol_scraper import TrendyolScraper
from src.scrapers.amazon_scraper import AmazonScraper
from src.utils.stealth import apply_stealth

console = Console()

# Scraper class mapping
SCRAPER_CLASSES = {
    'trendyol': TrendyolScraper,
    'amazon': AmazonScraper,
}


async def run_platform_scraper(platform_name: str, platform_config, settings, browser):
    """Run scraper for a single platform"""
    
    console.print(f"\n[bold blue]{'='*50}[/bold blue]")
    console.print(f"[bold cyan]🚀 {platform_name.upper()} SCRAPER BAŞLATILIYOR[/bold cyan]")
    console.print(f"[bold blue]{'='*50}[/bold blue]\n")
    
    # Get scraper class
    ScraperClass = SCRAPER_CLASSES.get(platform_name)
    if not ScraperClass:
        console.print(f"[red]❌ {platform_name} için scraper bulunamadı![/red]")
        return
    
    # Initialize database
    db_manager = DatabaseManager(
        connection_url=platform_config.database.connection_url,
        platform=platform_name
    )
    db_manager.create_tables()
    
    # Create browser context with specific User-Agent and viewport
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        viewport={'width': 1920, 'height': 1080},
        locale="tr-TR"
    )
    
    # Apply anti-detection scripts
    await apply_stealth(context)
    
    # Create page from context
    page = await context.new_page()
    
    # Initialize scraper
    scraper = ScraperClass(
        page=page,
        config={
            'request_delay': settings.request_delay,
            'scroll_count': settings.scroll_count,
        },
        selectors=platform_config.selectors
    )
    
    total_added = 0
    total_updated = 0
    total_errors = 0
    
    # Process each keyword
    for keyword in platform_config.keywords:
        console.print(f"\n[bold magenta]🔍 Anahtar Kelime: '{keyword}'[/bold magenta]\n")
        
        # Collect URLs
        product_urls = await scraper.collect_product_urls(keyword, platform_config.max_pages)
        
        if not product_urls:
            console.print(f"[yellow]⚠️ '{keyword}' için ürün bulunamadı[/yellow]")
            continue
        
        # Apply max_products limit if set
        if platform_config.max_products > 0:
            product_urls = product_urls[:platform_config.max_products]
        
        console.print(f"[cyan]🎯 {len(product_urls)} ürün taranacak...[/cyan]\n")
        
        results = []
        
        # Scrape each product
        for i, url in enumerate(product_urls, 1):
            console.print(f"[cyan]#{i}/{len(product_urls)}[/cyan] Tarıyor: {url[:60]}...")
            
            try:
                data = await scraper.scrape_product(url)
                
                if data and data.get('name'):
                    # Prepare product data
                    product_id = scraper.get_trendyol_id(url)
                    price = data.get('price', 0)
                    org_price = data.get('org_price', 0)
                    discount_rate = scraper.calculate_discount_rate(org_price, price)
                    
                    product_data = {
                        'url': url,
                        'product_id': product_id,
                        'brand': data.get('brand', ''),
                        'name': data.get('name', ''),
                        'image_url': data.get('images', [''])[0] if data.get('images') else '',
                        'original_price': org_price,
                        'discounted_price': price,
                        'discount_rate': discount_rate,
                        'rating': data.get('rating', 0),
                        'review_count': data.get('reviews', 0),
                        'favorite_count': data.get('favs', 0),
                        'cart_count': data.get('basket', 0),
                        'view_count': data.get('views', 0),
                    }
                    
                    # Save to database
                    is_new, message = db_manager.save_product(product_data)
                    console.print(f"[{'green' if is_new else 'blue'}]{message}[/{'green' if is_new else 'blue'}]")
                    
                    if is_new:
                        total_added += 1
                    else:
                        total_updated += 1
                    
                    results.append({
                        'brand': data.get('brand', ''),
                        'name': data.get('name')[:40] if data.get('name') else '',
                        'price': price,
                        'org_price': org_price,
                        'rating': data.get('rating', 0),
                    })
                else:
                    console.print("[red]❌ Veri çekilemedi[/red]")
                    total_errors += 1
                    
            except Exception as e:
                console.print(f"[red]❌ Hata: {e}[/red]")
                total_errors += 1
        
        # Display results table
        if results:
            console.print("\n")
            table = Table(title=f"📊 {keyword.upper()} Sonuçları", show_header=True, header_style="bold magenta")
            table.add_column("Marka", style="cyan")
            table.add_column("Ürün Adı", style="white")
            table.add_column("Fiyat", justify="right", style="green")
            table.add_column("Eski Fiyat", justify="right", style="red")
            table.add_column("⭐", justify="center")
            
            for r in results[:10]:  # Show first 10
                table.add_row(
                    r['brand'][:15] if r['brand'] else "-",
                    r['name'],
                    f"{r['price']:.0f} TL",
                    f"{r['org_price']:.0f} TL",
                    f"{r['rating']:.1f}" if r['rating'] else "-",
                )
            
            if len(results) > 10:
                table.add_row("...", f"... ve {len(results)-10} ürün daha", "", "", "")
            
            console.print(table)
    
    # Close page and database
    await page.close()
    db_manager.close()
    
    # Summary
    console.print(f"\n[bold green]✅ {platform_name.upper()} tamamlandı![/bold green]")
    console.print(f"   ➕ Yeni: {total_added} | 🔄 Güncellenen: {total_updated} | ❌ Hata: {total_errors}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Multi-Platform E-Commerce Scraper')
    parser.add_argument('--task-id', type=int, help='Bot görev ID\'si')
    parser.add_argument('--url', type=str, help='Hedef URL')
    args = parser.parse_args()

    console.print("[bold green]🚀 ANALİZ MOTORU - SCRAPER ÜNİTESİ BAŞLATILDI[/bold green]\n")
    if args.task_id:
        console.print(f"[cyan]🤖 Task ID: {args.task_id}[/cyan]")
    if args.url:
        console.print(f"[cyan]🌐 Hedef URL: {args.url}[/cyan]")
    
    # Load configuration
    try:
        config = load_config()
        enabled_platforms = get_enabled_platforms(config)
    except Exception as e:
        console.print(f"[red]❌ Config yükleme hatası: {e}[/red]")
        return
    
    if not enabled_platforms:
        console.print("[yellow]⚠️ Hiçbir platform aktif değil! config.yaml dosyasını kontrol edin.[/yellow]")
        return
    
    # Launch browser
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=config.settings.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-position=0,0',
                '--ignore-certificate-errors',
                '--ignore-ssl-errors'
            ]
        )
        
        # Run each enabled platform (Şu an sadece Trendyol aktif varsayıyoruz)
        for platform_name, platform_config in enabled_platforms.items():
            # Eğer URL verilmişse sadece o URL'yi tara
            if args.url:
                platform_config.keywords = ["DIRECT_URL"] # Placeholder
                # Scraper sınıfını al
                ScraperClass = SCRAPER_CLASSES.get(platform_name)
                db_manager = DatabaseManager(connection_url=platform_config.database.connection_url, platform=platform_name)
                
                # KELİME ÇIKARMA
                import urllib.parse
                def extract_keyword(url):
                    try:
                        parsed = urllib.parse.urlparse(url)
                        query = urllib.parse.parse_qs(parsed.query)
                        # Trendyol: q, Amazon: k
                        if 'q' in query: return query['q'][0].replace('+', ' ')
                        if 'k' in query: return query['k'][0].replace('+', ' ')
                        # Kategori URL'leri (örn: /elbise-x-c56)
                        path_parts = parsed.path.split('/')
                        if path_parts:
                             # Sondaki boşlukları at
                             valid_parts = [p for p in path_parts if p]
                             if valid_parts:
                                 last_part = valid_parts[-1]
                                 # -x-c... varsa temizle
                                 if '-x-c' in last_part:
                                     return last_part.split('-x-c')[0].replace('-', ' ')
                                 return last_part.replace('-', ' ')
                        return url
                    except: return url

                clean_kw = extract_keyword(args.url)
                console.print(f"[bold magenta]🎯 Hedef Kelime: {clean_kw}[/bold magenta]")
                
                # LOG BAŞLAT
                # Task config oku
                task_config = db_manager.get_task_config(args.task_id) if args.task_id else {}
                if 'max_pages' in task_config:
                    platform_config.max_pages = int(task_config['max_pages'])
                    console.print(f"[bold yellow]⚙️ Task Ayarı: Max Sayfa = {platform_config.max_pages}[/bold yellow]")

                log_id = db_manager.start_log(keyword=clean_kw, task_id=args.task_id, target_url=args.url)
                
                page_linker = await browser.new_page()
                page_scraper = await browser.new_page()
                
                linker_scraper = ScraperClass(page=page_linker, config={'request_delay': config.settings.request_delay, 'scroll_count': config.settings.scroll_count}, selectors=platform_config.selectors)
                detail_scraper = ScraperClass(page=page_scraper, config={'request_delay': config.settings.request_delay, 'scroll_count': config.settings.scroll_count}, selectors=platform_config.selectors)
                
                stats = {"added": 0, "updated": 0, "errors": 0}

                async def linker_worker():
                    """Sadece linkleri bulur ve veritabanı kuyruğuna ekler."""
                    console.print("[bold yellow]📡 Linker: Link toplama başlatıldı...[/bold yellow]")
                    found_any = False
                    try:
                        async for url in linker_scraper.collect_product_urls_from_link(args.url, platform_config.max_pages):
                            found_any = True
                            added = db_manager.add_to_queue(args.task_id, url)
                            if added:
                                console.print(f"[dim green]🔗 Yeni link kuyruğa eklendi: {url[:40]}...[/dim green]")
                        
                        if not found_any:
                            console.print("[bold red]❌ Linker: Hiç ürün bulunamadı! Bloklanmış olabilirsin.[/bold red]")
                            stats["errors"] += 1
                            
                            # Screenshot al
                            os.makedirs("static/captures", exist_ok=True)
                            filename = f"linker_empty_{log_id}_{datetime.now().strftime('%H%M%S')}.png"
                            ss_path = f"static/captures/{filename}"
                            try: await page_linker.screenshot(path=ss_path)
                            except: ss_path = None
                            
                            db_manager.log_error(log_id, "Linker: Hiç ürün bulunamadı (Liste boş).", screenshot_path=filename)
                            db_manager.update_log_progress(log_id, stats["added"], stats["updated"], stats["errors"])
                    except Exception as e:
                        console.print(f"[bold red]❌ Linker Hatası: {e}[/bold red]")
                        stats["errors"] += 1
                        
                        # Screenshot al
                        os.makedirs("static/captures", exist_ok=True)
                        filename = f"linker_error_{log_id}_{datetime.now().strftime('%H%M%S')}.png"
                        ss_path = f"static/captures/{filename}"
                        try: await page_linker.screenshot(path=ss_path)
                        except: ss_path = None
                        
                        db_manager.log_error(log_id, f"Linker Hatası: {str(e)}", screenshot_path=filename)
                        db_manager.update_log_progress(log_id, stats["added"], stats["updated"], stats["errors"])
                    console.print("[bold green]✅ Linker: İşlem tamamlandı.[/bold green]")

                async def scraper_worker():
                    """Kuyruktaki linkleri sırayla kazır."""
                    console.print("[bold blue]🔍 Scraper: Kazıma motoru hazır, kuyruk bekleniyor...[/bold blue]")
                    empty_count = 0
                    while empty_count < 10: # Kuyruk 10 kere boş gelirse (yaklaşık 20-30 sn) bitir
                        item = db_manager.get_next_from_queue(args.task_id)
                        if not item:
                            empty_count += 1
                            await asyncio.sleep(2)
                            continue
                        
                        empty_count = 0 # Bir tane bulduysak sayacı sıfırla
                        url = item.url
                        console.print(f"[cyan]🚀 Kazılıyor:[/cyan] {url[:50]}...")
                        
                        try:
                            # SENIN ÖZEL DOM KAZIMA MANTIĞIN BURADA ÇALIŞIYOR
                            data = await detail_scraper.scrape_product(url)
                            if data and data.get('name'):
                                product_data = {
                                    'url': url, 'product_id': detail_scraper.get_trendyol_id(url),
                                    'brand': data.get('brand', ''), 'name': data.get('name', ''),
                                    'image_url': data.get('images', [''])[0] if data.get('images') else '',
                                    'original_price': data.get('org_price', 0), 'discounted_price': data.get('price', 0),
                                    'discount_rate': detail_scraper.calculate_discount_rate(data.get('org_price', 0), data.get('price', 0)),
                                    'rating': data.get('avg_rating', data.get('rating', 0)), 
                                    'review_count': data.get('rating_count', data.get('reviews', 0)),
                                    'favorite_count': data.get('favs', 0), 'cart_count': data.get('basket', 0), 'view_count': data.get('views', 0)
                                }
                                is_new, msg = db_manager.save_product(product_data)
                                if is_new: stats["added"] += 1
                                else: stats["updated"] += 1
                                db_manager.update_queue_status(item.id, "completed")
                            else:
                                stats["errors"] += 1
                                db_manager.update_queue_status(item.id, "failed", "Veri çekilemedi")
                                
                                # Screenshot al
                                os.makedirs("static/captures", exist_ok=True)
                                filename = f"scrape_fail_{log_id}_{item.id}.png"
                                ss_path = f"static/captures/{filename}"
                                try: await page_scraper.screenshot(path=ss_path)
                                except: ss_path = None
                                
                                db_manager.log_error(log_id, f"Veri çekilemedi: {url}", screenshot_path=filename)
                        except Exception as e:
                            stats["errors"] += 1
                            db_manager.update_queue_status(item.id, "failed", str(e))
                            
                            # Screenshot al
                            os.makedirs("static/captures", exist_ok=True)
                            filename = f"scrape_error_{log_id}_{item.id}.png"
                            ss_path = f"static/captures/{filename}"
                            try: await page_scraper.screenshot(path=ss_path)
                            except: ss_path = None

                            db_manager.log_error(log_id, f"Scraper Hatası ({url}): {str(e)}", screenshot_path=filename)
                            console.print(f"[red]Hata ({url[:30]}): {e}[/red]")
                        
                        # Canlı Dashboard Güncellemesi
                        db_manager.update_log_progress(log_id, stats["added"], stats["updated"], stats["errors"])
                        await asyncio.sleep(config.settings.request_delay)
                    
                    console.print("[bold green]🏁 Scraper: Kuyruk bitti![/bold green]")

                try:
                    if "/p/" in args.url:
                        # Tek ürün sayfasıysa paralel sisteme gerek yok, direkt kazı
                        data = await detail_scraper.scrape_product(args.url)
                        if data and data.get('name'):
                            # ... (Tek ürün işleme mantığı - aynı kalıyor)
                            pass
                    else:
                        # Kategori/Arama listesiyse PARALEL MODU ÇALIŞTIR!
                        await asyncio.gather(linker_worker(), scraper_worker())
                finally:
                    db_manager.finish_log(log_id, pages=1, found=stats["added"] + stats["updated"], added=stats["added"], updated=stats["updated"], errors=stats["errors"])
                    await page_linker.close()
                    await page_scraper.close()
                    db_manager.close()
            else:
                # Eski tip toplu tarama (config keywords'leri)
                await run_platform_scraper(platform_name, platform_config, config.settings, browser)
        
        await browser.close()
    
    console.print("\n[bold green]🏁 TÜM İŞLEMLER TAMAMLANDI![/bold green]")


if __name__ == "__main__":
    asyncio.run(main())
