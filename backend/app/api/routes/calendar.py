"""
Calendar routes for daily views and mood tracking.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Any
from datetime import date
from app.db.session import get_db
from app.models.user import User
from app.models.expense import Expense
from app.models.diary import DiaryEntry, DiaryPhoto
from app.models.mood import DateMood
from sqlalchemy import distinct
from app.schemas.mood import MoodCreate, MoodResponse
from app.schemas.diary import DiaryEntryResponse, DiaryPhotoResponse
from app.api.dependencies import get_current_user
from app.api.routes.trips import check_trip_access

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/{trip_id}/days")
async def get_daily_indicators(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get daily indicators (expenses, diary, moods) for calendar view."""
    check_trip_access(trip_id, current_user.id, db)
    
    # Get all dates with expenses, diary entries, and moods
    expense_dates = db.query(distinct(Expense.date)).filter(
        Expense.trip_id == trip_id
    ).all()
    
    diary_dates = db.query(distinct(DiaryEntry.date)).filter(
        DiaryEntry.trip_id == trip_id
    ).all()
    
    mood_dates = db.query(distinct(DateMood.date)).filter(
        DateMood.trip_id == trip_id
    ).all()
    
    # Combine all dates
    all_dates = set()
    for d in expense_dates:
        all_dates.add(d[0])
    for d in diary_dates:
        all_dates.add(d[0])
    for d in mood_dates:
        all_dates.add(d[0])
    
    # Build response
    indicators = []
    for d in sorted(all_dates):
        has_expense = d in [x[0] for x in expense_dates]
        has_diary = d in [x[0] for x in diary_dates]
        has_mood = d in [x[0] for x in mood_dates]
        
        indicators.append({
            "date": d.isoformat(),
            "has_expense": has_expense,
            "has_diary": has_diary,
            "has_mood": has_mood
        })
    
    return indicators


@router.get("/{trip_id}/{date}")
async def get_daily_data(
    trip_id: int,
    date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get full daily data (expenses, diary entries with photos and memos, moods)."""
    check_trip_access(trip_id, current_user.id, db)
    
    # Get expenses with relationships
    expenses = db.query(Expense).options(
        joinedload(Expense.payer),
        joinedload(Expense.participants)
    ).filter(
        Expense.trip_id == trip_id,
        Expense.date == date
    ).all()
    
    # Sort expenses: if time exists, sort by time (ascending), else by display_order (ascending)
    # Group expenses by whether they have time or not, then sort within each group
    expenses_with_time = [e for e in expenses if e.time is not None]
    expenses_without_time = [e for e in expenses if e.time is None]
    
    # Sort expenses with time by time (ascending)
    expenses_with_time.sort(key=lambda e: (e.time, e.display_order, e.id))
    # Sort expenses without time by display_order (ascending)
    expenses_without_time.sort(key=lambda e: (e.display_order, e.id))
    
    # Combine: expenses with time first (sorted by time), then expenses without time (sorted by display_order)
    expenses = expenses_with_time + expenses_without_time
    
    # Get diary entries with photos (both expense-linked and date-based)
    diary_entries = db.query(DiaryEntry).options(
        joinedload(DiaryEntry.user),
        joinedload(DiaryEntry.photos)
    ).filter(
        DiaryEntry.trip_id == trip_id,
        DiaryEntry.date == date
    ).all()
    
    # Get moods
    moods = db.query(DateMood).options(
        joinedload(DateMood.user)
    ).filter(
        DateMood.trip_id == trip_id,
        DateMood.date == date
    ).all()
    
    # Get trip's base currency
    from app.models.trip import Trip
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    base_currency = trip.base_currency if trip and hasattr(trip, 'base_currency') else "KRW"
    
    # Build expense responses
    from app.schemas.expense import ExpenseResponse, ExpenseParticipantResponse
    expense_responses = []
    for expense in expenses:
        participant_responses = []
        for ep in expense.participants:
            participant_responses.append(ExpenseParticipantResponse(
                user_id=ep.user_id,
                username=ep.user.username if ep.user else f"User {ep.user_id}",
                share_amount_base=ep.share_amount_base,
                base_currency=base_currency
            ))
        
        expense_responses.append(ExpenseResponse(
            id=expense.id,
            trip_id=expense.trip_id,
            payer_id=expense.payer_id,
            payer_username=expense.payer.username if expense.payer else f"User {expense.payer_id}",
            date=expense.date,
            time=expense.time,
            amount=expense.amount,
            currency=expense.currency,
            amount_base=expense.amount_base,
            base_currency=base_currency,
            description=expense.description,
            category=expense.category,
            display_order=getattr(expense, 'display_order', 0),
            participants=participant_responses,
            created_at=expense.created_at,
            updated_at=expense.updated_at
        ))
    
    # Build diary entry responses with photos
    diary_responses = []
    for diary_entry in diary_entries:
        # Build photo responses (memo is always None at photo level)
        photo_responses = [
            DiaryPhotoResponse(
                id=p.id,
                file_path=p.file_path,
                file_name=p.file_name,
                memo=None,  # Always None - memo is stored in DiaryEntry.memo
                order_index=p.order_index,
                created_at=p.created_at
            )
            for p in diary_entry.photos
        ]
        
        diary_responses.append(DiaryEntryResponse(
            id=diary_entry.id,
            trip_id=diary_entry.trip_id,
            user_id=diary_entry.user_id,
            username=diary_entry.user.username if diary_entry.user else f"User {diary_entry.user_id}",
            date=diary_entry.date,
            expense_id=diary_entry.expense_id,
            memo=diary_entry.memo,
            photos=photo_responses,
            created_at=diary_entry.created_at,
            updated_at=diary_entry.updated_at
        ))
    
    # Build mood responses
    from app.schemas.mood import MoodResponse
    mood_responses = []
    for mood in moods:
        mood_responses.append(MoodResponse(
            id=mood.id,
            trip_id=mood.trip_id,
            user_id=mood.user_id,
            username=mood.user.username if mood.user else f"User {mood.user_id}",
            date=mood.date,
            mood_emoji=mood.mood_emoji,
            created_at=mood.created_at,
            updated_at=mood.updated_at
        ))
    
    return {
        "date": date.isoformat(),
        "expenses": expense_responses,
        "diary_entries": diary_responses,
        "moods": mood_responses
    }


@router.post("/{trip_id}/{date}/mood", response_model=MoodResponse, status_code=status.HTTP_201_CREATED)
async def set_mood(
    trip_id: int,
    date: date,
    mood_data: MoodCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set or update mood emoji for a date."""
    check_trip_access(trip_id, current_user.id, db)
    
    # Check if mood already exists
    existing_mood = db.query(DateMood).filter(
        DateMood.trip_id == trip_id,
        DateMood.user_id == current_user.id,
        DateMood.date == date
    ).first()
    
    if existing_mood:
        existing_mood.mood_emoji = mood_data.mood_emoji
        db.commit()
        
        # Reload with user relationship
        mood = db.query(DateMood).options(
            joinedload(DateMood.user)
        ).filter(DateMood.id == existing_mood.id).first()
    else:
        new_mood = DateMood(
            trip_id=trip_id,
            user_id=current_user.id,
            date=date,
            mood_emoji=mood_data.mood_emoji
        )
        db.add(new_mood)
        db.commit()
        
        # Reload with user relationship
        mood = db.query(DateMood).options(
            joinedload(DateMood.user)
        ).filter(DateMood.id == new_mood.id).first()
    
    # Build response with username
    return MoodResponse(
        id=mood.id,
        trip_id=mood.trip_id,
        user_id=mood.user_id,
        username=mood.user.username,
        date=mood.date,
        mood_emoji=mood.mood_emoji,
        created_at=mood.created_at,
        updated_at=mood.updated_at
    )

