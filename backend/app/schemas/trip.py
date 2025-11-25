"""
Pydantic schemas for Trip entity.
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
from app.models.trip import TripStatus


class TripBase(BaseModel):
    """Base trip schema."""
    name: str
    start_date: date
    end_date: date
    base_currency: str = "KRW"  # Base currency for this trip (default: KRW)


class TripCreate(TripBase):
    """Schema for trip creation."""
    pass


class TripUpdate(BaseModel):
    """Schema for trip update."""
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    base_currency: Optional[str] = None  # Base currency for this trip


class TripResponse(TripBase):
    """Schema for trip response."""
    id: int
    status: TripStatus
    is_settled: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TripParticipantResponse(BaseModel):
    """Schema for trip participant response."""
    id: int
    username: str
    is_creator: bool
    has_settled: bool
    
    class Config:
        from_attributes = True


class TripDetailResponse(TripResponse):
    """Schema for detailed trip response with participants."""
    participants: List[TripParticipantResponse] = []


class ParticipantInvite(BaseModel):
    """Schema for participant invitation."""
    username: str

