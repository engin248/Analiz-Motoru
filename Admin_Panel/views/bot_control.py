
import streamlit as st
from datetime import datetime
import time
import os

def format_number_tr(number):
    try:
        return f"{int(number):,}".replace(",", ".")
    except:
        return str(number)

from Admin_Panel.core.engine import (
    fetch_tasks, fetch_task_stats, fetch_stats, get_bot_status, 
    start_bot, stop_bot, delete_task, add_task, update_task_name, 
    update_task_url, update_task_shift, update_task_active_status,
    seed_default_tasks, extract_keyword_from_url,
    fetch_all_task_stats, get_all_bot_statuses,
    update_task_search_params # YENİLER
)
from Admin_Panel.styles.main_styles import apply_bot_card_styles

def render_bot_control():
    # --- PRELOAD WITH SPINNER ---
    # Placeholder for the main content to avoid partial rendering
    main_placeholder = st.empty()

    with st.spinner("🤖 Sistem ve Botlar Taranıyor..."):
        # time.sleep(2) # Kullanıcı yükleme ekranını görsün diye hafif gecikme - KALDIRILDI PERFORMANS İÇİN
        apply_bot_card_styles()
        
        # 1. GLOBAL STATS
        stats = fetch_stats()
        
        # 2. TASKS & STATUS
        seed_default_tasks()
        tasks = fetch_tasks()
        all_task_stats = fetch_all_task_stats()
        running_bot_ids = get_all_bot_statuses()
        
        # 3. PREPARE CONSTANTS (Moved here to be in scope)
        from datetime import time as dt_time
        import urllib.parse
        
        page_opts = [10, 20, 30, 40, 200, 1000]
        page_labels = ["10", "20", "30", "40", "200 (Son)", "Hepsi"]
        val_map = dict(zip(page_labels, page_opts))

    # --- RENDER UI INSIDE THE PLACEHOLDER ---
    with main_placeholder.container():
        # --- PREMIUM BAŞLIK ---
        st.markdown('<div class="stats-container">', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("TOPLAM ÜRÜN", format_number_tr(stats.get("total_products", 0)), "Veri Tabanındaki Ürün")
        with c2:
            st.metric("GÜNLÜK DEĞİŞİM", f"+{format_number_tr(stats.get("daily_new", 0))}", "Bugün Eklenen")
        with c3:
            st.metric("AKTİF BOTLAR", stats.get("active_bots", 0), "Şu An Çalışan")
        with c4:
            st.metric("SİSTEM DURUMU", "NORMAL", "Sunucu Yükü: %12") # Örnek statik veri
        st.markdown('</div>', unsafe_allow_html=True)

        # --- TASKS ---
        st.write("")
        col_hdr, col_auto = st.columns([0.8, 0.2])
        col_hdr.markdown("### 🤖 İşçi Botlar")
        
        should_refresh = col_auto.toggle("📡 Canlı Veri Akışı", value=False)
        if should_refresh:
            time.sleep(3)
            st.rerun()

        
        if not tasks:
            st.warning("Henüz hiç bot görevi tanımlanmamış.")
            return

        main_cols = st.columns(3) # Re-introducing the 3-column layout for tasks

        for i, task in enumerate(tasks):
            # Durum ve İstatistikleri Map'ten çek
            is_actually_running = task.id in running_bot_ids
            is_user_enabled = task.is_active
            
            # Varsayılan boş istatistik
            t_stats = all_task_stats.get(task.id, {"total_scraped": 0, "errors": 0, "speed_hour": 0, "ip_changes": 0})
            
            # Status Color & Text
            status_badge_class, status_text, status_clr, status_msg, status_tip = "", "", "", "", ""
            if is_actually_running:
                status_badge_class, status_text, status_clr, status_msg, status_tip = "badge-active-v8", "🟢 ÇALIŞIYOR", "#00F5A0", "SAĞLIKLI", "Verim en üst düzeyde. İşlem stabil ilerliyor."
            elif is_user_enabled:
                status_badge_class, status_text, status_clr, status_msg, status_tip = "badge-waiting-v8", "🟡 BEKLEMEDE", "#FFA500", "BEKLEMEDE", "Otomasyon açık, mesai saatini bekliyor."
            else:
                status_badge_class, status_text, status_clr, status_msg, status_tip = "badge-passive-v8", "⚪ PASİF (KAPALI)", "#666", "DURAKLATILDI", f"{task.task_name} yeni bir 'Başlat' komutu bekliyor."

            with main_cols[i % 3]:
                with st.container(border=True):
                    st.markdown(f'<div class="bot-card-content">', unsafe_allow_html=True)
                    
                    # 1. ÜST ŞERİT
                    top_l, top_mid, top_r = st.columns([2, 5, 1])
                    with top_l:
                        st.markdown(f'<div class="b-badge-v8 {status_badge_class}">{status_text}</div>', unsafe_allow_html=True)
                    with top_mid:
                        p_name = task.target_platform.upper()
                        p_class = f"plat-{task.target_platform.lower()}" if task.target_platform.lower() in ["trendyol", "amazon"] else "plat-other"
                        st.markdown(f'<div style="text-align: center;"><div class="plat-badge-v8 {p_class}">{p_name}</div></div>', unsafe_allow_html=True)
                    with top_r:
                        # Butonu kıpkırmızı bir kutu yapmak için işaretçimiz
                        st.markdown('<div class="trash-btn-mark-final"></div>', unsafe_allow_html=True)
                        if st.button("🗑️", key=f"top_del_{task.id}", help="Görevi Sil"):
                            if delete_task(task.id): st.rerun()

                    # 2. İSİM VE DÜZENLEME
                    name_col, btn_col = st.columns([0.1 + (len(task.task_name) * 0.05), 1])
                    with name_col:
                        st.markdown(f'<div class="b-title-v8">{task.task_name}</div>', unsafe_allow_html=True)
                    with btn_col:
                        with st.popover("✏️", help="Yeniden Adlandır"):
                            new_name = st.text_input("Giriş Yapın", value=task.task_name, key=f"r_v8_{task.id}")
                            if st.button("Onayla", key=f"s_v8_{task.id}", type="primary", use_container_width=True):
                                if update_task_name(task.id, new_name): st.rerun()

                    st.markdown(f'<div class="b-sub-v8">{task.target_platform.upper()} KAZIMA BİRİMİ</div>', unsafe_allow_html=True)

                    # 2.5 HIZLI KELİME VE MESAİ PLANI
                    st.markdown('<div style="margin-top:15px; margin-bottom:5px; font-size:10px; font-weight:800; color:#555;">🕒 MESAİ VE KELİME PLANI</div>', unsafe_allow_html=True)
                    
                    try:
                        s_h, s_m = map(int, task.start_time.split(":"))
                        e_h, e_m = map(int, task.end_time.split(":"))
                        def_start, def_end = dt_time(s_h, s_m), dt_time(e_h, e_m)
                    except: def_start, def_end = dt_time(9, 0), dt_time(18, 0)

                    # GÜNCEL VERİLERİ ÇEK
                    current_kw = extract_keyword_from_url(task.target_url)
                    current_params = task.search_params if task.search_params and isinstance(task.search_params, dict) else {}
                    db_pages = int(current_params.get("max_pages", 50))
                    
                    curr_idx = 0
                    if db_pages in page_opts: curr_idx = page_opts.index(db_pages)
                    else: 
                        # Özel değer varsa listeye eklemeden en yakını seç veya 50 varsay
                        curr_idx = 4 if db_pages >= 200 else 0

                    # ---------------- FORM MODU: Sayfa Yenilemelerini Engellemek İçin ----------------
                    with st.form(key=f"settings_form_{task.id}", border=False):
                        c_kw, c_st, c_en, c_pg = st.columns([1.5, 0.8, 0.8, 1.0])
                        
                        with c_kw: 
                            new_kw = st.text_input("Kelime", value=current_kw, placeholder="Elbise", key=f"qkw_{task.id}")
                        with c_st: 
                            new_start = st.time_input("Başla", value=def_start, key=f"qst_{task.id}")
                        with c_en: 
                            new_end = st.time_input("Bitir", value=def_end, key=f"qen_{task.id}")
                        with c_pg:
                            sel_label = st.selectbox("Sayfa Limit", options=page_labels, index=curr_idx, key=f"qpg_{task.id}")
                        
                        submitted = st.form_submit_button("💾 Ayarları Kaydet", use_container_width=True, type="secondary")

                    if submitted:
                        new_pages = val_map[sel_label]
                        has_changes = False
                        
                        # 1. Kelime değişti mi?
                        if new_kw != current_kw:
                            new_url = f"https://www.trendyol.com/sr?q={urllib.parse.quote(new_kw)}"
                            if update_task_url(task.id, new_url): has_changes = True
                        
                        # 2. Saatler değişti mi?
                        s_str = new_start.strftime("%H:%M")
                        e_str = new_end.strftime("%H:%M")
                        if s_str != task.start_time or e_str != task.end_time:
                            if update_task_shift(task.id, s_str, e_str): has_changes = True
                        
                        # 3. Sayfa sayısı değişti mi?
                        if new_pages != db_pages:
                            if update_task_search_params(task.id, {"max_pages": new_pages}): has_changes = True
                        
                        if has_changes:
                            st.toast("✅ Ayarlar güncellendi!", icon="💾")
                            time.sleep(0.5)
                            st.rerun()

                    # 3. METRİKLER (2x2 GRID)
                    # t_stats artık fetch_task_stats ile çekilmiyor, yukarıdaki toplu listeden geliyor
                    st.write("")
                    m_row1_c1, m_row1_c2 = st.columns(2)
                    with m_row1_c1:
                        st.markdown(f'<div class="metric-pill-v8"><div class="m-val-v8">{t_stats["total_scraped"]}</div><div class="m-lab-v8">Kazılan Link</div></div>', unsafe_allow_html=True)
                    with m_row1_c2:
                        st.markdown(f'<div class="metric-pill-v8"><div class="m-val-v8">{t_stats["speed_hour"] if is_actually_running else 0}</div><div class="m-lab-v8">Hız (Ürün/Sa)</div></div>', unsafe_allow_html=True)
                    
                    st.write("")
                    m_row2_c1, m_row2_c2 = st.columns(2)
                    with m_row2_c1:
                        error_color = "#FF4B4B" if t_stats["errors"] > 0 else "#00F5A0"
                        st.markdown(f'<div class="metric-pill-v8"><div class="m-val-v8" style="color: {error_color};">{t_stats["errors"]}</div><div class="m-lab-v8">Hata Sayısı</div></div>', unsafe_allow_html=True)
                    with m_row2_c2:
                        st.markdown(f'<div class="metric-pill-v8"><div class="m-val-v8">{t_stats["ip_changes"]}</div><div class="m-lab-v8">IP Değişimi</div></div>', unsafe_allow_html=True)

                    # 4. AI SAĞLIK ANALİZİ
                    if is_actually_running:
                        if t_stats["errors"] > 5: status_msg, status_tip, status_clr = "KRİTİK", "Hedef site engel koymuş olabilir.", "#FF4B4B"
                        elif t_stats["speed_hour"] < 10: status_msg, status_tip, status_clr = "YAVAŞ", "Ağ gecikmesi tespit edildi.", "#FFA500"
                    
                    st.markdown(f"""
                        <div style="background: #262626; border: 1px solid #444; border-left: 3px solid {status_clr}; padding: 12px; border-radius: 8px; margin-top: 20px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                                <span style="font-size: 10px; font-weight: 800; color: {status_clr}; letter-spacing: 1px;">AI SAĞLIK ANALİZİ</span>
                                <span style="background: {status_clr}33; color: {status_clr}; font-size: 8px; padding: 2px 6px; border-radius: 4px; font-weight: 900;">{status_msg}</span>
                            </div>
                            <div style="font-size: 12px; color: #EEE; font-weight: 500; line-height: 1.4;">{status_tip}</div>
                        </div>
                        <div style="font-size: 9px; color: #444; margin-top: 10px; padding: 0 5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">🌐 {task.target_url}</div>
                    """, unsafe_allow_html=True)

                    # 5. AKSİYONLAR
                    # İstenilen düzen: [PLANLA/İPTAL] [BAŞLAT/DURDUR] [⚠️] [⚙️]
                    act_c1, act_c2, act_c3, act_c4 = st.columns([1, 1, 0.5, 0.5])
                    
                    # Sütun 1: PLANLA / İPTAL (Mesai Takvimi Kontrolü)
                    with act_c1:
                        if is_user_enabled:
                             if st.button("İPTAL ET", key=f"plan_off_{task.id}", use_container_width=True, help="Planlı çalışmayı durdur"):
                                 update_task_active_status(task.id, False)
                                 st.rerun()
                        else:
                            if st.button("PLANLA", key=f"plan_on_{task.id}", type="secondary", use_container_width=True, help="Mesai saatlerinde otomatik çalışsın"):
                                 update_task_active_status(task.id, True)
                                 st.rerun()

                    # Sütun 2: BAŞLAT / DURDUR (Manuel Kontrol)
                    with act_c2:
                        if is_actually_running:
                            if st.button("DURDUR", key=f"force_stop_{task.id}", type="primary", use_container_width=True):
                                stop_bot(task.id)
                                st.rerun()
                        else:
                            if st.button("BAŞLAT", key=f"force_start_{task.id}", type="primary", use_container_width=True, help="Saati beklemeden hemen başlat"):
                                # BAŞLAT butonuna basıldığında hem otomasyonu açıyoruz hem de saati beklemeden başlatıyoruz
                                update_task_active_status(task.id, True)
                                start_bot(task.id, task.target_url, force=True)
                                time.sleep(2) # Botun tam olarak başlaması ve PID dosyasının oluşması için bekle
                                st.rerun()

                    # Sütun 3: HATA LOGLARI
                    with act_c3:
                        error_count = t_stats.get("errors", 0)
                        btn_label = f"⚠️ {error_count}" if error_count > 0 else "⚠️"
                        if st.button(btn_label, key=f"wr_v8_{task.id}", use_container_width=True, help="Hata Kayıtlarını Gör"):
                            st.query_params["p"] = "📜 Sistem Logları"
                            st.query_params["filter"] = "errors"
                            st.rerun()
                    
                    # Sütun 4: AYARLAR
                    with act_c4:
                        with st.popover("⚙️", help="Ayarlar", use_container_width=True):
                            st.markdown('<div style="font-size: 14px; font-weight: 700; margin-bottom: 10px;">Gelişmiş Ayarlar</div>', unsafe_allow_html=True)
                            
                            # 1. HIZ KONTROLÜ
                            current_delay = int(current_params.get("request_delay", 2))
                            new_delay = st.slider("Hız Limiti (Sn)", 1, 10, current_delay, key=f"spd_{task.id}", help="Her sayfa arası bekleme süresi")
                            
                            if new_delay != current_delay:
                                update_task_search_params(task.id, {"request_delay": new_delay})
                                st.toast(f"Hız güncellendi: {new_delay} sn", icon="⚡")
                                time.sleep(0.5)
                                st.rerun()

                            st.markdown("---")
                            
                            # 2. İSTATİSTİK SIFIRLAMA
                            if st.button("♻️ İstatistikleri Sıfırla", key=f"rst_v8_{task.id}", use_container_width=True, help="Hata ve işlem sayacı sıfırlanır"):
                                from Admin_Panel.core.engine import clear_task_stats
                                success, msg = clear_task_stats(task.id)
                                if success:
                                    st.toast(msg, icon="✅")
                                    time.sleep(0.5)
                                    st.rerun()
                            
                            st.markdown("---")

                            # 3. SİLME
                            if st.button("🗑️ Görevi Sil", key=f"dl_v8_{task.id}", type="secondary", use_container_width=True):
                                if delete_task(task.id): st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)

        # YENİ BOT EKLEME KARTI
        with main_cols[len(tasks) % 3]:
            with st.container(border=True):
                st.markdown('<div class="bot-card-content" style="padding: 20px; text-align: center;">', unsafe_allow_html=True)
                st.markdown("""
                    <div style='margin-bottom: 20px; padding-top: 10px; text-align: center; width: 100%; display: flex; flex-direction: column; align-items: center;'>
                        <div style='font-size: 48px; margin-bottom: 10px; filter: grayscale(1); opacity: 0.3; width: 100%; text-align: center;'>🤖</div>
                        <div class="b-title-v8" style="color: #888; font-size: 20px; font-weight: 700; width: 100%; text-align: center;">Yeni İşçi Ekle</div>
                    </div>
                """, unsafe_allow_html=True)
                with st.popover("➕ YENİ BOT TANIMLA", use_container_width=True):
                    with st.form(key="new_bot_form", border=False):
                        n_name = st.text_input("Bot İsmi", placeholder="Örn: İşçi 2")
                        n_plat = st.selectbox("Platform", ["trendyol", "amazon"])
                        n_val = st.text_input("Kelime/URL", placeholder="Örn: mont veya https://...")
                        
                        submitted = st.form_submit_button("🚀 BİRİMİ AKTİF ET", type="primary", use_container_width=True)
                        
                        if submitted:
                            if n_name and n_val:
                                final_url = n_val
                                if n_plat == "trendyol" and "http" not in n_val:
                                     import urllib.parse
                                     final_url = f"https://www.trendyol.com/sr?q={urllib.parse.quote(n_val)}"
                                
                                add_task(n_name, n_plat, final_url, 24)
                                st.success("Yeni bot başarıyla tanımlandı!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Lütfen tüm alanları doldurun.")
                st.markdown('</div>', unsafe_allow_html=True)
