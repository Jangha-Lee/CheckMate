"""
Pydantic schemas for Diary entity.
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime


class DiaryPhotoBase(BaseModel):
    """Base diary photo schema."""
    file_name: str
    # Note: memo is stored at DiaryEntry level, not photo level


class DiaryPhotoResponse(DiaryPhotoBase):
    """Schema for diary photo response."""
    id: int
    file_path: str
    order_index: int
    created_at: datetime
    memo: Optional[str] = None  # Always None - memo is stored in DiaryEntry.memo
    
    class Config:
        from_attributes = True


class DiaryEntryBase(BaseModel):
    """Base diary entry schema."""
    date: date
    memo: Optional[str] = None


class DiaryEntryResponse(DiaryEntryBase):
    """Schema for diary entry response."""
    id: int
    trip_id: int
    user_id: int
    username: str
    expense_id: Optional[int] = None
    photos: List[DiaryPhotoResponse] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DiaryEntryCreate(BaseModel):
    """Schema for diary entry creation."""
    date: date
    memo: Optional[str] = None
    expense_id: Optional[int] = None


class PhotoUpload(BaseModel):
    """Schema for photo upload."""
    memo: Optional[str] = None


class PhotoUpdate(BaseModel):
    """Schema for photo update."""
    memo: Optional[str] = None


class MemoCreate(BaseModel):
    """Schema for memo creation."""
    memo: str

