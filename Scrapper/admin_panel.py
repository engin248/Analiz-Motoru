
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import text, inspect
from datetime import datetime, timedelta
import sys
import os
import time

# --- DB CONNECTION ---
from src.database import DatabaseManager, Product, DailyMetric, ScrapingLog, ScrapingTask
from src.config import load_config

def check_and_migrate_db():
    """Veritabanı şemasını kontrol eder ve eksik kolonları ekler."""
    try:
        # Config yükle
        config = load_config()
        # Varsayılan olarak ilk platformun DB'sini kullan (Hepsi aynı DB ise)
        # Genelde SQLite tek dosya. Trendyol configi alalım.
        if 'trendyol' in config.platforms:
            db_url = config.platforms['trendyol'].database.connection_url
        else:
            # Fallback
            db_url = "sqlite:///scrapper.db"
            
        # Geçici DB Manager
        temp_manager = DatabaseManager(connection_url=db_url)
        session = temp_manager.get_session()
        
        try:
            # SQLAlchemy connection üzerinden raw SQL çalıştır
            with session.connection() as conn:
                # Sütunları kontrol et (inspect)
                insp = inspect(temp_manager.engine)
                # Tablo var mı?
                if insp.has_table('scraping_logs'):
                    columns = [c['name'] for c in insp.get_columns('scraping_logs')]
                    
                    if 'target_url' not in columns:
                        conn.execute(text("ALTER TABLE scraping_logs ADD COLUMN target_url TEXT"))
                        session.commit()
                    
                    if 'screenshot_path' not in columns:
                        conn.execute(text("ALTER TABLE scraping_logs ADD COLUMN screenshot_path TEXT"))
                        session.commit()
        finally:
            session.close()
    except Exception:
        pass

# Başlangıçta migration çalıştır
check_and_migrate_db()

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
def get_db_session():
    config = load_config()
    platform_config = config.platforms.get('trendyol')
    if not platform_config:
        raise Exception("Trendyol config not found")
    
    db_manager = DatabaseManager(connection_url=platform_config.database.connection_url)
    db_manager.create_tables() # Eksik tabloları oluştur
    return db_manager.get_session(), db_manager

@st.cache_data(ttl=5)
def fetch_task_stats(task_id):
    """Belirli bir bot görevine ait verileri çeker."""
    session, db_manager = get_db_session()
    try:
        # Son logları al (Bu görev için)
        task_logs = session.execute(
            text("SELECT SUM(products_added + products_updated) as total, SUM(errors) as err FROM scraping_logs WHERE task_id = :tid"), 
            {"tid": task_id}
        ).fetchone()
        
        total_scraped = task_logs[0] if task_logs and task_logs[0] else 0
        total_errors = task_logs[1] if task_logs and task_logs[1] else 0
        
        # PROJEKSİYON HIZ HESABI (Anlık saatlik hız)
        # En son başlayan logu alıp, o anki verimliliğini saate vuralım
        last_log = session.execute(
            text("SELECT started_at, products_added, products_updated FROM scraping_logs WHERE task_id = :tid ORDER BY id DESC LIMIT 1"),
            {"tid": task_id}
        ).fetchone()
        
        speed_hour = 0
        if last_log and last_log[1] + last_log[2] > 0:
            start_at, added, updated = last_log
            elapsed_sec = (datetime.utcnow() - start_at).total_seconds()
            if elapsed_sec > 5: # En az 5 saniye geçsin ki matematik gerçekçi olsun
                speed_hour = int(((added + updated) / elapsed_sec) * 3600)
        
        return {
            "total_scraped": total_scraped,
            "speed_hour": speed_hour,
            "errors": total_errors,
            "ip_changes": total_scraped // 45 # Tahmini bir rakam (her 45 üründe bir IP değiştiğini varsayalım)
        }
    finally:
        session.close()
        db_manager.close()

def extract_keyword_from_url(url):
    """URL içindeki q= parametresini okuyup temiz kelimeyi döner."""
    try:
        if not url: return ""
        if "q=" not in url: return ""
        
        # En sağlam yöntem: q= dan sonrasını al ve unquote et
        import urllib.parse
        raw_kw = url.split("q=")[-1].split("&")[0]
        # Önce unquote et, sonra varsa + işaretlerini boşluk yap
        decoded_kw = urllib.parse.unquote(raw_kw).replace('+', ' ')
        return decoded_kw.strip()
    except:
        return ""

@st.cache_data(ttl=5)  # 5 saniyede bir veriyi yenile
def fetch_stats():
    session, db_manager = get_db_session()
    try:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 1. Ana Metrikler
        total_links = session.execute(text("SELECT COUNT(*) FROM products")).scalar()
        
        # Kaç tanesinin detay verisi var? (Tüm zamanlar)
        total_scraped_all_time = session.execute(text("SELECT COUNT(DISTINCT product_id) FROM daily_metrics WHERE discounted_price > 0")).scalar()
        
        today_scraped = session.execute(text("SELECT COUNT(DISTINCT product_id) FROM daily_metrics WHERE recorded_at >= :t"), {"t": today_start}).scalar()
        error_count = session.execute(text("SELECT COUNT(*) FROM scraping_logs WHERE status = 'error' AND started_at >= :t"), {"t": today_start}).scalar()
        
        # Hız Hesaplama (Son 15 dk)
        time_threshold = datetime.utcnow() - timedelta(minutes=15)
        recent_count = session.execute(text("SELECT COUNT(DISTINCT product_id) FROM daily_metrics WHERE recorded_at >= :t"), {"t": time_threshold}).scalar()
        speed_per_min = round(recent_count / 15, 1) if recent_count else 0
        speed_per_hour = int(speed_per_min * 60)
        
        # 2. Son Loglar
        logs = pd.read_sql(text("SELECT * FROM scraping_logs ORDER BY id DESC LIMIT 20"), session.connection())
        
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
        session.close()
        db_manager.close()

def fetch_detailed_logs(limit=100, show_errors_only=False):
    """Sistem logları sayfası için detaylı veri çeker."""
    session, db_manager = get_db_session()
    try:
        query = "SELECT * FROM scraping_logs"
        params = {}
        if show_errors_only:
             # Basitçe status error olan veya errors kolonu > 0 olanlar
             query += " WHERE status = 'error' OR errors > 0"
        
        query += " ORDER BY id DESC LIMIT :limit"
        params["limit"] = limit
        
        return pd.read_sql(text(query), session.connection(), params=params)
    finally:
        session.close()
        db_manager.close()

def fetch_tasks():
    session, db_manager = get_db_session()
    try:
        tasks = session.query(ScrapingTask).order_by(ScrapingTask.id.asc()).all()
        return tasks
    finally:
        session.close()
        db_manager.close()

def add_task(name, platform, url, interval):
    session, db_manager = get_db_session()
    try:
        new_task = ScrapingTask(
            task_name=name,
            target_platform=platform,
            target_url=url,
            scrape_interval_hours=interval,
            is_active=True
        )
        session.add(new_task)
        session.commit()
        return True, "Görev başarıyla eklendi."
    except Exception as e:
        session.rollback()
        return False, str(e)
    finally:
        session.close()
        db_manager.close()

def delete_task(task_id):
    session, db_manager = get_db_session()
    try:
        task = session.query(ScrapingTask).filter(ScrapingTask.id == task_id).first()
        if task:
            session.delete(task)
            session.commit()
            return True
        return False
    finally:
        session.close()
        db_manager.close()

def update_task_name(task_id, new_name):
    session, db_manager = get_db_session()
    try:
        task = session.query(ScrapingTask).filter(ScrapingTask.id == task_id).first()
        if task:
            task.task_name = new_name
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        return False
    finally:
        session.close()
        db_manager.close()

def update_task_url(task_id, new_url):
    session, db_manager = get_db_session()
    try:
        task = session.query(ScrapingTask).filter(ScrapingTask.id == task_id).first()
        if task:
            task.target_url = new_url
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        return False
    finally:
        session.close()
        db_manager.close()

def update_task_interval(task_id, interval):
    session, db_manager = get_db_session()
    try:
        task = session.query(ScrapingTask).filter(ScrapingTask.id == task_id).first()
        if task:
            task.scrape_interval_hours = interval
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        return False
    finally:
        session.close()
        db_manager.close()

def update_task_shift(task_id, start_time, end_time):
    session, db_manager = get_db_session()
    try:
        task = session.query(ScrapingTask).filter(ScrapingTask.id == task_id).first()
        if task:
            task.start_time = start_time
            task.end_time = end_time
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        return False
    finally:
        session.close()
        db_manager.close()

def update_task_active_status(task_id, is_active):
    session, db_manager = get_db_session()
    try:
        task = session.query(ScrapingTask).filter(ScrapingTask.id == task_id).first()
        if task:
            task.is_active = is_active
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        return False
    finally:
        session.close()
        db_manager.close()

def seed_default_tasks():
    """Veritabanı boşsa varsayılan görevleri ekler."""
    session, db_manager = get_db_session()
    try:
        count = session.query(ScrapingTask).count()
        if count == 0:
            default_tasks = [
                ScrapingTask(task_name="Trendyol - Elbise (Ana)", target_platform="trendyol", target_url="https://www.trendyol.com/elbise-x-c56", scrape_interval_hours=12, is_active=True),
                ScrapingTask(task_name="Trendyol - Ayakkabı", target_platform="trendyol", target_url="https://www.trendyol.com/ayakkabi-x-c114", scrape_interval_hours=24, is_active=False),
                ScrapingTask(task_name="Amazon - Elektronik", target_platform="amazon", target_url="https://www.amazon.com.tr/b?node=12466532031", scrape_interval_hours=6, is_active=False)
            ]
            session.add_all(default_tasks)
            session.commit()
    except Exception as e:
        pass
    finally:
        session.close()
        db_manager.close()


@st.cache_data(ttl=60)
def fetch_price_data():
    session, db_manager = get_db_session()
    try:
        data = pd.read_sql(text("SELECT product_id, discounted_price, avg_rating FROM daily_metrics WHERE discounted_price > 0 LIMIT 1000"), session.connection())
        return data
    finally:
        session.close()
        db_manager.close()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2593/2593491.png", width=80)
    st.title("Analiz Motoru - Yönetim Paneli")
    st.write("---")
    
    # Sayfa Geçmişini (F5) Korumak İçin Query Params Kullanalım
    menu_options = ["🏠 Genel Bakış", "📜 Sistem Logları", "💰 Fiyat Analizi", "⚙️ Bot Kontrol"]
    
    # Mevcut sayfayı URL'den oku
    query_params = st.query_params
    saved_page = query_params.get("p", menu_options[0])
    
    default_index = 0
    if saved_page in menu_options:
        default_index = menu_options.index(saved_page)
    
    page = st.radio("Menü", menu_options, index=default_index)
    
    # Sayfayı URL'ye Kaydet (Sessizce)
    if query_params.get("p") != page:
        st.query_params["p"] = page
    
    st.write("---")
    if st.button("🔄 Verileri Yenile"):
        st.cache_data.clear()
        st.rerun()

import subprocess
import signal
import psutil
import threading
from datetime import datetime

# --- BEKÇİ SİNGLETON (TEKİL SİSTEM) ---
@st.cache_resource
def start_permanent_scheduler():
    """Arkaplanda çalışan tek bir bekçi başlatır. Sayfa yenilense de bu thread yaşar."""
    def scheduler_loop():
        # Bu fonksiyon sadece bir kez, sunucu yaşadığı sürece çalışır.
        while True:
            try:
                # Her döngüde veritabanından taze veriyi çek
                tasks = fetch_tasks() 
                now_str = datetime.now().strftime("%H:%M")
                
                for task in tasks:
                    status = get_bot_status(task.id)
                    start = task.start_time or "09:00"
                    end = task.end_time or "18:00"
                    
                    # Vardiya aktif mi?
                    is_shift_active = False
                    if start < end:
                        is_shift_active = start <= now_str <= end
                    else: 
                        is_shift_active = now_str >= start or now_str <= end
                    
                    # KRİTİK: Sadece kullanıcı 'Aktif' (is_active=True) bıraktıysa başlat.
                    if is_shift_active:
                        if task.is_active and status == "stopped":
                            start_bot(task.id, task.target_url)
                    else:
                        # Mesai bittiğinde sadece çalışan botu sessizce kapat
                        if status == "running":
                            stop_bot(task.id)
            except Exception:
                pass
            time.sleep(30) # Her 30 saniyede bir kontrol et

    # Thread başlat
    try: check_and_migrate_db() # Migration kontrolü
    except: pass
    
    thread = threading.Thread(target=scheduler_loop, daemon=True)
    thread.start()
    return True

# Sistemi uyandır (Sadece bir kez!)
start_permanent_scheduler()

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

def start_bot(task_id, target_url):
    """Botu belirli bir görev için arka planda başlatır."""
    pid_file = f"bot_{task_id}.pid"
    pid_path = os.path.abspath(pid_file)
    
    # 1. Kontrol
    current_status = get_bot_status(task_id)
    if current_status == "running":
        return False, "Bu bot zaten çalışıyor."

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(current_dir, "main.py")
        log_path = os.path.join(current_dir, f"bot_{task_id}.log")
        
        # 2. Çalıştır
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        
        # Eğer log dosyası varsa append yap
        mode = "a" if os.path.exists(log_path) else "w"
        with open(log_path, mode, encoding="utf-8") as out:
            process = subprocess.Popen(
                [sys.executable, script_path, "--task-id", str(task_id), "--url", target_url],
                cwd=current_dir,
                stdout=out,
                stderr=out,
                env=env
                # creationflags=subprocess.CREATE_NEW_CONSOLE -> Arka planda çalışması için kaldırdık
            )
            
        # 3. PID Kaydet
        with open(pid_path, "w") as f:
            f.write(str(process.pid))
            
        return True, "Başarılı"
    except Exception as e:
        return False, str(e)

def stop_bot(task_id):
    """Belirli bir botu durdurur."""
    pid_file = f"bot_{task_id}.pid"
    pid_path = os.path.abspath(pid_file)
    
    if not os.path.exists(pid_path):
        return False, "PID dosyası bulunamadı."
        
    try:
        with open(pid_path, "r") as f:
            pid = int(f.read().strip())
            
        if psutil.pid_exists(pid):
            parent = psutil.Process(pid)
            # Alt süreçleri de bul (Playwright vs)
            for child in parent.children(recursive=True):
                child.terminate()
            parent.terminate()
            
        if os.path.exists(pid_path): os.remove(pid_path)
        return True, "Bot durduruldu."
    except Exception as e:
        return False, str(e)

def get_bot_status(task_id):
    """Belirli bir bot görevini PID dosyası üzerinden kontrol eder."""
    pid_file = f"bot_{task_id}.pid"
    pid_path = os.path.abspath(pid_file)
    
    if not os.path.exists(pid_path):
        return "stopped"
        
    try:
        with open(pid_path, "r") as f:
            content = f.read().strip()
            
        if not content:
            if os.path.exists(pid_path): os.remove(pid_path)
            return "stopped"
            
        pid = int(content)
        if psutil.pid_exists(pid):
            # Ek kontrol: Bizim başlattığımız python mu?
            p = psutil.Process(pid)
            if "python" in p.name().lower():
                return "running"
        
        # Process ölmüşsa temizle
        if os.path.exists(pid_path): os.remove(pid_path)
        return "stopped"
    except Exception:
        if os.path.exists(pid_path): os.remove(pid_path)
        return "stopped"


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
            stats['logs'][['started_at', 'platform', 'status', 'keyword']],
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
    # --- FİLTRELER ---
    # URL'den filtre parametresini kontrol et
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
        # Veritabanı UTC ise Türkiye saati için +3 ekliyoruz
        if pd.api.types.is_datetime64_any_dtype(logs_df['started_at']):
            logs_df['started_at'] = pd.to_datetime(logs_df['started_at']) + pd.Timedelta(hours=3)
        if pd.api.types.is_datetime64_any_dtype(logs_df['finished_at']):
            logs_df['finished_at'] = pd.to_datetime(logs_df['finished_at']) + pd.Timedelta(hours=3)
        
        if 'screenshot_path' not in logs_df.columns:
            logs_df['screenshot_path'] = None
        
        if 'target_url' not in logs_df.columns:
            logs_df['target_url'] = None

        
        # URL'den temiz kelime çıkarma (Görsel İçin)
        import urllib.parse
        def clean_keyword_display(val):
            val_str = str(val)
            if not val_str.startswith('http'): return val_str
            try:
                parsed = urllib.parse.urlparse(val_str)
                query = urllib.parse.parse_qs(parsed.query)
                if 'q' in query: return query['q'][0].replace('+', ' ')
                if 'k' in query: return query['k'][0].replace('+', ' ')
                # Kategori
                path_parts = parsed.path.split('/')
                valid_parts = [p for p in path_parts if p]
                if valid_parts:
                    last_part = valid_parts[-1]
                    if '-x-c' in last_part: return last_part.split('-x-c')[0].replace('-', ' ')
                    return last_part.replace('-', ' ')
                return val_str
            except: return val_str

        # Orijinal 'keyword' kolonunu koruyalım (çünkü Tam Link için lazım olabilir)
        # Ama Hedef / Kelime olarak temiz halini gösterelim
        # Önce Tam Link'i oluştur
        if 'Tam Link' not in logs_df.columns:
             def get_tam_link(row):
                 if row.get('target_url'): return row['target_url']
                 kw = str(row.get('keyword', ''))
                 return kw if kw.startswith('http') else None
             
             logs_df['Tam Link'] = logs_df.apply(get_tam_link, axis=1)

        logs_df['Hedef / Kelime'] = logs_df['keyword'].apply(clean_keyword_display)
        
        logs_df['Başlangıç'] = logs_df['started_at'].dt.strftime('%d.%m.%Y %H:%M')
        # Bitiş tarihi NaT (Not a Time) ise '-' koy
        logs_df['Bitiş'] = logs_df['finished_at'].apply(lambda x: x.strftime('%d.%m.%Y %H:%M') if pd.notnull(x) else '-')
        
        # 2. DURUM ÇEVİRİSİ VE HATA KONTROLÜ
        # Eğer hata sayısı > 0 ise durumu 'Hata' olarak işaretle (Çalışıyor olsa bile)
        def get_status_label(row):
            status = row.get('status', '')
            errors = row.get('errors', 0)
            
            if errors and errors > 0:
                return '❌ Hata'
            
            status_map = {
                'completed': '✅ Tamamlandı',
                'running': '🔄 Çalışıyor',
                'error': '❌ Hata',
                'stopped': '⏹️ Durduruldu'
            }
            return status_map.get(status, status)

        logs_df['Durum'] = logs_df.apply(get_status_label, axis=1)

        # 3. EKRAN GÖRÜNTÜSÜ (URL FORMUNDA)
        # Kullanıcı isteği: Tıklanabilir link olsun.
        
        def get_screenshot_status(row):
            filename = row.get('screenshot_path')
            if not filename: return None
            
            # Eski veri 'captures/' ile başlıyorsa temizle
            clean_name = filename.replace('captures/', '').replace('static/', '')
            
            # Dosya var mı kontrol et
            real_path = os.path.join("static", "captures", clean_name)
            
            if os.path.exists(real_path):
                # Streamlit static path
                return f"app/static/captures/{clean_name}"
            return None

        logs_df['Ekran Görüntüsü'] = logs_df.apply(get_screenshot_status, axis=1)
        
        # 3. KOLON YÖNETİMİ
        display_df = logs_df.copy()
        
        # Kolon isimlerini Türkçeleştir
        display_df.rename(columns={
            'id': 'ID',
            'platform': 'Platform',
            'pages_scraped': 'Sayfa',
            'products_found': 'Bulunan',
            'products_added': 'Eklenen',
            'errors': 'Hata'
        }, inplace=True)
        
        # URL iyileştirmesi: target_url bazen boştur, keyword alanını kontrol edip oluşturabiliriz
        # Ancak scraping_logs tablosunda target_url olmayabilir, bu durumda keyword kolonundaki URL'yi kullan
        if 'Tam Link' not in display_df.columns and 'Hedef / Kelime' in display_df.columns:
             # Eğer keyword bir URL ise onu Tam Link yapalım
             display_df['Tam Link'] = display_df['Hedef / Kelime'].apply(lambda x: x if str(x).startswith('http') else None)
        
        # Sadece istediklerimizi alalım
        # 'Eklenen' yerine 'Sonuç' kolonunu kullanacağız
        # Sadece istediklerimizi alalım
        # 'Eklenen' yerine 'Sonuç' kolonunu kullanacağız
        final_cols = ['ID', 'Durum', 'Platform', 'Tam Link', 'Hedef / Kelime', 'Başlangıç', 'Bitiş', 'Sayfa', 'Bulunan', 'Ekran Görüntüsü', 'Hata']
        # Varsa al, yoksa geç (hata vermesin)
        available_cols = [c for c in final_cols if c in display_df.columns]
        
        st.dataframe(
            display_df[available_cols],
            use_container_width=True,
            height=600,
            column_config={
                "ID": st.column_config.NumberColumn(format="%d"),
                "Tam Link": st.column_config.LinkColumn(
                     "Hedef Linki Görüntüle", 
                     help="Botun gittiği tam adres",
                     validate="^https://.*",
                     max_chars=30
                ),
                "Hata": st.column_config.ProgressColumn(
                    "Hata Sayısı",
                    format="%d",
                    min_value=0,
                    max_value=max(int(display_df['Hata'].max()) if not display_df.empty else 10, 10),
                ),
                "Ekran Görüntüsü": st.column_config.LinkColumn(
                    "Ekran Görüntüsü", 
                    help="Tıkla ve hatayı gör", 
                    display_text="📸 Görüntüle"
                ),
            }
        )
        
        # Hata Detayları Gösterimi (Eğer Hata Varsa ve veride detay varsa)
        if show_errors:
            # error_details olmayabilir, logs_df'i tekrar kontrol edelim
            if 'error_details' in logs_df.columns:
                error_logs = logs_df[logs_df['error_details'].notnull()]
                if not error_logs.empty:
                    st.markdown("### 🛠️ Hata Detayları")
                    st.info("Aşağıdaki listeden hata detaylarını görebilirsiniz.")
                    for index, row in error_logs.iterrows():
                        # Sütun isimleri veritabanından küçük harf gelir (id, error_details)
                        log_id = row.get('id', row.get('ID'))
                        details = str(row.get('error_details', ''))
                        screenshot = row.get('screenshot_path')
                        
                        # Link bulma mantığı
                        link = row.get('target_url')
                        if not link and str(row.get('keyword', '')).startswith('http'):
                            link = row.get('keyword')
                            
                        # Screenshot path düzeltme
                        ss_path = None
                        raw_ss = row.get('screenshot_path')
                        if raw_ss:
                            clean_name = raw_ss.replace('captures/', '').replace('static/', '')
                            potential_path = os.path.join("static", "captures", clean_name)
                            if os.path.exists(potential_path):
                                ss_path = potential_path

                        err_title = f"{details[:50]}..." if details else "Detay Yok"
                        with st.expander(f"🔴 Hata #{log_id} - {err_title}"):
                            st.code(details, language='text')
                            cols = st.columns(2)
                            with cols[0]:
                                if link:
                                    st.markdown(f"**🔗 Hatalı Link:** [Tıkla Git]({link})")
                            with cols[1]:
                                if ss_path:
                                    st.image(ss_path, caption=f"Hata Anı (#{log_id})")
                                elif raw_ss:
                                    st.warning(f"Screenshot dosyası bulunamadı: {raw_ss}")
    else:
        st.warning("Bu kriterlere veya filtreye uygun kayıt bulunamadı.")

elif page == "⚙️ Bot Kontrol":
    st.header("🏭 Bot Filosu Yönetimi (Fleet Command)")
    
    # --- ÜST METRİK KUTULARI (YENİ) ---
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(label="🔗 Kazılan Link Sayısı", value=f"{stats['total_scraped']:,}")
    with m2:
        # Toplam hızı simüle ediyoruz (şuan sadece bot-01 aktif ama yapı hazır)
        st.metric(label="⚡ Bot Hız Sayısı (Toplam)", value=f"{stats['speed_min']} /dk")
    with m3:
        remaining = max(0, stats['total_links'] - stats['total_scraped'])
        st.metric(label="⏳ Kazılmayan Link Sayısı", value=f"{remaining:,}")
    with m4:
        # Sağlık hesabı: Hata oranına göre % belirleme
        health_per = max(0, 100 - (stats['errors'] * 5))
        health_status = "🟢 Mükemmel" if health_per > 95 else "🟡 Stabil" if health_per > 70 else "🔴 Kritik"
        st.metric(label="🩺 Bot Sağlığı (Toplam)", value=f"%{health_per}", delta=health_status)

    st.write("---")
    
    # GLOBAL KONTROLLER
    col1, col2 = st.columns([5, 1.5])
    with col1:
        st.info("💡 Bot yönetimi panelinden yeni botlar ekleyebilir ve durumlarını izleyebilirsiniz.")
    with col2:
        if st.button("🚨 ACİL DURDURMA (TÜMÜ)", type="primary", use_container_width=True):
            tasks_to_stop = fetch_tasks()
            for t in tasks_to_stop:
                stop_bot(t.id)
            st.error("Durdurma Sinyali Gönderildi!")
            time.sleep(1)
            st.rerun()

    # --- YENİ BOT EKLEME (FİLO GENİŞLETME) ---
    with st.expander("➕ Yeni Bot (Görev) Tanımla"):
        st.markdown("### 🤖 Yeni Bir Görev Oluştur")
        c1, c2 = st.columns(2)
        with c1:
            new_name = st.text_input("Bot İsmi", placeholder="Örn: Elbise Botu")
            new_platform = st.selectbox("Platform", ["trendyol", "amazon"])
            type_choice = st.radio("Tanımlama Türü", ["🔍 Anahtar Kelime", "🔗 Hedef URL"], horizontal=True)
            
        with c2:
            if type_choice == "🔍 Anahtar Kelime":
                keyword_input = st.text_input("Aranacak Kelime", placeholder="Örn: Kulaklık, Elbise...")
                target_value = keyword_input
            else:
                url_input = st.text_input("Hedef URL", placeholder="https://www.trendyol.com/...")
                target_value = url_input
                
            new_interval = st.number_input("Çalışma Aralığı (Saat)", min_value=1, value=24)
        
        if st.button("Botu Filoya Ekle", type="primary", use_container_width=True):
            if new_name and target_value:
                # Eğer anahtar kelime ise URL'ye dönüştür
                final_url = target_value
                if type_choice == "🔍 Anahtar Kelime" and new_platform == "trendyol":
                    import urllib.parse
                    safe_keyword = urllib.parse.quote(target_value)
                    final_url = f"https://www.trendyol.com/sr?q={safe_keyword}"
                
                succ, msg = add_task(new_name, new_platform, final_url, new_interval)
                if succ:
                    st.success(f"✅ {new_name} başarıyla filoya katıldı!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ Hata: {msg}")
            else:
                st.warning("⚠️ Lütfen bot ismini ve hedef değeri (URL veya Kelime) boş bırakmayın.")

    st.write("---")
    
    seed_default_tasks()
    tasks = fetch_tasks()
    
    # --- PREMIUM CSS ENHANCEMENTS ---
    st.markdown("""
    <style>
        /* Streamlit'in kenarlıklı konteynerini (st.container border=True) yakalayıp beyaza çeviriyoruz */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 2px solid #FFFFFF !important;
            border-radius: 24px !important;
            background-color: rgba(255, 255, 255, 0.03) !important;
            padding: 2px !important;
        }
        
        /* Popover (Kalem) Butonunu Küçültme */
        div[data-testid="stPopover"] > button {
            padding: 0px 5px !important;
            min-height: 22px !important;
            height: 22px !important;
            width: 30px !important;
            border: 1px solid rgba(255,255,255,0.2) !important;
            background: rgba(255,255,255,0.05) !important;
            margin-top: 5px !important;
        }

        .bot-card-content {
            padding: 20px;
        }

        .status-strip-v8 {
            height: 6px;
            width: 60px;
            border-radius: 3px;
            margin-bottom: 20px;
        }
        .bg-running-v8 { background: #00F5A0; box-shadow: 0 0 15px rgba(0,245,160,0.5); }
        .bg-stopped-v8 { background: #666; }
        
        .b-title-v8 { font-size: 19px; font-weight: 800; color: #FFF; margin-bottom: 0px; white-space: nowrap; }
        .b-sub-v8 { font-size: 9px; color: #666; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700; margin-bottom: 2px; }
        
        .b-badge-v8 {
            font-size: 11px;
            font-weight: 900;
            padding: 6px 15px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
            display: inline-block;
        }
        .badge-active-v8 { background: rgba(0,245,160,0.15); color: #00F5A0; border-color: rgba(0,245,160,0.3); }
        .badge-passive-v8 { background: rgba(255,255,255,0.05); color: #888; border-color: rgba(255,255,255,0.1); }

        /* Üst Sağ Silme Butonu - SABİT VE SAĞA YASLI */
        button[key*="top_del"] {
            background-color: #FF4B4B !important;
            color: #FFFFFF !important;
            border: none !important;
            min-height: 28px !important;
            height: 28px !important;
            width: 32px !important;
            padding: 0 !important;
            margin-top: -15px !important;
            margin-right: -15px !important; /* Sağa, çizgiye yaklaştır */
            float: right !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 12px rgba(255, 75, 75, 0.4) !important;
        }
        
        button[key*="top_del"]:hover {
            background-color: #FF1E1E !important;
            transform: scale(1.05);
        }

        .metric-pill-v8 {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 18px;
            text-align: center;
        }
        .m-val-v8 { font-size: 22px; font-weight: 800; color: #00F5A0; line-height: 1; }
        .m-lab-v8 { font-size: 9px; color: #555; font-weight: 700; margin-top: 6px; text-transform: uppercase; }
        
        .url-box-v8 {
            font-size: 9px; 
            color: #666; 
            background: rgba(0,0,0,0.3); 
            padding: 8px 12px; 
            border-radius: 10px; 
            border: 1px solid rgba(255,255,255,0.05);
            margin: 15px 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
    </style>
    """, unsafe_allow_html=True)

    main_cols = st.columns(3)
    
    for i, task in enumerate(tasks):
        # Durumu PID dosyasından dinamik kontrol et
        status = get_bot_status(task.id)
        
        # GÖRSEL MANTIK:
        # 1. Badge (Rozet) kullanıcının 'Niyeti'ni göstersin (Şalter açık mı?).
        # 2. Butonlar ise bilgisayardaki 'Gerçek Durum'u temsil etsin.
        
        is_user_enabled = task.is_active
        is_actually_running = (status == "running")
        
        status_color_class = "bg-running-v8" if is_user_enabled else "bg-stopped-v8"
        status_badge_class = "badge-active-v8" if is_user_enabled else "badge-passive-v8"
        status_text = "AKTİF (OTOMASYON)" if is_user_enabled else "PASİF (KAPALI)"
        
        with main_cols[i % 3]:
            # TÜM BOTU KAPSAYAN TEK BÜYÜK BEYAZ KUTU
            with st.container(border=True):
                st.markdown(f'<div class="bot-card-content">', unsafe_allow_html=True)
                
                # 1. ÜST ŞERİT (DURUM VE SİLME)
                top_l, top_mid, top_r = st.columns([2, 5, 1])
                with top_l:
                    st.markdown(f'<div class="b-badge-v8 {status_badge_class}">{status_text}</div>', unsafe_allow_html=True)
                with top_r:
                    if st.button("🗑️", key=f"top_del_{task.id}", help="Görevi Sil"):
                        if delete_task(task.id):
                            st.rerun()

                # 2. İSİM VE DÜZENLEME (Şimdi Birbirine Çok Yakın)
                title_col, edit_col = st.columns([1, 4]) # İsmi sola yasladık, butonu hemen yanına aldık
                # Ama aslında Title genişliği kadar yer kaplamalı. st.columns bazen zorluyor.
                # Daha iyi bir yaklaşım:
                t1, t2 = st.columns([len(task.task_name)*0.5, 10]) # Dinamik ama basit bir oran
                # Aslında manuel oran [1, 5] gibi bir şey iş görür
                name_col, btn_col = st.columns([0.1 + (len(task.task_name) * 0.05), 1])
                
                with name_col:
                    st.markdown(f'<div class="b-title-v8">{task.task_name}</div>', unsafe_allow_html=True)
                with btn_col:
                    with st.popover("✏️", help="Yeniden Adlandır"):
                        new_name = st.text_input("Giriş Yapın", value=task.task_name, key=f"r_v8_{task.id}")
                        if st.button("Onayla", key=f"s_v8_{task.id}", type="primary", use_container_width=True):
                            if update_task_name(task.id, new_name):
                                st.rerun()

                st.markdown(f'<div class="b-sub-v8">{task.target_platform.upper()} KAZIMA BİRİMİ</div>', unsafe_allow_html=True)

                # 2.5 HIZLI KELİME VE MESAİ PLANI (YARDİYALI SİSTEM)
                st.markdown('<div style="margin-top:15px; margin-bottom:5px; font-size:10px; font-weight:800; color:#555;">� MESAİ VE KELİME PLANI</div>', unsafe_allow_html=True)
                
                # Saatleri datetime.time objesine çevirelim (Görünüm için)
                from datetime import time as dt_time
                try:
                    s_h, s_m = map(int, task.start_time.split(":"))
                    e_h, e_m = map(int, task.end_time.split(":"))
                    def_start = dt_time(s_h, s_m)
                    def_end = dt_time(e_h, e_m)
                except:
                    def_start, def_end = dt_time(9, 0), dt_time(18, 0)

                # Mevcut kelimeyi URL'den çek
                current_kw = extract_keyword_from_url(task.target_url)

                c_kw, c_st, c_en, c_btn = st.columns([1.5, 0.8, 0.8, 0.8])
                with c_kw:
                    quick_kw = st.text_input("Aranacak Kelime", value=current_kw, placeholder="Elbise", key=f"qkw_{task.id}")
                with c_st:
                    start_val = st.time_input("Başlangıç Tarihi", value=def_start, key=f"qst_{task.id}")
                with c_en:
                    end_val = st.time_input("Bitiş Tarihi", value=def_end, key=f"qen_{task.id}")
                with c_btn:
                    st.markdown('<div style="margin-top:28px;"></div>', unsafe_allow_html=True) # Hassas hizalama
                    if st.button("PLANLA", key=f"qplan_btn_{task.id}", use_container_width=True, help="Kelimeyi ve mesai saatlerini kaydet"):
                        import urllib.parse
                        success = True
                        # 1. Kelime girilmişse URL'yi güncelle
                        if quick_kw:
                            new_url = f"https://www.trendyol.com/sr?q={urllib.parse.quote(quick_kw)}"
                            if not update_task_url(task.id, new_url): success = False
                        
                        # 2. Mesai saatlerini güncelle
                        s_str = start_val.strftime("%H:%M")
                        e_str = end_val.strftime("%H:%M")
                        if not update_task_shift(task.id, s_str, e_str): success = False
                        
                        # 3. Planla denildiğine göre otomasyonu aktif et
                        update_task_active_status(task.id, True)

                        if success:
                            st.toast(f"Planlandı: {s_str} - {e_str}", icon="🕒")
                            time.sleep(0.5)
                            st.rerun()

                # 3. METRİKLER (2x2 IZGARA)
                st.write("") # Küçük bir boşluk

                # 3. METRİKLER (4'LÜ PANEL) - GERÇEK VERİLER
                t_stats = fetch_task_stats(task.id)
                
                m_row1_c1, m_row1_c2 = st.columns(2)
                with m_row1_c1:
                    st.markdown(f'<div class="metric-pill-v8"><div class="m-val-v8">{t_stats["total_scraped"]}</div><div class="m-lab-v8">Kazılan Link</div></div>', unsafe_allow_html=True)
                with m_row1_c2:
                    st.markdown(f'<div class="metric-pill-v8"><div class="m-val-v8">{t_stats["speed_hour"] if status == "running" else "0"}</div><div class="m-lab-v8">Hız (Ürün/Sa)</div></div>', unsafe_allow_html=True)
                
                st.write("") # Satır arası boşluk
                
                m_row2_c1, m_row2_c2 = st.columns(2)
                with m_row2_c1:
                    error_color = "#FF4B4B" if t_stats["errors"] > 0 else "#00F5A0"
                    st.markdown(f'<div class="metric-pill-v8"><div class="m-val-v8" style="color: {error_color};">{t_stats["errors"]}</div><div class="m-lab-v8">Hata Sayısı</div></div>', unsafe_allow_html=True)
                with m_row2_c2:
                    st.markdown(f'<div class="metric-pill-v8"><div class="m-val-v8">{t_stats["ip_changes"]}</div><div class="m-lab-v8">IP Değişimi</div></div>', unsafe_allow_html=True)

                # 4. AI SAĞLIK ANALİZİ VE ÖNERİLER (DİNAMİK)
                if status == 'running':
                    if t_stats["errors"] > 5:
                        h_msg, h_tip, h_clr = "KRİTİK", "Hedef site engel koymuş olabilir. Proxy rotasyonunu artırın.", "#FF4B4B"
                    elif t_stats["speed_hour"] < 10: # Çok yavaşsa
                        h_msg, h_tip, h_clr = "YAVAŞ", "Ağ gecikmesi veya düşük verim tespit edildi.", "#FFA500"
                    else:
                        h_msg, h_tip, h_clr = "SAĞLIKLI", "Verim en üst düzeyde. İşlem stabil ilerliyor.", "#00F5A0"
                else:
                    h_msg, h_tip, h_clr = "DURAKLATILDI", f"{task.task_name} yeni bir 'Başlat' komutu bekliyor.", "#666"

                st.markdown(f"""
                    <div style="background: rgba(0,0,0,0.4); border-left: 3px solid {h_clr}; padding: 12px; border-radius: 8px; margin-top: 20px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                            <span style="font-size: 10px; font-weight: 800; color: {h_clr}; letter-spacing: 1px;">AI SAĞLIK ANALİZİ</span>
                            <span style="background: {h_clr}33; color: {h_clr}; font-size: 8px; padding: 2px 6px; border-radius: 4px; font-weight: 900;">{h_msg}</span>
                        </div>
                        <div style="font-size: 12px; color: #EEE; font-weight: 500; line-height: 1.4;">
                            {h_tip}
                        </div>
                    </div>
                    <div style="font-size: 9px; color: #444; margin-top: 10px; padding: 0 5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        🌐 {task.target_url}
                    </div>
                """, unsafe_allow_html=True)

                # 5. AKSİYONLAR
                b_c1, b_c2, b_c3 = st.columns([1.8, 0.8, 0.8])
                with b_c1:
                    if is_actually_running:
                        if st.button("BOTU DURDUR", key=f"stop_v8_{task.id}", use_container_width=True):
                            with st.spinner("Bot durduruluyor..."):
                                stop_bot(task.id)
                                update_task_active_status(task.id, False) # Otomasyonu da kapat
                                time.sleep(0.8) # OS'un süreci öldürmesi için mola
                            st.rerun()
                    else:
                        if st.button("BOTU BAŞLAT", key=f"start_v8_{task.id}", type="primary", use_container_width=True):
                            with st.spinner("Bot hazırlanıyor..."):
                                # 1. Eğer yeni bir kelime yazılmışsa, önce onu KAYDET
                                final_url = task.target_url
                                if quick_kw:
                                    import urllib.parse
                                    final_url = f"https://www.trendyol.com/sr?q={urllib.parse.quote(quick_kw)}"
                                    update_task_url(task.id, final_url)
                                
                                # 2. Otomasyonu aç ve botu YENİ URL ile başlat
                                update_task_active_status(task.id, True) 
                                res, msg = start_bot(task.id, final_url)
                                time.sleep(1.2) 
                            if res: st.rerun()
                            else: st.error(msg)
                
                with b_c2:
                    # Hatayı veritabanından güncel çekelim
                    error_count = t_stats.get("errors", 0)
                    btn_label = f"⚠️ {error_count}" if error_count > 0 else "⚠️"
                    
                    if st.button(btn_label, key=f"wr_v8_{task.id}", use_container_width=True, help="Hata Kayıtlarını Gör"):
                        # Sayfa değiştirme Navigasyonu ve Filtre
                        st.query_params["p"] = "📜 Sistem Logları"
                        st.query_params["filter"] = "errors"
                        st.rerun()
                
                with b_c3:
                    with st.popover("⚙️", help="Ayarlar", use_container_width=True):
                        st.markdown("**Gelişmiş Ayarlar**")
                        if st.button("🗑️ Görevi Sil", key=f"dl_v8_{task.id}", type="secondary", use_container_width=True):
                            if delete_task(task.id):
                                st.rerun()
                        st.info("Diğer ayarlar yakında eklenecek.")
                
                st.markdown('</div>', unsafe_allow_html=True) # bot-card-content kapatma

# --- FOOTER ---
st.write("Analiz Motoru v1.0 | 2026")
# --- FOOTER ---
st.write("---")
