"""
Foreign exchange rates routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from app.db.session import get_db
from app.models.user import User
from app.models.exchange_rate import ExchangeRate
from app.schemas.exchange_rate import ExchangeRateResponse
from app.api.dependencies import get_current_user
from app.services.fx_service import get_exchange_rate, get_base_currency

router = APIRouter(prefix="/fx-rates", tags=["fx-rates"])


@router.get("/latest", response_model=ExchangeRateResponse)
async def get_latest_exchange_rate(
    currency: str = "USD",
    trip_id: int = None,
    force_refresh: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the latest (today's) exchange rate for a currency.
    
    Args:
        currency: Currency code (default: USD)
        trip_id: Trip ID (required)
        force_refresh: If True, fetch fresh rate from API even if cached in database.
    """
    if not trip_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="trip_id is required"
        )
    
    # Use today's date for latest rate
    today = date.today()
    
    # If force_refresh, delete existing rate from database
    if force_refresh:
        existing_rate = db.query(ExchangeRate).filter(
            ExchangeRate.trip_id == trip_id,
            ExchangeRate.date == today,
            ExchangeRate.currency == currency.upper()
        ).first()
        if existing_rate:
            db.delete(existing_rate)
            db.commit()
    
    # Get or fetch exchange rate
    try:
        rate_value = get_exchange_rate(trip_id, today, currency, db)
    except ValueError as e:
        # API key missing or API error
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to fetch exchange rate: {str(e)}"
        )
    
    # Get the stored rate record
    rate = db.query(ExchangeRate).filter(
        ExchangeRate.trip_id == trip_id,
        ExchangeRate.date == today,
        ExchangeRate.currency == currency.upper()
    ).first()
    
    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exchange rate not found"
        )
    
    # Get trip's base currency
    from app.models.trip import Trip
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    base_currency = trip.base_currency if trip and hasattr(trip, 'base_currency') else "KRW"
    
    # Build response with base_currency
    return ExchangeRateResponse(
        id=rate.id,
        trip_id=rate.trip_id,
        date=rate.date,
        currency=rate.currency,
        rate_to_base=rate.rate_to_base,
        base_currency=base_currency,
        created_at=rate.created_at
    )


@router.get("/{date}", response_model=ExchangeRateResponse)
async def get_exchange_rate_for_date(
    date: date,
    currency: str = "USD",
    trip_id: int = None,
    force_refresh: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get exchange rate for a specific date and currency.
    
    Args:
        force_refresh: If True, fetch fresh rate from API even if cached in database.
    """
    if not trip_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="trip_id is required"
        )
    
    # If force_refresh, delete existing rate from database
    if force_refresh:
        existing_rate = db.query(ExchangeRate).filter(
            ExchangeRate.trip_id == trip_id,
            ExchangeRate.date == date,
            ExchangeRate.currency == currency.upper()
        ).first()
        if existing_rate:
            db.delete(existing_rate)
            db.commit()
    
    # Get or fetch exchange rate
    try:
        rate_value = get_exchange_rate(trip_id, date, currency, db)
    except ValueError as e:
        # API key missing or API error
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to fetch exchange rate: {str(e)}"
        )
    
    # Get the stored rate record
    rate = db.query(ExchangeRate).filter(
        ExchangeRate.trip_id == trip_id,
        ExchangeRate.date == date,
        ExchangeRate.currency == currency.upper()
    ).first()
    
    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exchange rate not found"
        )
    
    # Get trip's base currency
    from app.models.trip import Trip
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    base_currency = trip.base_currency if trip and hasattr(trip, 'base_currency') else "KRW"
    
    # Build response with base_currency
    return ExchangeRateResponse(
        id=rate.id,
        trip_id=rate.trip_id,
        date=rate.date,
        currency=rate.currency,
        rate_to_base=rate.rate_to_base,
        base_currency=base_currency,
        created_at=rate.created_at
    )

