"""
Trip management routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date, datetime
from app.db.session import get_db
from app.models.user import User
from app.models.trip import Trip, TripParticipant, TripStatus
from app.schemas.trip import (
    TripCreate, TripResponse, TripDetailResponse, 
    ParticipantInvite, TripParticipantResponse
)
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/trips", tags=["trips"])


def check_trip_access(trip_id: int, user_id: int, db: Session) -> Trip:
    """Check if user has access to trip."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    participant = db.query(TripParticipant).filter(
        TripParticipant.trip_id == trip_id,
        TripParticipant.user_id == user_id
    ).first()
    
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this trip"
        )
    
    return trip


@router.post("", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(
    trip_data: TripCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new trip."""
    # Get base_currency from trip_data or use default from settings
    base_currency = trip_data.base_currency if hasattr(trip_data, 'base_currency') and trip_data.base_currency else "KRW"
    from app.core.config import settings
    # Use FX_BASE_CURRENCY as default if trip_data doesn't specify
    if base_currency == "KRW" and hasattr(settings, 'FX_BASE_CURRENCY') and settings.FX_BASE_CURRENCY:
        base_currency = settings.FX_BASE_CURRENCY
    
    # Determine initial status based on dates
    today = date.today()
    if trip_data.start_date > today:
        initial_status = TripStatus.UPCOMING
    elif trip_data.end_date < today:
        initial_status = TripStatus.FINISHED
    else:
        initial_status = TripStatus.ONGOING
    
    new_trip = Trip(
        name=trip_data.name,
        start_date=trip_data.start_date,
        end_date=trip_data.end_date,
        status=initial_status,
        base_currency=base_currency.upper()
    )
    db.add(new_trip)
    db.flush()
    
    # Add creator as participant
    participant = TripParticipant(
        trip_id=new_trip.id,
        user_id=current_user.id,
        is_creator=True
    )
    db.add(participant)
    db.commit()
    db.refresh(new_trip)
    
    return new_trip


@router.get("", response_model=List[TripResponse])
async def list_trips(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all trips for current user."""
    trips = db.query(Trip).join(TripParticipant).filter(
        TripParticipant.user_id == current_user.id
    ).all()
    return trips


@router.get("/{trip_id}", response_model=TripDetailResponse)
async def get_trip(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get trip details."""
    trip = check_trip_access(trip_id, current_user.id, db)
    
    # Get participants
    participants = db.query(TripParticipant).filter(
        TripParticipant.trip_id == trip_id
    ).all()
    
    participant_responses = []
    for p in participants:
        participant_responses.append(TripParticipantResponse(
            id=p.user.id,
            username=p.user.username,
            is_creator=p.is_creator,
            has_settled=p.has_settled
        ))
    
    trip_detail = TripDetailResponse(
        **trip.__dict__,
        participants=participant_responses
    )
    
    return trip_detail


@router.post("/{trip_id}/participants", status_code=status.HTTP_201_CREATED)
async def invite_participant(
    trip_id: int,
    invite: ParticipantInvite,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invite a participant to the trip."""
    trip = check_trip_access(trip_id, current_user.id, db)
    
    # Find user by username
    user = db.query(User).filter(User.username == invite.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already a participant
    existing = db.query(TripParticipant).filter(
        TripParticipant.trip_id == trip_id,
        TripParticipant.user_id == user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a participant"
        )
    
    # Create invitation (user needs to accept)
    participant = TripParticipant(
        trip_id=trip_id,
        user_id=user.id,
        is_creator=False
    )
    db.add(participant)
    db.commit()
    
    return {"message": "Participant invited successfully"}


@router.delete("/{trip_id}/participants/{username}")
async def remove_participant(
    trip_id: int,
    username: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a participant from the trip."""
    trip = check_trip_access(trip_id, current_user.id, db)
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    participant = db.query(TripParticipant).filter(
        TripParticipant.trip_id == trip_id,
        TripParticipant.user_id == user.id
    ).first()
    
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found"
        )
    
    db.delete(participant)
    db.commit()
    
    return {"message": "Participant removed successfully"}


@router.post("/{trip_id}/set_current")
async def set_current_trip(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set trip as current (client-side implementation)."""
    check_trip_access(trip_id, current_user.id, db)
    return {"message": "Trip set as current"}


@router.get("/{trip_id}/status")
async def get_trip_status(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current trip status."""
    trip = check_trip_access(trip_id, current_user.id, db)
    
    today = date.today()
    if trip.start_date > today:
        status = TripStatus.UPCOMING
    elif trip.end_date < today:
        status = TripStatus.FINISHED
    else:
        status = TripStatus.ONGOING
    
    # Update trip status if changed
    if trip.status != status:
        trip.status = status
        db.commit()
    
    return {"status": status.value}


@router.post("/{trip_id}/settle")
async def trigger_settlement(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Press settlement button for a trip."""
    trip = check_trip_access(trip_id, current_user.id, db)
    
    participant = db.query(TripParticipant).filter(
        TripParticipant.trip_id == trip_id,
        TripParticipant.user_id == current_user.id
    ).first()
    
    participant.has_settled = True
    db.commit()
    
    # Check if all participants have settled
    all_participants = db.query(TripParticipant).filter(
        TripParticipant.trip_id == trip_id
    ).all()
    
    if all(p.has_settled for p in all_participants):
        # Trigger settlement calculation
        from app.services.settlement_service import calculate_settlement
        calculate_settlement(trip_id, db)
    
    return {"message": "Settlement triggered"}


@router.get("/{trip_id}/settlement")
async def get_settlement(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get settlement result."""
    trip = check_trip_access(trip_id, current_user.id, db)
    
    from app.models.settlement import SettlementResult
    settlement = db.query(SettlementResult).filter(
        SettlementResult.trip_id == trip_id
    ).order_by(SettlementResult.created_at.desc()).first()
    
    if not settlement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settlement not found"
        )
    
    return settlement


@router.get("/{trip_id}/participants", response_model=List[TripParticipantResponse])
async def get_participants(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get participant list with settlement states."""
    check_trip_access(trip_id, current_user.id, db)
    
    participants = db.query(TripParticipant).filter(
        TripParticipant.trip_id == trip_id
    ).all()
    
    return [
        TripParticipantResponse(
            id=p.user.id,
            username=p.user.username,
            is_creator=p.is_creator,
            has_settled=p.has_settled
        )
        for p in participants
    ]

