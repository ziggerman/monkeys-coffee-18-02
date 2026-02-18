"""Loyalty system handler."""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.services.loyalty_service import LoyaltyService
from src.utils.formatters import format_progress_bar
from config import LOYALTY_LEVELS
from src.utils.image_constants import MODULE_LOYALTY

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("loyalty"))
@router.message(F.text == "💎 Бонуси")
@router.callback_query(F.data == "loyalty_program")
async def show_loyalty_status(event: Message | CallbackQuery, session: AsyncSession, state: FSMContext = None, user: User = None):
    """Show user's loyalty status and progress."""
    if not user:
        user_id = event.from_user.id
        # Get user
        query = select(User).where(User.id == user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
    
    if not user:
        text = "Помилка: користувач не знайдений"
        if isinstance(event, Message):
            await event.answer(text)
        else:
            await event.answer(text, show_alert=True)
        return
    
    # Get formatted loyalty status
    # Calculate progress to next level
    current_kg = user.total_purchased_kg
    next_level = user.loyalty_level + 1
    
    from src.utils.constants import UIStyle
    
    progress_info = ""
    if next_level in LOYALTY_LEVELS:
        target_kg = LOYALTY_LEVELS[next_level]['threshold_kg']
        needed_kg = target_kg - current_kg
        # Use more premium bar symbols
        bar_length = 12
        filled = int((current_kg / target_kg) * bar_length)
        bar = "▰" * filled + "▱" * (bar_length - filled)
        
        progress_info = (
            f"{UIStyle.DIVIDER}\n"
            f"🟠 <b>До наступного рівня ({LOYALTY_LEVELS[next_level]['name']}):</b>\n"
            f"<code>{bar}</code>\n"
            f"Залишилось: <b>{needed_kg:.1f} кг</b> до знижки {LOYALTY_LEVELS[next_level]['discount']}%! ☕\n"
        )

    status_text = (
        f"🔴 <b>Твоя Кавова Статистика</b> 🐒\n"
        f"<i>Тут ми рахуємо кожну твою чашку.</i> ☕\n\n"
        f"{UIStyle.BOLD_DIVIDER}\n"
        f"👤 <b>ПРОФІЛЬ</b>\n"
        f"• Ім'я: <b>{user.first_name}</b>\n"
        f"• ID: <code>{user.id}</code>\n\n"
        f"🎖️ <b>ТВІЙ СТАТУС</b>\n"
        f"• Рівень: <b>{LOYALTY_LEVELS[user.loyalty_level]['name']}</b>\n"
        f"• Знижка: <b>{LOYALTY_LEVELS[user.loyalty_level]['discount']}%</b>\n\n"
        f"📈 <b>МАШТАБИ</b>\n"
        f"• Замовлень: <b>{user.total_orders}</b>\n"
        f"• Всього кави: <b>{user.total_purchased_kg:.1f} кг</b>\n"
        f"{progress_info}"
        f"{UIStyle.BOLD_DIVIDER}\n"
        f"💡 <i>Від 2 кг в одному чеку — твоя особиста знижка +25%.</i>"
    )
    
    # Get dynamic image
    from src.utils.ui_utils import get_module_image
    from src.utils.image_constants import MODULE_LOYALTY
    photo = await get_module_image(session, "cabinet", MODULE_LOYALTY)
    
    if isinstance(event, Message):
        from src.utils.message_manager import delete_previous, save_message
        await delete_previous(event, state)
        if photo:
            sent = await event.answer_photo(photo, caption=status_text, parse_mode="HTML")
        else:
            sent = await event.answer(status_text, parse_mode="HTML")
        await save_message(state, sent)

    else:
        # Handle CallbackQuery
        try:
            if photo:
                from aiogram.types import InputMediaPhoto
                # If it's a file_id (string), use it directly. If it's FSInputFile, use it.
                media = InputMediaPhoto(media=photo, caption=status_text, parse_mode="HTML")
                await event.message.edit_media(media=media)
            else:
                await event.message.edit_text(status_text, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Failed to edit loyalty message: {e}")
            # Do NOT delete+send — just send new message as last resort
            if photo:
                await event.message.answer_photo(photo, caption=status_text, parse_mode="HTML")
            else:
                await event.message.answer(status_text, parse_mode="HTML")
        
        await event.answer()

