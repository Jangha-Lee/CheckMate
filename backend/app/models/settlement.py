"""
Settlement model for automated fair settlement.
"""
from sqlalchemy import Column, Text, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship
from app.db.base import BaseModel


class SettlementResult(BaseModel):
    """Settlement result model storing calculation results."""
    __tablename__ = "settlement_results"
    
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False, index=True)
    calculation_data = Column(JSON, nullable=False)  # Stores net balances, transfers, etc.
    summary = Column(Text, nullable=True)
    
    # Relationships
    trip = relationship("Trip", back_populates="settlement_results")

