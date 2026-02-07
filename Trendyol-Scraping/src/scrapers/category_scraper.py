from typing import List, Dict
import asyncio
from playwright.async_api import Page
from rich.console import Console

class CategoryScraper:
    """Kategori sayfalarından ürün linklerini toplayan sınıf"""
    
    BASE_URL = "https://www.trendyol.com"
    
    def __init__(self, page: Page):
        self.page = page

    async def scrape_category(self, category_url: str, max_pages: int = 3) -> List[Dict]:
        """Kategorideki ürün linklerini tara"""
        all_products = []
        
        for page_num in range(1, max_pages + 1):
            url = category_url
            if '?' in url:
                url += f"&pi={page_num}"
            else:
                url += f"?pi={page_num}"
                
            try:
                console = Console()
                # Sayfanın tam yüklenmesini bekle (Network Idle)
                await self.page.goto(url, wait_until='networkidle', timeout=60000)
                await asyncio.sleep(3) 
                
                # Çerez vb. kapat
                try: await self.page.click('.overlay', timeout=1000)
                except: pass

                # Sayfayı yavaşça aşağı kaydır (Lazy load tetiklensin)
                for _ in range(5):
                    await self.page.evaluate('window.scrollBy(0, 500)')
                    await asyncio.sleep(0.5)

                # YÖNTEM: Spesifik Ürün Kartı Linklerini Al
                links = await self.page.evaluate('''() => {
                    // 1. En yaygın ürün kartı yapısı
                    let anchors = Array.from(document.querySelectorAll(".p-card-chldrn-cntnr a"));
                    
                    // 2. Yedek yapı
                    if (anchors.length === 0) {
                        anchors = Array.from(document.querySelectorAll(".prdct-cntnr-wrppr a"));
                    }
                    
                    // 3. Hiçbiri yoksa, tüm sayfa (AMA Riskli)
                    if (anchors.length === 0) {
                        // Sadece main content içindekileri almaya çalışalım
                        const main = document.querySelector('.search-app-container') || document.body;
                        anchors = Array.from(main.querySelectorAll("a"));
                    }

                    return anchors
                        .map(a => a.href)
                        .filter(href => href.includes("-p-") && !href.includes("boutiqueId=") && !href.includes("review"));
                }''')
                
                # Filtreleme (Tekrarları ve anlamsızları at)
                unique_links = list(set(links))
                
                console.print(f"[cyan]   📄 Sayfa {page_num}: {len(unique_links)} olası ürün linki bulundu.[/cyan]")
                
                count = 0
                for href in unique_links:
                    if not href.startswith('http'): href = self.BASE_URL + href
                    
                    # Zaten listemizde var mı?
                    if not any(p['product_url'] == href for p in all_products):
                        all_products.append({'product_url': href})
                        count += 1
                
                if count == 0:
                    console.print(f"[yellow]⚠️ Sayfa {page_num}'de yeni ürün bulunamadı. Ekran görüntüsü alınıyor...[/yellow]")
                    await self.page.screenshot(path=f"debug_cat_fail_p{page_num}.png")
                
                # Eğer hiç ürün bulamadıysak döngüyü kır
                if not all_products: break
                
            except Exception as e:
                print(f"Sayfa {page_num} tarama hatası: {e}")
                
        return all_products
                
        return all_products
