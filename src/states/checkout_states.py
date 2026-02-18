"""Checkout FSM states."""
from aiogram.fsm.state import State, StatesGroup


class CheckoutStates(StatesGroup):
    """States for checkout flow."""
    # New step for interactive confirmation
    confirming_saved_data = State()
    waiting_for_grind = State()
    waiting_for_delivery_method = State()
    waiting_for_city = State()
    waiting_for_address = State()
    waiting_for_recipient_name = State()
    waiting_for_recipient_phone = State()
    confirming_order = State()


class PromoCodeStates(StatesGroup):
    """States for promo code entry."""
    waiting_for_code = State()
