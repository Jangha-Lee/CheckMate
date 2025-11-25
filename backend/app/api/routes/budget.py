"""
Budget management routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.budget import MyBudget
from app.models.expense import ExpenseParticipant, Expense
from sqlalchemy import func
from app.schemas.budget import BudgetCreate, BudgetResponse, BudgetUpdate, BudgetSummary
from app.api.dependencies import get_current_user
from app.api.routes.trips import check_trip_access
from decimal import Decimal

router = APIRouter(prefix="/budget", tags=["budget"])


@router.get("/{trip_id}", response_model=BudgetResponse)
async def get_budget(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current budget for a trip."""
    check_trip_access(trip_id, current_user.id, db)
    
    budget = db.query(MyBudget).filter(
        MyBudget.trip_id == trip_id,
        MyBudget.user_id == current_user.id
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    return budget


@router.post("/{trip_id}", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_budget(
    trip_id: int,
    budget_data: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set or edit budget for a trip."""
    check_trip_access(trip_id, current_user.id, db)
    
    budget = db.query(MyBudget).filter(
        MyBudget.trip_id == trip_id,
        MyBudget.user_id == current_user.id
    ).first()
    
    if budget:
        budget.budget_amount_base = budget_data.budget_amount_base
    else:
        budget = MyBudget(
            trip_id=trip_id,
            user_id=current_user.id,
            budget_amount_base=budget_data.budget_amount_base
        )
        db.add(budget)
    
    db.commit()
    db.refresh(budget)
    
    return budget


@router.get("/{trip_id}/summary", response_model=BudgetSummary)
async def get_budget_summary(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed budget summary with spending."""
    check_trip_access(trip_id, current_user.id, db)
    
    budget = db.query(MyBudget).filter(
        MyBudget.trip_id == trip_id,
        MyBudget.user_id == current_user.id
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    # Get trip to access base currency
    from app.models.trip import Trip
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    base_currency = trip.base_currency if trip and hasattr(trip, 'base_currency') else "KRW"
    
    # Calculate total spending
    from app.models.expense import Expense
    total_spent = db.query(func.sum(ExpenseParticipant.share_amount_base)).join(
        Expense, ExpenseParticipant.expense_id == Expense.id
    ).filter(
        ExpenseParticipant.user_id == current_user.id,
        Expense.trip_id == trip_id
    ).scalar() or Decimal(0)
    
    remaining = budget.budget_amount_base - total_spent
    fill_ratio = float((total_spent / budget.budget_amount_base * 100) if budget.budget_amount_base > 0 else 0)
    
    # Calculate category-wise spending for this user
    # Get all expenses where this user is a participant
    user_expenses = db.query(Expense).join(
        ExpenseParticipant, Expense.id == ExpenseParticipant.expense_id
    ).filter(
        ExpenseParticipant.user_id == current_user.id,
        Expense.trip_id == trip_id
    ).all()
    
    # Group by category
    category_spending = {}
    category_counts = {}
    uncategorized_spent = Decimal(0)
    uncategorized_count = 0
    
    for expense in user_expenses:
        # Get user's share for this expense
        participant = db.query(ExpenseParticipant).filter(
            ExpenseParticipant.expense_id == expense.id,
            ExpenseParticipant.user_id == current_user.id
        ).first()
        
        if not participant:
            continue
        
        user_share = participant.share_amount_base
        category = expense.category if expense.category else "uncategorized"
        
        if category == "uncategorized" or not category:
            uncategorized_spent += user_share
            uncategorized_count += 1
        else:
            if category not in category_spending:
                category_spending[category] = Decimal(0)
                category_counts[category] = 0
            category_spending[category] += user_share
            category_counts[category] += 1
    
    # Build category items
    from app.schemas.budget import BudgetCategoryItem
    category_items = []
    for category, spent_amount in category_spending.items():
        percentage_of_total = float((spent_amount / total_spent * 100) if total_spent > 0 else 0)
        percentage_of_budget = float((spent_amount / budget.budget_amount_base * 100) if budget.budget_amount_base > 0 else 0)
        
        category_items.append(BudgetCategoryItem(
            category=category,
            spent_amount_base=spent_amount,
            expense_count=category_counts[category],
            percentage_of_total=percentage_of_total,
            percentage_of_budget=percentage_of_budget
        ))
    
    # Sort by spent amount (descending)
    category_items.sort(key=lambda x: x.spent_amount_base, reverse=True)
    
    # Calculate percentages for uncategorized
    uncategorized_percentage_of_total = float((uncategorized_spent / total_spent * 100) if total_spent > 0 else 0)
    uncategorized_percentage_of_budget = float((uncategorized_spent / budget.budget_amount_base * 100) if budget.budget_amount_base > 0 else 0)
    
    return BudgetSummary(
        budget_amount_base=budget.budget_amount_base,
        total_spent_base=total_spent,
        remaining_base=remaining,
        fill_ratio=fill_ratio,
        base_currency=base_currency,
        categories=category_items,
        uncategorized_spent_base=uncategorized_spent,
        uncategorized_count=uncategorized_count
    )

