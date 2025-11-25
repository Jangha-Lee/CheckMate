"""
Foreign exchange service for currency conversion.
"""
from sqlalchemy.orm import Session
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from app.models.exchange_rate import ExchangeRate
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_base_currency(trip_id: int = None, db: Session = None) -> str:
    """
    Get the base currency for a trip.
    If trip_id is provided, uses the trip's base_currency.
    Otherwise, falls back to global FX_BASE_CURRENCY setting.
    Defaults to KRW if not configured.
    
    Args:
        trip_id: Optional trip ID to get trip-specific base currency
        db: Database session (required if trip_id is provided)
    
    Returns:
        Base currency code (e.g., 'KRW', 'USD', 'EUR')
    """
    if trip_id and db:
        from app.models.trip import Trip
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if trip and hasattr(trip, 'base_currency') and trip.base_currency:
            return trip.base_currency.upper()
    
    # Fallback to global setting
    base_currency = getattr(settings, 'FX_BASE_CURRENCY', 'KRW')
    return base_currency.upper() if base_currency else 'KRW'


def get_exchange_rate(
    trip_id: int,
    target_date: date,
    currency: str,
    db: Session
) -> Decimal:
    """
    Get exchange rate for a currency on a specific date.
    Returns rate to trip's base currency (1 unit of currency = rate base_currency).
    """
    base_currency = get_base_currency(trip_id, db)
    currency_upper = currency.upper()
    
    if currency_upper == base_currency:
        return Decimal(1.0)
    
    # Check if rate exists in database
    rate = db.query(ExchangeRate).filter(
        ExchangeRate.trip_id == trip_id,
        ExchangeRate.date == target_date,
        ExchangeRate.currency == currency_upper
    ).first()
    
    if rate:
        # Return rate to base currency (stored in rate_to_base column)
        return rate.rate_to_base
    
    # Fetch from external API if not in database
    rate_value = fetch_exchange_rate_from_api(target_date, currency_upper, base_currency)
    
    # Store in database
    new_rate = ExchangeRate(
        trip_id=trip_id,
        date=target_date,
        currency=currency_upper,
        rate_to_base=rate_value
    )
    db.add(new_rate)
    db.commit()
    
    return rate_value


def fetch_exchange_rate_from_api(target_date: date, currency: str, base_currency: str = None) -> Decimal:
    """
    Fetch exchange rate from ExchangeRate-API v6.
    Returns rate to base currency (1 unit of currency = rate base_currency).
    
    Uses /latest/{currency} endpoint for today's date, /history/{currency}/{year}/{month}/{day} for historical dates.
    
    API Documentation: 
    - Latest: https://www.exchangerate-api.com/docs/latest-rates
    - Historical: https://www.exchangerate-api.com/docs/historical-data-requests
    Get API key: https://www.exchangerate-api.com/
    
    Args:
        target_date: Date for which to fetch the rate
        currency: Currency code to convert FROM
        base_currency: Currency code to convert TO (defaults to FX_BASE_CURRENCY from settings)
    """
    if base_currency is None:
        base_currency = get_base_currency()
    
    currency_upper = currency.upper()
    base_currency_upper = base_currency.upper()
    
    # If already base currency, return 1.0
    if currency_upper == base_currency_upper:
        return Decimal("1.0")
    
    # Check if API key is configured
    if not hasattr(settings, 'FX_API_KEY') or not settings.FX_API_KEY:
        logger.error("FX_API_KEY is not configured. Please set it in .env file.")
        raise ValueError("FX_API_KEY is required for ExchangeRate-API")
    
    # Use /latest endpoint for today's date, /history for historical dates
    today = date.today()
    if target_date == today:
        # Latest rates endpoint: https://v6.exchangerate-api.com/v6/{API_KEY}/latest/{CURRENCY}
        api_url = f"https://v6.exchangerate-api.com/v6/{settings.FX_API_KEY}/latest/{currency_upper}"
        logger.info(f"Fetching latest exchange rate from ExchangeRate-API for {currency_upper}")
    else:
        # Historical rates endpoint: https://v6.exchangerate-api.com/v6/{API_KEY}/history/{CURRENCY}/{YEAR}/{MONTH}/{DAY}
        year = target_date.year
        month = target_date.month
        day = target_date.day
        api_url = f"https://v6.exchangerate-api.com/v6/{settings.FX_API_KEY}/history/{currency_upper}/{year}/{month}/{day}"
        logger.info(f"Fetching historical exchange rate from ExchangeRate-API for {currency_upper} on {target_date}")
    
    try:
        response = httpx.get(api_url, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        # Log response for debugging (only in debug mode)
        if settings.DEBUG:
            logger.debug(f"ExchangeRate-API response: {data}")
        
        # Check if request was successful
        if data.get("result") != "success":
            error_msg = data.get("error-type", "Unknown error")
            logger.error(f"ExchangeRate-API returned error: {error_msg}")
            raise ValueError(f"ExchangeRate-API error: {error_msg}")
        
        # Parse conversion_rates to get rate for base currency
        # Response format: {"conversion_rates": {"USD": 1, "KRW": 118, ...}}
        # conversion_rates directly contains the exchange rates (1 base_currency = X target_currency)
        # Note: The API returns rates with the requested currency as base
        conversion_rates = data.get("conversion_rates", {})
        
        # Get rate for base currency (e.g., if currency is USD and base is KRW, get KRW rate)
        base_rate = conversion_rates.get(base_currency_upper)
        if base_rate is None:
            logger.error(f"{base_currency_upper} not found in conversion_rates. Available currencies: {list(conversion_rates.keys())}")
            raise ValueError(f"{base_currency_upper} rate not available in API response")
        
        # conversion_rates contains the rate (e.g., 1 USD = 118 KRW if base_currency is KRW)
        rate = Decimal(str(base_rate))
        
        if rate <= 0:
            logger.error(f"Invalid rate: {rate}")
            raise ValueError(f"Invalid exchange rate: {rate}")
        
        logger.info(f"Successfully fetched rate from ExchangeRate-API: {currency_upper} = {rate} {base_currency_upper}")
        return rate
        
    except httpx.HTTPStatusError as e:
        # HTTP error with status code
        error_text = e.response.text if hasattr(e.response, 'text') else str(e)
        logger.error(f"HTTP error with ExchangeRate-API: {e.response.status_code} - {error_text}")
        raise ValueError(f"ExchangeRate-API HTTP error: {e.response.status_code}")
    except httpx.HTTPError as e:
        # Other HTTP errors (network, timeout, etc.)
        logger.error(f"HTTP error with ExchangeRate-API: {e}")
        raise ValueError(f"ExchangeRate-API network error: {str(e)}")
    except Exception as e:
        # Other unexpected errors
        logger.error(f"Unexpected error with ExchangeRate-API: {e}", exc_info=True)
        raise
    
    # No fallback - API key is required
    # If we reach here, it means an exception was raised and not caught
    # This should not happen, but just in case
    raise ValueError(f"Failed to fetch exchange rate for {currency_upper} on {target_date}")


def convert_to_base(amount: Decimal, currency: str, rate: Decimal, base_currency: str = None) -> Decimal:
    """
    Convert amount from currency to base currency.
    
    Args:
        amount: Amount in the source currency
        currency: Source currency code
        rate: Exchange rate (1 source_currency = rate base_currency)
        base_currency: Optional base currency code (if None, will use global setting)
    
    Returns:
        Amount in base currency
    """
    if base_currency is None:
        base_currency = get_base_currency()
    else:
        base_currency = base_currency.upper()
    
    currency_upper = currency.upper()
    if currency_upper == base_currency:
        return amount
    return amount * rate


def convert_to_krw(amount: Decimal, currency: str, rate: Decimal) -> Decimal:
    """
    Convert amount from currency to KRW.
    Deprecated: Use convert_to_base() instead for dynamic base currency support.
    Kept for backward compatibility.
    """
    return convert_to_base(amount, currency, rate)


def update_daily_rates(trip_id: int, target_date: date, db: Session):
    """Update exchange rates for all currencies for a specific date."""
    # This can be called as a scheduled task to update rates
    currencies = ["USD", "EUR", "JPY", "CNY", "AUD", "GBP"]  # Add more as needed
    
    for currency in currencies:
        get_exchange_rate(trip_id, target_date, currency, db)

