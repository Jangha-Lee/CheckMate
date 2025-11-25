"""
Pydantic schemas for ExchangeRate entity.
"""
from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal


class ExchangeRateBase(BaseModel):
    """Base exchange rate schema."""
    date: date
    currency: str
    rate_to_base: Decimal  # Rate to trip's base currency (1 currency = rate_to_base base_currency)


class ExchangeRateCreate(ExchangeRateBase):
    """Schema for exchange rate creation."""
    trip_id: int


class ExchangeRateResponse(ExchangeRateBase):
    """Schema for exchange rate response."""
    id: int
    trip_id: int
    base_currency: str  # Trip's base currency
    created_at: datetime
    
    class Config:
        from_attributes = True

