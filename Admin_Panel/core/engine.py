
import os
import psutil
import subprocess
import sys
import threading
import time
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text, inspect
import streamlit as st

# --- PATH HACK ---
admin_panel_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # .../Admin_Panel
analiz_motoru_root = os.path.dirname(admin_panel_dir) # .../Analiz-Motoru
scrapper_root = os.path.join(analiz_motoru_root, "Scrapper")

if scrapper_root not in sys.path:
    sys.path.append(scrapper_root)

from src.database import DatabaseManager, ScrapingTask
from src.config import load_config

# --- AUTH HELPER ---
@st.cache_resource
def get_server_secret():
    import random, string
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

def get_auth_hash():
    import hashlib
    secret = get_server_secret()
    return hashlib.sha256(f"admin_logged_in_{secret}".encode()).hexdigest()

# --- DATABASE OPERATIONS ---
def get_db_session():
    config = load_config(config_path=os.path.join(scrapper_root, "config.yaml"))
    platform_config = config.platforms.get('trendyol')
    if not platform_config:
        raise Exception("Trendyol config not found")
    
    db_url = platform_config.database.connection_url
    if db_url.startswith("sqlite:///"):
        db_file = db_url.replace("sqlite:///", "")
        db_url = "sqlite:///" + os.path.join(scrapper_root, db_file)

    db_manager = DatabaseManager(connection_url=db_url)
    return db_manager.get_session(), db_manager

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
    except Exception:
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
    except Exception:
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
    except Exception:
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
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()
        db_manager.close()

def update_task_search_params(task_id, params):
    session, db_manager = get_db_session()
    try:
        task = session.query(ScrapingTask).filter(ScrapingTask.id == task_id).first()
        if task:
            current = task.search_params or {}
            # SQLAlchemy mutable detection can be tricky with JSON, so we copy
            new_params = dict(current)
            new_params.update(params)
            task.search_params = new_params
            session.commit()
            return True
        return False
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()
        db_manager.close()

@st.cache_data(ttl=5)
def fetch_task_stats(task_id):
    session, db_manager = get_db_session()
    try:
        task_logs = session.execute(
            text("SELECT SUM(products_added + products_updated) as total, SUM(errors) as err FROM scraping_logs WHERE task_id = :tid"), 
            {"tid": task_id}
        ).fetchone()
        
        total_scraped = task_logs[0] if task_logs and task_logs[0] else 0
        total_errors = task_logs[1] if task_logs and task_logs[1] else 0
        
        last_log = session.execute(
            text("SELECT started_at, products_added, products_updated FROM scraping_logs WHERE task_id = :tid ORDER BY id DESC LIMIT 1"),
            {"tid": task_id}
        ).fetchone()
        
        speed_hour = 0
        if last_log and last_log[1] + last_log[2] > 0:
            start_at, added, updated = last_log
            elapsed_sec = (datetime.utcnow() - start_at).total_seconds()
            if elapsed_sec > 5:
                speed_hour = int(((added + updated) / elapsed_sec) * 3600)
        
        return {
            "total_scraped": total_scraped,
            "speed_hour": speed_hour,
            "errors": total_errors,
            "ip_changes": total_scraped // 45
        }
    finally:
        session.close()
        db_manager.close()

@st.cache_data(ttl=5)
def fetch_stats():
    session, db_manager = get_db_session()
    try:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        total_links = session.execute(text("SELECT COUNT(*) FROM products")).scalar()
        total_scraped_all_time = session.execute(text("SELECT COUNT(DISTINCT product_id) FROM daily_metrics WHERE discounted_price > 0")).scalar()
        today_scraped = session.execute(text("SELECT COUNT(DISTINCT product_id) FROM daily_metrics WHERE recorded_at >= :t"), {"t": today_start}).scalar()
        error_count = session.execute(text("SELECT COUNT(*) FROM scraping_logs WHERE status = 'error' AND started_at >= :t"), {"t": today_start}).scalar()
        
        time_threshold = datetime.utcnow() - timedelta(minutes=15)
        recent_count = session.execute(text("SELECT COUNT(DISTINCT product_id) FROM daily_metrics WHERE recorded_at >= :t"), {"t": time_threshold}).scalar()
        speed_per_min = round(recent_count / 15, 1) if recent_count else 0
        speed_per_hour = int(speed_per_min * 60)
        
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
    session, db_manager = get_db_session()
    try:
        query = "SELECT * FROM scraping_logs"
        params = {}
        if show_errors_only:
             query += " WHERE status = 'error' OR errors > 0"
        query += " ORDER BY id DESC LIMIT :limit"
        params["limit"] = limit
        return pd.read_sql(text(query), session.connection(), params=params)
    finally:
        session.close()
        db_manager.close()

def seed_default_tasks():
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
    except Exception:
        pass
    finally:
        session.close()
        db_manager.close()

# --- BOT MANAGEMENT ---
def get_bot_status(task_id):
    pid_file = f"bot_{task_id}.pid"
    pid_path = os.path.join(scrapper_root, pid_file)
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
            p = psutil.Process(pid)
            if "python" in p.name().lower():
                return "running"
        if os.path.exists(pid_path): os.remove(pid_path)
        return "stopped"
    except Exception:
        if os.path.exists(pid_path): os.remove(pid_path)
        return "stopped"

def start_bot(task_id, target_url):
    current_status = get_bot_status(task_id)
    if current_status == "running":
        return False, "Bu bot zaten çalışıyor."
    try:
        pid_file = f"bot_{task_id}.pid"
        pid_path = os.path.join(scrapper_root, pid_file)
        script_path = os.path.join(scrapper_root, "main.py")
        log_path = os.path.join(scrapper_root, f"bot_{task_id}.log")
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        mode = "a" if os.path.exists(log_path) else "w"
        with open(log_path, mode, encoding="utf-8") as out:
            process = subprocess.Popen(
                [sys.executable, script_path, "--task-id", str(task_id), "--url", target_url],
                cwd=scrapper_root,
                stdout=out,
                stderr=out,
                env=env
            )
        with open(pid_path, "w") as f:
            f.write(str(process.pid))
        return True, "Başarılı"
    except Exception as e:
        return False, str(e)

def stop_bot(task_id):
    pid_file = f"bot_{task_id}.pid"
    pid_path = os.path.join(scrapper_root, pid_file)
    if not os.path.exists(pid_path):
        return False, "PID dosyası bulunamadı."
    try:
        with open(pid_path, "r") as f:
            pid = int(f.read().strip())
        if psutil.pid_exists(pid):
            parent = psutil.Process(pid)
            for child in parent.children(recursive=True):
                child.terminate()
            parent.terminate()
        if os.path.exists(pid_path): os.remove(pid_path)
        return True, "Bot durduruldu."
    except Exception as e:
        return False, str(e)

# --- SCHEDULER ---
def start_permanent_scheduler():
    def scheduler_loop():
        while True:
            try:
                tasks = fetch_tasks() 
                now_str = datetime.now().strftime("%H:%M")
                for task in tasks:
                    status = get_bot_status(task.id)
                    start = task.start_time or "09:00"
                    end = task.end_time or "18:00"
                    is_shift_active = False
                    if start < end:
                        is_shift_active = start <= now_str <= end
                    else: 
                        is_shift_active = now_str >= start or now_str <= end
                    if is_shift_active:
                        if task.is_active and status == "stopped":
                            start_bot(task.id, task.target_url)
                    else:
                        if status == "running":
                            stop_bot(task.id)
            except Exception:
                pass
            time.sleep(30)
    thread = threading.Thread(target=scheduler_loop, daemon=True)
    thread.start()
    return True

# --- UTIL ---
def extract_keyword_from_url(url):
    try:
        if not url or "q=" not in url: return ""
        import urllib.parse
        raw_kw = url.split("q=")[-1].split("&")[0]
        return urllib.parse.unquote(raw_kw).replace('+', ' ').strip()
    except: return ""
