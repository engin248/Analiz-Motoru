"""
Trendyol Scraping - Database Models
Ürün, metrikler ve özellikler için SQLAlchemy modelleri
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, 
    Boolean, ForeignKey, BigInteger, JSON, Index
)
from sqlalchemy.orm import relationship
from src.database import Base


class Product(Base):
    """Ana ürün tablosu"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Trendyol'dan gelen unique ID
    trendyol_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Temel Bilgiler
    product_name = Column(Text, nullable=False)
    seller_name = Column(String(255), nullable=False, index=True)
    product_url = Column(Text)
    image_url = Column(Text)
    category = Column(String(255), index=True)
    
    # Fiyat Bilgileri
    original_price = Column(Float)
    discounted_price = Column(Float)
    discount_rate = Column(Float)
    currency = Column(String(10), default="TRY")
    
    # Durum
    is_active = Column(Boolean, default=True)
    
    # Zaman Damgaları
    first_scraped_at = Column(DateTime, default=datetime.utcnow)
    last_scraped_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # İlişkiler
    metrics = relationship("ProductMetrics", back_populates="product", cascade="all, delete-orphan")
    attributes = relationship("ProductAttribute", back_populates="product", cascade="all, delete-orphan")
    
    # İndeksler
    __table_args__ = (
        Index('idx_product_seller', 'seller_name'),
        Index('idx_product_category', 'category'),
        Index('idx_product_price', 'discounted_price'),
    )
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.product_name[:30]}...')>"


class ProductMetrics(Base):
    """Ürün etkileşim metrikleri (zamana bağlı değişen veriler)"""
    __tablename__ = "product_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    
    # Değerlendirme
    rating_average = Column(Float)  # 4.8
    rating_count = Column(Integer)  # 31 kişi değerlendirdi
    review_summary = Column(Text)  # AI tarafından üretilen özet
    
    # Etkileşim Metrikleri
    cart_count = Column(Integer)  # Sepette: 880
    favorite_count = Column(BigInteger)  # Favori: 14k
    click_count_24h = Column(BigInteger)  # Son 24 saat: 5k
    qa_count = Column(Integer)  # Soru-Cevap: 46
    
    # Zaman Damgası
    scraped_at = Column(DateTime, default=datetime.utcnow)
    
    # İlişki
    product = relationship("Product", back_populates="metrics")
    
    # İndeksler
    __table_args__ = (
        Index('idx_metrics_product', 'product_id'),
        Index('idx_metrics_scraped', 'scraped_at'),
    )
    
    def __repr__(self):
        return f"<ProductMetrics(product_id={self.product_id}, rating={self.rating_average})>"


class ProductAttribute(Base):
    """Ürün özellikleri (Beden, Renk, Kumaş Tipi vb.)"""
    __tablename__ = "product_attributes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    
    # Özellik key-value
    attribute_name = Column(String(100), nullable=False)  # "Beden", "Renk", "Kumaş Tipi"
    attribute_value = Column(Text, nullable=False)  # "S", "Bordo", "Örme"
    
    # Zaman
    scraped_at = Column(DateTime, default=datetime.utcnow)
    
    # İlişki
    product = relationship("Product", back_populates="attributes")
    
    # İndeksler
    __table_args__ = (
        Index('idx_attr_product', 'product_id'),
        Index('idx_attr_name', 'attribute_name'),
    )
    
    def __repr__(self):
        return f"<ProductAttribute({self.attribute_name}={self.attribute_value})>"


class ScrapingLog(Base):
    """Scraping işlem logları"""
    __tablename__ = "scraping_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # İşlem Bilgisi
    job_type = Column(String(50), nullable=False)  # "category", "product", "search"
    target_url = Column(Text)
    category_name = Column(String(255))
    
    # Sonuçlar
    status = Column(String(20), nullable=False)  # "started", "completed", "failed"
    products_found = Column(Integer, default=0)
    products_scraped = Column(Integer, default=0)
    products_saved = Column(Integer, default=0)
    
    # Hata Bilgisi
    error_message = Column(Text)
    
    # Zaman
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    # İndeksler
    __table_args__ = (
        Index('idx_log_status', 'status'),
        Index('idx_log_started', 'started_at'),
    )
    
    def __repr__(self):
        return f"<ScrapingLog(job={self.job_type}, status={self.status})>"
