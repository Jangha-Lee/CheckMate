"""
Expense model for tracking spending.
"""
from sqlalchemy import Column, String, Numeric, Date, Time, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from app.db.base import BaseModel


class Expense(BaseModel):
    """Expense model representing a single spending event."""
    __tablename__ = "expenses"
    
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False, index=True)
    payer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    time = Column(Time, nullable=True)  # Optional time for expense ordering
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="KRW")
    amount_base = Column(Numeric(15, 2), nullable=False)  # Normalized to trip's base currency
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    display_order = Column(Integer, nullable=False, default=1, index=True)  # Order within the same date (1, 2, 3... smaller = top)
    
    # Relationships
    trip = relationship("Trip", back_populates="expenses")
    payer = relationship("User", foreign_keys=[payer_id], back_populates="expenses_paid")
    participants = relationship("ExpenseParticipant", back_populates="expense", cascade="all, delete-orphan")
    diary_entry = relationship("DiaryEntry", back_populates="expense", uselist=False)


class ExpenseParticipant(BaseModel):
    """Junction table for Expense and User many-to-many relationship."""
    __tablename__ = "expense_participants"
    
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    share_amount_base = Column(Numeric(15, 2), nullable=False)  # User's share in trip's base currency
    
    # Relationships
    expense = relationship("Expense", back_populates="participants")
    user = relationship("User", back_populates="expense_participants")

