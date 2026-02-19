"""Category management handlers."""
import logging
import asyncio
from typing import Optional

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Category, Product
from src.states.admin_states import AdminStates
from src.keyboards.main_menu import get_cancel_keyboard, get_admin_main_menu_keyboard
from config import settings

router = Router()
logger = logging.getLogger(__name__)


from src.utils.admin_utils import is_admin


# ========== KEYBOARDS ==========

def get_category_management_keyboard(categories: list) -> InlineKeyboardBuilder:
    """Get keyboard for category management."""
    builder = InlineKeyboardBuilder()
    
    for cat in categories:
        status_icon = "✅" if cat.is_active else "🚫"
        # Display: [Status] Name (Sort)
        builder.row(InlineKeyboardButton(
            text=f"{status_icon} {cat.name_ua} [#{cat.sort_order}]",
            callback_data=f"admin_cat_edit:{cat.id}"
        ))
        
    builder.row(InlineKeyboardButton(text="➕ Додати категорію", callback_data="admin_cat_add"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main"))
    
    return builder.as_markup()


def get_category_edit_keyboard(category_id: int, is_active: bool) -> InlineKeyboardBuilder:
    """Get keyboard for editing a category."""
    builder = InlineKeyboardBuilder()
    
    toggle_text = "Деактивувати 🚫" if is_active else "Активувати ✅"
    
    builder.row(InlineKeyboardButton(text="✏️ Змінити назву (UA)", callback_data=f"admin_cat_rename:{category_id}:ua"))
    builder.row(InlineKeyboardButton(text="✏️ Змінити назву (EN)", callback_data=f"admin_cat_rename:{category_id}:en"))
    builder.row(InlineKeyboardButton(text="🔢 Змінити порядок", callback_data=f"admin_cat_reorder:{category_id}"))
    builder.row(InlineKeyboardButton(text=toggle_text, callback_data=f"admin_cat_toggle:{category_id}"))
    builder.row(InlineKeyboardButton(text="🗑 Видалити", callback_data=f"admin_cat_del:{category_id}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_categories"))
    
    return builder.as_markup()


def get_skip_keyboard() -> InlineKeyboardBuilder:
    """Get skip button."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Пропустити ➡️", callback_data="admin_cat_skip"))
    return builder.as_markup()


# ========== HANDLERS ==========

@router.callback_query(F.data == "admin_categories")
async def show_category_management(callback: CallbackQuery, session: AsyncSession):
    """Show category management menu."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    query = select(Category).order_by(Category.sort_order.asc())
    result = await session.execute(query)
    categories = result.scalars().all()
    
    keyboard = get_category_management_keyboard(categories)
    
    text = (
        "<b>📂 Управління категоріями</b>\n\n"
        "Тут ви можете створювати, редагувати та сортувати категорії товарів.\n"
        "Порядок сортування впливає на відображення в меню."
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
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
    """Process slug."""
    slug = message.text.strip().lower()
    
    # Validate format
    import re
    if not re.match(r'^[a-z0-9_]+$', slug):
        await message.answer("❌ Некоректний формат! Тільки латинські літери, цифри та `_`.")
        return

    # Check uniqueness
    query = select(Category).where(Category.slug == slug)
    result = await session.execute(query)
    if result.scalar_one_or_none():
        await message.answer("❌ Такий slug вже існує! Придумайте інший.")
        return
        
    await state.update_data(slug=slug)
    
    # Find next sort order
    query_max = select(func.max(Category.sort_order))
    result_max = await session.execute(query_max)
    max_order = result_max.scalar() or 0
    next_order = max_order + 10
    
    await state.update_data(sort_order=next_order)
    
    # Finalize creation (Step 4 is implied/auto)
    await create_category(message, state, session)


async def create_category(message: Message, state: FSMContext, session: AsyncSession):
    """Create the category in DB."""
    data = await state.get_data()
    
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
         
        await message.answer(
            f"✅ Категорія <b>{new_category.name_ua}</b> успішно створена!\n"
            f"Slug: <code>{new_category.slug}</code>\n"
            f"Порядок: {new_category.sort_order}",
            reply_markup=get_admin_main_menu_keyboard(),
            parse_mode="HTML"
        )
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
        
    text = f"""
<b>📂 Редагування категорії #{category.id}</b>

🇺🇦 Назва: <b>{category.name_ua}</b>
🇬🇧 Назва EN: {category.name_en or '---'}
🔗 Slug: <code>{category.slug}</code>
🔢 Порядок: {category.sort_order}
Статус: {"✅ Активна" if category.is_active else "🚫 Прихована"}
"""
    keyboard = get_category_edit_keyboard(category.id, category.is_active)
    
    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
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
        await message.answer(f"✅ Назву оновлено!", reply_markup=get_admin_main_menu_keyboard())
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
    """Check before deleting."""
    cat_id = int(callback.data.split(":")[1])
    
    # Check for products
    query_prod = select(func.count(Product.id)).where(Product.category == (
        select(Category.slug).where(Category.id == cat_id).scalar_subquery()
    ))
    # Note: Product.category stores the SLUG, not ID. We need to get slug first.
    
    cat_query = select(Category).where(Category.id == cat_id)
    cat = (await session.execute(cat_query)).scalar_one_or_none()
    
    if not cat:
        await callback.answer("Категорія не знайдена", show_alert=True)
        return

    # Count products with this category slug
    prod_query = select(func.count(Product.id)).where(Product.category == cat.slug)
    prod_count = (await session.execute(prod_query)).scalar() or 0
    
    if prod_count > 0:
        await callback.answer(f"❌ Не можна видалити! У категорії є {prod_count} товарів.", show_alert=True)
        return
        
    # If safe, delete
    await session.delete(cat)
    await session.commit()
    await callback.answer("🗑 Категорія видалена")
    await show_category_management(callback, session)
