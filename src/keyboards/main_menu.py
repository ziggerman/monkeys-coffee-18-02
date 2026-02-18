"""Main menu keyboards."""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from src.utils.constants import CallbackPrefix


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Get main menu keyboard."""
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
        KeyboardButton(text="📖 Корисна Інфо"),
        KeyboardButton(text="🆘 Допомога та SOS")
    )
    
    return builder.as_markup(resize_keyboard=True)


def get_admin_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Get admin main menu keyboard with additional options."""
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text="☕ Каталог кави"),
        KeyboardButton(text="🛒 Мій Кошик")
    )
    builder.row(
        KeyboardButton(text="📋 Замовлення"),
        KeyboardButton(text="💎 Бонуси")
    )
    builder.row(
        KeyboardButton(text="⚡ Акції"),
        KeyboardButton(text="💬 Підтримка")
    )
    builder.row(
        KeyboardButton(text="⚙️ Адмін-панель"),
        KeyboardButton(text="🐒 Про нас")
    )
    
    return builder.as_markup(resize_keyboard=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Get cancel keyboard for FSM states."""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ Скасувати"))
    return builder.as_markup(resize_keyboard=True)
