"""Category management handlers."""
import logging
import asyncio
from pathlib import Path
from typing import Optional

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, FSInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Category, Product
from src.states.admin_states import AdminStates
from src.keyboards.main_menu import get_cancel_keyboard, get_admin_main_menu_keyboard
from src.keyboards.admin_kb import get_image_management_keyboard
from src.utils.image_constants import ASSETS_DIR
from config import settings

router = Router()
logger = logging.getLogger(__name__)


from src.utils.admin_utils import is_admin


# ========== CONSTANTS ==========
CATEGORIES_PER_PAGE = 8


# ========== KEYBOARDS ==========

def get_category_management_keyboard(categories: list, page: int = 0, total_pages: int = 1) -> InlineKeyboardBuilder:
    """Get keyboard for category management with pagination."""
    builder = InlineKeyboardBuilder()
    
    for cat in categories:
        status_icon = "✅" if cat.is_active else "🚫"
        has_image = "🖼️" if cat.image_file_id or cat.image_path else ""
        # Display: [Status] Name (Sort) [Products count]
        builder.row(InlineKeyboardButton(
            text=f"{status_icon} {cat.name_ua} #{cat.sort_order} {has_image}",
            callback_data=f"admin_cat_edit:{cat.id}"
        ))
    
    # Pagination controls
    if total_pages > 1:
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(InlineKeyboardButton(
                text="⬅️",
                callback_data=f"admin_cat_page:{page-1}"
            ))
        pagination_buttons.append(InlineKeyboardButton(
            text=f"{page + 1}/{total_pages}",
            callback_data="admin_cat_page_info"
        ))
        if page < total_pages - 1:
            pagination_buttons.append(InlineKeyboardButton(
                text="➡️",
                callback_data=f"admin_cat_page:{page+1}"
            ))
        builder.row(*pagination_buttons)
        
    builder.row(InlineKeyboardButton(text="🔄 Сортування", callback_data="admin_cat_sort_menu"))
    builder.row(InlineKeyboardButton(text="➕ Додати категорію", callback_data="admin_cat_add"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main"))
    
    return builder.as_markup()


def get_category_edit_keyboard(category_id: int, is_active: bool, has_image: bool = False, product_count: int = 0) -> InlineKeyboardBuilder:
    """Get keyboard for editing a category."""
    builder = InlineKeyboardBuilder()
    
    toggle_text = "Деактивувати 🚫" if is_active else "Активувати ✅"
    
    # Move up/down buttons
    builder.row(
        InlineKeyboardButton(text="⬆️ Вгору", callback_data=f"admin_cat_move:{category_id}:up"),
        InlineKeyboardButton(text="⬇️ Вниз", callback_data=f"admin_cat_move:{category_id}:down")
    )
    
    builder.row(InlineKeyboardButton(text="✏️ Змінити назву (UA)", callback_data=f"admin_cat_rename:{category_id}:ua"))
    builder.row(InlineKeyboardButton(text="✏️ Змінити назву (EN)", callback_data=f"admin_cat_rename:{category_id}:en"))
    builder.row(InlineKeyboardButton(text="🔗 Змінити slug", callback_data=f"admin_cat_change_slug:{category_id}"))
    builder.row(InlineKeyboardButton(text="🔢 Змінити порядок", callback_data=f"admin_cat_reorder:{category_id}"))
    
    # Image management
    img_text = "🖼️ Змінити зображення" if has_image else "🖼️ Додати зображення"
    builder.row(InlineKeyboardButton(text=img_text, callback_data=f"admin_cat_image:{category_id}"))
    
    # Show preview image if exists
    if has_image:
        builder.row(InlineKeyboardButton(text="👁️ Переглянути", callback_data=f"admin_cat_preview:{category_id}"))
    
    builder.row(InlineKeyboardButton(text=toggle_text, callback_data=f"admin_cat_toggle:{category_id}"))
    
    # Delete with warning
    if product_count > 0:
        builder.row(InlineKeyboardButton(
            text=f"🗑 Видалити ({product_count} товарів)",
            callback_data=f"admin_cat_del:{category_id}"
        ))
    else:
        builder.row(InlineKeyboardButton(text="🗑 Видалити", callback_data=f"admin_cat_del_confirm:{category_id}"))
    
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_categories"))
    
    return builder.as_markup()


def get_category_delete_confirm_keyboard(category_id: int) -> InlineKeyboardBuilder:
    """Get keyboard for confirming category deletion."""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="❌ ТАК, ВИДАЛИТИ",
        callback_data=f"admin_cat_del_final:{category_id}"
    ))
    builder.row(InlineKeyboardButton(
        text="✅ Скасувати",
        callback_data=f"admin_cat_edit:{category_id}"
    ))
    
    return builder.as_markup()


def get_category_sort_menu_keyboard(categories: list) -> InlineKeyboardBuilder:
    """Get keyboard for sorting categories."""
    builder = InlineKeyboardBuilder()
    
    # Auto-sort options
    builder.row(InlineKeyboardButton(text="🔢 За порядком (0-9)", callback_data="admin_cat_sort:order_asc"))
    builder.row(InlineKeyboardButton(text="🔢 За порядком (9-0)", callback_data="admin_cat_sort:order_desc"))
    builder.row(InlineKeyboardButton(text="А-Я За назвою (UA)", callback_data="admin_cat_sort:name_ua"))
    builder.row(InlineKeyboardButton(text="Я-А За назвою (UA)", callback_data="admin_cat_sort:name_ua_desc"))
    builder.row(InlineKeyboardButton(text="🔄 Перемішати", callback_data="admin_cat_sort:shuffle"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_categories"))
    
    return builder.as_markup()


def get_skip_keyboard() -> InlineKeyboardBuilder:
    """Get skip button."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Пропустити ➡️", callback_data="admin_cat_skip"))
    return builder.as_markup()


# ========== HANDLERS ==========

@router.callback_query(F.data == "admin_categories")
async def show_category_management(callback: CallbackQuery, session: AsyncSession, page: int = 0):
    """Show category management menu with pagination."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    query = select(Category).order_by(Category.sort_order.asc())
    result = await session.execute(query)
    all_categories = result.scalars().all()
    
    # Calculate pagination
    total_categories = len(all_categories)
    total_pages = max(1, (total_categories + CATEGORIES_PER_PAGE - 1) // CATEGORIES_PER_PAGE)
    page = min(page, total_pages - 1)
    start_idx = page * CATEGORIES_PER_PAGE
    end_idx = min(start_idx + CATEGORIES_PER_PAGE, total_categories)
    categories_page = all_categories[start_idx:end_idx]
    
    # Get product counts for each category
    category_counts = {}
    for cat in all_categories:
        prod_query = select(func.count(Product.id)).where(Product.category == cat.slug)
        prod_result = await session.execute(prod_query)
        category_counts[cat.id] = prod_result.scalar() or 0
    
    # Build text with stats
    active_count = sum(1 for c in all_categories if c.is_active)
    total_products = sum(category_counts.values())
    
    text = (
        f"<b>📂 Управління категоріями</b>\n\n"
        f"<i>Всього: {total_categories} | Активних: {active_count} | Товарів: {total_products}</i>\n\n"
        "Тут ви можете створювати, редагувати та сортувати категорії товарів.\n"
        "Порядок сортування впливає на відображення в меню."
    )
    
    # Build keyboard with product counts
    builder = InlineKeyboardBuilder()
    
    for cat in categories_page:
        status_icon = "✅" if cat.is_active else "🚫"
        has_image = "🖼️" if cat.image_file_id or cat.image_path else ""
        prod_count = category_counts.get(cat.id, 0)
        builder.row(InlineKeyboardButton(
            text=f"{status_icon} {cat.name_ua} #{cat.sort_order} {has_image} ({prod_count})",
            callback_data=f"admin_cat_edit:{cat.id}"
        ))
    
    # Pagination
    if total_pages > 1:
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(InlineKeyboardButton(
                text="⬅️",
                callback_data=f"admin_cat_page:{page-1}"
            ))
        pagination_buttons.append(InlineKeyboardButton(
            text=f"{page + 1}/{total_pages}",
            callback_data="admin_cat_page_info"
        ))
        if page < total_pages - 1:
            pagination_buttons.append(InlineKeyboardButton(
                text="➡️",
                callback_data=f"admin_cat_page:{page+1}"
            ))
        builder.row(*pagination_buttons)
    
    builder.row(InlineKeyboardButton(text="🔄 Сортування", callback_data="admin_cat_sort_menu"))
    builder.row(InlineKeyboardButton(text="➕ Додати категорію", callback_data="admin_cat_add"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main"))
    
    keyboard = builder.as_markup()
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_cat_page:"))
async def handle_category_page(callback: CallbackQuery, session: AsyncSession):
    """Handle pagination of category list."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    page = int(callback.data.split(":")[1])
    await show_category_management(callback, session, page)
    await callback.answer()


@router.callback_query(F.data == "admin_cat_sort_menu")
async def show_sort_menu(callback: CallbackQuery, session: AsyncSession):
    """Show sorting options menu."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    query = select(Category).order_by(Category.sort_order.asc())
    result = await session.execute(query)
    categories = result.scalars().all()
    
    keyboard = get_category_sort_menu_keyboard(categories)
    
    text = (
        "<b>🔄 Сортування категорій</b>\n\n"
        "Оберіть спосіб сортування:"
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_cat_sort:"))
async def handle_category_sort(callback: CallbackQuery, session: AsyncSession):
    """Handle category sorting options."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    sort_type = callback.data.split(":")[1]
    
    if sort_type == "order_asc":
        query = select(Category).order_by(Category.sort_order.asc())
    elif sort_type == "order_desc":
        query = select(Category).order_by(Category.sort_order.desc())
    elif sort_type == "name_ua":
        query = select(Category).order_by(Category.name_ua.asc())
    elif sort_type == "name_ua_desc":
        query = select(Category).order_by(Category.name_ua.desc())
    elif sort_type == "shuffle":
        import random
        query = select(Category)
        result = await session.execute(query)
        categories = list(result.scalars().all())
        random.shuffle(categories)
        for i, cat in enumerate(categories):
            cat.sort_order = (i + 1) * 10
        await session.commit()
        await callback.answer("🔄 Категорії перемішано!")
        await show_category_management(callback, session)
        return
    else:
        query = select(Category).order_by(Category.sort_order.asc())
    
    result = await session.execute(query)
    categories = result.scalars().all()
    
    # Apply new sort order
    for i, cat in enumerate(categories):
        cat.sort_order = (i + 1) * 10
    
    await session.commit()
    await callback.answer("✅ Сортування застосовано!")
    await show_category_management(callback, session)


# --- ADD CATEGORY FROM PRODUCT FLOW ---

@router.callback_query(F.data == "admin_cat_add_from_product")
async def start_add_category_from_product(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Start category creation flow from product add - will return to product add after."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    await state.clear()
    await state.update_data(return_to_product_add=True)
    await state.set_state(AdminStates.waiting_for_category_name)
    
    await callback.message.answer(
        "📝 <b>Створення нової категорії</b>\n\n"
        "<b>Крок 1/4: Назва (UA)</b>\n"
        "Введіть назву категорії українською мовою:\n"
        "Наприклад: <i>Зернова кава</i>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# --- ADD CATEGORY FLOW ---

@router.callback_query(F.data == "admin_cat_add")
async def start_add_category(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Start category creation flow."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    await state.clear()
    await state.set_state(AdminStates.waiting_for_category_name)
    
    await callback.message.answer(
        "📝 <b>Крок 1/4: Назва (UA)</b>\n"
        "Введіть назву категорії українською мовою:\n"
        "Наприклад: <i>Зернова кава</i>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_category_name)
async def process_category_name(message: Message, state: FSMContext):
    """Process UA name."""
    await state.update_data(name_ua=message.text)
    
    # Next step: EN name
    await state.set_state(AdminStates.waiting_for_category_name_en)
    
    kb = get_skip_keyboard()
    # Add cancel button manually since get_skip_keyboard returns markup
    # We can reconstruct or just allow /cancel via command which is global
    
    await message.answer(
        "🇬🇧 <b>Крок 2/4: Назва (English)</b>\n"
        "Введіть назву англійською (для інтерфейсу іншою мовою):\n"
        "Наприклад: <i>Coffee Beans</i>\n\n"
        "Можна пропустити.",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.message(AdminStates.waiting_for_category_name_en)
async def process_category_name_en(message: Message, state: FSMContext):
    """Process EN name."""
    await state.update_data(name_en=message.text)
    await process_slug_step(message, state)


@router.callback_query(AdminStates.waiting_for_category_name_en, F.data == "admin_cat_skip")
async def skip_category_name_en(callback: CallbackQuery, state: FSMContext):
    """Skip EN name."""
    await state.update_data(name_en=None)
    await process_slug_step(callback.message, state)
    await callback.answer()


async def process_slug_step(message: Message, state: FSMContext):
    """Common step to ask for slug."""
    data = await state.get_data()
    name_ua = data['name_ua']
    
    # Simple slugify
    slug_suggestion = name_ua.lower().strip()
    slug_replacements = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'h', 'ґ': 'g', 'д': 'd', 'е': 'e',
        'є': 'ye', 'ж': 'zh', 'з': 'z', 'и': 'y', 'і': 'i', 'ї': 'yi', 'й': 'y',
        'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
        'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch',
        'ш': 'sh', 'щ': 'shch', 'ь': '', 'ю': 'yu', 'я': 'ya', ' ': '_'
    }
    
    for cyr, lat in slug_replacements.items():
        slug_suggestion = slug_suggestion.replace(cyr, lat)
    
    # Remove non-alphanumeric (except underscore)
    slug_suggestion = "".join(c for c in slug_suggestion if c.isalnum() or c == '_')
    
    await state.set_state(AdminStates.waiting_for_category_slug)
    await message.answer(
        f"🔗 <b>Крок 3/4: Системний код (slug)</b>\n"
        f"Унікальний ідентифікатор для системи. Тільки латиниця та `_`.\n\n"
        f"Пропозиція: <code>{slug_suggestion}</code>\n"
        f"Введіть свій варіант або скопіюйте запропонований.",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(AdminStates.waiting_for_category_slug)
async def process_category_slug(message: Message, state: FSMContext, session: AsyncSession):
    """Process slug - for both creation and editing."""
    data = await state.get_data()
    is_edit = data.get('action') == 'change_slug'
    cat_id = data.get('cat_id')
    
    slug = message.text.strip().lower()
    
    # Validate format
    import re
    if not re.match(r'^[a-z0-9_]+$', slug):
        await message.answer("❌ Некоректний формат! Тільки латинські літери, цифри та `_`.")
        return
    
    # Check uniqueness (excluding current category if editing)
    query = select(Category).where(Category.slug == slug)
    if is_edit and cat_id:
        query = query.where(Category.id != cat_id)
    result = await session.execute(query)
    if result.scalar_one_or_none():
        await message.answer("❌ Такий slug вже існує! Придумайте інший.")
        return
    
    if is_edit:
        # Update existing category
        query = select(Category).where(Category.id == cat_id)
        result = await session.execute(query)
        category = result.scalar_one_or_none()
        
        if category:
            old_slug = category.slug
            category.slug = slug
            
            # Update all products that use this category
            from sqlalchemy import update
            await session.execute(
                update(Product).where(Product.category == old_slug).values(category=slug)
            )
            
            await session.commit()
            
            await message.answer(
                f"✅ <b>Slug оновлено!</b>\n\n"
                f"Старий: <code>{old_slug}</code>\n"
                f"Новий: <code>{slug}</code>",
                reply_markup=get_admin_main_menu_keyboard(),
                parse_mode="HTML"
            )
        else:
            await message.answer("❌ Категорію не знайдено.")
        
        await state.clear()
    else:
        # Creating new category
        await state.update_data(slug=slug)
        
        # Find next sort order
        query_max = select(func.max(Category.sort_order))
        result_max = await session.execute(query_max)
        max_order = result_max.scalar() or 0
        next_order = max_order + 10
        
        await state.update_data(sort_order=next_order)
        
        # Finalize creation
        await create_category(message, state, session)


async def create_category(message: Message, state: FSMContext, session: AsyncSession):
    """Create the category in DB."""
    data = await state.get_data()
    return_to_product_add = data.get('return_to_product_add', False)
    
    try:
        new_category = Category(
            slug=data['slug'],
            name_ua=data['name_ua'],
            name_en=data.get('name_en'),
            sort_order=data['sort_order'],
            is_active=True
        )
        session.add(new_category)
        await session.commit()
        
        # Refresh session to get the new category ID
        await session.refresh(new_category)
        
        if return_to_product_add:
            # Return to product add flow with the new category
            from src.keyboards.admin_kb import get_product_category_keyboard
            
            await state.update_data(category=new_category.slug)
            await state.set_state(AdminStates.waiting_for_product_name)
            
            await message.answer(
                f"✅ Категорія <b>{new_category.name_ua}</b> створена!\n\n"
                f"Тепер продовжуємо додавання товару.\n\n"
                f"📝 <b>Крок 1: Назва товару (UA)</b>\n"
                "Введіть повну назву товару:",
                reply_markup=get_cancel_keyboard(),
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"✅ Категорія <b>{new_category.name_ua}</b> успішно створена!\n"
                f"Slug: <code>{new_category.slug}</code>\n"
                f"Порядок: {new_category.sort_order}",
                reply_markup=get_admin_main_menu_keyboard(),
                parse_mode="HTML"
            )
            await state.clear()
            
    except Exception as e:
        logger.error(f"Error creating category: {e}")
        await message.answer("❌ Помилка при збереженні в базу даних.")
        await state.clear()


# --- EDIT FLOW ---

@router.callback_query(F.data.startswith("admin_cat_edit:"))
async def edit_category(callback: CallbackQuery, session: AsyncSession):
    """Show category edit menu."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
        
    try:
        cat_id = int(callback.data.split(":")[1])
    except ValueError:
        await callback.answer("❌ Помилка ID", show_alert=True)
        return
    
    query = select(Category).where(Category.id == cat_id)
    result = await session.execute(query)
    category = result.scalar_one_or_none()
    
    if not category:
        await callback.answer("❌ Категорія не знайдена", show_alert=True)
        return
    
    # Get product count
    prod_query = select(func.count(Product.id)).where(Product.category == category.slug)
    prod_result = await session.execute(prod_query)
    product_count = prod_result.scalar() or 0
    
    # Check if has image
    has_image = bool(category.image_file_id or category.image_path)
    
    text = f"""
<b>📂 Редагування категорії #{category.id}</b>

🇺🇦 Назва: <b>{category.name_ua}</b>
🇬🇧 Назва EN: {category.name_en or '---'}
🔗 Slug: <code>{category.slug}</code>
🔢 Порядок: {category.sort_order}
📦 Товарів: {product_count}
Статус: {"✅ Активна" if category.is_active else "🚫 Прихована"}
"""
    keyboard = get_category_edit_keyboard(category.id, category.is_active, has_image, product_count)
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# --- MOVE CATEGORY UP/DOWN ---

@router.callback_query(F.data.startswith("admin_cat_move:"))
async def move_category(callback: CallbackQuery, session: AsyncSession):
    """Move category up or down in the list."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    parts = callback.data.split(":")
    cat_id = int(parts[1])
    direction = parts[2]  # 'up' or 'down'
    
    # Get all categories ordered by sort_order
    query = select(Category).order_by(Category.sort_order.asc())
    result = await session.execute(query)
    categories = list(result.scalars().all())
    
    # Find current category
    current_idx = None
    for i, cat in enumerate(categories):
        if cat.id == cat_id:
            current_idx = i
            break
    
    if current_idx is None:
        await callback.answer("❌ Категорію не знайдено", show_alert=True)
        return
    
    # Calculate swap target
    if direction == "up" and current_idx > 0:
        target_idx = current_idx - 1
    elif direction == "down" and current_idx < len(categories) - 1:
        target_idx = current_idx + 1
    else:
        await callback.answer("🚫 Неможливо перемістити", show_alert=True)
        return
    
    # Swap sort orders
    current_cat = categories[current_idx]
    target_cat = categories[target_idx]
    
    current_order = current_cat.sort_order
    target_order = target_cat.sort_order
    
    current_cat.sort_order = target_order
    target_cat.sort_order = current_order
    
    await session.commit()
    
    direction_text = "⬆️ Вгору" if direction == "up" else "⬇️ Вниз"
    await callback.answer(f"✅ Переміщено {direction_text}")
    
    # Refresh view
    await edit_category(callback, session)


# --- CHANGE SLUG ---

@router.callback_query(F.data.startswith("admin_cat_change_slug:"))
async def start_change_slug(callback: CallbackQuery, state: FSMContext):
    """Start slug change flow."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    cat_id = int(callback.data.split(":")[1])
    await state.update_data(cat_id=cat_id, action="change_slug")
    await state.set_state(AdminStates.waiting_for_category_slug)
    
    await callback.message.answer(
        "🔗 <b>Зміна slug</b>\n\n"
        "Введіть новий slug (тільки латинські літери, цифри та `_`):",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_cat_del_confirm:"))
async def confirm_delete_category(callback: CallbackQuery, session: AsyncSession):
    """Show delete confirmation dialog."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    cat_id = int(callback.data.split(":")[1])
    
    query = select(Category).where(Category.id == cat_id)
    result = await session.execute(query)
    category = result.scalar_one_or_none()
    
    if not category:
        await callback.answer("❌ Категорію не знайдено", show_alert=True)
        return
    
    text = (
        f"<b>⚠️ Підтвердження видалення</b>\n\n"
        f"Ви впевнені, що хочете видалити категорію <b>{category.name_ua}</b>?\n\n"
        f"Ця дія <b>незворотня</b>!"
    )
    
    keyboard = get_category_delete_confirm_keyboard(category.id)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_cat_del_final:"))
async def final_delete_category(callback: CallbackQuery, session: AsyncSession):
    """Actually delete the category."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    cat_id = int(callback.data.split(":")[1])
    
    query = select(Category).where(Category.id == cat_id)
    result = await session.execute(query)
    category = result.scalar_one_or_none()
    
    if not category:
        await callback.answer("❌ Категорію не знайдено", show_alert=True)
        return
    
    cat_name = category.name_ua
    
    # Delete the category
    await session.delete(category)
    await session.commit()
    
    await callback.answer("🗑 Категорію видалено!")
    
    # Show updated list
    await show_category_management(callback, session)


# --- PREVIEW CATEGORY IMAGE ---

@router.callback_query(F.data.startswith("admin_cat_preview:"))
async def preview_category_image(callback: CallbackQuery, session: AsyncSession):
    """Preview category image."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    cat_id = int(callback.data.split(":")[1])
    
    query = select(Category).where(Category.id == cat_id)
    result = await session.execute(query)
    category = result.scalar_one_or_none()
    
    if not category:
        await callback.answer("❌ Категорію не знайдено", show_alert=True)
        return
    
    # Try to show image
    if category.image_file_id:
        # Send from Telegram file_id
        try:
            await callback.message.answer_photo(
                photo=category.image_file_id,
                caption=f"🖼️ <b>{category.name_ua}</b>",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Error sending photo by file_id: {e}")
            await callback.answer("❌ Не вдалося завантажити зображення", show_alert=True)
    elif category.image_path:
        # Send local file
        try:
            path = Path(category.image_path)
            if path.exists():
                await callback.message.answer_photo(
                    FSInputFile(path),
                    caption=f"🖼️ <b>{category.name_ua}</b>",
                    parse_mode="HTML"
                )
            else:
                await callback.answer("❌ Файл не знайдено", show_alert=True)
        except Exception as e:
            logger.error(f"Error sending local image: {e}")
            await callback.answer("❌ Не вдалося завантажити зображення", show_alert=True)
    else:
        await callback.answer("❌ Зображення відсутнє", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin_cat_rename:"))
async def start_category_rename(callback: CallbackQuery, state: FSMContext):
    """Start rename flow."""
    parts = callback.data.split(":")
    cat_id = int(parts[1])
    lang = parts[2]  # 'ua' or 'en'
    
    await state.update_data(cat_id=cat_id, lang=lang)
    await state.set_state(AdminStates.waiting_for_category_rename)
    
    lang_str = "українською" if lang == 'ua' else "англійською"
    
    await callback.message.answer(
        f"✏️ Введіть нову назву для категорії {lang_str}:",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_category_rename)
async def process_category_rename_final(message: Message, state: FSMContext, session: AsyncSession):
    """Update name."""
    data = await state.get_data()
    cat_id = data['cat_id']
    lang = data['lang']
    new_name = message.text.strip()
    
    query = select(Category).where(Category.id == cat_id)
    result = await session.execute(query)
    category = result.scalar_one_or_none()
    
    if category:
        if lang == 'ua':
            category.name_ua = new_name
        else:
            category.name_en = new_name
            
        await session.commit()
        
        # Return to category edit view
        await message.answer(f"✅ Назву оновлено!")
        callback_data = f"admin_cat_edit:{cat_id}"
        
        # Create a mock callback to reuse edit_category
        from aiogram.types import CallbackQuery
        # Just call edit_category logic directly
        text = f"""
<b>📂 Редагування категорії #{category.id}</b>

🇺🇦 Назва: <b>{category.name_ua}</b>
🇬🇧 Назва EN: {category.name_en or '---'}
🔗 Slug: <code>{category.slug}</code>
🔢 Порядок: {category.sort_order}
Статус: {"✅ Активна" if category.is_active else "🚫 Прихована"}
"""
        keyboard = get_category_edit_keyboard(category.id, category.is_active)
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.answer("❌ Категорію не знайдено.")
        
    await state.clear()


@router.callback_query(F.data.startswith("admin_cat_toggle:"))
async def toggle_category(callback: CallbackQuery, session: AsyncSession):
    """Toggle active status."""
    cat_id = int(callback.data.split(":")[1])
    
    query = select(Category).where(Category.id == cat_id)
    result = await session.execute(query)
    category = result.scalar_one_or_none()
    
    if category:
        category.is_active = not category.is_active
        await session.commit()
        await callback.answer(f"Статус змінено на: {'✅' if category.is_active else '🚫'}")
        
        # Refresh view
        callback.data = f"admin_cat_edit:{cat_id}"
        await edit_category(callback, session)


@router.callback_query(F.data.startswith("admin_cat_reorder:"))
async def start_reorder(callback: CallbackQuery, state: FSMContext):
    """Start reorder flow (simple manual input for now)."""
    cat_id = int(callback.data.split(":")[1])
    await state.update_data(cat_id=cat_id)
    await state.set_state(AdminStates.waiting_for_category_sort_order)
    
    await callback.message.answer(
        "🔢 Введіть новий номер для сортування (число):\n"
        "Менше число = вище в списку.",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_category_sort_order)
async def process_reorder(message: Message, state: FSMContext, session: AsyncSession):
    try:
        new_order = int(message.text)
    except ValueError:
        await message.answer("❌ Будь ласка, введіть ціле число.")
        return
        
    data = await state.get_data()
    cat_id = data['cat_id']
    
    query = select(Category).where(Category.id == cat_id)
    result = await session.execute(query)
    category = result.scalar_one_or_none()
    
    if category:
        category.sort_order = new_order
        await session.commit()
        await message.answer(f"✅ Порядок змінено на {new_order}.", reply_markup=get_admin_main_menu_keyboard())
    else:
        await message.answer("❌ Категорію не знайдено.")
        
    await state.clear()


@router.callback_query(F.data.startswith("admin_cat_del:"))
async def delete_category_check(callback: CallbackQuery, session: AsyncSession):
    """Check before deleting - redirect to confirmation if has products."""
    cat_id = int(callback.data.split(":")[1])
    
    cat_query = select(Category).where(Category.id == cat_id)
    cat = (await session.execute(cat_query)).scalar_one_or_none()
    
    if not cat:
        await callback.answer("Kategorie ne znaydena", show_alert=True)
        return

    # Count products with this category slug
    prod_query = select(func.count(Product.id)).where(Product.category == cat.slug)
    prod_count = (await session.execute(prod_query)).scalar() or 0
    
    if prod_count > 0:
        # Show error - can't delete
        await callback.answer(f"❌ Ne mozhna vydalyty! U kategoriyi ye {prod_count} tovariv.", show_alert=True)
        return
    
    # If no products, go to confirmation
    callback.data = f"admin_cat_del_confirm:{cat_id}"
    await confirm_delete_category(callback, session)


# --- IMAGE MANAGEMENT ---

@router.callback_query(F.data.startswith("admin_cat_image:"))
async def start_category_image_update(callback: CallbackQuery, state: FSMContext):
    """Start category image update flow - show options."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    cat_id = int(callback.data.split(":")[1])
    await state.update_data(cat_id=cat_id)
    
    # Build options keyboard
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🤖 Згенерувати з AI",
        callback_data=f"admin_cat_ai_gen:{cat_id}"
    ))
    builder.row(InlineKeyboardButton(
        text="📤 Завантажити своє",
        callback_data=f"admin_cat_upload:{cat_id}"
    ))
    builder.row(InlineKeyboardButton(
        text="❌ Видалити зображення",
        callback_data=f"admin_cat_img_del:{cat_id}"
    ))
    builder.row(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data=f"admin_cat_edit:{cat_id}"
    ))
    
    await callback.message.edit_text(
        "🖼️ <b>Зображення категорії</b>\n\n"
        "Оберіть дію:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_cat_ai_gen:"))
async def generate_category_image_ai(callback: CallbackQuery, session: AsyncSession):
    """Generate category image using AI (DALL-E)."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    cat_id = int(callback.data.split(":")[1])
    
    # Get category info
    query = select(Category).where(Category.id == cat_id)
    result = await session.execute(query)
    category = result.scalar_one_or_none()
    
    if not category:
        await callback.answer("❌ Категорію не знайдено", show_alert=True)
        return
    
    # Send loading message
    loading_msg = await callback.message.answer(
        "🤖 <b>AI генерує зображення...</b>\n"
        "<i>Це може зайняти 10-30 секунд.</i>",
        parse_mode="HTML"
    )
    
    try:
        from src.services.ai_service import ai_service
        
        # Determine profile from slug - map Ukrainian category names to profiles
        profile = None
        category_slug = category.slug.lower() if category.slug else ""
        
        # Map slugs and names to profiles
        if category_slug in ["espresso", "espresso_coffee"]:
            profile = "espresso"
        elif category_slug in ["filter", "filter_coffee", "альтернатива"]:
            profile = "filter"
        elif category_slug in ["universal", "coffee", "кава"]:
            profile = "universal"
        else:
            # Also check the Ukrainian name
            name_lower = category.name_ua.lower() if category.name_ua else ""
            if "еспресо" in name_lower:
                profile = "espresso"
            elif "фільтр" in name_lower or "альтернатива" in name_lower:
                profile = "filter"
            elif "універсальн" in name_lower:
                profile = "universal"
        
        # Generate image - pass both name and profile for better prompt
        save_path = ASSETS_DIR / f"category_{category.slug}.png"
        image_url, error, local_path = await ai_service.generate_category_image(
            category_name=category.name_ua or category.slug,
            profile=profile,
            save_path=save_path
        )
        
        await loading_msg.delete()
        
        if error:
            await callback.message.answer(
                f"❌ <b>Помилка генерації</b>\n\n{error}",
                parse_mode="HTML"
            )
            return
        
        if local_path:
            # Save to database - store relative path for portability
            try:
                # Try to make path relative to project root
                category.image_path = str(local_path)
                await session.commit()
            except Exception as db_error:
                logger.error(f"Error saving image path to DB: {db_error}")
                # Still show the image even if DB save fails
            
            await callback.message.answer_photo(
                FSInputFile(local_path),
                caption=f"✅ <b>Зображення для {category.name_ua} згенеровано!</b>\n\n"
                        f"Збережено локально.",
                parse_mode="HTML"
            )
        else:
            # If URL was returned but not saved locally
            if image_url:
                await callback.message.answer(
                    f"⚠️ Зображення згенеровано.\n"
                    f"URL: {image_url}\n\n"
                    f"Спробуйте ще раз або завантажте вручну.",
                    parse_mode="HTML"
                )
            else:
                await callback.message.answer(
                    "❌ Не вдалося згенерувати зображення. Спробуйте пізніше.",
                    parse_mode="HTML"
                )
            
    except Exception as e:
        logger.error(f"Error generating category image: {e}", exc_info=True)
        try:
            await loading_msg.delete()
        except:
            pass
        await callback.message.answer(f"❌ Помилка: {str(e)}", parse_mode="HTML")
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin_cat_upload:"))
async def start_category_image_upload(callback: CallbackQuery, state: FSMContext):
    """Ask admin to upload image for category."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    cat_id = int(callback.data.split(":")[1])
    await state.update_data(cat_id=cat_id)
    await state.set_state(AdminStates.waiting_for_module_image)
    
    await callback.message.answer(
        "📤 <b>Завантаження зображення</b>\n\n"
        "Надішліть фото для категорії:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_module_image, F.photo)
async def process_category_image_upload(message: Message, state: FSMContext, session: AsyncSession):
    """Save uploaded category image."""
    data = await state.get_data()
    cat_id = data.get('cat_id')
    
    if not cat_id:
        await message.answer("❌ Помилка сесії. Спробуйте знову.")
        await state.clear()
        return
    
    # Get photo file_id
    file_id = message.photo[-1].file_id
    
    # Get category
    query = select(Category).where(Category.id == cat_id)
    result = await session.execute(query)
    category = result.scalar_one_or_none()
    
    if not category:
        await message.answer("❌ Категорію не знайдено.")
        await state.clear()
        return
    
    # Save to database (file_id for Telegram)
    category.image_file_id = file_id
    await session.commit()
    
    await message.answer(
        f"✅ <b>Зображення для {category.name_ua} завантажено!</b>",
        parse_mode="HTML"
    )
    await state.clear()


@router.callback_query(F.data.startswith("admin_cat_img_del:"))
async def delete_category_image(callback: CallbackQuery, session: AsyncSession):
    """Delete category image."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    cat_id = int(callback.data.split(":")[1])
    
    query = select(Category).where(Category.id == cat_id)
    result = await session.execute(query)
    category = result.scalar_one_or_none()
    
    if not category:
        await callback.answer("❌ Категорію не знайдено", show_alert=True)
        return
    
    # Clear image fields
    category.image_file_id = None
    category.image_path = None
    await session.commit()
    
    await callback.answer("🗑 Зображення видалено")
    await callback.message.edit_text(
        f"✅ <b>Зображення для {category.name_ua} видалено!</b>",
        parse_mode="HTML"
    )
