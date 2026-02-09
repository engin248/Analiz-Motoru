"""
Amazon Scraper - Platform-specific implementation (Skeleton)
To be implemented when Amazon selectors are configured.
"""

import asyncio
from typing import Dict, List, Optional, Any
from playwright.async_api import Page
from rich.console import Console

from .base_scraper import BaseScraper

console = Console()


class AmazonScraper(BaseScraper):
    """
    Amazon-specific scraper implementation.
    Currently a skeleton - selectors need to be configured in platform_selectors.yaml
    """
    
    def __init__(self, page: Page, config: Dict[str, Any], selectors: Dict[str, Any]):
        super().__init__(page, config, selectors)
        self.platform_name = "amazon"
    
    def get_trendyol_id(self, url: str) -> Optional[str]:
        """Extract Amazon product ID (ASIN) from URL"""
        pattern = self.selectors.get('product_id_pattern', r'/dp/([A-Z0-9]+)')
        return self.extract_id_from_url(url, pattern)
    
    async def collect_product_urls(self, keyword: str, max_pages: int) -> List[str]:
        """Collect product URLs from Amazon search pages"""
        all_urls = []
        search_url_template = self.selectors.get('search_url', 'https://www.amazon.com.tr/s?k={keyword}&page={page}')
        product_selectors = self.selectors.get('listing', {}).get('product_card', [])
        link_contains = self.selectors.get('listing', {}).get('product_link_contains', '/dp/')
        
        console.print(f"[yellow]⚠️ Amazon scraper henüz tam implementasyonu yapılmadı.[/yellow]")
        
        for page_num in range(1, max_pages + 1):
            url = search_url_template.format(keyword=keyword, page=page_num)
            console.print(f"[cyan]📄 Sayfa {page_num}/{max_pages} taranıyor...[/cyan]")
            
            try:
                await self.page.goto(url, wait_until='networkidle', timeout=60000)
                await asyncio.sleep(3)
                await self.scroll_page()
                
                # Try each selector
                links = await self.page.evaluate('''(args) => {
                    const selectors = args.selectors;
                    const linkContains = args.linkContains;
                    const urls = [];
                    for (const selector of selectors) {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(a => {
                            let href = a.getAttribute('href');
                            if (href && href.includes(linkContains)) {
                                if (!href.startsWith('http')) {
                                    href = 'https://www.amazon.com.tr' + href;
                                }
                                // Clean URL - remove query params
                                const cleanUrl = href.split('?')[0];
                                if (!urls.includes(cleanUrl)) {
                                    urls.push(cleanUrl);
                                }
                            }
                        });
                        if (urls.length > 0) break;
                    }
                    return urls;
                }''', {'selectors': product_selectors, 'linkContains': link_contains})
                
                if links:
                    console.print(f"[green]✅ Sayfa {page_num}: {len(links)} ürün bulundu[/green]")
                    all_urls.extend(links)
                else:
                    console.print(f"[yellow]⚠️ Sayfa {page_num}: Ürün bulunamadı[/yellow]")
                    
            except Exception as e:
                console.print(f"[red]❌ Sayfa {page_num} hatası: {e}[/red]")
            
            await asyncio.sleep(self.config.get('request_delay', 2))
        
        unique_urls = list(dict.fromkeys(all_urls))
        console.print(f"\n[bold green]🎯 Toplam {len(unique_urls)} benzersiz ürün URL'si toplandı![/bold green]\n")
        return unique_urls
    
    async def scrape_product(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape a single Amazon product page"""
        try:
            await self.page.goto(url, wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(3)
        except:
            return None
        
        product_selectors = self.selectors.get('product', {})
        
        # Basic implementation - needs refinement based on actual Amazon structure
        data = await self.page.evaluate('''(selectors) => {
            const res = {
                brand: '', name: '', 
                price: 0, org_price: 0, 
                rating: 0, reviews: 0, 
                favs: 0, views: 0, basket: 0,
                images: []
            };
            
            const getFirst = (selectorList) => {
                if (!selectorList) return null;
                for (const sel of selectorList) {
                    const el = document.querySelector(sel);
                    if (el && el.innerText.trim()) return el;
                }
                return null;
            };
            
            const cleanPrice = (txt) => {
                if(!txt) return 0;
                let t = txt.replace('TL','').replace('₺','').replace('$','').replace('€','').trim();
                return parseFloat(t.replace(/\\./g, '').replace(',', '.')) || 0;
            };

            // Brand & Name
            const brandEl = getFirst(selectors.brand);
            const nameEl = getFirst(selectors.name);
            res.brand = brandEl ? brandEl.innerText.trim() : '';
            res.name = nameEl ? nameEl.innerText.trim() : '';

            // Price
            const priceEl = getFirst(selectors.price);
            const orgPriceEl = getFirst(selectors.original_price);
            res.price = priceEl ? cleanPrice(priceEl.innerText) : 0;
            res.org_price = orgPriceEl ? cleanPrice(orgPriceEl.innerText) : res.price;

            // Rating & Reviews
            const ratingEl = getFirst(selectors.rating);
            const reviewEl = getFirst(selectors.review_count);
            if(ratingEl) {
                const m = ratingEl.innerText.match(/([\\d]+[.,][\\d]+)/);
                if(m) res.rating = parseFloat(m[0].replace(',', '.'));
            }
            if(reviewEl) {
                const nums = reviewEl.innerText.match(/\\d+/g);
                if(nums) res.reviews = parseInt(nums.join(''));
            }

            // Image
            const imgSelectors = selectors.image || ['#landingImage', '#imgBlkFront'];
            for(const sel of imgSelectors) {
                const img = document.querySelector(sel);
                if(img && img.src) {
                    res.images.push(img.src);
                    break;
                }
            }

            return res;
        }''', product_selectors)
        
        return data
