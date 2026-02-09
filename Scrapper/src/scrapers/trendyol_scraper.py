"""
Trendyol Scraper - Platform-specific implementation
"""

import asyncio
from typing import Dict, List, Optional, Any
from playwright.async_api import Page
from rich.console import Console

from .base_scraper import BaseScraper

console = Console()


class TrendyolScraper(BaseScraper):
    """
    Trendyol-specific scraper implementation.
    Inherits common functionality from BaseScraper.
    """
    
    def __init__(self, page: Page, config: Dict[str, Any], selectors: Dict[str, Any]):
        super().__init__(page, config, selectors)
        self.platform_name = "trendyol"
    
    def get_trendyol_id(self, url: str) -> Optional[str]:
        """Extract Trendyol product ID from URL"""
        pattern = self.selectors.get('product_id_pattern', r'-p-(\d+)')
        return self.extract_id_from_url(url, pattern)
    
    async def collect_product_urls(self, keyword: str, max_pages: int) -> List[str]:
        """Collect product URLs from Trendyol search pages"""
        all_urls = []
        search_url_template = self.selectors.get('search_url', 'https://www.trendyol.com/sr?q={keyword}&pi={page}')
        product_selectors = self.selectors.get('listing', {}).get('product_card', [])
        link_contains = self.selectors.get('listing', {}).get('product_link_contains', '-p-')
        
        for page_num in range(1, max_pages + 1):
            url = search_url_template.format(keyword=keyword, page=page_num)
            console.print(f"[cyan]📄 Sayfa {page_num}/{max_pages} taranıyor...[/cyan]")
            
            try:
                await self.page.goto(url, wait_until='networkidle', timeout=60000)
                await asyncio.sleep(3)
                
                # ÖZEL KONTROL: Bot tespiti veya Sonuç Bulunamadı ekranı mı?
                is_blocked = await self.page.evaluate("""() => {
                    const text = document.body.innerText;
                    return text.includes('İlgili Sonuç Bulunamadı') || 
                           text.includes('Aradığınız sayfayı bulamadık') ||
                           text.includes('Robot olmadığını doğrula');
                }""")
                
                if is_blocked:
                    raise Exception("⛔ BLOKLANDI: Trendyol 'Sonuç Bulunamadı' veya doğrulama ekranı gösterdi.")
                
                # Scroll for lazy loading
                await self.scroll_page()
                
                # Try each selector until we find products
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
                                    href = 'https://www.trendyol.com' + href;
                                }
                                if (!urls.includes(href)) {
                                    urls.push(href);
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
        
        # Return unique URLs
        unique_urls = list(dict.fromkeys(all_urls))
        console.print(f"\n[bold green]🎯 Toplam {len(unique_urls)} benzersiz ürün URL'si toplandı![/bold green]\n")
        return unique_urls

    async def collect_product_urls_from_link(self, target_url: str, max_pages: int):
        """Collect product URLs directly from a given category or search link"""
        product_selectors = self.selectors.get('listing', {}).get('product_card', [])
        link_contains = self.selectors.get('listing', {}).get('product_link_contains', '-p-')
        
        base_url = target_url
        if '?' not in base_url: base_url += '?'
        else:
            if '&pi=' in base_url or '?pi=' in base_url:
                import re
                base_url = re.sub(r'([?&])pi=\d+', r'\1', base_url).rstrip('&?')
                if '?' not in base_url: base_url += '?'
                else: base_url += '&'
            else: base_url += '&'

        for page_num in range(1, max_pages + 1):
            url = f"{base_url}pi={page_num}"
            console.print(f"[cyan]📄 Sayfa {page_num}/{max_pages} taranıyor...[/cyan]")
            try:
                await self.page.goto(url, wait_until='networkidle', timeout=60000)
                await asyncio.sleep(2)
                
                # ÖZEL KONTROL: Bot tespiti veya Sonuç Bulunamadı ekranı mı?
                is_blocked = await self.page.evaluate("""() => {
                    const text = document.body.innerText;
                    return text.includes('İlgili Sonuç Bulunamadı') || 
                           text.includes('Aradığınız sayfayı bulamadık') ||
                           text.includes('Robot olmadığını doğrula');
                }""")
                if is_blocked:
                    raise Exception("⛔ BLOKLANDI: Trendyol 'Sonuç Bulunamadı' veya doğrulama ekranı gösterdi.")

                await self.scroll_page()
                links = await self.page.evaluate('''(args) => {
                    const selectors = args.selectors;
                    const linkContains = args.linkContains;
                    const urls = [];
                    for (const selector of selectors) {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(a => {
                            let href = a.getAttribute('href');
                            if (href && href.includes(linkContains)) {
                                if (!href.startsWith('http')) href = 'https://www.trendyol.com' + href;
                                if (!urls.includes(href)) urls.push(href);
                            }
                        });
                        if (urls.length > 0) break;
                    }
                    return urls;
                }''', {'selectors': product_selectors, 'linkContains': link_contains})
                if links:
                    console.print(f"[green]✅ Sayfa {page_num}: {len(links)} ürün bulundu[/green]")
                    for l in links:
                        yield l
                else:
                    console.print(f"[yellow]⚠️ Sayfa {page_num}: Ürün bulunamadı[/yellow]")
                    break
            except Exception as e:
                console.print(f"[red]❌ Sayfa {page_num} hatası: {e}[/red]")
            await asyncio.sleep(self.config.get('request_delay', 2))
    
    async def scrape_product(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape a single Trendyol product page"""
        try:
            await self.page.goto(url, wait_until='domcontentloaded', timeout=60000)
            await self.page.mouse.wheel(0, 500)
            await asyncio.sleep(3)
        except:
            return None
        
        product_selectors = self.selectors.get('product', {})
        
        data = await self.page.evaluate('''(selectors) => {
            const res = {
                brand: '', name: '', 
                price: 0, org_price: 0, 
                rating: 0, reviews: 0, 
                favs: 0, views: 0, basket: 0,
                images: [], attrs: '',
                debug_info: []
            };
            
            const cleanPrice = (txt) => {
                if(!txt) return 0;
                let t = txt.replace('TL','').replace('₺','').trim();
                return parseFloat(t.replace(/\\./g, '').replace(',', '.')) || 0;
            };

            // Helper to get first matching element
            const getFirst = (selectorList) => {
                if (!selectorList) return null;
                for (const sel of selectorList) {
                    const el = document.querySelector(sel);
                    if (el && el.innerText.trim()) return el;
                }
                return null;
            };

            // Check if element is visible and not in recommendation containers
            const isVisible = (el) => {
                if(!el) return false;
                if(el.closest('.p-card-wrppr') || 
                   el.closest('.product-card') || 
                   el.closest('.widget-product') || 
                   el.closest('.recommendation-box') ||
                   el.closest('.carousel') ||
                   el.closest('.reco-slider')) return false;
                
                const style = window.getComputedStyle(el);
                return style.display !== 'none' && 
                       style.visibility !== 'hidden' && 
                       el.offsetParent !== null;
            };

            // Brand & Name
            const brandEl = getFirst(selectors.brand);
            const nameEl = getFirst(selectors.name);
            res.brand = brandEl ? brandEl.innerText.trim() : '';
            res.name = nameEl ? nameEl.innerText.trim() : '';

            // Main price container
            let mainContainer = document.querySelector('.product-detail-container') || 
                                document.querySelector('.pr-in-w') ||
                                document.querySelector('.price-wrapper') ||
                                document;

            // Price detection with priority
            const priceSelectors = [
                { price: '.price-view .discounted', org: '.price-view .original' },
                { price: '.ty-plus-price-discounted-price', org: '.ty-plus-price-original-price' },
                { price: '.prc-dsc', org: '.prc-org' },
                { price: '.discounted', org: '.original' },
                { price: '.product-price', org: null }
            ];

            for (const ps of priceSelectors) {
                const priceEl = mainContainer.querySelector(ps.price);
                if (priceEl && isVisible(priceEl)) {
                    res.price = cleanPrice(priceEl.innerText);
                    if (ps.org) {
                        const orgEl = mainContainer.querySelector(ps.org);
                        res.org_price = orgEl && isVisible(orgEl) ? cleanPrice(orgEl.innerText) : res.price;
                    } else {
                        res.org_price = res.price;
                    }
                    break;
                }
            }
            
            if(res.org_price < res.price) res.org_price = res.price;

            // Metric Parser
            const parseMetric = (text) => {
                if(!text) return 0;
                let cleanText = text.toLowerCase();
                cleanText = cleanText.replace(/son\\s+\\d+\\s+(saat|gün|dakika|hafta|ay)[te]*/g, '');
                const match = cleanText.match(/([\\d.,]+)\\s*(bin|mn|b|m|k)?/);
                if(!match) return 0;
                let numStr = match[1].replace(/\\./g, '').replace(',', '.');
                let val = parseFloat(numStr);
                const unit = match[2];
                if(['bin', 'b', 'k'].includes(unit)) val *= 1000;
                if(['mn', 'm'].includes(unit)) val *= 1000000;
                return Math.round(val);
            };

            // Rating & Reviews
            const reviewEl = getFirst(selectors.review_count);
            if(reviewEl && isVisible(reviewEl)) {
                const nums = reviewEl.innerText.match(/\\d+/g);
                if(nums) res.reviews = parseInt(nums.join(''));
            }
            
            const ratingEl = getFirst(selectors.rating);
            if(ratingEl && isVisible(ratingEl)) {
                const m = ratingEl.innerText.match(/([\\d]+[.,][\\d]+)|([\\d]+)/);
                if(m) res.rating = parseFloat(m[0].replace(',', '.'));
            }

            // Social Proofs (favorites, basket, views)
            const proofs = document.querySelectorAll('.social-proof-content');
            proofs.forEach(box => {
                if(!isVisible(box)) return;
                const rawText = box.innerText;
                const focusedSpan = box.querySelector('.social-proof-item-focused-text');
                const val = focusedSpan ? parseMetric(focusedSpan.innerText) : parseMetric(rawText);
                const textLower = rawText.toLowerCase();
                if(textLower.includes('favori')) res.favs = val;
                else if(textLower.includes('sepet')) res.basket = val;
                else if(textLower.includes('görüntü') || textLower.includes('baktı')) res.views = val;
            });

            // Image
            const imgSelectors = selectors.image || ['.product-slide img', '.gallery-container img'];
            for(const sel of imgSelectors) {
                const img = document.querySelector(sel);
                if(img && img.src && !img.src.includes('data:')) {
                    res.images.push(img.src);
                    break;
                }
            }

            return res;
        }''', product_selectors)
        
        return data
