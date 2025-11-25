"""
Database migration script to:
1. Add base_currency column to trips table
2. Rename columns:
   - expenses.amount_krw -> expenses.amount_base
   - expense_participants.share_amount_krw -> expense_participants.share_amount_base
   - exchange_rates.rate_to_krw -> exchange_rates.rate_to_base
   - my_budgets.budget_amount_krw -> my_budgets.budget_amount_base

This script should be run after updating the code but before running the application.

Usage:
    python migrate_to_base_currency.py
"""

import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    """Run the migration to support trip-specific base currency."""
    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        # Start transaction
        trans = connection.begin()
        try:
            print("Starting migration to trip-specific base currency...")
            
            # 1. Add base_currency column to trips table (with default value from settings)
            print("\n1. Adding base_currency column to trips table...")
            default_base_currency = getattr(settings, 'FX_BASE_CURRENCY', 'KRW')
            connection.execute(text(f"""
                ALTER TABLE trips 
                ADD COLUMN base_currency VARCHAR(3) NOT NULL DEFAULT '{default_base_currency}'
            """))
            print(f"   ✓ Added base_currency column with default '{default_base_currency}'")
            
            # 2. Rename columns in expenses table
            print("\n2. Renaming columns in expenses table...")
            connection.execute(text("""
                ALTER TABLE expenses 
                CHANGE COLUMN amount_krw amount_base NUMERIC(15, 2) NOT NULL
            """))
            print("   ✓ Renamed amount_krw to amount_base")
            
            # 3. Rename columns in expense_participants table
            print("\n3. Renaming columns in expense_participants table...")
            connection.execute(text("""
                ALTER TABLE expense_participants 
                CHANGE COLUMN share_amount_krw share_amount_base NUMERIC(15, 2) NOT NULL
            """))
            print("   ✓ Renamed share_amount_krw to share_amount_base")
            
            # 4. Rename columns in exchange_rates table
            print("\n4. Renaming columns in exchange_rates table...")
            connection.execute(text("""
                ALTER TABLE exchange_rates 
                CHANGE COLUMN rate_to_krw rate_to_base NUMERIC(15, 6) NOT NULL
            """))
            print("   ✓ Renamed rate_to_krw to rate_to_base")
            
            # 5. Rename columns in my_budgets table
            print("\n5. Renaming columns in my_budgets table...")
            connection.execute(text("""
                ALTER TABLE my_budgets 
                CHANGE COLUMN budget_amount_krw budget_amount_base NUMERIC(15, 2) NOT NULL
            """))
            print("   ✓ Renamed budget_amount_krw to budget_amount_base")
            
            # Commit transaction
            trans.commit()
            print("\n✅ Migration completed successfully!")
            print("\nNext steps:")
            print("1. Restart your backend server")
            print("2. Update existing trips' base_currency if needed (currently set to default)")
            
        except Exception as e:
            trans.rollback()
            print(f"\n❌ Migration failed: {e}")
            print("Transaction rolled back. Database state unchanged.")
            sys.exit(1)

if __name__ == "__main__":
    run_migration()

