"""
Settlement service for automated fair settlement calculation.
"""
from sqlalchemy.orm import Session
from typing import List, Dict
from decimal import Decimal
from app.models.settlement import SettlementResult
from app.models.expense import Expense, ExpenseParticipant
from app.models.trip import Trip
from app.models.user import User


class Transfer:
    """Represents a single transfer between users."""
    def __init__(self, from_user_id: int, to_user_id: int, amount: Decimal):
        self.from_user_id = from_user_id
        self.to_user_id = to_user_id
        self.amount = amount


def calculate_settlement(trip_id: int, db: Session) -> SettlementResult:
    """
    Calculate settlement for a trip using debt minimization algorithm.
    Returns SettlementResult with calculation data.
    """
    # Get all expenses for the trip
    expenses = db.query(Expense).filter(Expense.trip_id == trip_id).all()
    
    # Calculate net balance for each user
    net_balances: Dict[int, Decimal] = {}  # user_id -> net balance (positive = owed, negative = owes)
    
    for expense in expenses:
        # Add what payer paid
        payer_id = expense.payer_id
        if payer_id not in net_balances:
            net_balances[payer_id] = Decimal(0)
        net_balances[payer_id] += expense.amount_base
        
        # Subtract what each participant owes
        participants = db.query(ExpenseParticipant).filter(
            ExpenseParticipant.expense_id == expense.id
        ).all()
        
        for participant in participants:
            user_id = participant.user_id
            if user_id not in net_balances:
                net_balances[user_id] = Decimal(0)
            net_balances[user_id] -= participant.share_amount_base
    
    # Calculate net balances (positive = should receive, negative = should pay)
    # Convert to list of (user_id, balance) tuples
    balances = [(user_id, balance) for user_id, balance in net_balances.items()]
    
    # Minimize transfers using greedy algorithm
    transfers = minimize_transfers(balances)
    
    # Get usernames for response
    user_map = {}
    for user_id in net_balances.keys():
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user_map[user_id] = user.username
    
    # Build calculation data
    calculation_data = {
        "net_balances": {user_map[uid]: float(bal) for uid, bal in net_balances.items()},
        "transfers": [
            {
                "from_user_id": t.from_user_id,
                "from_username": user_map.get(t.from_user_id, ""),
                "to_user_id": t.to_user_id,
                "to_username": user_map.get(t.to_user_id, ""),
                "amount_base": float(t.amount)  # Amount in trip's base currency
            }
            for t in transfers
        ],
        "total_expenses_base": float(sum(exp.amount_base for exp in expenses)),
        "participant_count": len(net_balances)
    }
    
    # Create summary text
    summary_lines = []
    # Get trip's base currency
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    base_currency = trip.base_currency if trip and hasattr(trip, 'base_currency') else "KRW"
    
    summary_lines.append(f"Total expenses: {calculation_data['total_expenses_base']:.2f} {base_currency}")
    summary_lines.append(f"Participants: {calculation_data['participant_count']}")
    summary_lines.append("\nNet balances:")
    for username, balance in calculation_data["net_balances"].items():
        summary_lines.append(f"  {username}: {balance:+.2f} {base_currency}")
    summary_lines.append("\nTransfers:")
    for transfer in calculation_data["transfers"]:
        summary_lines.append(
            f"  {transfer['from_username']} -> {transfer['to_username']}: "
            f"{transfer['amount_base']:.2f} {base_currency}"
        )
    summary = "\n".join(summary_lines)
    
    # Delete old settlement results for this trip (we only need the latest)
    db.query(SettlementResult).filter(
        SettlementResult.trip_id == trip_id
    ).delete()
    
    # Create new settlement result
    settlement = SettlementResult(
        trip_id=trip_id,
        calculation_data=calculation_data,
        summary=summary
    )
    db.add(settlement)
    
    # Mark trip as settled
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if trip:
        trip.is_settled = True
        from app.models.trip import TripStatus
        trip.status = TripStatus.SETTLED
    
    db.commit()
    db.refresh(settlement)
    
    return settlement


def minimize_transfers(balances: List[tuple]) -> List[Transfer]:
    """
    Minimize the number of transfers needed to settle debts.
    Uses a greedy algorithm.
    """
    # Separate creditors (positive balance) and debtors (negative balance)
    creditors = [(uid, bal) for uid, bal in balances if bal > 0]
    debtors = [(uid, -bal) for uid, bal in balances if bal < 0]  # Store as positive for easier calculation
    
    # Sort in descending order
    creditors.sort(key=lambda x: x[1], reverse=True)
    debtors.sort(key=lambda x: x[1], reverse=True)
    
    transfers = []
    cred_idx = 0
    debt_idx = 0
    
    while cred_idx < len(creditors) and debt_idx < len(debtors):
        creditor_id, cred_amount = creditors[cred_idx]
        debtor_id, debt_amount = debtors[debt_idx]
        
        if cred_amount == 0:
            cred_idx += 1
            continue
        if debt_amount == 0:
            debt_idx += 1
            continue
        
        # Transfer the minimum of what's owed and what's needed
        transfer_amount = min(cred_amount, debt_amount)
        transfers.append(Transfer(debtor_id, creditor_id, transfer_amount))
        
        creditors[cred_idx] = (creditor_id, cred_amount - transfer_amount)
        debtors[debt_idx] = (debtor_id, debt_amount - transfer_amount)
        
        if creditors[cred_idx][1] == 0:
            cred_idx += 1
        if debtors[debt_idx][1] == 0:
            debt_idx += 1
    
    return transfers

