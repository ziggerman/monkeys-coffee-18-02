"""Shopping cart keyboards."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Tuple

from src.database.models import CartItem, Product
from src.utils.constants import CallbackPrefix


def get_cart_keyboard(cart_items: List[Tuple[CartItem, Product]]) -> InlineKeyboardMarkup:
    """Get shopping cart keyboard with item controls.
    
    Args:
        cart_items: List of (CartItem, Product) tuples
    """
    builder = InlineKeyboardBuilder()
    
    if not cart_items:
        builder.row(InlineKeyboardButton(
            text="☕ До каталогу",
            callback_data="goto_catalog"
        ))
        return builder.as_markup()
    
    # Item control buttons for each product
    for cart_item, product in cart_items:
        # Product name row
        builder.row(InlineKeyboardButton(
            text=f"{product.name_ua} ({cart_item.format})",
            callback_data=f"cart_item_info:{cart_item.id}"
        ))
        
        # Quantity controls row
        builder.row(
            InlineKeyboardButton(
                text="−",
                callback_data=f"{CallbackPrefix.CART_DECREASE}{cart_item.id}"
            ),
            InlineKeyboardButton(
                text=str(cart_item.quantity),
                callback_data=f"cart_qty_info:{cart_item.id}"
            ),
            InlineKeyboardButton(
                text="+",
                callback_data=f"{CallbackPrefix.CART_INCREASE}{cart_item.id}"
            ),
            InlineKeyboardButton(
                text="🗑️",
                callback_data=f"{CallbackPrefix.CART_REMOVE}{cart_item.id}"
            )
        )
    
    # Promo code and checkout buttons
    builder.row(
        InlineKeyboardButton(
            text="🎟️ Вже є промокод?",
            callback_data=CallbackPrefix.CART_PROMO
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="📦 Оформити замовлення",
            callback_data=CallbackPrefix.CART_CHECKOUT
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="☕ Продовжити покупки",
            callback_data="goto_catalog"
        )
    )
    
    return builder.as_markup()


def get_empty_cart_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for empty cart."""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="☕ До каталогу",
        callback_data="goto_catalog"
    ))
    
    return builder.as_markup()
