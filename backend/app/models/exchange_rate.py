"""
Exchange rate model for currency conversion.
"""
from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import BaseModel


class ExchangeRate(BaseModel):
    """Exchange rate model for daily currency to trip's base currency conversion."""
    __tablename__ = "exchange_rates"
    
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    currency = Column(String(3), nullable=False)
    rate_to_base = Column(Numeric(15, 6), nullable=False)  # Rate to trip's base currency (1 currency = rate_to_base base_currency)
    
    # Relationships
    trip = relationship("Trip", back_populates="exchange_rates")
    
    # Unique constraint: one rate per currency per date per trip
    __table_args__ = (
        UniqueConstraint('trip_id', 'date', 'currency', name='uq_trip_date_currency'),
    )

