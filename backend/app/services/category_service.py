"""
Category classification service using OpenAI API.
Automatically categorizes expenses based on their description.

Supports two methods:
1. Chat Completions API: More accurate, understands context, but slower and more expensive
2. Embeddings API: Faster and cheaper, uses semantic similarity matching
"""
import logging
from typing import Optional
import httpx
import numpy as np
from app.core.config import settings

logger = logging.getLogger(__name__)

# Predefined categories for expense classification
EXPENSE_CATEGORIES = [
    "food",           # Restaurants, cafes, groceries, food delivery
    "drink",          # Alcohol, beverages, tea, etc.
    "transportation", # Taxi, bus, train, flight, car rental, parking
    "accommodation",  # Hotel, hostel, Airbnb
    "shopping",      # Souvenirs, clothes, gifts, general shopping
    "entertainment",  # Movies, concerts, shows, activities
    "ticket",        # Museum tickets, attraction tickets, event tickets
    "souvenir",      # Specific souvenir items
    "cafe",         # Cafe, coffee, tea, etc.
    "health",        # Pharmacy, medical, health products
    "communication", # Phone, internet, SIM card
    "other"          # Default category for unclassified expenses
]


async def classify_expense_category(
    description: Optional[str],
    trip_name: Optional[str] = None,
    amount: Optional[float] = None,
    currency: Optional[str] = None
) -> Optional[str]:
    """
    Classify expense category based on description, trip context, and amount using OpenAI API.
    
    Args:
        description: Expense description text
        trip_name: Trip name/destination (e.g., "Trip to Japan", "Sydney Adventure")
        amount: Expense amount (optional, helps with context)
        currency: Currency code (optional, helps with context)
        
    Returns:
        Category string (one of EXPENSE_CATEGORIES) or None if classification fails
    """
    if not description or not description.strip():
        return "other"
    
    # Check if OpenAI API key is configured
    openai_api_key = getattr(settings, 'OPENAI_API_KEY', '')
    if not openai_api_key:
        logger.warning("OpenAI API key not configured. Skipping category classification.")
        return "other"
    
    # Get OpenAI API URL (default to official API)
    openai_api_url = getattr(settings, 'OPENAI_API_URL', 'https://api.openai.com/v1/chat/completions')
    
    # Build context information
    context_parts = []
    if trip_name:
        context_parts.append(f"Trip/Destination: {trip_name}")
    if amount is not None and currency:
        context_parts.append(f"Amount: {amount} {currency}")
    elif amount is not None:
        context_parts.append(f"Amount: {amount}")
    
    context_info = "\n".join(context_parts) if context_parts else None
    
    # Prepare the prompt
    categories_list = ", ".join(EXPENSE_CATEGORIES)
    
    if context_info:
        prompt = f"""Classify the following expense into one of these categories: {categories_list}

Trip Context:
{context_info}

Expense description: "{description}"

Consider the trip destination and amount when classifying. For example:
- In Japan, a ¥500 expense at a shop might be a souvenir or ticket
- A $50 expense at a restaurant is likely food
- A $200 expense at a hotel is accommodation
- A small amount at a convenience store might be food or drink

Return ONLY the category name (lowercase, one word) that best matches the expense. Do not include any explanation or additional text.

Examples:
- "COLES 0921" (Australia, $50) -> food
- "SUSHI N co PTY LTD" (Australia, $22.73) -> food
- "Taxi to airport" (anywhere, $30) -> transportation
- "Hotel booking" (anywhere, $200) -> accommodation
- "Museum entrance" (Japan, ¥1000) -> ticket
- "Gift shop" (anywhere, $15) -> souvenir
- "Coffee shop" (anywhere, $5) -> drink
- "Pharmacy" (anywhere, $20) -> health

Category:"""
    else:
        prompt = f"""Classify the following expense description into one of these categories: {categories_list}

Expense description: "{description}"

Return ONLY the category name (lowercase, one word) that best matches the expense. Do not include any explanation or additional text.

Examples:
- "COLES 0921" -> food
- "SUSHI N co PTY LTD" -> food
- "Taxi to airport" -> transportation
- "Hotel booking" -> accommodation
- "Museum entrance" -> ticket
- "Gift shop" -> souvenir
- "Coffee shop" -> drink
- "Pharmacy" -> health

Category:"""
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                openai_api_url,
                headers={
                    "Authorization": f"Bearer {openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo'),
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that classifies expenses into predefined categories. Always respond with only the category name, nothing else."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,  # Lower temperature for more consistent classification
                    "max_tokens": 10    # Only need category name
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                category = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip().lower()
                
                # Validate that the returned category is in our list
                if category in EXPENSE_CATEGORIES:
                    logger.debug(f"Classified '{description}' as '{category}'")
                    return category
                else:
                    logger.warning(f"OpenAI returned invalid category '{category}' for '{description}'. Using 'other'.")
                    return "other"
            else:
                logger.error(f"OpenAI API error {response.status_code}: {response.text}")
                return "other"
                
    except httpx.TimeoutException:
        logger.error("OpenAI API request timed out. Using default category 'other'.")
        return "other"
    except Exception as e:
        logger.error(f"Error classifying expense category: {e}", exc_info=True)
        return "other"


def get_available_categories() -> list:
    """Get list of available expense categories."""
    return EXPENSE_CATEGORIES.copy()

