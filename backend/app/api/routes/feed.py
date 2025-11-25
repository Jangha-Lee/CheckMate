"""
Image feed routes for photo timeline.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.user import User
from app.models.diary import DiaryPhoto, DiaryEntry
from app.schemas.diary import DiaryPhotoResponse
from app.api.dependencies import get_current_user
from app.api.routes.trips import check_trip_access

router = APIRouter(tags=["feed"])


@router.get("/trips/{trip_id}/feed", response_model=List[DiaryPhotoResponse])
async def get_photo_feed(
    trip_id: int,
    offset: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get photo feed (latest first, infinite scroll)."""
    check_trip_access(trip_id, current_user.id, db)
    
    # Get photos for the trip, ordered by creation date (latest first)
    photos = db.query(DiaryPhoto).join(DiaryEntry).filter(
        DiaryEntry.trip_id == trip_id
    ).order_by(DiaryPhoto.created_at.desc()).offset(offset).limit(limit).all()
    
    return photos


@router.get("/photos/{photo_id}", response_model=DiaryPhotoResponse)
async def get_photo_detail(
    photo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get photo detail (fullscreen, zoom/swipe)."""
    photo = db.query(DiaryPhoto).filter(DiaryPhoto.id == photo_id).first()
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )
    
    # Check trip access
    diary_entry = db.query(DiaryEntry).filter(DiaryEntry.id == photo.diary_entry_id).first()
    if diary_entry:
        check_trip_access(diary_entry.trip_id, current_user.id, db)
    
    return photo

