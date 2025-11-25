"""
Pydantic schemas for Mood entity.
"""
from pydantic import BaseModel
from datetime import date, datetime


class MoodBase(BaseModel):
    """Base mood schema."""
    date: date
    mood_emoji: str


class MoodCreate(MoodBase):
    """Schema for mood creation."""
    pass


class MoodUpdate(BaseModel):
    """Schema for mood update."""
    mood_emoji: str


class MoodResponse(MoodBase):
    """Schema for mood response."""
    id: int
    trip_id: int
    user_id: int
    username: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

