"""Message Manager — tracks and deletes the previous bot module message.

Usage in any Message handler (reply keyboard button):

    from src.utils.message_manager import delete_previous, save_message

    async def show_something(message: Message, state: FSMContext, ...):
        await delete_previous(message)           # delete old module message
        sent = await message.answer_photo(...)   # send new one
        await save_message(state, sent)          # remember it

For CallbackQuery handlers you don't need this — edit_media handles it in-place.
"""
import logging
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

logger = logging.getLogger(__name__)

_KEY = "__last_bot_msg_id"


async def delete_previous(message: Message, state: FSMContext | None = None) -> None:
    """Delete the previous bot module message for this user.

    Reads the stored message_id from FSM state and tries to delete it.
    Silently ignores errors (message already deleted, too old, etc.).
    """
    if state is None:
        return

    data = await state.get_data()
    msg_id = data.get(_KEY)

    if msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        except Exception as e:
            logger.debug(f"Could not delete previous message {msg_id}: {e}")


async def save_message(state: FSMContext, sent: Message) -> None:
    """Save the message_id of the newly sent bot message into FSM state."""
    await state.update_data({_KEY: sent.message_id})
