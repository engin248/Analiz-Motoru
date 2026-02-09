"""
Database Models - Product + DailyMetric
Matches ACTUAL Database Schema (verified via inspection)
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

class Product(Base):
    """Statik ürünler"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String(100), index=True)
    url = Column(String(500), unique=True, nullable=False, index=True)
    name = Column(String(500))
    image_url = Column(String(500))
    brand = Column(String(200)) # Var
    
    # Extra columns found in DB
    seller = Column(String(200))
    category = Column(String(200))
    category_tag = Column(String(200))
    attributes = Column(JSONB)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_scraped_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    daily_metrics = relationship("DailyMetric", back_populates="product", cascade="all, delete-orphan")


class DailyMetric(Base):
    """Günlük metrikler"""
    __tablename__ = "daily_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    price = Column(Float, default=0)
    discounted_price = Column(Float, default=0)
    discount_rate = Column(Float, default=0)
    
    # Match actual DB columns
    avg_rating = Column(Float, default=0)       # Was rating
    rating_count = Column(Integer, default=0)   # Was review_count
    
    favorite_count = Column(Integer, default=0)
    cart_count = Column(Integer, default=0)
    clicks_24h = Column(Integer, default=0)
    
    # Other columns in DB
    qa_count = Column(Integer, default=0)
    stock_status = Column(Boolean, default=True)
    
    product = relationship("Product", back_populates="daily_metrics")


class ScrapingLog(Base):
    """Log tablosu"""
    __tablename__ = "scraping_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50))
    keyword = Column(String(200))
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)
    pages_scraped = Column(Integer, default=0)
    products_found = Column(Integer, default=0)
    products_added = Column(Integer, default=0)
    products_updated = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    task_id = Column(Integer, ForeignKey("scraping_tasks.id"), nullable=True) # Hangi bot görevine ait?
    status = Column(String(50), default="running")
    error_details = Column(Text, nullable=True) # Hata detayları
    screenshot_path = Column(String(255), nullable=True) # Hata anındaki ekran görüntüsü yolu
    target_url = Column(Text, nullable=True) # Orijinal Hedef URL


class ScrapingTask(Base):
    """Bot görevleri tablosu"""
    __tablename__ = "scraping_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(255))
    target_platform = Column(String(100))
    target_url = Column(String, unique=True, nullable=False)
    search_params = Column(JSONB, nullable=True)
    scrape_interval_hours = Column(Integer, default=24)
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)
    start_time = Column(String(5), default="09:00") # HH:MM
    end_time = Column(String(5), default="18:00")   # HH:MM

class ScrapingQueue(Base):
    """Bulunan ama henüz detayları kazılmamış linkler havuzu"""
    __tablename__ = "scraping_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("scraping_tasks.id"), nullable=False)
    url = Column(String(500), nullable=False, index=True)
    status = Column(String(20), default="pending") # pending, processing, completed, failed
    discovered_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    error_msg = Column(Text)
