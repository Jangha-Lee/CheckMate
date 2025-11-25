"""
Main API router that includes all route modules.
"""
from fastapi import APIRouter
from app.api.routes import (
    auth, users, trips, expenses, diary, 
    budget, settlements, ocr, calendar, fx_rates, feed
)

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(trips.router)
api_router.include_router(expenses.router)
api_router.include_router(diary.router)
api_router.include_router(budget.router)
api_router.include_router(settlements.router)
api_router.include_router(ocr.router)
api_router.include_router(calendar.router)
api_router.include_router(fx_rates.router)
api_router.include_router(feed.router)

