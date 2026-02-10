
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

# DEBUG
print(f"DEBUG: sys.path includes {scrapper_root}")
init_path = os.path.join(scrapper_root, "src", "database", "__init__.py")
if os.path.exists(init_path):
    with open(init_path, "r") as f:
        print(f"DEBUG: __init__.py content snippet: {f.read()[:100]}")
else:
    print(f"DEBUG: __init__.py NOT FOUND at {init_path}")

from src.database.database_manager import DatabaseManager
from src.database.models import ScrapingTask, Product, ScrapingLog, ScrapingQueue
from src.config import load_config

# --- DATABASE OPERATIONS ---
def get_db_session():
    config = load_config(config_path=os.path.join(scrapper_root, "config.yaml"))
    # Platform bağımsız DB url'sini config'den al
    platform_config = config.platforms.get('trendyol')
    if not platform_config:
        raise Exception("Platform config not found")
    
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

def fetch_task_stats(task_id, session=None):
    external_session = session is not None
    if not external_session:
        session, db_manager = get_db_session()
    
    try:
        # TÜM GEÇMİŞ LOGLARI AL (Kümülatif hesaplama için)
        logs = session.query(ScrapingLog).filter(ScrapingLog.task_id == task_id).all()
        
        cumulative_scraped = 0
        cumulative_errors = 0
        total_duration_hours = 0.0
        
        for log in logs:
            # 1. Scraped Count
            if log.status == "completed":
                log_scraped = log.products_found
            else:
                log_scraped = log.products_added + log.products_updated
            
            cumulative_scraped += log_scraped
            cumulative_errors += (log.errors or 0)
            
            # 2. Duration for Speed
            log_duration = 0
            if log.finished_at:
                log_duration = (log.finished_at - log.started_at).total_seconds() / 3600
            else:
                # Aktif log ise şu anki zamana göre
                log_duration = (datetime.utcnow() - log.started_at).total_seconds() / 3600
            
            if log_duration > 0:
                total_duration_hours += log_duration

        # 3. Average Speed (Global Average)
        speed = 0
        if total_duration_hours > 0.001:
            speed = int(cumulative_scraped / total_duration_hours)

        return {
            "total_scraped": cumulative_scraped,
            "errors": cumulative_errors,
            "speed_hour": speed,
            "ip_changes": 0 # Proxy takibi şu an pasif
        }
    finally:
        if not external_session:
            session.close()
            db_manager.close()

def fetch_stats():
    session, db_manager = get_db_session()
    try:
        total_links = session.query(ScrapingQueue).count()
        total_scraped = session.query(Product).count()
        
        today = datetime.now().date()
        today_scraped = session.query(ScrapingLog).filter(ScrapingLog.started_at >= today).count()
        today_errors = session.query(ScrapingLog).filter(ScrapingLog.started_at >= today).filter(ScrapingLog.errors > 0).count()
        
        # Son 1 saatteki hıza bak
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_logs = session.query(ScrapingLog).filter(ScrapingLog.started_at >= one_hour_ago).all()
        found_sum = sum([l.products_found for l in recent_logs])
        
        # Son loglar
        logs = session.query(ScrapingLog).order_by(ScrapingLog.started_at.desc()).limit(10).all()
        logs_data = []
        for l in logs:
            logs_data.append({
                "started_at": l.started_at,
                "platform": l.platform or "trendyol",
                "status": l.status,
                "keyword": l.keyword or l.target_url or "-"
            })
        
        return {
            "total_links": total_links + total_scraped, # Toplam havuz
            "total_scraped": total_scraped,
            "today": today_scraped,
            "errors": today_errors,
            "speed_min": int(found_sum / 60) if found_sum > 0 else 0,
            "speed_hour": found_sum,
            "logs": pd.DataFrame(logs_data),
            "total_products": total_scraped,
            "daily_new": session.query(Product).filter(Product.first_seen_at >= today).count(),
            "active_bots": sum([1 for t in session.query(ScrapingTask).all() if get_bot_status(t.id) == "running"])
        }
    finally:
        session.close()
        db_manager.close()

def fetch_detailed_logs(limit=100, show_errors_only=False):
    session, db_manager = get_db_session()
    try:
        query = session.query(ScrapingLog)
        if show_errors_only:
            query = query.filter(ScrapingLog.errors > 0)
        
        logs = query.order_by(ScrapingLog.started_at.desc()).limit(limit).all()
        
        data = []
        for l in logs:
            data.append({
                "id": l.id,
                "platform": l.platform or "trendyol",
                "keyword": l.keyword or l.target_url or "-",
                "started_at": l.started_at,
                "finished_at": l.finished_at,
                "pages_scraped": l.pages_scraped,
                "products_found": l.products_found,
                "products_added": l.products_added,
                "errors": l.errors,
                "status": l.status,
                "error_details": l.error_details,
                "screenshot_path": l.screenshot_path,
                "target_url": l.target_url
            })
        return pd.DataFrame(data)
    finally:
        session.close()
        db_manager.close()

# --- NEW: ALL TASK STATS FOR BULK FETCH ---
def fetch_all_task_stats():
    session, db_manager = get_db_session()
    all_stats = {}
    try:
        tasks = session.query(ScrapingTask).all()
        for task in tasks:
            all_stats[task.id] = fetch_task_stats(task.id, session=session)
        return all_stats
    finally:
        session.close()
        db_manager.close()

def get_all_bot_statuses():
    tasks = fetch_tasks()
    running_ids = []
    for task in tasks:
        if get_bot_status(task.id) == "running":
            running_ids.append(task.id)
    return running_ids


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

def start_bot(task_id, target_url, force=False):
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
        env["PYTHONUNBUFFERED"] = "1"
        
        mode = "a" if os.path.exists(log_path) else "w"
        out = open(log_path, mode, encoding="utf-8")
        
        process = subprocess.Popen(
            [sys.executable, script_path, "--task-id", str(task_id), "--url", target_url],
            cwd=scrapper_root,
            stdout=out,
            stderr=out,
            env=env,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        
        # Manual start override
        force_file = os.path.join(scrapper_root, f"bot_{task_id}.force")
        if force:
            with open(force_file, "w") as f: f.write("1")
        
        # Write PID immediately
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
        
        # Clean up force file
        force_file = os.path.join(scrapper_root, f"bot_{task_id}.force")
        if os.path.exists(force_file): os.remove(force_file)
        
        return True, "Bot durduruldu."
    except Exception as e:
        return False, str(e)

# --- SCHEDULER ---
def start_permanent_scheduler():
    def scheduler_loop():
        # Small wait to ensure root files can be written if needed
        time.sleep(5)
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
                        
                    force_file = os.path.join(scrapper_root, f"bot_{task.id}.force")
                    is_forced = os.path.exists(force_file)

                    if is_shift_active or is_forced:
                        if task.is_active and status == "stopped":
                            start_bot(task.id, task.target_url)
                    else:
                        if status == "running" and task.is_active:
                            # Not forced and outside shift -> STOP
                            stop_bot(task.id)
            except Exception:
                pass
            time.sleep(15) # Check every 15s

    thread = threading.Thread(target=scheduler_loop, daemon=True, name="SchedulerThread")
    thread.start()
    return True

# --- SETTERS ---
def update_task_active_status(task_id, is_active):
    session, db_manager = get_db_session()
    try:
        task = session.query(ScrapingTask).get(task_id)
        if task:
            task.is_active = is_active
            session.commit()
            return True
        return False
    finally:
        session.close()
        db_manager.close()

def update_task_url(task_id, new_url):
    session, db_manager = get_db_session()
    try:
        task = session.query(ScrapingTask).get(task_id)
        if task:
            task.target_url = new_url
            session.commit()
            return True
        return False
    finally:
        session.close()
        db_manager.close()

def update_task_shift(task_id, start_time, end_time):
    session, db_manager = get_db_session()
    try:
        task = session.query(ScrapingTask).get(task_id)
        if task:
            task.start_time = start_time
            task.end_time = end_time
            session.commit()
            return True
        return False
    finally:
        session.close()
        db_manager.close()

def update_task_name(task_id, new_name):
    session, db_manager = get_db_session()
    try:
        task = session.query(ScrapingTask).get(task_id)
        if task:
            task.task_name = new_name
            session.commit()
            return True
        return False
    finally:
        session.close()
        db_manager.close()

def update_task_search_params(task_id, params):
    session, db_manager = get_db_session()
    try:
        task = session.query(ScrapingTask).get(task_id)
        if task:
            if not task.search_params: task.search_params = {}
            current = dict(task.search_params)
            current.update(params)
            task.search_params = current
            session.commit()
            return True
        return False
    finally:
        session.close()
        db_manager.close()

def delete_task(task_id):
    stop_bot(task_id)
    session, db_manager = get_db_session()
    try:
        task = session.query(ScrapingTask).get(task_id)
        if task:
            session.delete(task)
            session.commit()
            return True
        return False
    finally:
        session.close()
        db_manager.close()

def clear_task_stats(task_id):
    session, db_manager = get_db_session()
    try:
        session.query(ScrapingLog).filter(ScrapingLog.task_id == task_id).delete()
        session.commit()
        return True, "İstatistikler sıfırlandı."
    finally:
        session.close()
        db_manager.close()

def seed_default_tasks():
    session, db_manager = get_db_session()
    try:
        count = session.query(ScrapingTask).count()
        if count == 0:
            task1 = ScrapingTask(
                task_name="İşçi 1",
                target_platform="trendyol",
                target_url="https://www.trendyol.com/sr?q=kad%C4%B1n%20g%C3%B6mlek",
                scrape_interval_hours=24,
                is_active=True,
                start_time="09:00",
                end_time="18:00",
                search_params={"max_pages": 40, "request_delay": 2}
            )
            session.add(task1)
            session.commit()
    finally:
        session.close()
        db_manager.close()

def add_task(name, platform, url, interval=24):
    session, db_manager = get_db_session()
    try:
        new_task = ScrapingTask(
            task_name=name,
            target_platform=platform,
            target_url=url,
            scrape_interval_hours=interval,
            is_active=True,
            start_time="09:00",
            end_time="18:00",
            search_params={"max_pages": 40, "request_delay": 2}
        )
        session.add(new_task)
        session.commit()
        return True
    finally:
        session.close()
        db_manager.close()

def get_auth_hash():
    import hashlib
    # Statik secret yerine basit bir değer kullanıyoruz şimdilik
    return hashlib.sha256(f"admin_logged_in_static_secret_123".encode()).hexdigest()

def extract_keyword_from_url(url):
    try:
        if not url or "q=" not in url: return ""
        import urllib.parse
        raw_kw = url.split("q=")[-1].split("&")[0]
        return urllib.parse.unquote(raw_kw).replace('+', ' ').strip()
    except: return ""
