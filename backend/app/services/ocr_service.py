"""
OCR service for expense extraction from images.
Supports multiple OCR providers: OCR.space (free), Google Cloud Vision, etc.
"""
import logging
from fastapi import UploadFile
from sqlalchemy.orm import Session
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
import httpx
import os
import base64
import re
from urllib.parse import urlparse
from app.core.config import settings
from app.schemas.expense import OCRExpensePreview

logger = logging.getLogger(__name__)


async def parse_expense_image(
    file: UploadFile,
    trip_id: Optional[int],
    db: Session,
    target_date: Optional[date] = None
) -> List[OCRExpensePreview]:
    """
    Parse expense image using OCR API.
    Returns provisional expense data for preview (amount, currency, description).
    Note: Date is not parsed from OCR - always use URL date parameter.
    """
    # Save file temporarily
    temp_dir = os.path.join(settings.UPLOAD_DIR, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    temp_path = os.path.join(temp_dir, file.filename)
    with open(temp_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    try:
        # Read file content for API
        with open(temp_path, "rb") as f:
            file_content = f.read()
        
        # Call appropriate OCR provider
        ocr_provider = getattr(settings, 'OCR_PROVIDER', 'ocrspace')
        
        if ocr_provider == "openai_vision":
            # OpenAI Vision directly extracts structured payment records
            parsed_expenses = await _ocr_openai_vision(file_content, trip_id, target_date)
        else:
            # Traditional OCR: extract text first, then parse
            if ocr_provider == "ocrspace":
                text = await _ocr_ocrspace(file_content, file.filename)
            elif ocr_provider == "google_vision":
                text = await _ocr_google_vision(file_content)
            elif ocr_provider == "naver_clova":
                text = await _ocr_naver_clova(file_content)
            else:
                # Fallback to OCR.space
                text = await _ocr_ocrspace(file_content, file.filename)
            
            # Parse extracted text to extract ALL expense data
            parsed_expenses = _parse_expense_text(text)
        
        # Convert list of dicts to list of OCRExpensePreview
        previews = []
        for parsed_data in parsed_expenses:
            amount = parsed_data.get("amount")
            if amount is None:
                amount = Decimal(0)
                logger.warning(f"No amount found in parsed expense: {parsed_data}")
            
            currency = parsed_data.get("currency") or "KRW"
            description = parsed_data.get("description")
            time_str = parsed_data.get("time")
            
            # Parse time string to time object
            expense_time = None
            if time_str:
                try:
                    from datetime import time as dt_time
                    # Handle various time formats: "HH:MM", "HH:MM:SS", "HHMM"
                    time_str_clean = time_str.strip()
                    if ':' in time_str_clean:
                        parts = time_str_clean.split(':')
                        if len(parts) >= 2:
                            hour = int(parts[0])
                            minute = int(parts[1])
                            second = int(parts[2]) if len(parts) > 2 else 0
                            expense_time = dt_time(hour, minute, second)
                    elif len(time_str_clean) >= 4:
                        # Format like "1430" -> 14:30
                        hour = int(time_str_clean[:2])
                        minute = int(time_str_clean[2:4])
                        expense_time = dt_time(hour, minute, 0)
                except (ValueError, IndexError) as e:
                    logger.debug(f"Failed to parse time '{time_str}': {e}")
            
            # Build preview dict, only including time if it's not None
            preview_dict = {
                "amount": amount,
                "currency": currency,
                "description": description,
                "date": None  # Date comes from URL parameter, not OCR
            }
            if expense_time is not None:
                preview_dict["time"] = expense_time
            
            preview = OCRExpensePreview(**preview_dict)
            previews.append(preview)
        
        # If no expenses found, return at least one empty preview
        if not previews:
            previews.append(OCRExpensePreview(
                amount=Decimal(0),
                currency="KRW",
                description=None,
                date=None
            ))
        
        return previews
    
    except Exception as e:
        import traceback
        logger.error(f"OCR parsing error: {e}", exc_info=True)
        # Fallback: return basic structure if OCR fails
        return [OCRExpensePreview(
            amount=Decimal(0),
            currency="KRW",
            description=None,
            date=None
        )]
    
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


async def _ocr_ocrspace(file_content: bytes, filename: str) -> str:
    """
    Use OCR.space API (free tier: 25,000 requests/month).
    Get API key: https://ocr.space/ocrapi/freekey
    """
    api_key = getattr(settings, 'OCR_API_KEY', '')
    
    # OCR.space API endpoint
    api_url = "https://api.ocr.space/parse/image"
    
    # Prepare request
    files = {
        "file": (filename, file_content)
    }
    data = {
        "apikey": api_key if api_key else "helloworld",  # Free tier key
        "language": "eng",  # English
        "isOverlayRequired": False,
        "detectOrientation": True,
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(api_url, files=files, data=data, timeout=30.0)
        response.raise_for_status()
        result = response.json()
        
        # Extract text from OCR.space response
        if result.get("OCRExitCode") == 1:
            parsed_results = result.get("ParsedResults", [])
            if parsed_results:
                return parsed_results[0].get("ParsedText", "")
        
        # If parsing failed, try to get error message
        error_message = result.get("ErrorMessage", ["Unknown error"])
        raise Exception(f"OCR.space error: {error_message[0] if error_message else 'Unknown error'}")


async def _ocr_google_vision(file_content: bytes) -> str:
    """
    Use Google Cloud Vision API.
    Requires: GOOGLE_APPLICATION_CREDENTIALS or API key
    Documentation: https://cloud.google.com/vision/docs
    """
    api_key = getattr(settings, 'OCR_API_KEY', '')
    
    if not api_key:
        raise Exception("Google Vision API key not configured")
    
    # Google Vision API endpoint
    api_url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
    
    # Encode image to base64
    image_base64 = base64.b64encode(file_content).decode('utf-8')
    
    # Prepare request body
    request_body = {
        "requests": [{
            "image": {
                "content": image_base64
            },
            "features": [{
                "type": "TEXT_DETECTION"
            }]
        }]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(api_url, json=request_body, timeout=30.0)
        response.raise_for_status()
        result = response.json()
        
        # Extract text from Google Vision response
        if "responses" in result and len(result["responses"]) > 0:
            text_annotations = result["responses"][0].get("textAnnotations", [])
            if text_annotations:
                return text_annotations[0].get("description", "")
        
        return ""


async def _ocr_naver_clova(file_content: bytes) -> str:
    """
    Use Naver Clova OCR API.
    Requires: NAVER_CLOVA_API_URL and NAVER_CLOVA_SECRET_KEY in settings
    Documentation: https://www.ncloud.com/product/aiService/ocr
    
    Naver Clova OCR returns structured data with fields, which is perfect for
    parsing payment records like "MERCHANT - A$ X.XX" format.
    """
    import time
    
    api_url = getattr(settings, 'NAVER_CLOVA_API_URL', '')
    secret_key = getattr(settings, 'NAVER_CLOVA_SECRET_KEY', '')
    
    if not api_url or not secret_key:
        raise Exception("Naver Clova OCR API URL and Secret Key must be configured. Set NAVER_CLOVA_API_URL and NAVER_CLOVA_SECRET_KEY in .env file")
    
    import uuid
    import json
    
    # Detect image format from file content
    image_format = "jpeg"  # Default
    if file_content.startswith(b'\xff\xd8\xff'):
        image_format = "jpeg"
    elif file_content.startswith(b'\x89PNG'):
        image_format = "png"
    elif file_content.startswith(b'GIF'):
        image_format = "gif"
    
    # Prepare request JSON payload (without image data - image is sent as file)
    # Check if template IDs are configured (for template-based OCR)
    template_ids_str = getattr(settings, 'NAVER_CLOVA_TEMPLATE_IDS', '')
    template_ids = None
    
    # Only use template IDs if explicitly set and not empty
    if template_ids_str and template_ids_str.strip():
        # Parse comma-separated template IDs
        try:
            template_ids = [int(tid.strip()) for tid in template_ids_str.split(',') if tid.strip()]
            if not template_ids:  # Empty list after parsing
                template_ids = None
        except ValueError:
            logger.warning(f"Invalid NAVER_CLOVA_TEMPLATE_IDS format: {template_ids_str}. Using general OCR.")
            template_ids = None
    
    # Log current configuration for debugging
    logger.debug(f"Naver Clova OCR config - URL: {api_url[:50]}..., Template IDs: {template_ids}")
    
    # Build image config
    image_config = {
        "format": image_format,
        "name": "receipt"
    }
    
    # Add templateIds if configured (for template-based OCR)
    if template_ids:
        image_config["templateIds"] = template_ids
        logger.debug(f"Using template-based OCR with template IDs: {template_ids}")
    else:
        logger.debug("Using general OCR (no template IDs)")
    
    request_json = {
        "images": [image_config],
        "requestId": str(uuid.uuid4()),
        "version": "V2",
        "timestamp": int(round(time.time() * 1000))
    }
    
    # Check if using auto integration (JSON with base64) or manual integration (multipart/form-data)
    use_auto_integration = getattr(settings, 'NAVER_CLOVA_AUTO_INTEGRATION', False)
    
    result = None
    if use_auto_integration:
        # Auto Integration: JSON with base64 encoded image
        # Encode image to base64
        image_base64 = base64.b64encode(file_content).decode('utf-8')
        
        # Add image data to request JSON
        image_config["data"] = image_base64
        
        # Update request JSON with image data
        request_json["images"][0] = image_config
        
        # Prepare headers for JSON request
        headers = {
            'X-OCR-SECRET': secret_key,
            'Content-Type': 'application/json'
        }
        
        # Make API request with JSON body
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    api_url,
                    headers=headers,
                    json=request_json,
                    timeout=30.0
                )
                
                # Log request details for debugging
                logger.debug(f"Naver Clova OCR request URL: {api_url}")
                logger.debug(f"Naver Clova OCR integration mode: Auto (JSON with base64)")
                logger.debug(f"Naver Clova OCR request headers: {headers}")
                
                # Check response status
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"Naver Clova OCR API error {response.status_code}: {error_text}")
                    try:
                        error_json = response.json()
                        logger.error(f"Naver Clova OCR error details: {error_json}")
                    except:
                        pass
                    response.raise_for_status()
                
                result = response.json()
                logger.debug(f"Naver Clova OCR response keys: {list(result.keys())}")
            except httpx.HTTPStatusError as e:
                error_text = e.response.text if e.response else "No response"
                logger.error(f"Naver Clova OCR HTTP error: {e.response.status_code if e.response else 'Unknown'} - {error_text}")
                raise Exception(f"Naver Clova OCR API error: {e.response.status_code if e.response else 'Unknown'} - {error_text}")
    else:
        # Manual Integration: multipart/form-data
        # Image file is sent as 'file' field
        # JSON payload is sent as 'message' field (UTF-8 encoded JSON string)
        files = {
            'file': ('receipt.' + image_format, file_content, f'image/{image_format}')
        }
        
        # For httpx, data should be dict with string values
        data = {
            'message': json.dumps(request_json)
        }
        
        # Prepare headers
        headers = {
            'X-OCR-SECRET': secret_key
        }
        
        # Make API request
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    api_url,
                    headers=headers,
                    data=data,
                    files=files,
                    timeout=30.0
                )
                
                # Log request details for debugging
                logger.debug(f"Naver Clova OCR request URL: {api_url}")
                logger.debug(f"Naver Clova OCR integration mode: Manual (multipart/form-data)")
                logger.debug(f"Naver Clova OCR request headers: {headers}")
                
                # Check response status
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"Naver Clova OCR API error {response.status_code}: {error_text}")
                    try:
                        error_json = response.json()
                        logger.error(f"Naver Clova OCR error details: {error_json}")
                    except:
                        pass
                    response.raise_for_status()
                
                result = response.json()
                logger.debug(f"Naver Clova OCR response keys: {list(result.keys())}")
            except httpx.HTTPStatusError as e:
                error_text = e.response.text if e.response else "No response"
                logger.error(f"Naver Clova OCR HTTP error: {e.response.status_code if e.response else 'Unknown'} - {error_text}")
                raise Exception(f"Naver Clova OCR API error: {e.response.status_code if e.response else 'Unknown'} - {error_text}")
    
    # Extract text from Naver Clova OCR response (common for both integration modes)
    # Response format: {"version": "V2", "requestId": "...", "timestamp": ..., "images": [{"uid": "...", "name": "...", "inferResult": "SUCCESS", "message": "SUCCESS", "fields": [...]}]}
    if result and "images" in result and len(result["images"]) > 0:
        image_result = result["images"][0]
        
        if image_result.get("inferResult") == "SUCCESS":
            # Extract text from fields
            fields = image_result.get("fields", [])
            text_lines = []
            
            for field in fields:
                # Each field has: "valueType", "boundingPoly", "inferText", "lineBreak", etc.
                infer_text = field.get("inferText", "")
                if infer_text:
                    text_lines.append(infer_text)
            
            # Join all text lines
            extracted_text = "\n".join(text_lines)
            logger.debug(f"Naver Clova OCR extracted {len(text_lines)} text fields")
            return extracted_text
        else:
            error_message = image_result.get("message", "Unknown error")
            raise Exception(f"Naver Clova OCR error: {error_message}")
    
    raise Exception("Naver Clova OCR: No images in response")


async def _ocr_openai_vision(file_content: bytes, trip_id: Optional[int] = None, target_date: Optional[date] = None) -> List[dict]:
    """
    Use OpenAI Vision API (GPT-4 Vision) to directly extract payment records from images.
    This is more accurate than OCR + text parsing because it understands layout and context.
    
    Args:
        file_content: Image file bytes
        trip_id: Optional trip ID for context
        target_date: Target date to filter payments (only extract payments matching this date)
    
    Returns:
        List of expense dictionaries with amount, currency, and description.
        Expenses are returned in top-to-bottom order (first in list = top of image).
    """
    import json
    
    openai_api_key = getattr(settings, 'OPENAI_API_KEY', '')
    if not openai_api_key:
        raise Exception("OpenAI API key not configured. Set OPENAI_API_KEY in .env file")
    
    # Encode image to base64
    image_base64 = base64.b64encode(file_content).decode('utf-8')
    
    # Detect image format
    if file_content.startswith(b'\xff\xd8\xff'):
        image_format = "jpeg"
    elif file_content.startswith(b'\x89PNG'):
        image_format = "png"
    elif file_content.startswith(b'GIF'):
        image_format = "gif"
    else:
        image_format = "jpeg"  # Default
    
    # Get trip context if available
    trip_context = ""
    if trip_id:
        try:
            from app.models.trip import Trip
            from app.db.session import get_db
            db = next(get_db())
            trip = db.query(Trip).filter(Trip.id == trip_id).first()
            if trip:
                trip_context = f"\nTrip context: {trip.name}"
        except Exception:
            pass  # Ignore if trip lookup fails
    
    # Build date filter instruction
    date_filter = ""
    if target_date:
        # Format date in multiple formats for better matching
        date_str = target_date.strftime("%Y-%m-%d")
        date_str_alt1 = target_date.strftime("%Y/%m/%d")
        date_str_alt2 = target_date.strftime("%m/%d/%Y")
        date_str_alt3 = target_date.strftime("%d/%m/%Y")
        date_filter = f"""
CRITICAL: Only extract payment transactions that match this date: {date_str} (or {date_str_alt1}, {date_str_alt2}, {date_str_alt3})
- Check the date shown with each transaction in the image
- If a transaction shows a different date, SKIP it
- Only include transactions that match the target date: {date_str}
- If you cannot determine the date of a transaction, SKIP it to avoid errors"""
    
    # Prepare the prompt for structured extraction
    prompt = f"""Analyze this transaction/banking screen image and extract payment (expense) records.

CRITICAL: Extract ONLY EXPENSE transactions (payments, outgoing money).
- Look for amounts with MINUS SIGN (-) or negative indicators
- IGNORE deposits, cashbacks, refunds (positive amounts with + sign)
- IGNORE running balances (typically shown after transaction amounts)
- For Korean banking apps: extract only "-원" amounts, ignore "+원" and balance amounts

For each EXPENSE transaction, extract:
1. Merchant/Store/Description name (in Korean or English)
2. Amount paid (the expense amount, as a positive number)
3. Currency code (USD, EUR, AUD, JPY, KRW, etc.)
4. Time (transaction time in HH:MM format, NOT date)

IMPORTANT - Time vs Date distinction:
- TIME: Format is "HH:MM" (hours:minutes), e.g., "14:30", "23:04", "02:02", "20:52"
  - Time appears with EACH individual transaction
  - Time is usually 2 digits:2 digits (like "23:04" or "02:02")
  - Time represents when the transaction occurred (morning/afternoon/evening)
- DATE: Format is like "11월 30일", "November 30", "11/30", "30/11", etc.
  - Date appears as SECTION HEADERS/SEPARATORS grouping multiple transactions
  - Date is NOT a transaction time - it's a date label/separator
  - DO NOT extract date as time
  - DO NOT confuse date separators (월/일 format) with transaction times
  - IGNORE date separators completely

Important rules:
- Only extract OUTGOING/EXPENSE transactions (negative amounts: -원, -$, etc.)
- SKIP deposits, cashbacks, refunds (positive amounts)
- SKIP running balances (often shown right after transaction amounts or separately)
{date_filter}
- Extract TIME (HH:MM) that appears WITH each individual transaction row
- IGNORE date labels/separators like "11월 30일", "November 30", etc.
- Time format: exactly 2 digits:2 digits (e.g., "14:30", "23:04", "02:02")
- Date format: contains month/day words or slashes (e.g., "11월 30일", "11/30")
- If transaction time is not visible or unclear, omit the "time" field (do not use date as time)
- Extract transactions in TOP-TO-BOTTOM visual order (first transaction in array = top of image)
- Maintain the exact visual order from top to bottom

Example for Korean banking app:
- Transaction row: "정수빈 20:52 -30,000원 잔액: 58,618원"
  Extract: {{"description": "정수빈", "amount": 30000, "currency": "KRW", "time": "20:52"}}
  ✅ "20:52" is TIME (HH:MM format, appears with transaction)
- Date separator: "11월 30일" (November 30)
  ❌ This is DATE, NOT time - IGNORE it completely
- SKIP: "정수빈 02:02 +200,000원" (deposit, not expense)
- SKIP: "잔액: 58,618원" (balance, not transaction)

Return a JSON array of expense records in this exact format:
[
  {{
    "description": "MERCHANT NAME",
    "amount": 50.00,
    "currency": "KRW",
    "time": "14:30"
  }},
  {{
    "description": "ANOTHER MERCHANT",
    "amount": 22.73,
    "currency": "KRW",
    "time": "15:45"
  }}
]

If no expense transactions are found (or none match the target date), return an empty array: []
{trip_context}

Return ONLY valid JSON array, no explanation, no markdown formatting, no code blocks."""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o",  # GPT-4 Vision model
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert at extracting payment records from receipt and transaction screen images. Always return valid JSON arrays."
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/{image_format};base64,{image_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "temperature": 0.1,  # Low temperature for consistent extraction
                    "max_tokens": 2000  # Enough for multiple records
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # Parse JSON response
                try:
                    # Try to extract JSON from response (might be wrapped in markdown)
                    content = content.strip()
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.startswith("```"):
                        content = content[3:]
                    if content.endswith("```"):
                        content = content[:-3]
                    content = content.strip()
                    
                    # Parse as JSON
                    if content.startswith("{"):
                        # Single object, wrap in array
                        data = json.loads(content)
                        if "expenses" in data:
                            expenses = data["expenses"]
                        elif "payments" in data:
                            expenses = data["payments"]
                        elif "transactions" in data:
                            expenses = data["transactions"]
                        else:
                            # Assume it's a single expense object
                            expenses = [data]
                    else:
                        # Assume it's already an array
                        expenses = json.loads(content)
                    
                    # Validate and normalize expenses
                    parsed_expenses = []
                    for exp in expenses:
                        if isinstance(exp, dict):
                            amount = exp.get("amount")
                            if amount is not None:
                                try:
                                    amount = float(amount)
                                    if amount > 0:
                                        parsed_expense = {
                                            "amount": Decimal(str(amount)),
                                            "currency": exp.get("currency", "KRW").upper(),
                                            "description": exp.get("description") or exp.get("merchant") or None
                                        }
                                        # Add time if present
                                        if "time" in exp:
                                            parsed_expense["time"] = exp["time"]
                                        parsed_expenses.append(parsed_expense)
                                except (ValueError, TypeError):
                                    logger.warning(f"Invalid amount in OpenAI Vision response: {exp}")
                    
                    logger.info(f"OpenAI Vision extracted {len(parsed_expenses)} payment records")
                    return parsed_expenses
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse OpenAI Vision JSON response: {e}. Response: {content[:200]}")
                    return []
            else:
                logger.error(f"OpenAI Vision API error {response.status_code}: {response.text}")
                return []
                
    except httpx.TimeoutException:
        logger.error("OpenAI Vision API request timed out.")
        return []
    except Exception as e:
        logger.error(f"Error with OpenAI Vision API: {e}", exc_info=True)
        return []


def _parse_expense_text(text: str) -> List[dict]:
    """
    Parse OCR text to extract ALL expense information from the image.
    Returns a list of expenses, each with amount, currency, and description.
    Handles multiple receipt formats and cases.
    Looks for: amount, currency, description (date not parsed - always uses URL date)
    Maintains payment order by processing amounts in text position order.
    
    Supports Naver Clova OCR format:
    - "MERCHANT NAME - A$ X.XX" (transaction amount)
    - "결제 A$ X.XX" (balance amount - should be ignored)
    """
    expenses = []
    
    if not text:
        return expenses
    
    # Normalize text - replace common OCR errors
    text = text.replace('O', '0').replace('l', '1').replace('I', '1')  # Common OCR mistakes
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    
    # First, try to match the specific format: "MERCHANT - A$ X.XX" or "MERCHANT - A$X.XX"
    # This pattern extracts both merchant name and transaction amount in one go
    # Pattern handles: "COLES 0921 - A$ 0.75", "SUSHI N co PTY LTD - A$ 22.73", etc.
    # Find ALL matches, not just the first one
    merchant_amount_patterns = [
        r'([A-Z][A-Z0-9\s\*\.\-/]+?)\s*-\s*A?\s*[€$£¥₩]\s*(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?)',  # With space: " - A$ 0.75"
        r'([A-Z][A-Z0-9\s\*\.\-/]+?)\s*-\s*A?\s*[€$£¥₩](\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?)',  # Without space: " - A$0.75"
    ]
    
    # Find all merchant-amount matches
    merchant_amount_matches = []
    for pattern in merchant_amount_patterns:
        matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))
        if matches:
            merchant_amount_matches = matches
            break
    
    if merchant_amount_matches:
        # Process each match as a separate expense
        for match in merchant_amount_matches:
            try:
                merchant_name = match.group(1).strip()
                amount_str = match.group(2).replace(',', '').replace(' ', '')
                
                # Clean up merchant name
                merchant_name = re.sub(r'\s*(PTY\s*LTD|LTD|INC|LLC|CO|SL)\s*$', '', merchant_name, flags=re.IGNORECASE)
                merchant_name = re.sub(r'^(필드\s*\d+|record\d+)\s*', '', merchant_name, flags=re.IGNORECASE)
                merchant_name = merchant_name.strip()
                
                amount_value = Decimal(amount_str)
                if 0.01 <= amount_value <= 10000000:
                    # Extract currency from the match
                    full_match = match.group(0)
                    currency = "KRW"  # Default
                    currency_symbols = {
                        'A$': 'AUD', 'A $': 'AUD',
                        '$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY', '₩': 'KRW', '원': 'KRW'
                    }
                    for symbol, code in currency_symbols.items():
                        if symbol in full_match or symbol.replace(' ', '') in full_match.replace(' ', ''):
                            currency = code
                            break
                    
                    # Try to extract time near this transaction (within 50 characters before or after)
                    expense_time = None
                    match_start = match.start()
                    match_end = match.end()
                    context_start = max(0, match_start - 50)
                    context_end = min(len(text), match_end + 50)
                    context = text[context_start:context_end]
                    
                    # Look for time patterns near the transaction
                    time_patterns = [
                        r'\b(\d{1,2}):(\d{2})(?::(\d{2}))?\b',  # HH:MM or HH:MM:SS
                        r'\b(\d{1,2})\.(\d{2})\b',  # HH.MM (less common)
                        r'\b(\d{4})\b(?=\s*(?:AM|PM|오전|오후))',  # 1430 AM/PM format
                    ]
                    
                    for time_pattern in time_patterns:
                        time_match = re.search(time_pattern, context)
                        if time_match:
                            try:
                                from datetime import time as dt_time
                                if ':' in time_match.group(0):
                                    # HH:MM or HH:MM:SS format
                                    hour = int(time_match.group(1))
                                    minute = int(time_match.group(2))
                                    second = int(time_match.group(3)) if time_match.lastindex >= 3 and time_match.group(3) else 0
                                    if 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59:
                                        expense_time = f"{hour:02d}:{minute:02d}" + (f":{second:02d}" if second > 0 else "")
                                elif '.' in time_match.group(0):
                                    # HH.MM format
                                    hour = int(time_match.group(1))
                                    minute = int(time_match.group(2))
                                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                                        expense_time = f"{hour:02d}:{minute:02d}"
                                break
                            except (ValueError, IndexError):
                                continue
                    
                    expense = {
                        "amount": amount_value,
                        "currency": currency,
                        "description": merchant_name[:100] if merchant_name else None,
                        "position": match.start()  # Store position for sorting
                    }
                    if expense_time:
                        expense["time"] = expense_time
                    expenses.append(expense)
                    logger.debug(f"Extracted expense: merchant='{merchant_name}', amount={amount_value}, currency={currency}, time={expense_time}")
            except (ValueError, IndexError):
                continue
        
        # If we found expenses using merchant-amount pattern, return them sorted by position
        if expenses:
            expenses.sort(key=lambda x: x["position"])
            # Remove position field before returning
            for exp in expenses:
                exp.pop("position", None)
            return expenses
    
    # Extract amount - ONLY amounts with minus sign and currency code/symbol
    # This ensures we don't parse dates or other numbers as amounts
    amount_patterns = [
        # Transaction screen patterns (REQUIRES minus sign and currency)
        r'-\s*A?\s*[€$£¥₩]\s*(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?)',  # - A$ 3.56, - € 3.56, - $100.00
        r'-\s*(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?)\s*A?[€$£¥₩]',  # - 3.56 A$, - 3.56 €
        r'-\s*A\s*[€$]\s*(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?)',  # - A$ 100.00 (Australian Dollar)
        r'-\s*(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?)\s*A\s*[€$]',  # - 100.00 A$ (Australian Dollar)
        
        # Transaction with minus sign and currency codes
        r'-\s*(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?)\s*(USD|EUR|GBP|JPY|CNY|KRW|WON|AUD)',  # - 100.00 USD
        r'-\s*(USD|EUR|GBP|JPY|CNY|KRW|WON|AUD)\s*(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?)',  # - USD 100.00
        
        # Transaction type patterns with minus sign (결제 = payment in Korean)
        r'결제[:\s]*-\s*A?[€$£¥₩]?\s*(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?)',  # 결제: - A$ 3.56
        r'결제[:\s]*-\s*(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?)\s*A?[€$£¥₩]',  # 결제: - 3.56 A$
    ]
    
    found_amounts = []
    for pattern in amount_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            try:
                match_context = text[max(0, match.start()-50):match.end()+50]
                match_text = match.group(0)
                
                # REQUIRED: Must have minus sign AND currency (symbol or code)
                has_minus = '-' in match_text
                has_currency_symbol = bool(re.search(r'[€$£¥₩원]', match_text, re.IGNORECASE))
                has_currency_code = bool(re.search(r'(USD|EUR|GBP|JPY|CNY|KRW|WON|AUD)', match_text, re.IGNORECASE))
                has_currency = has_currency_symbol or has_currency_code
                
                # Log for debugging if pattern matched but doesn't meet criteria
                if not (has_minus and has_currency):
                    logger.debug(f"Pattern matched but missing requirements: '{match_text}' (has_minus={has_minus}, has_currency={has_currency})")
                    continue
                
                # Skip if this looks like a date (YYYY.MM.DD, YYYY-MM-DD, MM.DD.YY, etc.)
                # Check if the matched number looks like a date
                amount_str = match.group(1).replace(',', '').replace(' ', '').replace('원', '')
                
                # Check if this looks like a date pattern
                # Dates often have specific formats: YYYY.MM.DD, YYYY-MM-DD, MM.DD, etc.
                date_patterns = [
                    r'\b(19|20)\d{2}[\.\-/]\d{1,2}[\.\-/]\d{1,2}\b',  # YYYY.MM.DD or YYYY-MM-DD
                    r'\b\d{1,2}[\.\-/]\d{1,2}[\.\-/](19|20)\d{2}\b',  # MM.DD.YYYY or MM-DD-YYYY
                    r'\b\d{1,2}[\.\-/]\d{1,2}\b',  # MM.DD
                ]
                match_context_expanded = text[max(0, match.start()-20):match.end()+20]
                if any(re.search(pattern, match_context_expanded, re.IGNORECASE) for pattern in date_patterns):
                    # This looks like a date - skip it
                    continue
                
                # Skip if this looks like a remaining balance (usually appears after transaction amount)
                # Balance amounts often appear as "결제 A$ X.XX" (without minus sign) after transaction
                match_context_lower = match_context.lower()
                if any(keyword in match_context_lower for keyword in ['remaining', 'balance', '잔액', '잔고']):
                    continue
                
                # Skip balance amounts: "결제 A$ X.XX" (payment/balance without minus sign)
                # Check if "결제" appears before this amount and it doesn't have a minus sign
                before_text = text[max(0, match.start()-30):match.start()]
                if '결제' in before_text and '-' not in match_text:
                    # This is likely a balance amount, not a transaction amount
                    logger.debug(f"Skipping balance amount: '{match_text}' (has '결제' before it without minus sign)")
                    continue
                
                amount_value = Decimal(amount_str)
                
                # Only consider reasonable amounts (between 0.01 and 10,000,000)
                # Also check if amount has too many decimal places (dates sometimes parsed as amounts)
                if amount_value >= 10000 and '.' in amount_str:
                    # Large amounts with decimals might be dates misparsed - skip
                    decimal_part = amount_str.split('.')[-1]
                    if len(decimal_part) != 2:
                        # Not a standard currency format - might be a date
                        continue
                
                if 0.01 <= amount_value <= 10000000:
                    found_amounts.append({
                        "amount": amount_value,
                        "position": match.start(),
                        "match": match,
                        "match_text": match_text
                    })
            except (ValueError, IndexError):
                continue
    
    # Log found amounts for debugging
    if found_amounts:
        logger.debug(f"Found {len(found_amounts)} potential amounts: {[(a['amount'], a['match_text']) for a in found_amounts]}")
    else:
        logger.warning(f"No amounts found in OCR text. Text preview (first 500 chars): {text[:500]}")
    
    # Process all found amounts as separate expenses
    if found_amounts:
        # Sort by position to maintain payment order in text
        found_amounts.sort(key=lambda x: x["position"])
        
        # Process each amount as a separate expense
        for amount_info in found_amounts:
            match = amount_info["match"]
            full_match = match.group(0)
            amount_position = amount_info["position"]
            
            # Extract currency from the match
            currency = "KRW"  # Default
            currency_symbols = {
                'A$': 'AUD',
                'A $': 'AUD',
                '$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY', '₩': 'KRW', '원': 'KRW'
            }
            for symbol, code in currency_symbols.items():
                if symbol in full_match or symbol.replace(' ', '') in full_match.replace(' ', ''):
                    currency = code
                    break
            
            # Check if currency code was in the match groups
            if len(match.groups()) > 1:
                currency_code = match.group(2) if match.lastindex and match.lastindex >= 2 else None
                if currency_code and currency_code.upper() in ["USD", "EUR", "GBP", "JPY", "CNY", "KRW", "WON", "AUD"]:
                    currency = "KRW" if currency_code.upper() == "WON" else currency_code.upper()
            
            # Try to extract merchant name near this transaction
            text_before = text[max(0, amount_position-300):amount_position]
            lines_before = [line.strip() for line in text_before.split('\n') if line.strip()]
            
            description = None
            # Look for merchant name in lines before the transaction amount
            for line in reversed(lines_before[-8:]):  # Check last 8 lines before amount
                line_clean = line.strip()
                # Skip if it's just numbers, dates, transaction type, or balance
                if (len(line_clean) > 3 and len(line_clean) < 100 and
                    not re.match(r'^[\d\s\$€£¥₩원A,\.:/-]+$', line_clean) and
                    '결제' not in line_clean and
                    not any(keyword in line_clean.lower() for keyword in [
                        'remaining', 'balance', '잔액', '잔고', '후기', 'review',
                        '방문 후기', 'please leave', 'leave a review'
                    ])):
                    # Check if this looks like a merchant name
                    if (re.match(r'^[A-Z][A-Z0-9\s\*\.\-/]+', line_clean) or
                        re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', line_clean)):
                        description = line_clean[:100]
                        break
            
            # Create expense entry
            expense = {
                "amount": amount_info["amount"],
                "currency": currency,
                "description": description,
                "position": amount_position
            }
            expenses.append(expense)
        
        # If we found expenses, sort by position and remove position field
        if expenses:
            expenses.sort(key=lambda x: x["position"])
            for exp in expenses:
                exp.pop("position", None)
            return expenses
    
    # If no expenses found, return empty list
    return expenses

