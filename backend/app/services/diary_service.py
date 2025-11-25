"""
Diary service for diary-related business logic.
"""
from sqlalchemy.orm import Session
from datetime import date
from app.models.diary import DiaryEntry, DiaryPhoto
from typing import List, Optional


def get_diary_entry_for_date(
    trip_id: int,
    user_id: int,
    entry_date: date,
    db: Session
) -> Optional[DiaryEntry]:
    """Get or create diary entry for a specific date."""
    diary_entry = db.query(DiaryEntry).filter(
        DiaryEntry.trip_id == trip_id,
        DiaryEntry.user_id == user_id,
        DiaryEntry.date == entry_date
    ).first()
    
    return diary_entry


def create_diary_entry(
    trip_id: int,
    user_id: int,
    entry_date: date,
    memo: Optional[str] = None,
    expense_id: Optional[int] = None,
    db: Session = None
) -> DiaryEntry:
    """Create a new diary entry."""
    diary_entry = DiaryEntry(
        trip_id=trip_id,
        user_id=user_id,
        date=entry_date,
        memo=memo,
        expense_id=expense_id
    )
    db.add(diary_entry)
    db.commit()
    db.refresh(diary_entry)
    
    return diary_entry


def get_photos_for_entry(
    diary_entry_id: int,
    db: Session
) -> List[DiaryPhoto]:
    """Get all photos for a diary entry."""
    photos = db.query(DiaryPhoto).filter(
        DiaryPhoto.diary_entry_id == diary_entry_id
    ).order_by(DiaryPhoto.order_index).all()
    
    return photos


def count_photos_for_user_date(
    trip_id: int,
    user_id: int,
    entry_date: date,
    db: Session
) -> int:
    """Count photos for a user on a specific date."""
    diary_entry = get_diary_entry_for_date(trip_id, user_id, entry_date, db)
    
    if not diary_entry:
        return 0
    
    return db.query(DiaryPhoto).filter(
        DiaryPhoto.diary_entry_id == diary_entry.id
    ).count()


def cleanup_old_photos(trip_id: int, max_photos: int = 50, db: Session = None):
    """
    Cleanup old photos when limit is exceeded.
    Keeps the most recent photos, deletes the oldest.
    """
    # Get all photos for the trip
    photos = db.query(DiaryPhoto).join(DiaryEntry).filter(
        DiaryEntry.trip_id == trip_id
    ).order_by(DiaryPhoto.created_at.desc()).all()
    
    if len(photos) > max_photos:
        # Delete oldest photos
        photos_to_delete = photos[max_photos:]
        for photo in photos_to_delete:
            # Delete file
            import os
            if os.path.exists(photo.file_path):
                os.remove(photo.file_path)
            db.delete(photo)
        
        db.commit()

