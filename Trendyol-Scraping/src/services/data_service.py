import os
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, text
from sqlalchemy.exc import IntegrityError

# Modelleri içe aktar
# Modelleri içe aktar
from src.database.models import Base, Product, ProductMetrics, ProductAttribute, ProductPriceHistory, ProductReview

class DataService:
    """Veritabanı işlemlerini yürüten servis sınıfı"""
    
    def __init__(self):
        load_dotenv()
        
        # Yapılandırmayı .env'den al
        self.db_type = os.getenv("DB_TYPE", "sqlite")
        
        if self.db_type == "postgres":
            user = os.getenv("DB_USER", "postgres")
            password = os.getenv("DB_PASSWORD", "")
            host = os.getenv("DB_HOST", "localhost")
            port = os.getenv("DB_PORT", "5432")
            dbname = os.getenv("DB_NAME", "trendyol_db")
            
            # PostgreSQL URL (asyncpg sürücüsü ile)
            # Eğer şifre yoksa boş geç
            auth = f"{user}:{password}" if password else user
            self.db_url = f"postgresql+asyncpg://{auth}@{host}:{port}/{dbname}"
            print(f"🔌 PostgreSQL'e bağlanılıyor: {host}/{dbname}")
        else:
            # SQLite (Varsayılan)
            db_name = os.getenv("DB_NAME", "trendyol_scraper.db")
            db_path = os.path.abspath(db_name)
            self.db_url = f"sqlite+aiosqlite:///{db_path}"
            print(f"🔌 SQLite kullanılıyor: {db_name}")

        self.engine = create_async_engine(self.db_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
    async def save_product(self, data: Dict) -> bool:
        """
        Scraper'dan gelen veriyi veritabanına kaydet
        """
        async with self.async_session() as session:
            try:
                # ID'yi garantiye al
                t_id = str(data.get('trendyol_id'))
                if not t_id or t_id == 'None':
                    return False

                # 1. Product Kaydı/Güncelleme
                stmt = select(Product).filter_by(trendyol_id=t_id)
                res = await session.execute(stmt)
                product = res.scalar_one_or_none()
                
                if not product:
                    product = Product(
                        trendyol_id=t_id,
                        product_url=data.get('product_url'),
                        name=data.get('product_name'),
                        brand=data.get('brand'),
                        category=data.get('category'),
                        seller_name=data.get('seller_name'),
                        current_price=data.get('discounted_price') or 0.0,
                        original_price=data.get('original_price') or 0.0,
                        image_url=data.get('image_url')
                    )
                    session.add(product)
                else:
                    product.current_price = data.get('discounted_price') or 0.0
                    product.original_price = data.get('original_price') or 0.0
                    product.seller_name = data.get('seller_name')
                    product.last_updated = datetime.utcnow()
                
                await session.flush()

                # 2. Metrikleri Kaydet
                m = data.get('metrics', {})
                metrics = ProductMetrics(
                    product_id=product.id,
                    favorite_count=m.get('favorite_count', 0),
                    rating_score=m.get('rating_score', 0),
                    review_count=m.get('review_count', 0),
                    view_count=m.get('view_count', 0),
                    sold_count_text=m.get('sold_count_text', "")
                )
                session.add(metrics)
                
                # 3. Özellikleri Kaydet (attributes)
                # Önce eskileri temizle
                await session.execute(text(f"DELETE FROM product_attributes WHERE product_id = {product.id}"))
                
                for attr in data.get('attributes', []):
                    # Scraper 'attribute_name' gönderiyor, Model 'name' bekliyor
                    new_attr = ProductAttribute(
                        product_id=product.id,
                        name=attr.get('attribute_name', 'Özellik'),
                        value=attr.get('attribute_value', '')
                    )
                    session.add(new_attr)
                
                await session.commit()
                return True
                
            except Exception as e:
                await session.rollback()
                print(f"SAVE ERROR: {e}")
                return False

    async def save_reviews(self, trendyol_id: str, reviews: List[Dict]) -> bool:
        """
        Bir ürüne ait yorumları veritabanına kaydeder.
        Önce ürünün veritabanında olup olmadığına bakar.
        """
        async with self.async_session() as session:
            try:
                # 1. Ürünü Bul
                stmt = select(Product).filter_by(trendyol_id=str(trendyol_id))
                res = await session.execute(stmt)
                product = res.scalar_one_or_none()
                
                if not product:
                    print(f"⚠️ Ürün bulunamadı (Trendyol ID: {trendyol_id}). Önce ürünü kaydedin.")
                    return False
                
                # 2. Eski Yorumları Temizle (Tercihen temizlenir, veya sadece yeniler eklenir)
                # Tam senkronizasyon için eskileri silip yenileri eklemek en temizidir 
                # (Eğer geçmiş yorumları tutmak istemiyorsak)
                await session.execute(text(f"DELETE FROM product_reviews WHERE product_id = {product.id}"))
                
                # 3. Yeni Yorumları Ekle
                count = 0
                for r in reviews:
                    new_review = ProductReview(
                        product_id=product.id,
                        review_date=r.get('date'),
                        rating=r.get('rating'),
                        comment=r.get('comment')
                    )
                    session.add(new_review)
                    count += 1
                
                await session.commit()
                print(f"✅ {count} yorum veritabanına kaydedildi.")
                return True
                
            except Exception as e:
                await session.rollback()
                print(f"REVIEW SAVE ERROR: {e}")
                return False

    async def export_to_excel(self, filename: str = "trendyol_products.xlsx"):
        """Excel'e aktar (Sütun ayırma garantili)"""
        import pandas as pd
        from sqlalchemy.orm import selectinload
        
        async with self.async_session() as session:
            stmt = select(Product).options(
                selectinload(Product.metrics),
                selectinload(Product.attributes)
            )
            res = await session.execute(stmt)
            products = res.scalars().all()
            
            data_list = []
            for p in products:
                # En son eklenen metriği al
                m = p.metrics[-1] if p.metrics else None
                
                # Özellikleri Tek Bir String Haline Getir
                # Örnek: "Materyal: Pamuk; Yaka: V Yaka; Renk: Kırmızı"
                attr_text = "; ".join([f"{a.name}: {a.value}" for a in p.attributes])
                
                row = {
                    'Marka': p.brand or p.seller_name,
                    'Ürün Adı': p.name,
                    'İndirimli Fiyat (TL)': p.current_price,
                    'Orijinal Fiyat (TL)': p.original_price,
                    'Puan': m.rating_score if m else 0,
                    'Değerlendirme Sayısı': m.review_count if m else 0,
                    'Favori Sayısı': m.favorite_count if m else 0,
                    'Görüntülenme (24s)': m.view_count if m else 0,
                    'Özellikler': attr_text, # Tek Sütunda Tüm Özellikler
                    'Link': p.product_url
                }
                
                data_list.append(row)
            
            if not data_list: return False
            
            df = pd.DataFrame(data_list)
            df.to_excel(filename, index=False)
            return True
