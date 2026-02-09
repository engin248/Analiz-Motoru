
import streamlit as st
import pandas as pd
import os
import urllib.parse
from Admin_Panel.core.engine import fetch_detailed_logs

def render_logs():
    # --- FİLTRELER ---
    default_error_val = st.query_params.get("filter") == "errors"
    
    col1, col2 = st.columns([2, 2])
    with col1:
        log_limit = st.select_slider("Gösterilecek Kayıt Sayısı:", options=[20, 50, 100, 250, 500, 1000], value=100)
    with col2:
        st.write("") # Spacer
        st.write("") # Spacer
        show_errors = st.checkbox("🚩 Sadece Hataları Göster", value=default_error_val)
        
    # --- VERİ ÇEKME ---
    logs_df = fetch_detailed_logs(limit=log_limit, show_errors_only=show_errors)
    
    if not logs_df.empty:
        # 1. TARİH FORMATLAMA
        if pd.api.types.is_datetime64_any_dtype(logs_df['started_at']):
            logs_df['started_at'] = pd.to_datetime(logs_df['started_at']) + pd.Timedelta(hours=3)
        if pd.api.types.is_datetime64_any_dtype(logs_df['finished_at']):
            logs_df['finished_at'] = pd.to_datetime(logs_df['finished_at']) + pd.Timedelta(hours=3)
        
        if 'screenshot_path' not in logs_df.columns:
            logs_df['screenshot_path'] = None
        if 'target_url' not in logs_df.columns:
            logs_df['target_url'] = None
        
        def clean_keyword_display(val):
            val_str = str(val)
            if not val_str.startswith('http'): return val_str
            try:
                parsed = urllib.parse.urlparse(val_str)
                query = urllib.parse.parse_qs(parsed.query)
                if 'q' in query: return query['q'][0].replace('+', ' ')
                if 'k' in query: return query['k'][0].replace('+', ' ')
                path_parts = parsed.path.split('/')
                valid_parts = [p for p in path_parts if p]
                if valid_parts:
                    last_part = valid_parts[-1]
                    if '-x-c' in last_part: return last_part.split('-x-c')[0].replace('-', ' ')
                    return last_part.replace('-', ' ')
                return val_str
            except: return val_str

        logs_df['Hedef / Kelime'] = logs_df['keyword'].apply(clean_keyword_display)
        logs_df['Başlangıç'] = logs_df['started_at'].dt.strftime('%d.%m.%Y %H:%M')
        logs_df['Bitiş'] = logs_df['finished_at'].apply(lambda x: x.strftime('%d.%m.%Y %H:%M') if pd.notnull(x) else '-')
        
        def get_status_label(row):
            errors = row.get('errors', 0)
            if errors and errors > 0: return '❌ Hata'
            status_map = {
                'completed': '✅ Tamamlandı',
                'running': '🔄 Çalışıyor',
                'error': '❌ Hata',
                'stopped': '⏹️ Durduruldu'
            }
            return status_map.get(row.get('status', ''), row.get('status', ''))

        logs_df['Durum'] = logs_df.apply(get_status_label, axis=1)

        def get_screenshot_status(row):
            filename = row.get('screenshot_path')
            if not filename: return None
            clean_name = filename.replace('captures/', '').replace('static/', '')
            # Yeni yapı: Scrapper klasöründen oku
            scrapper_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Scrapper")
            real_path = os.path.join(scrapper_root, "static", "captures", clean_name)
            if os.path.exists(real_path):
                return f"app/static/captures/{clean_name}"
            return None

        # Görünüm için kolonları hazırla
        display_df = logs_df.copy()
        display_df.rename(columns={'id': 'ID', 'platform': 'Platform', 'pages_scraped': 'Sayfa', 'products_found': 'Bulunan', 'products_added': 'Eklenen', 'errors': 'Hata'}, inplace=True)
        
        if 'Tam Link' not in display_df.columns:
             def get_tam_link(row):
                 if row.get('target_url'): return row['target_url']
                 kw = str(row.get('keyword', ''))
                 return kw if kw.startswith('http') else None
             display_df['Tam Link'] = display_df.apply(get_tam_link, axis=1)

        display_df['Ekran Görüntüsü'] = logs_df.apply(get_screenshot_status, axis=1)
        
        final_cols = ['ID', 'Durum', 'Platform', 'Tam Link', 'Hedef / Kelime', 'Başlangıç', 'Bitiş', 'Sayfa', 'Bulunan', 'Ekran Görüntüsü', 'Hata']
        available_cols = [c for c in final_cols if c in display_df.columns]
        
        st.dataframe(
            display_df[available_cols],
            use_container_width=True,
            height=600,
            column_config={
                "ID": st.column_config.NumberColumn(format="%d"),
                "Tam Link": st.column_config.LinkColumn("Hedef Linki Görüntüle", validate="^https://.*", max_chars=30),
                "Hata": st.column_config.ProgressColumn("Hata Sayısı", format="%d", min_value=0, max_value=max(int(display_df['Hata'].max()) if not display_df.empty else 10, 10)),
                "Ekran Görüntüsü": st.column_config.LinkColumn("Ekran Görüntüsü", display_text="📸 Görüntüle"),
            }
        )
        
        if show_errors and 'error_details' in logs_df.columns:
            error_logs = logs_df[logs_df['error_details'].notnull()]
            if not error_logs.empty:
                st.markdown("### 🛠️ Hata Detayları")
                for index, row in error_logs.iterrows():
                    log_id = row.get('id', row.get('ID'))
                    details = str(row.get('error_details', ''))
                    raw_ss = row.get('screenshot_path')
                    ss_path = None
                    if raw_ss:
                        scrapper_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Scrapper")
                        potential_path = os.path.join(scrapper_root, "static", "captures", raw_ss.replace('captures/', '').replace('static/', ''))
                        if os.path.exists(potential_path): ss_path = potential_path
                    
                    with st.expander(f"🔴 Hata #{log_id} - {details[:50]}..."):
                        st.code(details, language='text')
                        if ss_path: st.image(ss_path, caption=f"Hata Anı (#{log_id})")
    else:
        st.warning("Bu kriterlere veya filtreye uygun kayıt bulunamadı.")
