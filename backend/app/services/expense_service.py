"""
Expense service for expense-related business logic.
"""
from sqlalchemy.orm import Session
from datetime import date
from decimal import Decimal
from app.models.expense import Expense, ExpenseParticipant
from app.services.fx_service import get_exchange_rate, convert_to_base


def create_expense_with_participants(
    trip_id: int,
    payer_id: int,
    expense_date: date,
    amount: Decimal,
    currency: str,
    participant_ids: list,
    description: str = None,
    category: str = None,
    db: Session = None
) -> Expense:
    """Create an expense with participants and calculate shares."""
    # Get exchange rate and convert to KRW
    rate = get_exchange_rate(trip_id, expense_date, currency, db)
    # Get trip to access base_currency
    from app.models.trip import Trip
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    base_currency = trip.base_currency if trip else "KRW"
    amount_base = convert_to_base(amount, currency, rate, base_currency=base_currency)
    
    # Create expense
    expense = Expense(
        trip_id=trip_id,
        payer_id=payer_id,
        date=expense_date,
        amount=amount,
        currency=currency,
        amount_base=amount_base,
        description=description,
        category=category
    )
    db.add(expense)
    db.flush()
    
    # Calculate share per participant (round to integer)
    if participant_ids:
        share_per_person = Decimal(int(round(amount_base / len(participant_ids))))
        for user_id in participant_ids:
            participant = ExpenseParticipant(
                expense_id=expense.id,
                user_id=user_id,
                share_amount_base=share_per_person
            )
            db.add(participant)
    else:
        # If no participants specified, payer pays all
        participant = ExpenseParticipant(
            expense_id=expense.id,
            user_id=payer_id,
            share_amount_base=amount_base
        )
        db.add(participant)
    
    db.commit()
    db.refresh(expense)
    
    return expense


def update_expense_participants(
    expense_id: int,
    participant_ids: list,
    db: Session
):
    """Update participants for an expense."""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise ValueError("Expense not found")
    
    # Delete existing participants
    db.query(ExpenseParticipant).filter(
        ExpenseParticipant.expense_id == expense_id
    ).delete()
    
    # Add new participants (round to integer)
    if participant_ids:
        share_per_person = Decimal(int(round(expense.amount_base / len(participant_ids))))
        for user_id in participant_ids:
            participant = ExpenseParticipant(
                expense_id=expense_id,
                user_id=user_id,
                share_amount_base=share_per_person
            )
            db.add(participant)
    
    db.commit()

