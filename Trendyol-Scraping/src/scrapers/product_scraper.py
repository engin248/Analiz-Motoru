import asyncio
import json
import re
from typing import Dict, List, Optional
from rich.console import Console
from playwright.async_api import Page, Response

console = Console()

class ProductScraper:
    def __init__(self, page: Page):
        self.page = page
        self.api_data: Dict = {}
        self.product_data: Dict = {}
        self.page.on("response", self._handle_response)

    async def _handle_response(self, response: Response):
        """API yanıtlarını dinler ve ürün verilerini yakalar"""
        try:
            if "public/products" in response.url and response.status == 200:
                data = await response.json()
                if "result" in data:
                    self.product_data = data["result"]
            
            if "social-proof" in response.url and response.status == 200:
                data = await response.json()
                if "result" in data:
                     self.api_data['view_count'] = data['result'].get('viewCount', 0)
                     self.api_data['favorite_count'] = data['result'].get('favoriteCount', 0)
                     
            if "reviews" in response.url and "summary" in response.url:
                 data = await response.json()
                 if "result" in data:
                     self.api_data['rating_score'] = data['result'].get('averageRating', 0)
                     self.api_data['review_count'] = data['result'].get('totalCount', 0)

        except: pass

    async def scrape_product(self, product_url: str) -> Optional[Dict]:
        """
        Ürün detay sayfasını hem API hem HTML yöntemleriyle tarar.
        Fiyat doğruluğu için Hybrit (API + Schema + Regex + DOM) yöntem kullanır.
        """
        try:
            console.print(f"[bold blue]🔍 Ürün İnceleniyor: {product_url}[/bold blue]")
            
            # Veri temizliği
            self.product_data = {}
            self.api_data = {'view_count': 0, 'favorite_count': 0, 'rating_score': 0, 'review_count': 0}

            # Sayfaya git
            try:
                await self.page.goto(product_url, wait_until='domcontentloaded', timeout=60000)
            except: pass
            
            # API ve Dinamik içerik için bekle - ✅ Optimizasyon: 4sn -> 2.4sn
            await asyncio.sleep(2.4)  # %40 azaltıldı

            # ✅ DEBUG SCREENSHOT KALDIRILDI (Gereksiz I/O eliminasyonu)
            # await self.page.screenshot(path="debug_view.png", full_page=False)

            # Kritik: Fiyat elementlerinin tam yüklenmesi için kısa bir bekleme veya smart wait
            # Sepette indirimleri bazen geç yüklenir.
            try:
                # Hem yeni hem eski container yapısını kontrol et
                await self.page.wait_for_selector('.product-price-container, .price-container', timeout=3000)
            except: pass
            
            
            # ✅ STRATEJİ 0: API VERİSİ (EN GÜVENİLİR VE HIZLI)
            # Eğer API'den veri geldiyse, HTML parse etmeye gerek yok!
            if self.product_data:
                try:
                    # Fiyat bilgilerini güvenli şekilde al
                    price_info = self.product_data.get('price', {})
                    
                    # API'de fiyat formatları genelde şöyledir:
                    # discountedPrice: { text: "1.200 TL", value: 1200.0 }
                    # sellingPrice: { text: "1.500 TL", value: 1500.0 }
                    # originalPrice: { text: "1.800 TL", value: 1800.0 }
                    
                    disc_price = price_info.get('discountedPrice', {}).get('value', 0)
                    sell_price = price_info.get('sellingPrice', {}).get('value', 0)
                    orig_price = price_info.get('originalPrice', {}).get('value', 0)
                    
                    # Eğer discountedPrice 0 ise sellingPrice kullan
                    final_discounted = disc_price if disc_price > 0 else sell_price
                    # Eğer originalPrice yoksa, satış fiyatını baz al
                    final_original = orig_price if orig_price > 0 else final_discounted
                    
                    if final_discounted > 0:
                        # Diğer verileri de API'den al
                        name = self.product_data.get('name', '')
                        brand = self.product_data.get('brand', {}).get('name', '')
                        rating = self.api_data.get('rating_score', 0)
                        reviews = self.api_data.get('review_count', 0)
                        favorites = self.api_data.get('favorite_count', 0)
                        
                        console.print(f"[green]✅ API'den Fiyat Alındı: {final_discounted} TL[/green]")
                        
                        return {
                            "product_url": product_url,
                            "product_name": name,
                            "brand": brand,
                            "original_price": float(final_original),
                            "discounted_price": float(final_discounted),
                            "rating_score": float(rating),
                            "review_count": int(reviews),
                            "favorite_count": int(favorites),
                            "view_count": int(self.api_data.get('view_count', 0)),
                            "features": "API Data",
                            "method": "api_v1"
                        }
                except Exception as e:
                    console.print(f"[red]⚠️ API Parse Hatası: {e}[/red]")

            # --- ULTRA-SIMPLE FİYAT MOTORU: SADECE ANA FİYAT ALANINI ÇEK ---
            
            price_data = await self.page.evaluate('''() => {
                const result = { original: 0, discounted: 0, method: 'none', debug: [] };
                
                const parsePrice = (text) => {
                    if (!text) return 0;
                    let clean = text.replace(/[^0-9,.]/g, '').trim(); 
                    if (!clean) return 0;
                    
                    if (clean.includes(',') && clean.includes('.')) {
                        clean = clean.replace(/\\./g, '').replace(',', '.');
                    } else if (clean.includes(',')) {
                        clean = clean.replace(',', '.');
                    } else if (clean.includes('.')) {
                        const parts = clean.split('.');
                        if (parts[parts.length-1].length > 2) {
                            clean = clean.replace(/\\./g, '');
                        }
                    }
                    return parseFloat(clean) || 0;
                };
                
                const isVisible = (el) => {
                    if (!el) return false;
                    const style = window.getComputedStyle(el);
                    return style.display !== 'none' && 
                           style.visibility !== 'hidden' && 
                           style.opacity !== '0' &&
                           el.offsetParent !== null;
                };
                
                const getText = (el) => {
                    if (!el) return '';
                    return (el.innerText || el.textContent || '').trim();
                };
                
                const getFontSize = (el) => {
                    if (!el) return 0;
                    const style = window.getComputedStyle(el);
                    return parseFloat(style.fontSize) || 0;
                };
                
                const log = (msg) => result.debug.push(msg);
                
                // ========== YENİ YAKLAŞIM: ÖNCELİKLE ANA FİYAT CONTAINER'I BUL ==========
                log('Finding main price container...');
                
                // Ana fiyat container selectorleri (renk seçicilerin DIŞINDA)
                const mainContainerSelectors = [
                    '.product-price-container',
                    '.price-container',
                    '.price-wrapper',             // ✅ EKLENDİ (Image 1, 3, 4)
                    '.ty-plus-price-container',   // ✅ EKLENDİ (Image 2)
                    '[class*="detail"][class*="price"]',
                    '.pr-in-w',
                    '.product-detail-price'
                ];
                
                let mainPriceArea = null;
                for (let sel of mainContainerSelectors) {
                    const container = document.querySelector(sel);
                    if (container && isVisible(container)) {
                        mainPriceArea = container;
                        log(`Found main container: ${sel}`);
                        break;
                    }
                }
                
                // Container bulunamadıysa, body kullan
                if (!mainPriceArea) {
                    log('No specific container, using body');
                    mainPriceArea = document.body;
                }
                
                // ========== YENİ YAKLAŞIM: SADECE SAYFANIN ÜST KISMINA BAK ==========
                // Ana ürün fiyatı HEP en üstte, öneriler aşağıda. Çok dar aralık!
                const isInTopArea = (el) => {
                    if (!el) return false;
                    const rect = el.getBoundingClientRect();
                    // İlk 1200 piksel içinde mi? (300px çok dardı, geri açıldı)
                    return rect.top >= 0 && rect.top < 1200;
                };
                
                // Renk/beden seçici + ÜRÜN ÖNERİLERİ alanlarını exclude et
                const excludeSelectors = [
                    '[class*="variant"]',
                    '[class*="color"]',
                    '[class*="size"]',
                    '.slr-img-cntnr',  // Renk seçici
                    '[class*="option"]',
                    // ÜRÜN ÖNERİLERİ VE REKLAMLAR - GENİŞLETİLDİ
                    '[class*="product-card"]',  // Ürün kartları
                    '[class*="recommendation"]',  // Öneriler
                    '[class*="similar"]',  // Benzer ürünler
                    '[class*="related"]',  // İlgili ürünler
                    '[class*="popular"]',  // ✅ Popüler ürünler
                    '[class*="upsell"]',  // Cross-sell
                    '[class*="cross-sell"]',  // ✅ Cross-sell alternatifi
                    '[class*="carousel"]',  // Kaydırmalı ürün listeleri
                    '[class*="slider"]',  // Slider'lar
                    '[class*="widget"]',  // ✅ Widget'lar
                    '.prdct-cntnr-wrppr',  // Ürün container wrapper
                    '[class*="prd-"]',  // ✅ Ürün önizleme kartları (prd-card vb.)
                    '[class*="ads"]',  // Reklamlar
                    '[id*="ads"]'  // Reklam ID'leri
                ];
                
                const isInExcludedArea = (el) => {
                    // Eğer element bu exclude selector'lardan birinin altındaysa, atla
                    for (let sel of excludeSelectors) {
                        const excluded = document.querySelectorAll(sel);
                        for (let ex of excluded) {
                            if (ex !== el && ex.contains(el)) {
                                return true;
                            }
                        }
                    }
                    return false;
                };
                
                // ========== STRATEJİ 1: SEPETTE/TRENDYOL PLUS ==========
                log('Strategy 1: Campaign prices...');
                
                // Daha spesifik pattern'ler - footer'daki "Sepette" linklerini atla
                const campaignPatterns = [
                    /sepette\\s*%/i,  // "Sepette %15"
                    /sepette\\s+indir/i,  // "Sepette İndirim"
                    /plus.*özel.*sepette/i,  // ✅ "Plus'a Özel sepette" TAM MATCH
                    /trendyol\\s+plus.*sepette/i,  // ✅ "Trendyol Plus sepette"
                    /özel.*sepette/i  // "Özel sepette"
                ];
                
                for (let el of mainPriceArea.querySelectorAll('*')) {
                    const text = getText(el);
                    const matchesPattern = campaignPatterns.some(pattern => pattern.test(text));
                    
                    // ✅ SIKLAŞTIRILMIŞ KONTROL: Kısa metin (50 char max), üst alan, exclude dışı
                    if (matchesPattern && text.length > 10 && text.length < 100 && isVisible(el) && isInTopArea(el) && !isInExcludedArea(el)) {
                        log(`Found campaign text: "${text.substring(0, 50)}"`);
                        
                        // "Sepette" kelimesinden SONRA gelen fiyatları bul
                        const sepetteIndex = text.toLowerCase().indexOf('sepette');
                        if (sepetteIndex >= 0) {
                            const afterSepette = text.substring(sepetteIndex);
                            // afterSepette içindeki tüm fiyatları bul
                            // ✅ GELİŞTİRİLMİŞ REGEX: Türk fiyat formatını yakalar (1.308,52 veya 1308.52 veya 1308)
                            const priceRegex = /([0-9]{1,3}(?:[.,][0-9]{3})*(?:[.,][0-9]{1,2})?)\\s*(?:TL|₺)/gi;
                            const matches = [...afterSepette.matchAll(priceRegex)];
                            
                            if (matches.length > 0) {
                                // İlk bulunan 3+ haneli sayıyı al (50 gibi küçük kupon değerleri atlanır)
                                const price = parsePrice(matches[0][1]);
                                if (price > 100 && price < 50000) {  // 100 TL'den büyükse muhtemelen fiyattır
                                    log(`✓ Campaign price: ${price}`);
                                    result.discounted = price;
                                    
                                    // İkinci fiyat varsa (orijinal fiyat olabilir)
                                    if (matches.length > 1) {
                                        const origPrice = parsePrice(matches[1][1]);
                                        if (origPrice > price && origPrice < 50000) {
                                            result.original = origPrice;
                                            log(`✓ Original price: ${origPrice}`);
                                        } else {
                                            result.original = price;
                                        }
                                    } else {
                                        result.original = price;
                                    }
                                    
                                    result.method = 'campaign';
                                    return result;
                                }
                            }
                        }
                    }
                }
                log('No campaign price');
                
                // ========== STRATEJİ 2: STANDART İNDİRİMLİ/TEK FİYAT ==========
                log('Strategy 2: Standard pricing...');
                
                // Sadece TOP AREA'daki fiyatları topla
                const allPriceElements = [];
                const priceSelectors = [
                    '.prc-dsc', '.discounted', '.new-price', '.ty-plus-price-discounted-price', // İndirimli (Image 2 eklendi)
                    '.prc-org', '.original', '.old-price', '.ty-plus-price-original-price',    // Orijinal (Image 2 eklendi)
                    '.prc-box-dsc', '.product-price', '.selling-price'  // Tek fiyat
                ];
                
                priceSelectors.forEach(sel => {
                    mainPriceArea.querySelectorAll(sel).forEach(el => {
                        if (isVisible(el) && isInTopArea(el) && !isInExcludedArea(el)) {  // EXCLUDE EKLENDİ
                            const price = parsePrice(getText(el));
                            const fontSize = getFontSize(el);
                            if (price > 0 && price < 50000) {
                                allPriceElements.push({ 
                                    element: el, 
                                    price, 
                                    fontSize,
                                    selector: sel,
                                    isDiscount: sel.includes('dsc') || sel.includes('discount') || sel.includes('new')
                                });
                            }
                        }
                    });
                });
                
                // Font-size'a göre sırala
                allPriceElements.sort((a, b) => b.fontSize - a.fontSize);
                
                log(`Found ${allPriceElements.length} price elements in top area`);
                
                if (allPriceElements.length > 0) {
                    // En büyük fontlu fiyatı al
                    const mainPrice = allPriceElements[0];
                    
                    // Original fiyat ara (üstü çizili veya daha yüksek fiyat)
                    const origPrices = allPriceElements.filter(p => 
                        !p.isDiscount && p.price > mainPrice.price
                    );
                    
                    // Gerçek indirim var mı kontrol et
                    const hasRealDiscount = origPrices.length > 0;
                    
                    if (hasRealDiscount) {
                        // İNDİRİM VAR: İndirimli fiyat ve orijinal fiyat farklı
                        result.discounted = mainPrice.price;
                        result.original = origPrices[0].price;
                        result.method = 'standard_discounted';
                        log(`✓ DISCOUNT FOUND: ${result.discounted} / ${result.original}`);
                    } else {
                        // İNDİRİM YOK: Tek fiyat var, her iki alan da aynı fiyat (0 DEĞİL!)
                        result.discounted = mainPrice.price;
                        result.original = mainPrice.price;
                        result.method = 'standard_single_price';
                        log(`✓ SINGLE PRICE (no discount): ${result.discounted} / ${result.original}`);
                    }
                    return result;
                }
                
                // ========== STRATEJİ 3: REGEX FALLBACK (KALDIRILDI) ==========
                log('Strategy 3: Regex fallback REMOVED for safety');
                
                log('✗✗✗ ALL FAILED');
                return result;
                
                log('✗✗✗ ALL FAILED');
                return result;
            }''')

            discounted = float(price_data.get('discounted', 0))
            original = float(price_data.get('original', 0))
            method = price_data.get('method', 'none')
            debug_logs = price_data.get('debug', [])
            
            # Validation - discounted=0 is valid (no discount case)
            is_valid = original > 0 and original <= 50000 and discounted >= 0 and original >= discounted
            
            if is_valid:
                if discounted > 0:
                    console.print(f"[bold green]✅ İNDİRİMLİ: {discounted} TL (Orjinal: {original} TL) | Yöntem: {method}[/bold green]")
                else:
                    console.print(f"[bold yellow]✅ TEK FİYAT (İndirim Yok): {original} TL | Yöntem: {method}[/bold yellow]")
            else:
                console.print(f"[bold red]❌ Fiyat Geçersiz veya Bulunamadı: discounted={discounted}, original={original} (Yöntem: {method})[/bold red]")
            
            # Debug loglarını ALWAYS göster
            if debug_logs:
                console.print(f"[dim]🔍 Debug: {debug_logs}[/dim]")
            
            # API varsa verileri oradan al
            if self.product_data:
                # ... (API verisi varsa mevcut kod devam eder) ...
                p = self.product_data
                images = [img.get('url', '') for img in p.get('images', [])]
                
                data = {
                    'trendyol_id': str(p.get('id', '')),
                    'product_url': product_url,
                    'product_name': p.get('name', ''),
                    'brand': p.get('brand', {}).get('name', ''),
                    'seller_name': p.get('merchant', {}).get('name', 'Trendyol'),
                    # SADECE DOM'dan gelen fiyatlar
                    'discounted_price': discounted,
                    'original_price': original,
                    # Metrikler API'den
                    'rating_score': float(self.api_data.get('rating_score', 0)),
                    'review_count': int(self.api_data.get('review_count', 0)),
                    'favorite_count': int(self.api_data.get('favorite_count', 0)),
                    'image_urls': images[:3],
                    'metrics': {},
                    'attributes': {}
                }
            else:
                # API YOKSA HTML PARSING (GÜÇLENDİRİLMİŞ)
                
                # HTML Snapshot Al (API yoksa kritik)
                content = await self.page.content()

                # Temel Metinleri Çek
                brand_name = await self._get_text_content('a.product-brand-name-with-link') or \
                             await self._get_text_content('h1.product-title a') or \
                             await self._get_text_content('.brand-name') or \
                             "Trendyol"
                
                product_name = await self._get_text_content('h1.product-title span') or \
                               await self._get_text_content('h1.product-title') or \
                               await self._get_text_content('.product-name') or \
                               "Bilinmeyen Ürün"
                
                if brand_name and brand_name in product_name:
                    product_name = product_name.replace(brand_name, '').strip()

                seller_name = await self._get_text_content('.merchant-text') or "Trendyol"
                trendyol_id = product_url.split('-p-')[-1].split('?')[0]

                # Resimleri Çek (HTML + Script)
                images = await self.page.evaluate(r'''() => {
                    const foundImages = new Set();
                    
                    // 1. Script tag'lerinden yakala (En garantisi)
                    const scripts = Array.from(document.querySelectorAll('script'));
                    for (const script of scripts) {
                        const content = script.innerText;
                        if (content.includes('images') && content.includes('dsmcdn.com')) {
                            const match = content.match(/"(https:\/\/cdn\.dsmcdn\.com\/[^"]+?\.jpg)"/g);
                            if (match) {
                                match.forEach(url => foundImages.add(url.replace(/"/g, '')));
                            }
                        }
                    }

                    // 2. DOM'dan yakala
                    const selectors = [
                        '.product-slide img',
                        '.gallery-container img',
                        '.detail-section-img',
                        'img[data-testid="image"]',
                        '.base-product-image img',
                        '.product-image-container img'
                    ];
                    
                    selectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach(img => {
                            if (img.src && !img.src.includes('data:')) {
                                foundImages.add(img.src);
                            }
                        });
                    });

                    return Array.from(foundImages);
                }''')

                data = {
                    'trendyol_id': trendyol_id,
                    'product_url': product_url,
                    'product_name': product_name,
                    'brand': brand_name,
                    'seller_name': seller_name,
                    'discounted_price': float(discounted),
                    'original_price': float(original),
                    # Fallback ile Metrikler
                    'rating_score': 0.0,
                    'review_count': 0,
                    'favorite_count': 0,
                    'image_urls': images[:3],
                    'metrics': {},
                    'attributes': {}
                }

            # Eksik metrikleri (Puan, Yorum, Favori) HTML'den tamamla
            if data['rating_score'] == 0:
                 data['rating_score'] = await self._get_rating_score_fallback()
            
            if data['review_count'] == 0:
                 data['review_count'] = await self._get_review_count_fallback()

            # Sosyal Kanıt Verilerini Çek (Favori, Sepet, Görüntülenme)
            social = await self._get_social_proof()
            
            # Ana verileri güncelle (Eğer API'den gelmediyse veya 0 ise)
            if data['favorite_count'] == 0:
                data['favorite_count'] = social['fav_count']
            
            data['attributes'] = await self._get_attributes()
            
            # DB ve Excel için metrikleri hazırla
            data['metrics'] = {
                'rating_score': data.get('rating_score', 0),
                'review_count': data.get('review_count', 0),
                'favorite_count': data.get('favorite_count', 0),
                'basket_count': social['basket_count'],
                'view_count': social['view_count']
            }

            console.print(f"[green]✅ Veri: {data['product_name'][:20]}.. | {data['discounted_price']} TL | ⭐{data['rating_score']} ({data['review_count']}) | ♥{data['favorite_count']}[/green]")
            return data

        except Exception as e:
            console.print(f"[red]Hizmet Hatası: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
            return None

    # --- Yardımcı Fonksiyonlar ---
    async def _get_text_content(self, selector: str) -> str:
        try:
            el = await self.page.query_selector(selector)
            return (await el.inner_text()).strip() if el else ""
        except: return ""

    async def _get_schema_data(self):
        """Schema.js verilerini sayfadan çeker"""
        try:
            return await self.page.evaluate('''() => {
                const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                for (let s of scripts) {
                    try {
                        const data = JSON.parse(s.innerText);
                        if (data['@type'] === 'Product' || data['@type'] === 'ProductGroup') return data;
                    } catch(e) {}
                }
                return null;
            }''')
        except: return None

    async def _get_attributes(self):
        return await self.page.evaluate('''() => {
            let items = Array.from(document.querySelectorAll('[data-testid="attribute-item"]')).map(el => {
                const name = el.querySelector('.name')?.innerText?.trim();
                const value = el.querySelector('.value')?.innerText?.trim();
                return { attribute_name: name, attribute_value: value };
            }).filter(a => a.attribute_name && a.attribute_value);

            if (items.length === 0) {
                items = Array.from(document.querySelectorAll('.detail-attr-item')).map(el => {
                    const parts = el.innerText.split(':');
                    return { attribute_name: parts[0]?.trim(), attribute_value: parts[1]?.trim() };
                }).filter(a => a.attribute_name);
            }
            return items;
        }''')

    async def _get_social_proof(self):
        """Popüler ürün görüntüleme, sepet ve favori bilgisini HTML'den çeker"""
        try:
            results = await self.page.evaluate('''() => {
                const res = { fav: 0, view: 0, basket: 0 };
                const items = document.querySelectorAll('[data-testid="social-proof-item"]');
                
                items.forEach(item => {
                    const img = item.querySelector('img');
                    const focusedEl = item.querySelector('.social-proof-item-focused-text');
                    if (!focusedEl) return;
                    
                    // KRİTİK DÜZELTME: 'kişi' kelimesini temizle ki 'k' harfi 'bin' çarpanı sanılmasın!
                    let text = focusedEl.innerText.toLowerCase().replace(/kişi/g, '').trim();
                    
                    // Sayı ve çarpanı çek (örn: 2B, 1.2M, 500)
                    const match = text.match(/([\\d.,]+)\\s*([bm])?/);
                    if (match) {
                        let num = parseFloat(match[1].replace(/\\./g, '').replace(',', '.'));
                        const multiplier = match[2];
                        if (multiplier === 'b') num *= 1000;
                        if (multiplier === 'm') num *= 1000000;
                        
                        const val = Math.round(num);
                        const alt = img ? img.alt : '';
                        
                        if (alt === 'basket-count' || text.includes('sepet')) res.basket = val;
                        else if (alt === 'favorite-count' || text.includes('favori')) res.fav = val;
                        else if (alt === 'page-view-count' || text.includes('görüntü')) res.view = val;
                    }
                });
                return res;
            }''')
            
            return {
                'view_count': results.get('view', 0), 
                'fav_count': results.get('fav', 0),
                'basket_count': results.get('basket', 0)
            }

        except Exception as e:
            console.print(f"[dim]⚠️ Sosyal Kanıt Hatası: {e}[/dim]")
            return {'view_count': 0, 'fav_count': 0, 'basket_count': 0}

    def _parse_single_price(self, text: str) -> float:
        if not text: return 0.0
        text = str(text).strip()
        
        # 1. Doğrudan float mı? (Schema verisi genelde böyledir: 499.0)
        try:
            return float(text)
        except: pass
        
        # 2. Temizle
        cleaned = re.sub(r'[^\d,.]', '', text)
        if not cleaned: return 0.0
        
        # 3. Format Kararı
        if ',' in cleaned and '.' in cleaned:
            # 1.250,50 -> 1250.50
            final = cleaned.replace('.', '').replace(',', '.')
        elif ',' in cleaned:
            # 499,50 -> 499.50
            final = cleaned.replace(',', '.')
        elif '.' in cleaned:
            # Eğer nokta varsa ve sondan 3. karakterden önceyse (örn: 1.250) binliktir
            # Değilse (örn: 499.5) ondalıktır.
            # Ancak Trendyol DOM'da nokta genellikle binliktir.
            # Güvenli liman: Eğer nokta varsa ve sağında tam 2 rakam varsa ondalık sayalım.
            parts = cleaned.split('.')
            if len(parts[-1]) <= 2: # 499.5 veya 499.50
                 final = cleaned
            else: # 1.250
                 final = cleaned.replace('.', '')
        else:
            final = cleaned
            
        try:
            return float(final)
        except: return 0.0

    async def scrape_reviews(self, product_url: str, limit: int = 50) -> List[Dict]:
        if '/yorumlar' not in product_url:
            base = product_url.split('?')[0]
            review_url = f"{base}/yorumlar"
        else:
            review_url = product_url

        console.print(f"[blue]💬 Yorumlar sayfasına gidiliyor: {review_url}[/blue]")
        
        try:
            await self.page.goto(review_url, wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(1.8)  # ✅ Optimizasyon: 3sn -> 1.8sn
            
            reviews = []
            while len(reviews) < limit:
                new_reviews = await self.page.evaluate('''() => {
                    const items = document.querySelectorAll('.review');
                    return Array.from(items).map(el => {
                        const dateEl = el.querySelector('.detail-item.date');
                        const commentEl = el.querySelector('.review-comment span');
                        const fullStars = el.querySelectorAll('.star-w .full').length;
                        return {
                            date: dateEl ? dateEl.innerText.replace(/\\n/g, ' ').trim() : "",
                            rating: fullStars || 5,
                            comment: commentEl ? commentEl.innerText.trim() : ""
                        };
                    });
                }''')
                
                for r in new_reviews:
                    if r not in reviews:
                        reviews.append(r)
                
                if len(reviews) >= limit: break
                
                prev_height = await self.page.evaluate('document.body.scrollHeight')
                await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(1.2)  # ✅ Optimizasyon: 2sn -> 1.2sn
                new_height = await self.page.evaluate('document.body.scrollHeight')
                if new_height == prev_height: break 
            
            return reviews[:limit]
        except Exception as e:
            console.print(f"[red]❌ Yorumlar çekilemedi: {e}[/red]")
            return []

    async def _get_review_count_fallback(self):
        try:
            selectors = [
                '[data-testid="review-info-link"]', 
                '.reviews-summary-reviews-summary-detail', 
                '.total-review-count',
                '.pr-rnv-cnt-lnk-txt'
            ]
            for selector in selectors:
                text = await self._get_text_content(selector)
                if text:
                    nums = re.findall(r'\d+', text.replace('.', ''))
                    if nums: return int(nums[0])
            return 0
        except: return 0

    async def _get_rating_score_fallback(self):
        """HTML üzerinden puanı (örn: 4.5) çeker"""
        try:
            selectors = ['.rating-score', '.pr-rnv-rating-score', '.reviews-summary-rating-detail']
            for selector in selectors:
                text = await self._get_text_content(selector)
                if text:
                    match = re.search(r'(\d+[.,]\d+|\d+)', text)
                    if match:
                        return float(match.group(1).replace(',', '.'))
            return 0.0
        except: return 0.0
