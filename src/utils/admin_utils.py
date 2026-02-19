"""Admin utility functions."""
from config import settings

def is_admin(user_id: int) -> bool:
    """
    Check if a user has administrator privileges.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        bool: True if user is an admin, False otherwise
    """
    return user_id in settings.admin_id_list
