"""
Budget model for personal budget tracking.
"""
from sqlalchemy import Column, Numeric, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import BaseModel


class MyBudget(BaseModel):
    """Personal budget model per user per trip."""
    __tablename__ = "my_budgets"
    
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    budget_amount_base = Column(Numeric(15, 2), nullable=False)  # Budget amount in trip's base currency
    
    # Relationships
    trip = relationship("Trip", back_populates="budgets")
    user = relationship("User", back_populates="budgets")
    
    # Unique constraint: one budget per user per trip
    __table_args__ = (
        UniqueConstraint('trip_id', 'user_id', name='uq_trip_user_budget'),
    )

