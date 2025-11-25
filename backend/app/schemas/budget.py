"""
Pydantic schemas for Budget entity.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class BudgetBase(BaseModel):
    """Base budget schema."""
    budget_amount_base: Decimal  # Budget amount in trip's base currency


class BudgetCreate(BudgetBase):
    """Schema for budget creation."""
    pass


class BudgetUpdate(BaseModel):
    """Schema for budget update."""
    budget_amount_base: Optional[Decimal] = None


class BudgetResponse(BudgetBase):
    """Schema for budget response."""
    id: int
    trip_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BudgetCategoryItem(BaseModel):
    """Schema for category spending item in budget summary."""
    category: str
    spent_amount_base: Decimal  # Amount spent in this category (trip's base currency)
    expense_count: int  # Number of expenses in this category
    percentage_of_total: float  # Percentage of total spending (0-100)
    percentage_of_budget: float  # Percentage of budget (0-100)


class BudgetSummary(BaseModel):
    """Schema for budget summary with spending details."""
    budget_amount_base: Decimal  # Budget amount in trip's base currency
    total_spent_base: Decimal  # Total spent in trip's base currency
    remaining_base: Decimal  # Remaining in trip's base currency
    fill_ratio: float  # Percentage of budget used
    base_currency: str  # Trip's base currency
    categories: List[BudgetCategoryItem] = []  # Category-wise spending breakdown
    uncategorized_spent_base: Decimal = Decimal(0)  # Amount spent without category
    uncategorized_count: int = 0  # Number of expenses without category

