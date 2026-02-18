"""Catch-all handler for unhandled updates."""
import logging
from aiogram import Router
from aiogram.types import Message, CallbackQuery

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query()
async def unhandled_callback(callback: CallbackQuery):
    """Catch all unhandled callbacks."""
    logger.warning(f"⚠️ UNHANDLED CALLBACK: {callback.data} | User: {callback.from_user.id}")
    await callback.answer("⚠️ Ця кнопка поки що не працює або застаріла.", show_alert=True)

@router.message()
async def unhandled_message(message: Message):
    """Catch all unhandled messages."""
    # Only log if it's not a command (commands are usually handled)
    if not message.text.startswith("/"):
        logger.warning(f"⚠️ UNHANDLED MESSAGE: {message.text} | User: {message.from_user.id}")
