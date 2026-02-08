from sqlalchemy import Column, Integer, String, DateTime, func, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class SystemLog(Base):
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=func.now())  # Otomatik tarih
    level = Column(String(50))   # INFO, ERROR, WARNING
    bot_name = Column(String(100)) # "Kazıyıcı-1", "Hasatçı"
    message = Column(Text)       # "Ürün ID:555 Eklendi (Fiyat: 100)"
