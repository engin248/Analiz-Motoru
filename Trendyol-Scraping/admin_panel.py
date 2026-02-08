
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
        st.rerun()

import subprocess
import signal
import psutil

# --- BOT YÖNETİM FONKSİYONLARI ---
PID_FILE = "bot_pid.txt"
TOTAL_TIME_FILE = "bot_cumulative_seconds.txt"

def load_total_time():
    """Kayıtlı toplam çalışma süresini saniye olarak döner."""
    if os.path.exists(TOTAL_TIME_FILE):
        try:
            with open(TOTAL_TIME_FILE, "r") as f:
                return int(f.read().strip() or 0)
        except: return 0
    return 0

def save_total_time(seconds):
    """Toplam çalışma süresini dosyaya kaydeder."""
    old_total = load_total_time()
    with open(TOTAL_TIME_FILE, "w") as f:
        f.write(str(old_total + seconds))

def start_bot():
    """Botu arka planda başlatır ve PID'sini kaydeder."""
    pid_path = os.path.abspath(PID_FILE)
    
    # 1. PID Dosyası Kontrolü (ZOMBİ TEMİZLİĞİ)
    if os.path.exists(pid_path):
        try:
            with open(pid_path, "r") as f:
                content = f.read().strip()
                if content:
                    old_pid = int(content)
                    if psutil.pid_exists(old_pid):
                        return False, f"Bot zaten çalışıyor (PID: {old_pid})"
                    else:
                        # Process ölmüş ama dosya kalmış -> Sil
                        os.remove(pid_path)
                else:
                    os.remove(pid_path)
        except:
             if os.path.exists(pid_path): os.remove(pid_path)

    try:
        # Doğru Konumlandırma: admin_panel.py dosyasının olduğu klasör
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        script_path = os.path.join(current_dir, "scrape_ultra_final_v7.py")
        log_path = os.path.join(current_dir, "bot_output.log")
        
        if not os.path.exists(script_path):
             return False, f"Dosya Bulunamadı: {script_path}"

        # 2. Log Dosyası Hazırlığı
        # Dosya yoksa oluştur, varsa ekle
        mode = "a" if os.path.exists(log_path) else "w"
        
        # 3. Botu Başlat (UTF-8 Zorlaması ile)
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        
        with open(log_path, mode, encoding="utf-8") as out:
            process = subprocess.Popen(
                [sys.executable, script_path],
                cwd=os.path.dirname(script_path),
                stdout=out,
                stderr=out,
                env=env,
                creationflags=subprocess.CREATE_NEW_CONSOLE # Windows Konsolu (Görünür)
            )
            
        # 4. PID Kaydet
        with open(pid_path, "w") as f:
            f.write(str(process.pid))
            
        return True, "Başarılı"
        
    except Exception as e:
        return False, str(e)

def stop_bot():
    """Çalışan botu durdurur."""
    pid_path = os.path.abspath(PID_FILE)
    if not os.path.exists(pid_path):
        return False
        
    try:
        with open(pid_path, "r") as f:
            pid = int(f.read())
        
        # DURDURMADAN ÖNCE: Çalışma süresini kümülatif toplama ekle
        if psutil.pid_exists(pid):
            p = psutil.Process(pid)
            session_seconds = int(time.time() - p.create_time())
            save_total_time(session_seconds)

        parent = psutil.Process(pid)
        for child in parent.children(recursive=True):
            child.terminate()
        parent.terminate()
        
    except (psutil.NoSuchProcess, ValueError, FileNotFoundError):
        pass 
    finally:
        if os.path.exists(pid_path):
            os.remove(pid_path)
    return True

def get_bot_status():
    """Bot çalışıyor mu kontrol eder ve ölü PID'leri temizler."""
    pid_path = os.path.abspath(PID_FILE)
    
    if not os.path.exists(pid_path):
        return "stopped"
        
    try:
        with open(pid_path, "r") as f:
            content = f.read().strip()
            
        if not content:
            os.remove(pid_path)
            return "stopped"
            
        pid = int(content)
        if psutil.pid_exists(pid):
            return "running"
        else:
            # Process ölmüş -> Temizle
            os.remove(pid_path)
            return "stopped"
    except Exception:
        if os.path.exists(pid_path):
            os.remove(pid_path)
        return "stopped"

def get_bot_runtime():
    """Toplam kümülatif süreyi + (varsa) mevcut seansı döner."""
    saved_seconds = load_total_time()
    current_session = 0
    
    pid_path = os.path.abspath(PID_FILE)
    if os.path.exists(pid_path):
        try:
            with open(pid_path, "r") as f:
                content = f.read().strip()
                if content:
                    pid = int(content)
                    if psutil.pid_exists(pid):
                        p = psutil.Process(pid)
                        current_session = int(time.time() - p.create_time())
        except: pass
    
    total_sec = saved_seconds + current_session
    if total_sec == 0: return "---"
    
    hrs, rem = divmod(total_sec, 3600)
    mins, secs = divmod(rem, 60)
    
    if hrs > 0: return f"{hrs}sa {mins}dk"
    return f"{mins}dk {secs}sn"

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
    st.header("🏭 Bot Filosu Yönetimi (Fleet Command)")
    
    # GLOBAL KONTROLLER
    col1, col2 = st.columns([5, 1.5])
    with col1:
        st.info("💡 Bot-01 şu an gerçek `scrape_ultra_final_v7.py` dosyasına bağlıdır.")
    with col2:
        if st.button("🚨 ACİL DURDURMA (TÜMÜ)", type="primary", use_container_width=True):
            stop_bot()
            st.error("Durdurma Sinyali Gönderildi!")
            time.sleep(1)
            st.rerun()
            
    st.write("---")
    
    b01_status = get_bot_status()
    b01_runtime = get_bot_runtime()
    
    bots = [
        {"id": 1, "name": "Kazıyıcı-Bot-01 (ANA)", "status": b01_status, "total": stats['total_scraped'], "speed": stats['speed_min'], "proxies": 12, "uptime": b01_runtime},
        {"id": 2, "name": "Kazıyıcı-Bot-02", "status": "stopped", "total": 0, "speed": 0.0, "proxies": 0, "uptime": "---"},
        {"id": 3, "name": "Kazıyıcı-Bot-03", "status": "error", "total": 310, "speed": 0.0, "proxies": 4, "uptime": "1s 14dk"},
        {"id": 4, "name": "Kazıyıcı-Bot-04", "status": "running", "total": 1205, "speed": 1.2, "proxies": 18, "uptime": "5s 12dk"}
    ]

    # --- YENİ NESİL CSS (PREMIUM DASHBOARD) ---
    st.markdown("""
    <style>
        .bot-container {
            background: linear-gradient(135deg, #1e1e24 0%, #121217 100%);
            border-radius: 15px;
            padding: 18px;
            margin-bottom: 5px;
            border: 1px solid #333;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        .status-running { border-left: 5px solid #2ecc71; }
        .status-error { border-left: 5px solid #e74c3c; }
        .status-stopped { border-left: 5px solid #7f8c8d; }

        /* Metrik Kutuları */
        .metrics-wrapper {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
            margin-top: 15px;
        }
        .m-box {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 8px;
            padding: 8px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.05);
        }
        .m-title { font-size: 11px; color: #bbb; text-transform: uppercase; margin-bottom: 3px; }
        .m-value { font-size: 15px; font-weight: 700; color: #fff; }
        
        .b-header { display: flex; justify-content: space-between; align-items: center; }
        .b-name { font-size: 17px; font-weight: 700; color: #eee; }
        .b-badge { font-size: 10px; padding: 2px 8px; border-radius: 10px; font-weight: bold; }
        .badge-running { background: rgba(46, 204, 113, 0.2); color: #2ecc71; border: 1px solid #2ecc71; }
        .badge-stopped { background: rgba(127, 140, 141, 0.2); color: #7f8c8d; border: 1px solid #7f8c8d; }
    </style>
    """, unsafe_allow_html=True)

    # Botları 2 sütunlu yapıda göster
    main_cols = st.columns(2)
    
    for i, bot in enumerate(bots):
        status_css = "status-running" if bot['status'] == 'running' else "status-error" if bot['status'] == 'error' else "status-stopped"
        badge_css = "badge-running" if bot['status'] == 'running' else "badge-stopped"
        status_text = "Online" if bot['status'] == 'running' else "Offline"
        icon = "⚡" if bot['status'] == 'running' else "💤"
        
        with main_cols[i % 2]:
            st.markdown(f"""
            <div class="bot-container {status_css}">
                <div class="b-header">
                    <div class="b-name">{icon} {bot['name']}</div>
                    <div class="b-badge {badge_css}">{status_text}</div>
                </div>
                <div class="metrics-wrapper">
                    <div class="m-box"><div class="m-title">Operasyon Süresi</div><div class="m-value">{bot['uptime']}</div></div>
                    <div class="m-box"><div class="m-title">Aktif Proxy</div><div class="m-value">{bot['proxies']}</div></div>
                    <div class="m-box"><div class="m-title">Toplam Veri</div><div class="m-value">{bot['total']}</div></div>
                    <div class="m-box">
                        <div class="m-title">Hız (Tempo)</div>
                        <div class="m-value">{bot['speed']} <span style="font-size:9px">Ürün/dk</span></div>
                        <div style="font-size:9px; color:{'#2ecc71' if bot['speed'] > 2 else '#f1c40f' if bot['speed'] > 0 else '#95a5a6'}">
                            {'🚀 TURBO' if bot['speed'] > 8 else '🟢 STABİL' if bot['speed'] > 2 else '🟡 DÜŞÜK' if bot['speed'] > 0 else '⚪ BEKLEMEDE'}
                        </div>
                    </div>
                    <!-- YENİ: VERİMLİLİK PUANI -->
                    <div class="m-box" style="grid-column: span 2; background: rgba(46, 204, 113, 0.05); border: 1px solid rgba(46, 204, 113, 0.2);">
                        <div class="m-title">Verimlilik Skoru</div>
                        <div class="m-value" style="color:#2ecc71">
                            {round(min(5.0, bot['speed'] * 0.5), 1)} <span style="font-size:10px; color:#888;">/ 5.0</span>
                        </div>
                        <div style="font-size:12px; letter-spacing: 2px;">
                            {'⭐' * int(min(5, max(1, bot['speed'] * 0.5))) if bot['speed'] > 0 else '😶'}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Butonlar
            c1, c2 = st.columns([1, 1.2])
            if bot['id'] == 1:
                with c1:
                    if bot['status'] == 'running':
                        if st.button("DURDUR", key=f"stop_{bot['id']}", use_container_width=True):
                            stop_bot(); st.rerun()
                    else:
                        if st.button("BAŞLAT", key=f"start_{bot['id']}", type="primary", use_container_width=True):
                            status, msg = start_bot()
                            if status: st.rerun()
                            else: st.error(msg)
                with c2:
                    with st.expander("🔍 CANLI TERMİNAL (DETAY)"):
                        st.caption("Botun o anki teknik adımlarını ve proxy durumlarını gösterir.")
                        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_output.log")
                        if os.path.exists(log_path):
                            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                                st.code("".join(f.readlines()[-30:]), language="text")
                        else:
                            st.info("Bot henüz bir teknik kayıt üretmedi.")
            else:
                with c1: st.button("BAŞLAT", key=f"d_s_{bot['id']}", disabled=True, use_container_width=True)
                with c2: st.button("LOGLAR", key=f"d_l_{bot['id']}", disabled=True, use_container_width=True)
            
            st.write("---")

# --- FOOTER ---
st.write("Analiz Motoru v1.0 | 2026")
# --- FOOTER ---
st.write("---")
