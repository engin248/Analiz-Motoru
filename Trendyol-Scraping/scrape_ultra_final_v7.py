
import asyncio
import pandas as pd
import os
import sys
from playwright.async_api import async_playwright, Page
from rich.console import Console

from rich.console import Console
from datetime import datetime
import re

# Add project root to path for imports
# Add project root to path for imports
import sys
import os

# Paths setup to reach LangChain_backend
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
backend_path = os.path.join(parent_dir, 'LangChain_backend')
sys.path.append(backend_path)

# Database Integration (Main App)
from app.core.database import SessionLocal, engine
from app.models.product import Product
from app.models.daily_metric import DailyMetric
from sqlalchemy import text

console = Console()


class ProductScraperUltraV7:
    def __init__(self, page: Page):
        self.page = page

    async def scrape_product(self, product_url: str):
        try:
            await self.page.goto(product_url, wait_until='domcontentloaded', timeout=60000)
            await self.page.mouse.wheel(0, 500)
            await asyncio.sleep(3) 
        except: 
            return None
            
        data = await self.page.evaluate('''() => {
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

            // 1. KİMLİK
            res.brand = (document.querySelector('a.brand-link') || document.querySelector('.brand-name'))?.innerText.trim() || '';
            res.name  = (document.querySelector('h1.product-title span') || document.querySelector('h1.product-title'))?.innerText.trim() || '';

            // --- FİYAT MOTORU (SAĞLAM V6) ---
            // --- FİYAT MOTORU (HEDEFLENMİŞ V9 - SPATIAL VALIDATION) ---
            
            // Eleman görünür mü ve asıl ürün alanında mı? (Tuzakları ayıkla)
            const isVisible = (el) => {
                if(!el) return false;
                
                // --- TUZAK FİLTRESİ (REKLAM & ÖNERİ) ---
                if(el.closest('.p-card-wrppr') || 
                   el.closest('.product-card') || 
                   el.closest('.widget-product') || 
                   el.closest('.recommendation-box') ||
                   el.closest('.carousel') ||
                   el.closest('.reco-slider') ||
                   el.closest('[data-testid="recommendation"]')) {
                    return false;
                }
                
                const style = window.getComputedStyle(el);
                return style.display !== 'none' && 
                       style.visibility !== 'hidden' && 
                       el.offsetParent !== null && 
                       el.innerText.trim().length > 0;
            };

            // Ana konteyner (Sadece asıl ürünün bilgilerinin olduğu en dar alan)
            let mainContainer = document.querySelector('.product-detail-container') || 
                                document.querySelector('.product-container') ||
                                document.querySelector('.pr-in-w-gv') || 
                                document.querySelector('.pr-in-w') ||
                                document.querySelector('.price-wrapper');
            
            if(!mainContainer) {
                // Eğer spesifik containerlar yoksa, H1 başlığına en yakın ana bloğu al
                const h1 = document.querySelector('h1.product-title');
                mainContainer = h1 ? h1.closest('.product-detail-wrapper') || h1.parentElement : document;
            }

            const candidates = [
                {
                    type: 'lowest_price_button', 
                    priceEl: mainContainer.querySelector('.price-view .discounted'),
                    oldEl: mainContainer.querySelector('.price-view .original'),
                    priority: 1
                },
                {
                    type: 'red_plus', 
                    priceEl: mainContainer.querySelector('.ty-plus-price-discounted-price'),
                    oldEl: mainContainer.querySelector('.ty-plus-price-original-price'),
                    priority: 1
                },
                {
                    type: 'campaign_common', 
                    priceEl: mainContainer.querySelector('.price-campaign-price-variant-common-price .new-price') || 
                             mainContainer.querySelector('.campaign-price-wrapper .new-price'),
                    oldEl: mainContainer.querySelector('.price-campaign-price-variant-common-price .old-price') || 
                            mainContainer.querySelector('.campaign-price-wrapper .old-price'),
                    priority: 2
                },
                {
                    type: 'standard_discount', 
                    priceEl: mainContainer.querySelector('.price-container .discounted') || 
                             mainContainer.querySelector('.prc-dsc') || 
                             mainContainer.querySelector('.discounted'),
                    oldEl: mainContainer.querySelector('.price-container .original') || 
                            mainContainer.querySelector('.prc-org') || 
                            mainContainer.querySelector('.original'),
                    priority: 3
                },
                {
                    type: 'product_price_direct',
                    priceEl: mainContainer.querySelector('.product-price'),
                    oldEl: null,
                    priority: 4
                }
            ];

            // Görünür olanları filtrele ve önceliğe göre sırala
            const valid = candidates.filter(c => isVisible(c.priceEl)).sort((a,b) => a.priority - b.priority);

            if(valid.length > 0) {
                const winner = valid[0];
                res.price = cleanPrice(winner.priceEl.innerText);
                
                if(winner.oldEl && isVisible(winner.oldEl)) {
                    res.org_price = cleanPrice(winner.oldEl.innerText);
                } else {
                    const fallbackOld = mainContainer.querySelector('.prc-org') || 
                                      mainContainer.querySelector('.old-price') ||
                                      mainContainer.querySelector('.original');
                    res.org_price = isVisible(fallbackOld) ? cleanPrice(fallbackOld.innerText) : res.price;
                }
                res.debug_info.push(`WIN: ${winner.type}`);
            } else {
                // Hiçbiri bulunamazsa Regex ile mainContainer içinde ara
                const match = mainContainer.innerText.match(/(\\d+[.,]?\\d*)\\s*TL/);
                if(match) { res.price = cleanPrice(match[1]); res.org_price = res.price; }
            }
            if(res.org_price === 0) res.org_price = res.price;
            if(res.org_price < res.price) res.org_price = res.price;

            // --- METRİK MOTORU (V3'E DÖNÜŞ &ZAMAN FİLTRESİ) ---
            
            // Yardımcı: Gerçek Metrik Parse Edici
            const parseMetricV3 = (text) => {
                if(!text) return 0;
                let cleanText = text.toLowerCase();
                
                // 1. TUZAKLARI TEMİZLE (Son 2 saatte, Son 3 gün) -> Sayıları bozuyor
                cleanText = cleanText.replace(/son\\s+\\d+\\s+(saat|gün|dakika|hafta|ay)[te]*/g, ''); 
                cleanText = cleanText.replace(/[\\d.,]+\\s+(saat|gün|dakika)(te|de)*/g, ''); // "3 saatte" gibi ifadeler
                cleanText = cleanText.replace(/kişi[a-z]*/g, ''); // ✅ "kişinin", "kişi" kelimelerini temizle (k harfi karışmasın)
                
                // 2. REGEX İLE PARSE (Sayı + Birim)
                const match = cleanText.match(/([\\d.,]+)\\s*(bin|mn|b|m|k)?/);
                if(!match) return 0;
                
                let numStr = match[1];
                let unit = match[2]; // bin, b, k...
                
                // 3. SAYI DÖNÜŞÜMÜ
                if(unit) {
                    // Birim varsa virgül ondalıktır: "1,5 bin" -> 1.5
                    numStr = numStr.replace(',', '.');
                } else {
                    // Birim yoksa: "1.500" -> 1500 (Nokta binliktir), "100" -> 100
                    // Virgül varsa ondalıktır ama Trendyol genelde tamsayı verir metriklerde
                    // En güvenli yöntem: Noktaları sil, virgülü nokta yap
                    numStr = numStr.replace(/\\./g, '').replace(',', '.');
                }
                
                let val = parseFloat(numStr);
                
                // 4. ÇARPANLAR
                if(['bin', 'b', 'k'].includes(unit)) val *= 1000;
                if(['mn', 'm'].includes(unit)) val *= 1000000;
                
                return Math.round(val);
            };

            // Review & Rating
            const reviewEl = document.querySelector('.reviews-summary-reviews-detail') ||
                             document.querySelector('.total-review-count') ||
                             document.querySelector('[data-testid="review-info-link"]');
                             
            if(isVisible(reviewEl)) {
               const nums = reviewEl.innerText.match(/\\d+/g);
               if(nums) res.reviews = parseInt(nums.join(''));
            }
            
            const ratingEl = document.querySelector('.rating-score') || 
                             document.querySelector('.rating-line-count') ||
                             document.querySelector('.pr-rnv-rating-score') ||
                             document.querySelector('.reviews-summary-rating-detail');
                             
            if(isVisible(ratingEl)) {
                 const t = ratingEl.innerText.trim();
                 const m = t.match(/([\\d]+[.,][\\d]+)|([\\d]+)/); // Matches 4.5 or 4,5 or 4
                 if(m) {
                     res.rating = parseFloat(m[0].replace(',', '.'));
                 }
            }

            // Sosyal Kanıtlar
            const proofs = document.querySelectorAll('.social-proof-content');
            proofs.forEach(box => {
                if(!isVisible(box)) return;
                const rawText = box.innerText; // "Son 3 saatte 500 kişinin sepetinde"
                const focusedSpan = box.querySelector('.social-proof-item-focused-text');
                
                // Eğer focused span (koyu yazı) varsa sadece onu al, yoksa tüm metni
                let val = 0;
                if(focusedSpan) val = parseMetricV3(focusedSpan.innerText);
                else val = parseMetricV3(rawText);
                
                const textLower = rawText.toLowerCase();
                if(textLower.includes('favori')) res.favs = val;
                else if(textLower.includes('sepet')) res.basket = val;
                else if(textLower.includes('görüntü') || textLower.includes('baktı')) res.views = val;
            });

            // Resim (Geliştirilmiş)
            const imgSelectors = ['.product-slide img', '.gallery-container img', '.base-product-image img', 'img[data-testid="image"]'];
            for(let sel of imgSelectors) {
                const img = document.querySelector(sel);
                if(img && img.src && !img.src.includes('data:')) {
                    res.images.push(img.src);
                    break;
                }
            }

            return res;
        }''')
        return data

async def scrape_ultra_v7():
    console.print("[bold green]🚀 ULTRA V7 (INTEGRATED - LANGCHAIN_BACKEND DB)[/bold green]\n")
    
    # --- DB CONNECTION ---
    try:
        db = SessionLocal()
        console.print("[green]✅ Ana Veritabanı (Postgres) bağlantısı başarılı.[/green]")
    except Exception as e:
        console.print(f"[red]❌ Veritabanı bağlantı hatası: {e}[/red]")
        return

    # --- FETCH TASKS FROM DB ---
    # Henüz taranmamış veya güncellenmesi gereken ürünleri çekiyoruz
    console.print("[cyan]🔄 Veritabanından taranacak linkler çekiliyor...[/cyan]")
    
    # Strateji: last_scraped_at NULL olanlar (yeni) veya çok eski olanlar
    # Şimdilik basitçe tüm ürünleri sırayla gezelim (limitli)
    products_to_scrape = db.query(Product).order_by(Product.last_scraped_at.asc().nullsfirst()).limit(50).all()
    
    if not products_to_scrape:
        console.print("[yellow]⚠️ Veritabanında taranacak ürün bulunamadı. Önce Link Toplayıcıyı (harvest_links.py) çalıştırın.[/yellow]")
        db.close()
        return

    console.print(f"[green]🎯 Hedef: {len(products_to_scrape)} ürün taranacak.[/green]")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        scraper = ProductScraperUltraV7(page)
        
        results = []
        
        for i, db_product in enumerate(products_to_scrape, 1):
            if not db_product.url:
                continue
                
            link = db_product.url
            console.print(f"\n[cyan]#{i}[/cyan] Gidiliyor: {link}")
            
            try:
                data = await scraper.scrape_product(link)
                
                if data:
                    # --- DB SAVE (MAIN APP) ---
                    try:
                        # 1. Update Product Table (Main Info)
                        db_product.name = data.get('name', '')[:255]
                        db_product.brand = data.get('brand', '')[:255]
                        db_product.image_url = data.get('images', [''])[0] if data.get('images') else ''
                        
                        # Update Last Prices in Product Table for quick access
                        db_product.last_price = data.get('price', 0)
                        # Discount calculation
                        price = data.get('price', 0)
                        org_price = data.get('org_price', 0)
                        if org_price > price:
                             db_product.last_discount_rate = ((org_price - price) / org_price) * 100
                        else:
                             db_product.last_discount_rate = 0
                             
                        db_product.last_scraped_at = datetime.utcnow()
                        
                        # 2. Insert or Update DailyMetrics (Time Series)
                        # Check if a metric record already exists for today (likely created by harvest_links)
                        from datetime import timedelta
                        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                        
                        existing_metric = db.query(DailyMetric).filter(
                            DailyMetric.product_id == db_product.id,
                            DailyMetric.recorded_at >= today_start
                        ).order_by(DailyMetric.id.desc()).first()
                        
                        if existing_metric:
                            # UPDATE EXISTING RECORD
                            # We update the fields, preserving the sales_rank if it exists
                            existing_metric.price = org_price
                            existing_metric.discounted_price = price
                            existing_metric.discount_rate = db_product.last_discount_rate
                            existing_metric.avg_rating = data.get('rating', 0)
                            existing_metric.rating_count = data.get('reviews', 0)
                            existing_metric.favorite_count = data.get('favs', 0)
                            existing_metric.cart_count = data.get('basket', 0)
                            existing_metric.view_count = data.get('views', 0)
                            # recorded_at is kept as is (creation time)
                            
                            console.print(f"[blue]🔄 Günlük Veri Güncellendi (Rank Korundu): ID {existing_metric.id}[/blue]")
                        else:
                            # CREATE NEW RECORD
                            daily_metric = DailyMetric(
                                product_id=db_product.id,
                                price=org_price,
                                discounted_price=price,
                                discount_rate=db_product.last_discount_rate,
                                
                                # Metrics
                                avg_rating=data.get('rating', 0),
                                rating_count=data.get('reviews', 0),
                                favorite_count=data.get('favs', 0),
                                cart_count=data.get('basket', 0),
                                view_count=data.get('views', 0),
                                
                                recorded_at=datetime.utcnow()
                            )
                            db.add(daily_metric)
                            console.print(f"[green]➕ Yeni Günlük Veri Eklendi[/green]")
                        
                        db.commit()
                        
                        console.print(f"[green]💾 DB İşlemi Tamam: {db_product.name[:20]}...[/green]")
                        console.print(f"[green]✅ Fiyat: {price} TL | ⭐{data.get('rating')} | ♥{data.get('favs')}[/green]")
                        
                        # --- 3. SYSTEM LOG KAYDI (YENİ) ---
                        from src.models_log import SystemLog
                        
                        action_msg = f"Güncellendi: {db_product.name[:30]}... ({price} TL)"
                        if not existing_metric:
                            action_msg = f"Yeni Eklendi: {db_product.name[:30]}... ({price} TL)"
                            
                        new_log = SystemLog(
                            bot_name="Kazıyıcı-Bot-1",
                            level="INFO",
                            message=f"ID:{db_product.id} | {action_msg}"
                        )
                        db.add(new_log)
                        db.commit()
                        # --------------------------------
                        
                    except Exception as e:
                        console.print(f"[red]❌ DB Yazma Hatası: {e}[/red]")
                        
                        # Hata Logu
                        from src.models_log import SystemLog
                        err_log = SystemLog(
                            bot_name="Kazıyıcı-Bot-1",
                            level="ERROR",
                            message=f"ID:{db_product.id} HATA: {str(e)[:100]}"
                        )
                        db.add(err_log)
                        db.commit()
                        
                        db.rollback()
                        
                    except Exception as e:
                        console.print(f"[red]❌ DB Yazma Hatası: {e}[/red]")
                        db.rollback()
                    # ----------------
                    
                else: 
                    console.print("[red]❌ Veri çekilemedi[/red]")
                    
            except Exception as e: 
                console.print(f"[red]❌ Beklenmeyen Hata: {e}[/red]")
            
        await browser.close()
        db.close()
    
    console.print(f"\n✅ Tarama tamamlandı.")

if __name__ == "__main__":
    asyncio.run(scrape_ultra_v7())
