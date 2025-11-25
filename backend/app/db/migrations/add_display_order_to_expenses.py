"""
Migration script to add display_order column to expenses table.
Run this after updating the model to set display_order for existing expenses.
"""
from sqlalchemy import text
from app.db.session import SessionLocal

def migrate():
    """Add display_order column and set initial values based on id."""
    db = SessionLocal()
    try:
        # Check if column already exists
        result = db.execute(text("""
            SELECT COUNT(*) as count
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'expenses'
            AND COLUMN_NAME = 'display_order'
        """))
        column_exists = result.scalar() > 0
        
        if not column_exists:
            # Add display_order column
            db.execute(text("""
                ALTER TABLE expenses 
                ADD COLUMN display_order INT NOT NULL DEFAULT 0
            """))
            print("Added display_order column to expenses table")
        else:
            print("display_order column already exists, skipping column creation")
        
        # Set display_order based on id for existing expenses (grouped by trip_id and date)
        # For top-to-bottom ordering: older expenses (lower id) get smaller display_order (1, 2, 3...)
        # This ensures when sorted ASC, older expenses appear at top
        db.execute(text("""
            UPDATE expenses e1
            INNER JOIN (
                SELECT 
                    id,
                    trip_id,
                    date,
                    (SELECT COUNT(*)
                     FROM expenses e2 
                     WHERE e2.trip_id = e1_inner.trip_id 
                     AND e2.date = e1_inner.date 
                     AND e2.id <= e1_inner.id) AS new_display_order
                FROM expenses e1_inner
            ) AS temp ON e1.id = temp.id AND e1.trip_id = temp.trip_id AND e1.date = temp.date
            SET e1.display_order = temp.new_display_order
        """))
        print("Set display_order for existing expenses")
        
        # Add index for better query performance (if it doesn't exist)
        try:
            db.execute(text("""
                CREATE INDEX idx_expenses_display_order 
                ON expenses(trip_id, date, display_order)
            """))
            print("Created index on display_order")
        except Exception as idx_error:
            # Index might already exist
            if "Duplicate key name" not in str(idx_error):
                print(f"Index creation warning: {idx_error}")
        
        db.commit()
        print("Migration completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate()

