"""Catalog navigation keyboards."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.utils.constants import CallbackPrefix, CoffeeProfile
from config import COFFEE_PROFILES


def get_format_selection_keyboard() -> InlineKeyboardMarkup:
    """Get product format selection keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="🫘 Пачки 300г",
        callback_data=f"{CallbackPrefix.CATALOG_FORMAT}300g"
    ))
    builder.row(InlineKeyboardButton(
        text="🏷️ Опт від 6 пачок (-25%)",
        callback_data="info_discount_packs"
    ))
    builder.row(InlineKeyboardButton(
        text="⚖️ Кілограми 1кг",
        callback_data=f"{CallbackPrefix.CATALOG_FORMAT}1kg"
    ))
    builder.row(InlineKeyboardButton(
        text="🏷️ Опт від 2 кг (-25%)",
        callback_data="info_discount_kg"
    ))
    
    return builder.as_markup()


def get_profile_filter_keyboard() -> InlineKeyboardMarkup:
    """Get coffee profile filter keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="🥤 Еспресо",
        callback_data=f"{CallbackPrefix.CATALOG_PROFILE}espresso"
    ))
    
    builder.row(InlineKeyboardButton(
        text="🫖 Фільтр",
        callback_data=f"{CallbackPrefix.CATALOG_PROFILE}filter"
    ))
    
    builder.row(InlineKeyboardButton(
        text="⚗️ Універсальна",
        callback_data=f"{CallbackPrefix.CATALOG_PROFILE}universal"
    ))
    
    builder.row(InlineKeyboardButton(
        text="🫘 Весь Арсенал",
        callback_data=f"{CallbackPrefix.CATALOG_PROFILE}all"
    ))
    
    builder.row(InlineKeyboardButton(
        text="📦 Магазин",
        callback_data=f"{CallbackPrefix.CATALOG_PROFILE}equipment"
    ))
    
    builder.row(InlineKeyboardButton(
        text="🔙 Назад до меню",
        callback_data="start"
    ))
    
    return builder.as_markup()
    
    return builder.as_markup()


def get_product_card_keyboard(
    product_id: int,
    page: int = 0
) -> InlineKeyboardMarkup:
    """Get product card inline keyboard.
    
    Args:
        product_id: Product ID
        page: Current page number for pagination
    """
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🫘 300г ➕",
            callback_data=f"{CallbackPrefix.CATALOG_ADD}{product_id}:300g"
        ),
        InlineKeyboardButton(
            text="📦 1кг ➕",
            callback_data=f"{CallbackPrefix.CATALOG_ADD}{product_id}:1kg"
        )
    )
    
    builder.row(InlineKeyboardButton(
        text="📖 Детальніше",
        callback_data=f"{CallbackPrefix.CATALOG_PRODUCT}{product_id}"
    ))
    
    return builder.as_markup()


def get_product_list_keyboard(
    products: list,
    current_page: int,
    total_pages: int,
    selected_profile: str
) -> InlineKeyboardMarkup:
    """Get product list keyboard with buttons for each product.
    
    Args:
        products: List of products for current page
        current_page: Current page (0-indexed)
        total_pages: Total number of pages
        selected_profile: Profile filter
    """
    builder = InlineKeyboardBuilder()
    
    # 1. Product buttons
    for product in products:
        builder.row(InlineKeyboardButton(
            text=f"{product.name_ua} ☕",
            # Pass profile and page to return to same state
            callback_data=f"{CallbackPrefix.CATALOG_PRODUCT}{product.id}:{current_page}:{selected_profile}"
        ))
    
    # 2. Pagination
    if total_pages > 1:
        buttons = []
        
        if current_page > 0:
            buttons.append(InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"{CallbackPrefix.CATALOG_PAGE}{current_page-1}:{selected_profile}"
            ))
        
        buttons.append(InlineKeyboardButton(
            text=f"{current_page + 1}/{total_pages}",
            callback_data="page_info"
        ))
        
        if current_page < total_pages - 1:
            buttons.append(InlineKeyboardButton(
                text="Далі ➡️",
                callback_data=f"{CallbackPrefix.CATALOG_PAGE}{current_page+1}:{selected_profile}"
            ))
        
        builder.row(*buttons)
    
    # 3. Navigation
    builder.row(
        InlineKeyboardButton(
            text="🛒 До Кошика",
            callback_data=CallbackPrefix.CART_VIEW
        ),
        InlineKeyboardButton(
            text="🔙 До Вибору",
            callback_data="goto_catalog"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🏠 В Меню",
            callback_data="start"
        )
    )
    
    return builder.as_markup()


def get_product_details_keyboard(
    product_id: int,
    back_page: int = 0,
    back_profile: str = "all"
) -> InlineKeyboardMarkup:
    """Get keyboard for product details view."""
    builder = InlineKeyboardBuilder()
    
    is_equipment = back_profile == "equipment"
    
    if is_equipment:
        builder.row(
            InlineKeyboardButton(
                text="➕ Додати до кошика",
                callback_data=f"{CallbackPrefix.CATALOG_ADD}{product_id}:unit"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="⚫ Додати 300г ➕",
                callback_data=f"{CallbackPrefix.CATALOG_ADD}{product_id}:300g"
            ),
            InlineKeyboardButton(
                text="🔴 Додати 1кг ➕",
                callback_data=f"{CallbackPrefix.CATALOG_ADD}{product_id}:1kg"
            )
        )
    
    # Combined navigation row
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=f"{CallbackPrefix.CATALOG_PAGE}{back_page}:{back_profile}"
        ),
        InlineKeyboardButton(
            text="🛒 Кошик",
            callback_data=CallbackPrefix.CART_VIEW
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🫘 Категорії",
            callback_data="goto_catalog"
        ),
        InlineKeyboardButton(
            text="🏠 В Меню",
            callback_data="start"
        )
    )
    
    return builder.as_markup()
