"""Wholesale discount management handlers."""
import logging
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import VolumeDiscount
from src.states.admin_states import AdminStates
from src.keyboards.main_menu import get_cancel_keyboard, get_admin_main_menu_keyboard
from config import settings

router = Router()
logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    return user_id in settings.admin_id_list


# ========== KEYBOARDS ==========

def get_discount_management_keyboard(discounts: list) -> InlineKeyboardBuilder:
    """Get keyboard for discount management."""
    builder = InlineKeyboardBuilder()
    
    for discount in discounts:
        status_icon = "✅" if discount.is_active else "🚫"
        if discount.discount_type == 'weight':
            unit = "кг"
        elif discount.discount_type == 'packs':
            unit = "шт"
        else:
            unit = "грн"
        
        # Format: [✅] > 5кг (-10%)
        text = f"{status_icon} > {discount.threshold}{unit} (-{discount.discount_percent}%)"
        
        builder.row(InlineKeyboardButton(
            text=text,
            callback_data=f"admin_disc_edit:{discount.id}"
        ))
        
    builder.row(InlineKeyboardButton(text="➕ Додати знижку", callback_data="admin_disc_add"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_content_main"))
    
    return builder.as_markup()


def get_discount_edit_keyboard(discount_id: int, is_active: bool) -> InlineKeyboardBuilder:
    """Get keyboard for editing a discount."""
    builder = InlineKeyboardBuilder()
    
    toggle_text = "Деактивувати 🚫" if is_active else "Активувати ✅"
    
    builder.row(InlineKeyboardButton(text="🗑 Видалити", callback_data=f"admin_disc_del:{discount_id}"))
    builder.row(InlineKeyboardButton(text=toggle_text, callback_data=f"admin_disc_toggle:{discount_id}"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_content_discounts"))
    
    return builder.as_markup()


def get_discount_type_keyboard() -> InlineKeyboardBuilder:
    """Get keyboard for discount type."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⚖️ Вага (кг)", callback_data="admin_disc_type:weight"))
    builder.row(InlineKeyboardButton(text="📦 Кількість (пачки)", callback_data="admin_disc_type:packs"))
    builder.row(InlineKeyboardButton(text="💰 Сума (грн)", callback_data="admin_disc_type:price"))
    builder.row(InlineKeyboardButton(text="🔙 Скасувати", callback_data="admin_content_discounts"))
    return builder.as_markup()


# ========== HANDLERS ==========

@router.callback_query(F.data == "admin_content_discounts")
async def show_discount_management(callback: CallbackQuery, session: AsyncSession):
    """Show discount management menu."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    query = select(VolumeDiscount).order_by(VolumeDiscount.threshold.asc())
    result = await session.execute(query)
    discounts = result.scalars().all()
    
    keyboard = get_discount_management_keyboard(discounts)
    
    text = (
        "<b>⚡ Оптові знижки</b>\n\n"
        "Налаштуйте автоматичні знижки залежно від обсягу замовлення.\n"
        "Система автоматично застосує найбільшу доступну знижку."
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# --- ADD DISCOUNT WIZARD ---

@router.callback_query(F.data == "admin_disc_add")
async def start_add_discount(callback: CallbackQuery, state: FSMContext):
    """Start discount creation flow."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    await state.clear()
    await state.set_state(AdminStates.waiting_for_volume_discount_type)
    
    await callback.message.edit_text(
        "⚖️ <b>Крок 1/4: Тип умови</b>\n\n"
        "Від чого залежить знижка?\n"
        "• <b>Вага</b> — загальна вага кави в кошику.\n"
        "• <b>Кількість</b> — кількість пачок кави.\n"
        "• <b>Сума</b> — загальна вартість кошика.",
        reply_markup=get_discount_type_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(AdminStates.waiting_for_volume_discount_type, F.data.startswith("admin_disc_type:"))
async def process_discount_type(callback: CallbackQuery, state: FSMContext):
    """Process type selection."""
    disc_type = callback.data.split(":")[1]
    await state.update_data(disc_type=disc_type)
    
    if disc_type == 'weight':
        unit = "кг (наприклад: 5.5)"
    elif disc_type == 'packs':
        unit = "штук (ціле число)"
    else:
        unit = "грн (ціле число)"
    
    await state.set_state(AdminStates.waiting_for_volume_discount_threshold)
    await callback.message.edit_text(
        f"🔢 <b>Крок 2/4: Поріг спрацювання</b>\n\n"
        f"Введіть мінімальну кількість {unit}, необхідну для отримання знижки:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_volume_discount_threshold)
async def process_discount_threshold(message: Message, state: FSMContext):
    """Process threshold value."""
    text = message.text.replace(",", ".").strip()
    
    try:
        threshold = float(text)
        if threshold <= 0:
            raise ValueError("Must be positive")
            
        await state.update_data(threshold=threshold)
        
        await state.set_state(AdminStates.waiting_for_volume_discount_percent)
        await message.answer(
            "📉 <b>Крок 3/4: Розмір знижки (%)</b>\n\n"
            "Введіть відсоток знижки (ціле число від 1 до 99):",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
    except ValueError:
        await message.answer("❌ Будь ласка, введіть коректне число (більше 0).")


@router.message(AdminStates.waiting_for_volume_discount_percent)
async def process_discount_percent(message: Message, state: FSMContext):
    """Process percent value."""
    try:
        percent = int(message.text)
        if not (1 <= percent <= 99):
            await message.answer("❌ Відсоток має бути від 1 до 99.")
            return
            
        await state.update_data(percent=percent)
        
        await state.set_state(AdminStates.waiting_for_volume_discount_description)
        await message.answer(
            "📝 <b>Крок 4/4: Опис (необов'язково)</b>\n\n"
            "Напишіть короткий коментар для адміністратора (наприклад: 'Для кав'ярень').\n"
            "Користувач цього не бачить.",
            reply_markup=get_skip_keyboard(),
            parse_mode="HTML"
        )
    except ValueError:
        await message.answer("❌ Введіть ціле число.")


@router.callback_query(AdminStates.waiting_for_volume_discount_description, F.data == "admin_disc_skip_desc")
async def skip_discount_description(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Skip description."""
    await state.update_data(description=None)
    await create_discount(callback.message, state, session)
    await callback.answer()


@router.message(AdminStates.waiting_for_volume_discount_description)
async def process_discount_description(message: Message, state: FSMContext, session: AsyncSession):
    """Process description."""
    await state.update_data(description=message.text)
    await create_discount(message, state, session)


async def create_discount(message: Message, state: FSMContext, session: AsyncSession):
    """Create the discount in DB."""
    data = await state.get_data()
    
    try:
        new_discount = VolumeDiscount(
            discount_type=data['disc_type'],
            threshold=data['threshold'],
            discount_percent=data['percent'],
            description=data.get('description'),
            is_active=True
        )
        session.add(new_discount)
        await session.commit()
        
        if new_discount.discount_type == 'weight':
            unit = "кг"
        elif new_discount.discount_type == 'packs':
            unit = "шт"
        else:
            unit = "грн"
        
        await message.answer(
            f"✅ <b>Знижку успішно створено!</b>\n\n"
            f"Умова: > {new_discount.threshold} {unit}\n"
            f"Знижка: -{new_discount.discount_percent}%\n"
            f"Статус: Активна",
            reply_markup=get_admin_main_menu_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error creating discount: {e}")
        await message.answer("❌ Помилка при збереженні.", reply_markup=get_admin_main_menu_keyboard())
        
    await state.clear()


# --- EDIT FLOW ---

@router.callback_query(F.data.startswith("admin_disc_edit:"))
async def edit_discount(callback: CallbackQuery, session: AsyncSession):
    """Show details and actions for a discount."""
    try:
        disc_id = int(callback.data.split(":")[1])
    except ValueError:
        await callback.answer("❌ Помилка ID", show_alert=True)
        return

    query = select(VolumeDiscount).where(VolumeDiscount.id == disc_id)
    result = await session.execute(query)
    discount = result.scalar_one_or_none()
    
    if not discount:
        await callback.answer("❌ Знижку не знайдено", show_alert=True)
        return
        
    if discount.discount_type == 'weight':
        unit = "кг"
    elif discount.discount_type == 'packs':
        unit = "шт"
    else:
        unit = "грн"
    status = "✅ Активна" if discount.is_active else "🚫 Неактивна"
    desc = discount.description if discount.description else "—"
    
    text = f"""
<b>⚡ Редагування знижки #{discount.id}</b>

<b>Умова:</b> > {discount.threshold} {unit}
<b>Знижка:</b> -{discount.discount_percent}%
<b>Статус:</b> {status}
<b>Опис:</b> {desc}
"""
    keyboard = get_discount_edit_keyboard(discount.id, discount.is_active)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_disc_toggle:"))
async def toggle_discount(callback: CallbackQuery, session: AsyncSession):
    """Toggle active status."""
    disc_id = int(callback.data.split(":")[1])
    
    query = select(VolumeDiscount).where(VolumeDiscount.id == disc_id)
    result = await session.execute(query)
    discount = result.scalar_one_or_none()
    
    if discount:
        discount.is_active = not discount.is_active
        await session.commit()
        await callback.answer(f"Статус змінено")
        
        # Refresh view
        callback.data = f"admin_disc_edit:{disc_id}"
        await edit_discount(callback, session)
    else:
        await callback.answer("❌ Не знайдено", show_alert=True)


@router.callback_query(F.data.startswith("admin_disc_del:"))
async def delete_discount(callback: CallbackQuery, session: AsyncSession):
    """Delete discount immediately."""
    disc_id = int(callback.data.split(":")[1])
    
    query = select(VolumeDiscount).where(VolumeDiscount.id == disc_id)
    result = await session.execute(query)
    discount = result.scalar_one_or_none()
    
    if discount:
        await session.delete(discount)
        await session.commit()
        await callback.answer("🗑 Знижку видалено")
        await show_discount_management(callback, session)
    else:
        await callback.answer("❌ Не знайдено", show_alert=True)
