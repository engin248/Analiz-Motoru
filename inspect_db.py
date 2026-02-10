
import os
import sys
from sqlalchemy import create_engine, inspect

db_url = 'postgresql://postgres:postgres123@localhost:5432/bediralvesil_db'
engine = create_engine(db_url)
inspector = inspect(engine)

tables = ['scraping_logs', 'scraping_tasks', 'scraping_queue']
for table in tables:
    if table in inspector.get_table_names():
        cols = [c["name"] for c in inspector.get_columns(table)]
        print(f"--- {table} ---")
        for c in cols:
            print(f"Col: {c}")
    else:
        print(f"Table '{table}' not found!")
