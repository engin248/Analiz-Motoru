from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Product(Base):
    """Ürün Modeli"""
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    trendyol_id = Column(String(50), unique=True, nullable=False, index=True)
    product_url = Column(String(500), nullable=False)
    name = Column(String(500))
    brand = Column(String(100))
    category = Column(String(200))
    seller_name = Column(String(200)) # Satıcı Adı
    
    # Fiyat Bilgileri
    current_price = Column(Float)
    original_price = Column(Float)
    currency = Column(String(3), default='TL')
    
    # Meta Bilgileri
    image_url = Column(String(500))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # İlişkiler
    metrics = relationship("ProductMetrics", back_populates="product", cascade="all, delete-orphan")
    attributes = relationship("ProductAttribute", back_populates="product", cascade="all, delete-orphan")
    price_history = relationship("ProductPriceHistory", back_populates="product", cascade="all, delete-orphan")
    reviews = relationship("ProductReview", back_populates="product", cascade="all, delete-orphan")
    
    # property for backward compatibility if needed
    @property
    def images(self):
        return [self.image_url] if self.image_url else []
        
    @images.setter
    def images(self, value):
        if value and len(value) > 0:
            self.image_url = value[0]

class ProductMetrics(Base):
    """Zamanla değişen metrikler (Favori, Yorum, Puan)"""
    __tablename__ = 'product_metrics'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    
    favorite_count = Column(Integer)
    rating_score = Column(Float)
    review_count = Column(Integer)
    view_count = Column(Integer)       # Görüntülenme Sayısı
    sold_count_text = Column(String(50)) # "100+ satıldı" gibi
    
    captured_at = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product", back_populates="metrics")

class ProductAttribute(Base):
    """Ürün Özellikleri (Key-Value)"""
    __tablename__ = 'product_attributes'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    
    name = Column(String(100), nullable=False)  # Renk, Beden, Kumaş
    value = Column(String(500))                 # Kırmızı, M, Pamuk
    
    product = relationship("Product", back_populates="attributes")

class ProductPriceHistory(Base):
    """Fiyat değişim geçmişi"""
    __tablename__ = 'product_price_history'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    
    price = Column(Float, nullable=False)
    currency = Column(String(3), default='TL')
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product", back_populates="price_history")

class ProductReview(Base):
    """Ürün Yorumları"""
    __tablename__ = 'product_reviews'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    
    # Yorum Detayları
    review_date = Column(String(50)) # "12 Nisan 2023"
    rating = Column(Integer)         # 5
    comment = Column(Text)           # "Çok güzel..."
    
    # Teknik Detaylar
    is_analyzed = Column(Boolean, default=False) # AI Analizi yapıldı mı?
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # İlişki: Bir yorum bir ürüne aittir
    product = relationship("Product", back_populates="reviews")
