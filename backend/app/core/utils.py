"""
Utility functions for the application.
"""
from typing import Any, Dict
from datetime import date, datetime
import json


def serialize_date(obj: Any) -> str:
    """Serialize date objects to ISO format strings."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def format_response(data: Any, message: str = "Success") -> Dict[str, Any]:
    """Format API response."""
    return {
        "message": message,
        "data": data
    }


def format_error(message: str, details: Any = None) -> Dict[str, Any]:
    """Format error response."""
    response = {"error": message}
    if details:
        response["details"] = details
    return response

