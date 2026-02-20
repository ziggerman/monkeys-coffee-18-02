"""Main menu keyboards."""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from src.utils.constants import CallbackPrefix


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Get main menu keyboard."""
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text="🏪 Каталог"),
        KeyboardButton(text="🛒 Мій Кошик")
    )
    builder.row(
        KeyboardButton(text="👤 Мій Кабінет"),
        KeyboardButton(text="🎟️ Спецпропозиції")
    )
    builder.row(
        KeyboardButton(text="☕ Рецепти"),
        KeyboardButton(text="📖 Корисна Інфо")
    )
    builder.row(
        KeyboardButton(text="🆘 Допомога та SOS")
    )
    
    return builder.as_markup(resize_keyboard=True)


def get_admin_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Get admin main menu keyboard - same as user menu + admin panel."""
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text="☕ Каталог"),
        KeyboardButton(text="🛒 Мій Кошик")
    )
    builder.row(
        KeyboardButton(text="👤 Мій Кабінет"),
        KeyboardButton(text="🎟️ Спецпропозиції")
    )
    builder.row(
        KeyboardButton(text="☕ Рецепти"),
        KeyboardButton(text="📖 Корисна Інфо")
    )
    builder.row(
        KeyboardButton(text="🆘 Допомога та SOS")
    )
    builder.row(
        KeyboardButton(text="⚙️ Адмін-панель")
    )
    
    return builder.as_markup(resize_keyboard=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Get cancel keyboard for FSM states."""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ Скасувати"))
    return builder.as_markup(resize_keyboard=True)
