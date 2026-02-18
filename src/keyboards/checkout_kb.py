"""Checkout flow keyboards."""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from src.utils.constants import GrindType, DeliveryMethod, GRIND_TYPE_NAMES, DELIVERY_METHOD_NAMES


def get_grind_selection_keyboard() -> InlineKeyboardMarkup:
    """Get grind preference selection keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="🫘 В зернах",
        callback_data=f"grind:{GrindType.BEANS}"
    ))

    builder.row(InlineKeyboardButton(
        text="☕ Ріжкова кавоварка",
        callback_data=f"grind:{GrindType.FINE}"
    ))

    builder.row(InlineKeyboardButton(
        text="🥣 Чашка",
        callback_data=f"grind:{GrindType.COARSE}"
    ))

    builder.row(InlineKeyboardButton(
        text="🔷 Гейзерка",
        callback_data=f"grind:{GrindType.MEDIUM}"
    ))

    builder.row(InlineKeyboardButton(
        text="🫖 Турка",
        callback_data=f"grind:{GrindType.FINE}"
    ))

    builder.row(InlineKeyboardButton(
        text="🫖 Фільтр",
        callback_data=f"grind:{GrindType.MEDIUM}"
    ))
    
    return builder.as_markup()


def get_delivery_method_keyboard() -> InlineKeyboardMarkup:
    """Get delivery method selection keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="📦 Нова Пошта",
        callback_data=f"delivery:{DeliveryMethod.NOVA_POSHTA.value}"
    ))
    
    builder.row(InlineKeyboardButton(
        text="✉️ Укрпошта",
        callback_data=f"delivery:{DeliveryMethod.UKRPOSHTA.value}"
    ))
    
    builder.row(InlineKeyboardButton(
        text="🛵 Кур'єр Київ",
        callback_data=f"delivery:{DeliveryMethod.COURIER.value}"
    ))
    
    builder.row(InlineKeyboardButton(
        text="🐒 Інфо про доставку",
        callback_data="delivery_info"
    ))
    
    return builder.as_markup()

def get_order_confirmation_keyboard(order_id: int, payment_url: str = None) -> InlineKeyboardMarkup:
    """Get order confirmation keyboard."""
    builder = InlineKeyboardBuilder()
    
    if payment_url:
        builder.row(InlineKeyboardButton(
            text="💳 Оплатити замовлення (LiqPay)",
            web_app=WebAppInfo(url=payment_url)
        ))
    
    builder.row(
        InlineKeyboardButton(
            text="🍎 Apple / Google Pay",
            callback_data=f"checkout_tg_pay:{order_id}"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="✏️ Змінити",
            callback_data="checkout_edit"
        )
    )
    
    if not payment_url:
        builder.row(
            InlineKeyboardButton(
                text="✅ Підтвердити (LiqPay)",
                callback_data=f"checkout_pay:{order_id}"
            )
        )
    
    return builder.as_markup()


def get_payment_keyboard(payment_url: str) -> InlineKeyboardMarkup:
    """Get keyboard with direct payment link (using WebApp for speed)."""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="💳 Оплатити замовлення",
        web_app=WebAppInfo(url=payment_url)
    ))
    
    return builder.as_markup()


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Get cancel keyboard for text input states."""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="❌ Скасувати"))
    return builder.as_markup(resize_keyboard=True)


def get_profile_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for confirming existing user data."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Все вірно", callback_data="checkout_data_ok"))
    builder.row(InlineKeyboardButton(text="✏️ Змінити", callback_data="checkout_data_edit"))
    return builder.as_markup()


def get_use_saved_keyboard(saved_value: str) -> ReplyKeyboardMarkup:
    """Get keyboard with saved value option."""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=f"🏠 {saved_value}"))
    builder.row(KeyboardButton(text="❌ Скасувати"))
    return builder.as_markup(resize_keyboard=True)
