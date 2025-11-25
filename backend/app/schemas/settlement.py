"""
Pydantic schemas for Settlement entity.
"""
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
from decimal import Decimal


class Transfer(BaseModel):
    """Schema for a single transfer in settlement."""
    from_user_id: int
    from_username: str
    to_user_id: int
    to_username: str
    amount_base: Decimal  # Transfer amount in trip's base currency


class SettlementResultResponse(BaseModel):
    """Schema for settlement result response."""
    id: int
    trip_id: int
    calculation_data: Dict[str, Any]
    summary: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class SettlementSummary(BaseModel):
    """Schema for settlement summary."""
    net_balances: Dict[str, Decimal]  # username -> net balance (in trip's base currency)
    transfers: List[Transfer]
    total_expenses_base: Decimal  # Total expenses in trip's base currency
    participant_count: int

