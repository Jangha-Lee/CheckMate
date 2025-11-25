"""
Pydantic schemas for Expense entity.
"""
from pydantic import BaseModel
from typing import List, Optional, Union
from datetime import date, datetime, time as dt_time
from decimal import Decimal


class ExpenseBase(BaseModel):
    """Base expense schema."""
    date: date
    time: Optional[dt_time] = None
    amount: Decimal
    currency: str = "KRW"
    description: Optional[str] = None
    category: Optional[str] = None


class ExpenseCreate(BaseModel):
    """Schema for expense creation."""
    # Date comes from URL path, but can optionally be provided in body for validation
    date: Optional[date] = None
    time: Optional[dt_time] = None
    amount: Decimal
    currency: str = "KRW"
    description: Optional[str] = None
    category: Optional[str] = None
    participant_ids: List[int]  # User IDs who share this expense


class ExpenseUpdate(BaseModel):
    """Schema for expense update."""
    time: Optional[dt_time] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    participant_ids: Optional[List[int]] = None
    display_order: Optional[int] = None  # Order within the same date


class ExpenseParticipantResponse(BaseModel):
    """Schema for expense participant response."""
    user_id: int
    username: str
    share_amount_base: Decimal  # User's share in trip's base currency
    base_currency: str  # Trip's base currency
    
    class Config:
        from_attributes = True


class ExpenseResponse(ExpenseBase):
    """Schema for expense response."""
    id: int
    trip_id: int
    payer_id: int
    payer_username: str
    amount_base: Decimal  # Amount in trip's base currency
    base_currency: str  # Trip's base currency
    display_order: int = 0
    participants: List[ExpenseParticipantResponse] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OCRExpensePreview(BaseModel):
    """Schema for OCR expense preview before saving."""
    amount: Decimal
    currency: str
    description: Optional[str] = None
    time: Optional[dt_time] = None  # Optional time extracted from OCR
    date: Optional[date] = None  # Always null - use date from URL
    
    model_config = {"from_attributes": True}


class CategoryExpenseItem(BaseModel):
    """Schema for category expense item in summary."""
    category: str
    total_amount_base: Decimal  # Total amount spent in this category (trip's base currency)
    expense_count: int  # Number of expenses in this category
    percentage: float  # Percentage of total expenses (0-100)


class CategorySummaryResponse(BaseModel):
    """Schema for category summary response."""
    trip_id: int
    base_currency: str  # Trip's base currency
    total_expenses_base: Decimal  # Total expenses in trip's base currency
    categories: List[CategoryExpenseItem]  # Category-wise breakdown
    uncategorized_amount_base: Decimal  # Total amount for expenses without category
    uncategorized_count: int  # Number of expenses without category

