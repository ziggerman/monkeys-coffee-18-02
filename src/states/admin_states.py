"""Admin panel FSM states."""
from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    """Admin panel states."""
    waiting_for_tracking_number = State()
    waiting_for_product_category = State()
    waiting_for_product_name = State()
    waiting_for_product_origin = State()
    waiting_for_product_tasting_notes = State()
    waiting_for_product_price_300g = State()
    waiting_for_product_price_1kg = State()
    waiting_for_product_image = State()
    waiting_for_product_confirm_generated = State()
    
    # New interactive flow states
    waiting_for_product_roast_level = State()
    waiting_for_product_processing = State()
    
    # Product editing
    waiting_for_product_edit_field = State()
    waiting_for_product_edit_value = State()
    
    # Product deletion
    waiting_for_product_delete_confirm = State()
    
    # User management
    waiting_for_user_search = State()
    
    # Content & Discounts
    waiting_for_module_image = State()
    waiting_for_volume_discount_type = State()
    waiting_for_volume_discount_threshold = State()
    waiting_for_volume_discount_percent = State()
