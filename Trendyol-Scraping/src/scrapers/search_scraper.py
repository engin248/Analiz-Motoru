from playwright.async_api import Page
import asyncio

class SearchScraper:
    def __init__(self, page: Page):
        self.page = page

    async def get_product_links(self, keyword: str, page_num: int):
        """
        Belirtilen kelime ve sayfa numarasındaki ürün linklerini toplar.
        """
        # Daha doğal URL yapısı (Kullanıcı gibi)
        url = f"https://www.trendyol.com/sr?q={keyword}&qt={keyword}&st={keyword}&os=1&pi={page_num}"
        
        try:
            # 🛡️ İnatçı Mod (Retry Logic)
            max_retries = 3
            for attempt in range(max_retries):
                # Sayfaya git
                await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Sadece 1. sayfadan sonrası için kontrol yap
                if page_num > 1:
                    current_url = self.page.url
                    import re
                    match = re.search(r'[?&]pi=(\d+)', current_url)
                    current_pi = int(match.group(1)) if match else 1
                    
                    if current_pi != page_num:
                        print(f"⚠️ Yönlendirme (Redirect) Tespit Edildi! (Deneme {attempt+1}/{max_retries})")
                        print(f"   İstenen: {page_num} -> Gelen: {current_pi}")
                        
                        if attempt < max_retries - 1:
                            print("   ⏳ 5 Saniye bekleyip tekrar deniyorum...")
                            await asyncio.sleep(5)
                            continue # Tekrar dene
                        else:
                            print("   ❌ Israrla yanlış sayfaya atıyor. Pes ediyorum.")
                            return None # 3 kere denedik olmadı, dur.
                # 🛡️ 2. Katman: HTML İçerik Kontrolü (Kesin Çözüm)
                # URL doğru görünse bile içerik yanlış olabilir. Sayfanın altındaki "Aktif Sayfa" kutusuna bak.
                if page_num > 1:
                    actual_page = await self.page.evaluate('''() => {
                        // Olası aktif sayfa selectorleri
                        const selectors = [
                            '.pagination .active', 
                            '.pagination .current', 
                            '.p-pagination-wrapper .active',
                            'div[class*="pagination"] .active'
                        ];
                        
                        for (let sel of selectors) {
                            const el = document.querySelector(sel);
                            if (el) return parseInt(el.innerText);
                        }
                        return null; // Bulunamazsa null
                    }''')
                    
                    if actual_page and actual_page != page_num:
                        print(f"⚠️ İÇERİK HATASI: URL doğru ama sayfa içeriği {actual_page}. sayfa! (İstenen: {page_num})")
                        print(f"   (Deneme {attempt+1}/{max_retries})")
                        
                        if attempt < max_retries - 1:
                            print("   ⏳ 5 Saniye bekleyip tekrar deniyorum...")
                            await asyncio.sleep(5)
                            continue 
                        else:
                            return None

            # Ürün kartı yerine sadece body'nin yüklenmesini bekle (Daha güvenli)
            await self.page.wait_for_selector('body', timeout=10000)

            # Kesik Kesik Kaydırma (Daha Seri ve Uzun Timeout)
            await self.page.evaluate('''async () => {
                const sleep = (ms) => new Promise(r => setTimeout(r, ms));
                let totalHeight = 0;
                
                // 30 Saniye Güvenlik Kilidi (Yetişmesi için süre artırıldı)
                const startTime = Date.now();
                
                while (true) {
                    let scrollHeight = document.body.scrollHeight;
                    let currentPos = window.scrollY + window.innerHeight;
                    
                    // Sayfa sonuna geldik mi?
                    if (currentPos >= scrollHeight - 200) break;
                    
                    // Zaman aşımı kontrolü (30 sn)
                    if (Date.now() - startTime > 30000) break;
                    
                    // Biraz daha büyük adımlarla kaydır (600-800px)
                    let step = Math.floor(Math.random() * 200) + 600;
                    window.scrollBy(0, step);
                    
                    // Biraz daha kısa bekle (0.3 - 0.8 sn)
                    let wait = Math.floor(Math.random() * 500) + 300;
                    await sleep(wait);
                }
            }''')
            
            # Kaydırma bittikten sonra biraz soluklan
            await asyncio.sleep(1.5)

            # Linkleri topla - CSS Class bağımsız yöntem!
            # Sayfadaki TÜM linkleri al, içinde "-p-" geçenleri filtrele.
            links = await self.page.evaluate('''() => {
                const anchors = Array.from(document.querySelectorAll('a'));
                return anchors
                    .map(a => a.href)
                    .filter(href => href.includes('-p-') && !href.includes('javascript'));
            }''')
            
            # Tekrarlayan linkleri temizle (Set kullanarak)
            unique_links = list(set(links))
            return unique_links
            
            # Linkleri temizle (gereksiz parametreleri atabiliriz ama şimdilik ham alalım)
            # Sadece /b/ veya /brand/ veya p-123 gibi patternleri kontrol edebiliriz ama
            # Trendyol linkleri genelde temizdir.
            
            return links

        except Exception as e:
            print(f"Hata (Sayfa {page_num}): {str(e)}")
            return []
