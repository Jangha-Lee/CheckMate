"""
User model for authentication and user management.
"""
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from app.db.base import BaseModel


class User(BaseModel):
    """User model with immutable username."""
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    trips = relationship("TripParticipant", back_populates="user", cascade="all, delete-orphan")
    expenses_paid = relationship("Expense", foreign_keys="Expense.payer_id", back_populates="payer")
    expense_participants = relationship("ExpenseParticipant", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("MyBudget", back_populates="user", cascade="all, delete-orphan")
    diary_entries = relationship("DiaryEntry", back_populates="user", cascade="all, delete-orphan")
    moods = relationship("DateMood", back_populates="user", cascade="all, delete-orphan")

