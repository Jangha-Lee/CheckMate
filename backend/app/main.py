"""
FastAPI entrypoint for Checkmate backend application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.router import api_router
import os

app = FastAPI(
    title="Checkmate API",
    description="Backend API for group travel management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
# This serves files from app/static at /static URL path
static_dir = settings.UPLOAD_DIR
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Checkmate API is running"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

