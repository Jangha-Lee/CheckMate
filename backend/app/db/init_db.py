"""
Database initialization script.
"""
from app.db.session import engine, init_db
from app.db.base import Base

# Import all models so SQLAlchemy can register them
from app.models import (
    User, Trip, TripParticipant, Expense, ExpenseParticipant,
    DiaryEntry, DiaryPhoto, ExchangeRate, DateMood, MyBudget, SettlementResult
)

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")

