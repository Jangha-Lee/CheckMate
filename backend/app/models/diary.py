"""
Diary model for photos and memos.
"""
from sqlalchemy import Column, String, Date, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.db.base import BaseModel


class DiaryEntry(BaseModel):
    """Diary entry model for photos and memos per date."""
    __tablename__ = "diary_entries"
    
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=True, index=True)
    memo = Column(Text, nullable=True)
    
    # Relationships
    trip = relationship("Trip", back_populates="diary_entries")
    user = relationship("User", back_populates="diary_entries")
    expense = relationship("Expense", back_populates="diary_entry")
    photos = relationship("DiaryPhoto", back_populates="diary_entry", cascade="all, delete-orphan")


class DiaryPhoto(BaseModel):
    """Photo model linked to diary entries."""
    __tablename__ = "diary_photos"
    
    diary_entry_id = Column(Integer, ForeignKey("diary_entries.id"), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    memo = Column(Text, nullable=True)
    order_index = Column(Integer, default=0, nullable=False)
    
    # Relationships
    diary_entry = relationship("DiaryEntry", back_populates="photos")

