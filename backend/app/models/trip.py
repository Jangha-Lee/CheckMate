"""
Trip model for group travel management.
"""
from sqlalchemy import Column, String, Date, Boolean, Enum as SQLEnum, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.db.base import BaseModel
import enum


class TripStatus(str, enum.Enum):
    """Trip status enumeration."""
    UPCOMING = "Upcoming"
    ONGOING = "Ongoing"
    FINISHED = "Finished"
    SETTLED = "Settled"


class Trip(BaseModel):
    """Trip model representing a group travel event."""
    __tablename__ = "trips"
    
    name = Column(String(200), nullable=False)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    status = Column(SQLEnum(TripStatus), default=TripStatus.UPCOMING, nullable=False)
    is_settled = Column(Boolean, default=False, nullable=False)
    base_currency = Column(String(3), nullable=False, default="KRW")  # Base currency for this trip
    
    # Relationships
    participants = relationship("TripParticipant", back_populates="trip", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="trip", cascade="all, delete-orphan")
    diary_entries = relationship("DiaryEntry", back_populates="trip", cascade="all, delete-orphan")
    exchange_rates = relationship("ExchangeRate", back_populates="trip", cascade="all, delete-orphan")
    settlement_results = relationship("SettlementResult", back_populates="trip", cascade="all, delete-orphan")
    budgets = relationship("MyBudget", back_populates="trip", cascade="all, delete-orphan")
    moods = relationship("DateMood", back_populates="trip", cascade="all, delete-orphan")


class TripParticipant(BaseModel):
    """Junction table for Trip and User many-to-many relationship."""
    __tablename__ = "trip_participants"
    
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_creator = Column(Boolean, default=False, nullable=False)
    has_settled = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    trip = relationship("Trip", back_populates="participants")
    user = relationship("User", back_populates="trips")

