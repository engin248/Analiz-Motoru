
from src.database import engine
from src.models_log import Base

print("Tablolar oluşturuluyor...")
Base.metadata.create_all(bind=engine)
print("✅ Log Tablosu (system_logs) Hazır!")
