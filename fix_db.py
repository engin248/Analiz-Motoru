
import os
import sqlalchemy
from sqlalchemy import create_engine, text, inspect
from urllib.parse import quote_plus

# Connection details from .env
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "bediralvesil_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres123"

# Construct connection string
DATABASE_URL = f"postgresql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def migrate_db():
    print(f"Connecting to {DATABASE_URL}...")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as connection:
        # Check scraping_logs table columns
        inspector = inspect(engine)
        columns = [c['name'] for c in inspector.get_columns('scraping_logs')]
        print(f"Current columns in scraping_logs: {columns}")
        
        # Add target_url if missing
        if 'target_url' not in columns:
            print("Adding 'target_url' column...")
            connection.execute(text("ALTER TABLE scraping_logs ADD COLUMN target_url TEXT"))
            connection.commit()
            print("'target_url' column added.")
        else:
            print("'target_url' column already exists.")

        # Add screenshot_path if missing (just in case)
        if 'screenshot_path' not in columns:
            print("Adding 'screenshot_path' column...")
            connection.execute(text("ALTER TABLE scraping_logs ADD COLUMN screenshot_path VARCHAR(255)"))
            connection.commit()
            print("'screenshot_path' column added.")
        else:
             print("'screenshot_path' column already exists.")

        # Check daily_metrics for clicks_24h
        dm_columns = [c['name'] for c in inspector.get_columns('daily_metrics')]
        print(f"Current columns in daily_metrics: {dm_columns}")
        if 'clicks_24h' not in dm_columns:
            print("Adding 'clicks_24h' column...")
            connection.execute(text("ALTER TABLE daily_metrics ADD COLUMN clicks_24h INTEGER DEFAULT 0"))
            connection.commit()
            print("'clicks_24h' column added.")
        else:
             print("'clicks_24h' column already exists.")
             
        # Check scraping_tasks for search_params (JSONB compatibility)
        task_columns = [c['name'] for c in inspector.get_columns('scraping_tasks')]
        if 'search_params' not in task_columns:
             print("Adding 'search_params' column to scraping_tasks...")
             connection.execute(text("ALTER TABLE scraping_tasks ADD COLUMN search_params JSONB"))
             connection.commit()
             print("'search_params' column added.")

if __name__ == "__main__":
    try:
        migrate_db()
        print("Migration complete.")
    except Exception as e:
        print(f"Migration failed: {e}")
