"""
OCR service routes for expense extraction.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.expense import OCRExpensePreview
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/ocr", tags=["ocr"])


@router.post("/parse", response_model=List[OCRExpensePreview])
async def parse_expense_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload image for OCR parsing and return ALL provisional expense data found in the image."""
    from app.services.ocr_service import parse_expense_image
    
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPEG and PNG are supported."
        )
    
    # Parse image (does not parse date - only amount, currency, description)
    # Date should be provided by client when creating the expense
    results = await parse_expense_image(file, None, db)
    
    return results

