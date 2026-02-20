"""Profile editing FSM states."""
from aiogram.fsm.state import State, StatesGroup


class ProfileEditStates(StatesGroup):
    """States for profile editing flow."""
    waiting_for_city = State()
    waiting_for_address = State()
    waiting_for_phone = State()
