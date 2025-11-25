"""
Settlement management routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.settlement import SettlementResult
from app.schemas.settlement import SettlementResultResponse, SettlementSummary
from app.api.dependencies import get_current_user
from app.api.routes.trips import check_trip_access

router = APIRouter(prefix="/settlement", tags=["settlement"])


@router.post("/{trip_id}/trigger")
async def trigger_settlement(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger settlement calculation for a trip."""
    check_trip_access(trip_id, current_user.id, db)
    
    from app.services.settlement_service import calculate_settlement
    result = calculate_settlement(trip_id, db)
    
    return {"message": "Settlement calculated successfully", "settlement_id": result.id}


@router.get("/{trip_id}/result", response_model=SettlementResultResponse)
async def get_settlement_result(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get settlement result for a trip."""
    check_trip_access(trip_id, current_user.id, db)
    
    # Since we only keep the latest settlement, just get the first (and only) one
    settlement = db.query(SettlementResult).filter(
        SettlementResult.trip_id == trip_id
    ).first()
    
    if not settlement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settlement result not found"
        )
    
    return settlement

