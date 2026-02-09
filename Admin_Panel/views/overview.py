
import streamlit as st
import pandas as pd
from Admin_Panel.core.engine import fetch_stats

def render_overview():
    stats = fetch_stats()
    
    # KASA KUTULARI (TEK IZGARA - GRID SYSTEM)
    col1, col2, col3, col4 = st.columns(4)
    
    # Satır 1
    with col1:
        st.metric(label="📦 Toplam Link", value=f"{stats['total_links']:,}")
    with col2:
         st.metric(label="✅ Kazınmış (Detaylı)", value=f"{stats['total_scraped']:,}", delta="Aktif")
    with col3:
        st.metric(label="📅 Bugün İşlenen", value=f"{stats['today']}", delta=f"+{stats['today']}")
    with col4:
        pending = stats['total_links'] - stats['total_scraped']
        st.metric(label="⏳ Bekleyen İş", value=f"{pending:,}", delta_color="off")
        
    # Satır 2
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric(label="❌ Hata (Bugün)", value=f"{stats['errors']}", delta_color="inverse")
    with col6:
        st.metric(label="🚀 Anlık Hız", value=f"{stats['speed_min']} /dk", delta="Son 15dk")
    with col7:
        st.metric(label="⏱️ Tahmini Hız", value=f"~{stats['speed_hour']} /saat")
    with col8:
        # Boş kutu yerine sistem durumu
        status = "🟢 Normal" if stats['errors'] == 0 else "🔴 Sorun Var"
        st.metric(label="Sistem Durumu", value=status)

    if stats['speed_min'] < 5 and stats['today'] > 0:
        st.warning("⚠️ Bot yavaş ilerliyor! (Dakikada 5'in altında). Proxy veya İnternet kontrol edilebilir.")
        
    st.write("---")
    
    # SON LOGLAR (KÜÇÜK)
    st.subheader("📜 Son Aktiviteler (Canlı)")
    if not stats['logs'].empty:
        st.dataframe(
            stats['logs'][['started_at', 'platform', 'status', 'keyword']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Henüz log kaydı yok.")
