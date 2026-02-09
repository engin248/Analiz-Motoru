"""
Playwright için Stealth (Gizlilik) Modu Enjeksiyonları.
Bu scriptler tarayıcı ortamını değiştirerek bot tespitini zorlaştırır.
"""

async def apply_stealth(context):
    """
    Verilen Playwright context nesnesine gizlilik scriptlerini enjekte eder.
    """
    
    # 1. WebDriver Özelliğini Kaldır
    # Botların en büyük açık veren özelliği 'navigator.webdriver = true' olmasıdır.
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
    """)

    # 2. Chrome Runtime Mocking
    # Normal Chrome'da 'window.chrome' tanımlıdır, Playwright'ta bazen eksiktir.
    await context.add_init_script("""
        window.chrome = {
            runtime: {}
        };
    """)

    # 3. WebGL Fingerprint Spoofing (Ekran Kartı Gürültüsü)
    # Ekran kartının çizdiği grafikleri çok hafif değiştirir (Unique ID oluşturur).
    await context.add_init_script("""
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            // Vendor ve Renderer bilgisini maskele (Örn: Intel Iris yerine GenericGPU)
            if (parameter === 37446) return 'Intel Inc.';
            if (parameter === 37445) return 'Intel Iris OpenGL Engine';
            return getParameter(parameter);
        };
    """)

    # 4. Plugins (Eklentiler) Mocking
    # Botlarda genellikle plugin listesi boştur. Buraya sahte pluginler ekliyoruz.
    await context.add_init_script("""
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        Object.defineProperty(navigator, 'languages', {
            get: () => ['tr-TR', 'tr', 'en-US', 'en'],
        });
    """)

    # 5. Permission (İzinler) API Maskelemesi
    # Notification izinlerini sorulmuş gibi yapar.
    await context.add_init_script("""
        const originalQuery = window.navigator.permissions.query;
        return window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
        );
    """)
    
    # 6. Screen Dimension (Ekran Boyutu) Tutarlılığı
    await context.add_init_script("""
        Object.defineProperty(window, 'outerWidth', { value: window.innerWidth });
        Object.defineProperty(window, 'outerHeight', { value: window.innerHeight });
    """)
