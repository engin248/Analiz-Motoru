
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import text
from datetime import datetime, timedelta
import sys
import os
import time

# --- DB CONNECTION ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
backend_path = os.path.join(parent_dir, 'LangChain_backend')
sys.path.append(backend_path)

from app.core.database import SessionLocal

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Analiz Motoru - Yönetim Paneli",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS STYLING ---
st.markdown("""
<style>
    /* GENEL SAYFA */
    [data-testid="stAppViewContainer"] {
        background-color: #0E1117;
    }
    
    /* MERTİK KUTULARI (KARTLAR) */
    div[data-testid="stMetric"] {
        background-color: #262730;
        padding: 15px 10px;
        border-radius: 10px;
        border: 1px solid #41444C;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
        min-height: 140px; /* Sabit Yükseklik */
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center; /* İçerik Yatayda Ortala */
    }
    
    div[data-testid="stMetricLabel"] {
        color: #B2B5BE !important;
        font-size: 14px !important;
        font-weight: 500;
        margin-bottom: 5px;
        text-align: center !important; /* Zorla Ortala */
        width: 100%;
    }
    
    div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 28px !important;
        font-weight: 700;
        font-family: 'Inter', sans-serif;
        text-align: center !important; /* Zorla Ortala */
        width: 100%;
    }
    
    /* Delta (Değişim) Yazısı */
    div[data-testid="stMetricDelta"] {
        justify-content: center !important; /* Oku Ortala */
    }
    
    /* TABLO STİLİ */
    [data-testid="stDataFrame"] {
        border: 1px solid #41444C;
        border-radius: 8px;
    }
    
    /* BAŞLIKLAR */
    h1, h2, h3 {
        color: #FAFAFA !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: #262730;
    }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def get_db_connection():
    return SessionLocal()

@st.cache_data(ttl=5)  # 5 saniyede bir veriyi yenile
def fetch_stats():
    db = get_db_connection()
    try:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 1. Ana Metrikler
        total_links = db.execute(text("SELECT COUNT(*) FROM products")).scalar()
        
        # Kaç tanesinin detay verisi var? (Tüm zamanlar)
        total_scraped_all_time = db.execute(text("SELECT COUNT(DISTINCT product_id) FROM daily_metrics WHERE discounted_price > 0")).scalar()
        
        today_scraped = db.execute(text("SELECT COUNT(DISTINCT product_id) FROM daily_metrics WHERE recorded_at >= :t"), {"t": today_start}).scalar()
        error_count = db.execute(text("SELECT COUNT(*) FROM system_logs WHERE level = 'ERROR' AND timestamp >= :t"), {"t": today_start}).scalar()
        
        # Hız Hesaplama (Son 15 dk)
        time_threshold = datetime.utcnow() - timedelta(minutes=15)
        recent_count = db.execute(text("SELECT COUNT(DISTINCT product_id) FROM daily_metrics WHERE recorded_at >= :t"), {"t": time_threshold}).scalar()
        speed_per_min = round(recent_count / 15, 1) if recent_count else 0
        speed_per_hour = int(speed_per_min * 60)
        
        # 2. Son Loglar
        logs = pd.read_sql(text("SELECT * FROM system_logs ORDER BY id DESC LIMIT 20"), db.connection())
        
        return {
            "total_links": total_links,
            "total_scraped": total_scraped_all_time,
            "today": today_scraped,
            "speed_min": speed_per_min,
            "speed_hour": speed_per_hour,
            "errors": error_count,
            "logs": logs
        }
    finally:
        db.close()

@st.cache_data(ttl=60)
def fetch_price_data():
    db = get_db_connection()
    try:
        data = pd.read_sql(text("SELECT product_id, discounted_price, avg_rating FROM daily_metrics WHERE discounted_price > 0 LIMIT 1000"), db.connection())
        return data
    finally:
        db.close()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2593/2593491.png", width=80)
    st.title("Admin Panel v1.0")
    st.write("---")
    
    page = st.radio("Menü", ["🏠 Genel Bakış", "📜 Sistem Logları", "💰 Fiyat Analizi", "⚙️ Bot Kontrol"])
    
    st.write("---")
    if st.button("🔄 Verileri Yenile"):
        st.cache_data.clear()
        st.experimental_rerun()

# --- MAIN CONTENT ---
stats = fetch_stats()

if page == "🏠 Genel Bakış":
    st.header("🚀 Operasyon Özeti")
    
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
        # Renkli Log Gösterimi
        def color_log(val):
            color = 'red' if val == 'ERROR' else 'green'
            return f'color: {color}'
            
        st.dataframe(
            stats['logs'][['timestamp', 'bot_name', 'level', 'message']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Henüz log kaydı yok.")

elif page == "💰 Fiyat Analizi":
    st.header("📈 Fiyat Dağılımı")
    df = fetch_price_data()
    
    if not df.empty:
        fig = px.histogram(df, x="discounted_price", nbins=50, title="Fiyat Yoğunluk Grafiği", color_discrete_sequence=['#00CC96'])
        st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
             st.subheader("En Pahalı 5 Ürün")
             st.dataframe(df.nlargest(5, 'discounted_price'))
        with col2:
             st.subheader("En Yüksek Puanlılar")
             st.dataframe(df.nlargest(5, 'avg_rating'))
    else:
        st.warning("Yeterli veri yok.")

elif page == "📜 Sistem Logları":
    st.header("🔍 Detaylı Log İnceleme")
    st.dataframe(stats['logs'], use_container_width=True, height=600)

elif page == "⚙️ Bot Kontrol":
    st.header("🤖 Bot Yönetimi")
    st.warning("Bu özellik VPS kurulumundan sonra aktif olacaktır.")
    st.button("Botu Başlat (Devre Dışı)", disabled=True)
    st.button("Botu Durdur (Devre Dışı)", disabled=True)

# Otomatik Yenileme (Auto-Refresh)
time.sleep(1)
# st.experimental_rerun() # Aşırı CPU yememesi için kapalı, manuel yenileme önerilir.
