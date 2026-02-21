"""Catalog navigation keyboards."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.utils.constants import CallbackPrefix, CoffeeProfile
from config import COFFEE_PROFILES


def get_format_selection_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="🫘 Пачки 300г",
        callback_data=f"{CallbackPrefix.CATALOG_FORMAT}300g"
    ))
    builder.row(InlineKeyboardButton(
        text="🏷️ Опт від 7 пачок (-25%)",
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


async def get_profile_filter_keyboard(session) -> InlineKeyboardMarkup:
    from sqlalchemy import select
    from src.database.models import Category
    
    builder = InlineKeyboardBuilder()
    
    # Fetch ALL active categories from DB (except equipment)
    query = select(Category).where(
        Category.is_active == True,
        Category.slug != "equipment"
    ).order_by(Category.sort_order.asc())
    
    result = await session.execute(query)
    categories = result.scalars().all()
    
    # Build buttons for each category
    emoji_map = {
        "espresso": "🥤",
        "filter": "🫖",
        "universal": "⚗️",
        "zernova_kava": "☕"
    }
    
    for cat in categories:
        emoji = emoji_map.get(cat.slug, "🏷️")
        name = cat.name_ua.replace("🥤 ", "").replace("🫖 ", "").replace("⚗️ ", "").replace("☕ ", "")
        builder.row(InlineKeyboardButton(
            text=f"{emoji} {name}",
            callback_data=f"{CallbackPrefix.CATALOG_PROFILE}{cat.slug}"
        ))
    
    # Add "Весь Арсенал"
    builder.row(InlineKeyboardButton(
        text="🫘 Весь Арсенал",
        callback_data=f"{CallbackPrefix.CATALOG_PROFILE}all"
    ))
    
    # Add shop/equipment category if active
    eq_query = select(Category).where(
        Category.is_active == True,
        Category.slug == "equipment"
    ).order_by(Category.sort_order.asc())
    eq_result = await session.execute(eq_query)
    eq_categories = eq_result.scalars().all()
    
    for cat in eq_categories:
        builder.row(InlineKeyboardButton(
            text="📦 Магазин",
            callback_data=f"{CallbackPrefix.CATALOG_PROFILE}equipment"
        ))
    
    builder.row(InlineKeyboardButton(text="🔙 Назад до меню", callback_data="start"))
    
    return builder.as_markup()


def get_profile_filter_keyboard_sync() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(text="🥤 Еспресо", callback_data=f"{CallbackPrefix.CATALOG_PROFILE}espresso"))
    builder.row(InlineKeyboardButton(text="🫖 Фільтр", callback_data=f"{CallbackPrefix.CATALOG_PROFILE}filter"))
    builder.row(InlineKeyboardButton(text="⚗️ Універсальна", callback_data=f"{CallbackPrefix.CATALOG_PROFILE}universal"))
    builder.row(InlineKeyboardButton(text="🫘 Весь Арсенал", callback_data=f"{CallbackPrefix.CATALOG_PROFILE}all"))
    builder.row(InlineKeyboardButton(text="📦 Магазин", callback_data=f"{CallbackPrefix.CATALOG_PROFILE}equipment"))
    builder.row(InlineKeyboardButton(text="🔙 Назад до меню", callback_data="start"))
    
    return builder.as_markup()


_CATEGORY_EMOJI = {
    "coffee": "☕",
    "espresso": "🥤",
    "filter": "🫖",
    "universal": "⚗️",
    "all": "🫘",
    "equipment": "📦",
    "accessories": "🔧",
    "merch": "👕",
    "gift": "🎁",
}


def get_category_keyboard(categories: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for cat in categories:
        emoji = _CATEGORY_EMOJI.get(cat.slug, "🏷️")
        builder.row(InlineKeyboardButton(
            text=f"{emoji} {cat.name_ua}",
            callback_data=f"{CallbackPrefix.CATALOG_PROFILE}{cat.slug}"
        ))
    
    builder.row(InlineKeyboardButton(text="🔙 Назад до меню", callback_data="start"))
    
    return builder.as_markup()


def get_product_card_keyboard(product_id: int, page: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🫘 300г ➕", callback_data=f"{CallbackPrefix.CATALOG_ADD}{product_id}:300g"),
        InlineKeyboardButton(text="📦 1кг ➕", callback_data=f"{CallbackPrefix.CATALOG_ADD}{product_id}:1kg")
    )
    
    builder.row(InlineKeyboardButton(text="📖 Детальніше", callback_data=f"{CallbackPrefix.CATALOG_PRODUCT}{product_id}"))
    
    return builder.as_markup()


def get_product_list_keyboard(products: list, current_page: int, total_pages: int, selected_profile: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    for product in products:
        builder.row(InlineKeyboardButton(
            text=f"{product.name_ua} ☕",
            callback_data=f"{CallbackPrefix.CATALOG_PRODUCT}{product.id}:{current_page}:{selected_profile}"
        ))
    
    if total_pages > 1:
        buttons = []
        
        if current_page > 0:
            buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{CallbackPrefix.CATALOG_PAGE}{current_page-1}:{selected_profile}"))
        
        buttons.append(InlineKeyboardButton(text=f"{current_page + 1}/{total_pages}", callback_data="page_info"))
        
        if current_page < total_pages - 1:
            buttons.append(InlineKeyboardButton(text="Далі ➡️", callback_data=f"{CallbackPrefix.CATALOG_PAGE}{current_page+1}:{selected_profile}"))
        
        builder.row(*buttons)
    
    builder.row(
        InlineKeyboardButton(text="🛒 До Кошика", callback_data=CallbackPrefix.CART_VIEW),
        InlineKeyboardButton(text="🔙 До Вибору", callback_data="goto_catalog")
    )
    builder.row(InlineKeyboardButton(text="🏠 В Меню", callback_data="start"))
    
    return builder.as_markup()


def get_product_details_keyboard(product_id: int, back_page: int = 0, back_profile: str = "all") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    is_equipment = back_profile == "equipment"
    
    if is_equipment:
        builder.row(InlineKeyboardButton(text="➕ Додати до кошика", callback_data=f"{CallbackPrefix.CATALOG_ADD}{product_id}:unit"))
    else:
        builder.row(
            InlineKeyboardButton(text="⚫ Додати 300г ➕", callback_data=f"{CallbackPrefix.CATALOG_ADD}{product_id}:300g"),
            InlineKeyboardButton(text="🔴 Додати 1кг ➕", callback_data=f"{CallbackPrefix.CATALOG_ADD}{product_id}:1kg")
        )
    
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"{CallbackPrefix.CATALOG_PAGE}{back_page}:{back_profile}"),
        InlineKeyboardButton(text="🛒 Кошик", callback_data=CallbackPrefix.CART_VIEW)
    )
    builder.row(
        InlineKeyboardButton(text="🫘 Категорії", callback_data="goto_catalog"),
        InlineKeyboardButton(text="🏠 В Меню", callback_data="start")
    )
    
    return builder.as_markup()
