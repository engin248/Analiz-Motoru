import asyncio
import pandas as pd
from playwright.async_api import async_playwright
from rich.console import Console
from datetime import datetime
import random
import os

# Kendi modüllerimiz
# Kendi modüllerimiz
import sys
import os

# Paths setup to reach LangChain_backend
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
backend_path = os.path.join(parent_dir, 'LangChain_backend')
sys.path.append(backend_path)

from src.scrapers.search_scraper import SearchScraper
from src.utils.stealth import apply_stealth

# DB Imports
from app.core.database import SessionLocal
from app.models.product import Product
from app.models.daily_metric import DailyMetric

console = Console()

async def harvest_links(keyword: str, max_pages: int = 200):
    """
    Belirtilen kelime için sayfaları gezer ve linkleri toplar.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_file = f"linkler_{keyword}_{date_str}.xlsx"
    
    # Cookie/State yönetimi (Burada da hafızayı kullanalım)
    USER_DATA_DIR = "user_data"
    STATE_FILE = os.path.join(USER_DATA_DIR, "state.json")
    
    all_links = []
    seen_links = set()
    
    console.print(f"[bold green]🌱 Link Hasadı Başlıyor: '{keyword}' (Hedef: {max_pages} Sayfa)[/bold green]")

    async with async_playwright() as p:
        # Tarayıcıyı başlat (HEADLESS MODE - 2x Hız Artışı)
        browser = await p.chromium.launch(
            headless=True,  # ✅ Optimizasyon: False->True (Görsel mod kapalı)
            args=['--disable-blink-features=AutomationControlled']
        )
        
        # Context ayarları
        context_args = {
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
        
        # Cookie yükle (Varsa)
        if os.path.exists(STATE_FILE):
            context_args['storage_state'] = STATE_FILE
        
        context = await browser.new_context(**context_args)
        
        # 🕵️‍♂️ Gizlilik Modu
        await apply_stealth(context)
        
        page = await context.new_page()
        scraper = SearchScraper(page)
        
        try:
            for page_num in range(1, max_pages + 1):
                console.print(f"[cyan]📄 Sayfa Taraniyor: {page_num}/{max_pages}[/cyan]")
                
                links = await scraper.get_product_links(keyword, page_num)
                
                # Redirect kontrolü (URL Bazlı)
                if links is None:
                    console.print(f"[bold yellow]🔄 URL Yönlendirmesi algılandı. Oturum sıfırlanıp tekrar deneniyor...[/bold yellow]")
                    # --- OTURUM YENİLEME ---
                    await context.close()
                    await asyncio.sleep(2)
                    context = await browser.new_context(**context_args)
                    await apply_stealth(context)
                    page = await context.new_page()
                    scraper = SearchScraper(page)
                    console.print(f"[cyan]🔄 Yeni oturumla {page_num}. sayfa tekrar deneniyor...[/cyan]")
                    links = await scraper.get_product_links(keyword, page_num)
                    if links is None:
                        console.print(f"[bold red]⛔ Yeni oturumda da yönlendirme devam ediyor. Pes edildi.[/bold red]")
                        break

                if not links:
                    console.print(f"[red]⚠️  Sayfa {page_num} boş veya hata alındı.[/red]")
                    if page_num > 5: break
                    continue

                # --- İÇERİK BAZLI TEKRAR KONTROLÜ (DUPLICATE CHECK) ---
                new_links_count = 0
                temp_links_to_add = []
                
                for link in links:
                    if link not in seen_links:
                        seen_links.add(link)
                        # Linki ekle
                        temp_links_to_add.append({
                            'Link': link,
                            'Sayfa': page_num,
                            'Sıralama': (page_num - 1) * 24 + len(temp_links_to_add) + 1,
                            'Tarama Tarihi': datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                        new_links_count += 1
                
                # Eğer sayfa dolu geldi ama hepsi zaten bizde varsa -> TUZAK SAYFA
                if new_links_count == 0 and len(links) > 0:
                    console.print(f"[bold red]⛔ TUZAK TESPİTİ! Bu sayfadaki {len(links)} linkin hepsi zaten var. Trendyol bizi eski sayfaya attı.[/bold red]")
                    console.print(f"[bold yellow]🔄 Tuzak nedeniyle Oturum sıfırlanıp tekrar deneniyor...[/bold yellow]")
                    
                    # --- AYNI OTURUM YENİLEME MANTIĞI ---
                    await context.close()
                    await asyncio.sleep(2)
                    context = await browser.new_context(**context_args)
                    await apply_stealth(context)
                    page = await context.new_page()
                    scraper = SearchScraper(page)
                    
                    console.print(f"[cyan]🔄 Yeni oturumla {page_num}. sayfa tekrar deneniyor...[/cyan]")
                    # Tekrar dene
                    links = await scraper.get_product_links(keyword, page_num)
                    
                    # Tekrar kontrole gerek yok, bu turu pas geçip bir sonraki sayfaya veya aynı sayfaya bakacağız
                    # Ama burada links'i tekrar işleyebiliriz. Basitlik için:
                    # Eğer yeni oturumda link geldiyse, onları tekrar süzgeçten geçir.
                    if links:
                        # Tekrar süz
                        for link in links:
                            if link not in seen_links:
                                seen_links.add(link)
                                temp_links_to_add.append({
                                    'Link': link,
                                    'Sayfa': page_num,
                                    'Sıralama': (page_num - 1) * 24 + len(temp_links_to_add) + 1,
                                    'Tarama Tarihi': datetime.now().strftime("%Y-%m-%d %H:%M")
                                })

                # Listeye ekle
                all_links.extend(temp_links_to_add)
                
                if len(temp_links_to_add) > 0:
                    console.print(f"[green]✅ Sayfa {page_num} tamamlandı. {len(temp_links_to_add)} YENİ link eklendi. (Toplam: {len(all_links)})[/green]")
                else:
                    console.print(f"[yellow]⚠️ Sayfa {page_num} tamamlandı ama YENİ link çıkmadı.[/yellow]")
                
                # Excel'e anlık kaydet
                df = pd.DataFrame(all_links)
                df.to_excel(output_file, index=False)
                
                # --- DB KAYIT (LangChain_backend Entegrasyonu) ---
                try:
                    db = SessionLocal()
                    added_count = 0
                    
                    for i, item in enumerate(temp_links_to_add):
                        l = item['Link']
                        
                        # --- 1. SIRA HESAPLAMA (Rank Calculation) ---
                        # Sayfa başı 24 ürün varsayımıyla genel sıralama
                        # Formül: (Sayfa - 1) * 24 + (Sıfırdan Başlayan İndeks) + 1
                        current_rank = (page_num - 1) * 24 + i + 1
                        
                        # --- 2. ÜRÜN KONTROLÜ / EKLEME ---
                        product = db.query(Product).filter(Product.url == l).first()
                        
                        if not product:
                            # Extract ID from URL if possible, or use random
                            import re
                            t_id_match = re.search(r'-p-(\d+)', l)
                            t_id = t_id_match.group(1) if t_id_match else f"auto_{datetime.now().timestamp()}"
                            
                            product = Product(
                                product_code=t_id,
                                url=l,
                                first_seen_at=datetime.utcnow()
                            )
                            db.add(product)
                            db.commit() # ID almak için commit lazım
                            db.refresh(product)
                            added_count += 1
                        
                        # --- 3. METRİK KAYDI (Sadece Sıralama İçin) ---
                        # Eğer bugün için bu ürünün kaydı varsa güncelle, yoksa yeni aç
                        # Amaç: Rank bilgisini kaybetmemek
                        
                        # Not: Scraper (scrape_ultra) daha sonra gelip bu satırı detaylarla dolduracak
                        # Biz şimdilik sadece "Yer Tutucu" ve "Sıralama Bilgisi" ekliyoruz.
                        
                        today_metric = DailyMetric(
                            product_id=product.id,
                            sales_rank=current_rank, # İşte sihirli dokunuş burası! 🎯
                            recorded_at=datetime.utcnow()
                        )
                        db.add(today_metric)
                    
                    if added_count > 0:
                        db.commit()
                        console.print(f"[green]💾 Veritabanına {added_count} yeni ürün eklendi. (Sıralama Bilgisiyle)[/green]")
                    else:
                        db.commit() # Mevcut ürünlerin rank bilgisini kaydetmek için
                        console.print(f"[dim]💾 {len(temp_links_to_add)} ürünün sıralama bilgisi güncellendi.[/dim]")
                        
                    db.close()
                except Exception as e:
                    console.print(f"[red]❌ DB Kayıt Hatası: {e}[/red]")
                # -----------------------------------------------
                
                # --- PERİYODİK BAKIM (Her 20 Sayfada Bir) ---
                if page_num % 20 == 0 and page_num < max_pages:
                    console.print(f"[bold magenta]🛁 Periyodik Temizlik: {page_num} sayfa bitti. Oturum yenileniyor...[/bold magenta]")
                    await context.close()
                    await asyncio.sleep(3)
                    
                    # Yeni Oturum
                    context = await browser.new_context(**context_args)
                    await apply_stealth(context)
                    page = await context.new_page()
                    scraper = SearchScraper(page)
                    console.print("[magenta]✨ Oturum tazeledi. Devam ediliyor...[/magenta]")

                # İnsan Taklidi (Bekleme) - %40 AZALTILDI
                wait_time = random.uniform(1.2, 2.4)  # ✅ Optimizasyon: 2-4sn -> 1.2-2.4sn
                await asyncio.sleep(wait_time)
                
        except KeyboardInterrupt:
            console.print("[bold yellow]👋 İşlem kullanıcı tarafından durduruldu.[/bold yellow]")
        finally:
            # Çerezleri güncelle
            await context.storage_state(path=STATE_FILE)
            await browser.close()
            
    console.print(f"\n[bold blue]🎉 Toplam {len(all_links)} link toplandı![/bold blue]")
    console.print(f"📂 Dosya: {output_file}")

if __name__ == "__main__":
    # 🧪 TEST SENARYOSU: Stratejik 3 Kategori
    target_categories = ["elbise", "tayt", "kazak"]
    
    console.print(f"[bold yellow]🚀 SİSTEM TESTİ BAŞLIYOR: {len(target_categories)} Kategori, Kategori Başına 200 Sayfa[/bold yellow]")
    
    for cat in target_categories:
        console.print(f"\n[bold blue]🎯 Kategori İşleniyor: {cat.upper()}[/bold blue]")
        try:
            asyncio.run(harvest_links(cat, max_pages=200))
        except Exception as e:
            console.print(f"[red]❌ {cat} kategorisinde kritik hata: {e}[/red]")
            
    console.print("\n[bold green]🏁 MİSYON TAMAMLANDI: Tüm kategoriler tarandı![/bold green]")
