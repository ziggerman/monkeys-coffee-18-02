"""Input validation utilities."""
import re
from typing import Optional


def validate_phone(phone: str) -> Optional[str]:
    """Validate and normalize Ukrainian phone number.
    
    Accepts formats:
    - +380991234567
    - 380991234567
    - 0991234567
    
    Returns normalized format: +380991234567 or None if invalid
    """
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Check if starts with 380
    if digits.startswith('380') and len(digits) == 12:
        return f'+{digits}'
    
    # Check if starts with 0 (local format)
    if digits.startswith('0') and len(digits) == 10:
        return f'+38{digits}'
    
    return None


def validate_promo_code(code: str) -> bool:
    """Validate promo code format.
    
    Rules:
    - 3-20 characters
    - Letters and numbers only
    - Case insensitive
    """
    if not code or len(code) < 3 or len(code) > 20:
        return False
    
    return bool(re.match(r'^[A-Za-z0-9]+$', code))


def sanitize_user_input(text: str, max_length: int = 500) -> str:
    """Sanitize user text input.
    
    - Trim whitespace
    - Limit length
    - Remove potential HTML/markdown injection
    """
    # Trim whitespace
    text = text.strip()
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    # Escape potentially dangerous characters
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    
    return text


def validate_city_name(city: str) -> bool:
    """Validate Ukrainian city name."""
    if not city or len(city) < 2 or len(city) > 100:
        return False
     
    # Should contain mostly Cyrillic or Latin letters
    return bool(re.match(r'^[А-Яа-яІіЇїЄєҐґA-Za-z\s\-\']+$', city))


def validate_address(address: str) -> bool:
    """Validate delivery address format."""
    if not address or len(address) < 5 or len(address) > 500:
        return False
    
    return True  # Allow flexible address format
