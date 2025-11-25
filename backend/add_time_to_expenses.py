"""
Database migration script to add time column to expenses table.
Run this script to add the time column for expense ordering.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    """Add time column to expenses table."""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'expenses' 
            AND COLUMN_NAME = 'time'
        """))
        
        if result.scalar() > 0:
            print("Column 'time' already exists in 'expenses' table. Skipping migration.")
            return
        
        # Add time column
        print("Adding 'time' column to 'expenses' table...")
        conn.execute(text("""
            ALTER TABLE expenses 
            ADD COLUMN time TIME NULL AFTER date
        """))
        
        conn.commit()
        print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()

