"""
Database Manager - Handle database connections and operations
Supports Product + DailyMetric historical data model (Actual Schema)
"""

from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from rich.console import Console

from .models import Base, Product, DailyMetric, ScrapingLog, ScrapingQueue

console = Console()


class DatabaseManager:
    """
    Manages database connections and CRUD operations.
    Implements Product + DailyMetric pattern for historical data.
    """
    
    def __init__(self, connection_url: str, platform: str = "trendyol"):
        self.connection_url = connection_url
        self.platform = platform
        self.engine = create_engine(connection_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self._session: Optional[Session] = None
    
    def create_tables(self):
        """Create database tables if they don't exist"""
        try:
            Base.metadata.create_all(bind=self.engine)
        except Exception as e:
            console.print(f"[red]❌ Tablo oluşturma hatası: {e}[/red]")
    
    def get_session(self) -> Session:
        """Get or create a database session"""
        if self._session is None:
            self._session = self.SessionLocal()
        return self._session
    
    def close(self):
        """Close the database session"""
        if self._session:
            self._session.close()
            self._session = None
    
    def save_product(self, product_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Save product aligned with ACTUAL Backend schema.
        """
        session = self.get_session()
        url = product_data.get('url')
        
        if not url:
            return False, "URL eksik"
        
        try:
            # 1. Product (Statik)
            product = session.query(Product).filter(Product.url == url).first()
            is_new = product is None
            
            if is_new:
                product = Product(
                    product_code=product_data.get('product_id'),
                    url=url,
                    brand=product_data.get('brand', ''),
                    name=product_data.get('name', ''),
                    image_url=product_data.get('image_url', ''),
                    created_at=datetime.utcnow(),
                    last_scraped_at=datetime.utcnow()
                )
                session.add(product)
                session.flush()
            else:
                product.brand = product_data.get('brand') or product.brand
                product.name = product_data.get('name') or product.name
                product.image_url = product_data.get('image_url') or product.image_url
                product.last_scraped_at = datetime.utcnow()
            
            # 2. DailyMetric (Dinamik)
            metric = DailyMetric(
                product_id=product.id,
                recorded_at=datetime.utcnow(),
                price=product_data.get('original_price', 0),
                discounted_price=product_data.get('discounted_price', 0),
                discount_rate=product_data.get('discount_rate', 0),
                
                # Correct mapped columns
                avg_rating=product_data.get('rating', 0),         # rating -> avg_rating
                rating_count=product_data.get('review_count', 0), # review_count -> rating_count
                
                favorite_count=product_data.get('favorite_count', 0),
                cart_count=product_data.get('cart_count', 0),
                clicks_24h=product_data.get('view_count', 0),
            )
            session.add(metric)
            session.commit()
            
            name = product_data.get('name', '')[:40]
            if is_new:
                return True, f"➕ Eklendi: {name}..."
            else:
                return False, f"🔄 Güncellendi: {name}..."
                
        except Exception as e:
            session.rollback()
            return False, f"❌ Hata: {e}"
    
    def get_product_count(self) -> int:
        session = self.get_session()
        return session.query(Product).count()
    
    def get_metric_count(self) -> int:
        session = self.get_session()
        return session.query(DailyMetric).count()
    
    def start_log(self, keyword: str, task_id: Optional[int] = None, target_url: str = None) -> int:
        session = self.get_session()
        log = ScrapingLog(
            platform=self.platform,
            keyword=keyword,
            task_id=task_id,
            target_url=target_url,
            started_at=datetime.utcnow(),
            status="running"
        )
        session.add(log)
        session.commit()
        return log.id
    
    def finish_log(self, log_id: int, pages: int, found: int, added: int, updated: int, errors: int = 0):
        session = self.get_session()
        log = session.query(ScrapingLog).filter(ScrapingLog.id == log_id).first()
        if log:
            log.pages_scraped = pages
            log.products_found = found
            log.products_added = added
            log.products_updated = updated
            log.errors = errors
            log.finished_at = datetime.utcnow()
            log.status = "completed"
            session.commit()

    def update_log_progress(self, log_id: int, added: int, updated: int, errors: int):
        """Log kaydını canlı olarak günceller."""
        session = self.get_session()
        log = session.query(ScrapingLog).filter(ScrapingLog.id == log_id).first()
        if log:
            log.products_added = added
            log.products_updated = updated
            log.errors = errors
            session.commit()

    def log_error(self, log_id: int, error_message: str, screenshot_path: str = None):
        """Hata detayını veritabanına kaydeder."""
        session = self.get_session()
        log = session.query(ScrapingLog).filter(ScrapingLog.id == log_id).first()
        if log:
            # Hata sayısını artır
            if log.errors is None: log.errors = 0
            log.errors += 1
            
            # Hata detayını biriktir (En son 5000 karaktere kadar)
            timestamp = datetime.now().strftime("%H:%M:%S")
            new_detail = f"[{timestamp}] {error_message}\n"
            
            if hasattr(log, 'error_details') and log.error_details:
                # Mevcut log çok uzunsa başını kes
                current_log = str(log.error_details)
                if len(current_log) > 4000:
                    current_log = "..." + current_log[-4000:]
                log.error_details = current_log + new_detail
            elif hasattr(log, 'error_details'):
                log.error_details = new_detail
            
            # Screenshot varsa kaydet (Son alınan screenshot geçerli olur)
            if screenshot_path and hasattr(log, 'screenshot_path'):
                log.screenshot_path = screenshot_path
                
            session.commit()

    def add_to_queue(self, task_id: int, url: str):
        """Linki kazıma kuyruğuna ekler (Eğer yoksa)"""
        session = self.get_session()
        # Zaten ekli mi kontrol et (pending veya processing ise tekrar ekleme)
        exists = session.query(ScrapingQueue).filter(
            ScrapingQueue.task_id == task_id,
            ScrapingQueue.url == url,
            ScrapingQueue.status.in_(['pending', 'processing'])
        ).first()
        
        if not exists:
            new_item = ScrapingQueue(task_id=task_id, url=url, status="pending")
            session.add(new_item)
            session.commit()
            return True
        return False

    def get_next_from_queue(self, task_id: int):
        """Sıradaki bekleyen linki çeker ve durumunu 'processing' yapar."""
        session = self.get_session()
        item = session.query(ScrapingQueue).filter(
            ScrapingQueue.task_id == task_id,
            ScrapingQueue.status == "pending"
        ).order_by(ScrapingQueue.discovered_at.asc()).first()
        
        if item:
            item.status = "processing"
            session.commit()
            return item
        return None

    def update_queue_status(self, queue_id: int, status: str, error: str = None):
        """Kuyruktaki linkin durumunu günceller."""
        session = self.get_session()
        item = session.query(ScrapingQueue).filter(ScrapingQueue.id == queue_id).first()
        if item:
            item.status = status
            item.processed_at = datetime.utcnow()
            if error:
                item.error_msg = error
            session.commit()
