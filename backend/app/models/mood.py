"""
Mood model for daily mood tracking.
"""
from sqlalchemy import Column, String, Date, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import BaseModel


class DateMood(BaseModel):
    """Mood model for one mood emoji per user per date."""
    __tablename__ = "date_moods"
    
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    mood_emoji = Column(String(10), nullable=False)  # Emoji character
    
    # Relationships
    trip = relationship("Trip", back_populates="moods")
    user = relationship("User", back_populates="moods")
    
    # Unique constraint: one mood per user per date per trip
    __table_args__ = (
        UniqueConstraint('trip_id', 'user_id', 'date', name='uq_trip_user_date_mood'),
    )

