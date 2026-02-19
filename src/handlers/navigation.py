"""Global navigation and cancellation handler."""
import logging
from aiogram import Router, F
from aiogram.filters import Command, StateFilter, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from src.keyboards.main_menu import get_admin_main_menu_keyboard, get_main_menu_keyboard
from src.handlers.start import cmd_start, show_main_menu, show_about, show_support
from src.handlers.catalog import show_catalog_start
from src.handlers.cart import show_cart
from src.handlers.profile import show_profile
from src.handlers.promotions import show_promotions

router = Router()
logger = logging.getLogger(__name__)

from src.utils.admin_utils import is_admin


@router.message(StateFilter("*"), Command("cancel"))
@router.message(StateFilter("*"), F.text.casefold() == "❌ скасувати")
async def global_cancel(message: Message, state: FSMContext):
    """Global cancel: clears state and returns to main menu."""
    current_state = await state.get_state()
    logger.info(f"Global cancel triggered by user {message.from_user.id}. State was: {current_state}")
    
    await state.clear()
    
    # Determine keyboard
    keyboard = get_admin_main_menu_keyboard() if is_admin(message.from_user.id) else get_main_menu_keyboard()
    
    await message.answer(
        "❌ Дія скасована. Куди далі?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# --- Global Menu Navigation (Works in ANY state) ---

@router.message(StateFilter("*"), CommandStart())
async def global_start(message: Message, session: AsyncSession, state: FSMContext):
    """Handle /start globally."""
    # We delegate to the original start handler, but verify state clearing
    await state.clear()
    await cmd_start(message, session, state)


@router.message(StateFilter("*"), F.text == "🏠 Головне меню")
async def global_main_menu(message: Message, session: AsyncSession, state: FSMContext):
    await state.clear()
    await show_main_menu(message, session, state)


@router.message(StateFilter("*"), F.text.in_({"☕ Каталог", "☕ Каталог кави"}))
async def global_catalog(message: Message, session: AsyncSession, state: FSMContext):
    await state.clear()
    await show_catalog_start(message, session, state)


@router.message(StateFilter("*"), F.text == "🛒 Мій Кошик")
async def global_cart(message: Message, session: AsyncSession, state: FSMContext):
    await state.clear()
    await show_cart(message, session, state)


@router.message(StateFilter("*"), F.text == "👤 Мій Кабінет")
async def global_profile(message: Message, session: AsyncSession, state: FSMContext):
    await state.clear()
    await show_profile(message, session, state)


@router.message(StateFilter("*"), F.text == "🎟️ Спецпропозиції")
async def global_promotions(message: Message, session: AsyncSession, state: FSMContext):
    await state.clear()
    await show_promotions(message, session, state)
    
@router.message(StateFilter("*"), F.text.in_({"📖 Корисна Інфо", "🐒 Про нас"}))
async def global_about(message: Message, session: AsyncSession, state: FSMContext):
    await state.clear()
    await show_about(message, session, state)

@router.message(StateFilter("*"), F.text.in_({"🆘 Допомога та SOS", "Підтримка", "💬 Підтримка"}))
async def global_support(message: Message, session: AsyncSession, state: FSMContext):
    await state.clear()
    await show_support(message, session, state)
