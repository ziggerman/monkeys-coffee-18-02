"""Profile handler and repeat order logic."""
import logging
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import User, Order
from src.services.cart_service import CartService
from src.utils.formatters import format_currency, format_date
from src.utils.constants import CallbackPrefix
from src.states.profile_states import ProfileEditStates

router = Router()
logger = logging.getLogger(__name__)


def sanitize_user_input(text: str, max_length: int = 255) -> str:
    """Sanitize user input to prevent injection."""
    if not text:
        return ""
    # Remove any special characters that could cause issues
    text = text.strip()
    if len(text) > max_length:
        text = text[:max_length]
    return text


@router.message(F.text == "👤 Мій Кабінет")
async def show_profile(message: Message, session: AsyncSession, state: FSMContext, user: User = None):
    """Show user profile."""
    user_id = message.from_user.id
    
    # Use user from middleware if available, otherwise query
    if not user:
        query = select(User).where(User.id == user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
    
    if not user:
        return

    # Use SQL aggregate functions for better performance
    stats_query = select(
        func.count(Order.id).label('orders_count'),
        func.coalesce(func.sum(Order.total), 0).label('total_spent')
    ).where(
        Order.user_id == user_id,
        Order.status == "paid"
    )
    stats_result = await session.execute(stats_query)
    stats = stats_result.one()
    
    orders_count = stats.orders_count
    total_spent = stats.total_spent
    
    text = f"""
👤 <b>Особистий Кабінет</b> 🐒
{user.first_name} {user.last_name or ''}

━━━━━━━━━━━━━━━━━━━━━━
<b>📊 Твоя статистика:</b>
• Замовлень: <b>{orders_count}</b>
• Всього витрачено: <b>{format_currency(total_spent)}</b>
• Бонусний рахунок: <b>0 грн</b> (в розробці)

<b>📍 Твої дані доставки:</b>
• Місто: {user.delivery_city or 'Не вказано'}
• Адреса: {user.last_address or 'Не вказано'}
• Телефон: {user.phone or 'Не вказано'}
"""

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    
    # Add "Repeat Last Order" button if history exists
    if orders_count > 0:
        builder.row(InlineKeyboardButton(
            text="🔄 Повторити останнє замовлення",
            callback_data="profile_repeat_order"
        ))
        
    builder.row(InlineKeyboardButton(
        text="✏️ Змінити дані",
        callback_data="profile_edit_data"
    ))
    
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data == "profile_repeat_order")
async def repeat_last_order(callback: CallbackQuery, session: AsyncSession):
    """Add items from last paid order to cart."""
    user_id = callback.from_user.id
    
    # Get last paid order with items
    query = select(Order).options(selectinload(Order.items)).where(
        Order.user_id == user_id,
        Order.status != "cancelled", 
        Order.status != "pending"
    ).order_by(Order.created_at.desc()).limit(1)
    
    result = await session.execute(query)
    last_order = result.scalar_one_or_none()
    
    if not last_order:
        await callback.answer("❌ Немає попередніх замовлень для повтору", show_alert=True)
        return
    
    # Add items to cart
    added_count = 0
    for item in last_order.items:
        await CartService.add_to_cart(
            session=session,
            user_id=user_id,
            product_id=item.product_id,
            format=item.format,
            quantity=item.quantity
        )
        added_count += 1
        
    if added_count > 0:
        await callback.answer(f"✅ {added_count} товарів додано в кошик!")
        # Redirect to cart
        from src.handlers.cart import show_cart
        await show_cart(callback, session)
    else:
        await callback.answer("⚠️ Не вдалося відновити товари (можливо, вони видалені)", show_alert=True)


@router.callback_query(F.data == "profile_edit_data")
async def edit_profile_data(callback: CallbackQuery, state: FSMContext):
    """Start profile editing flow."""
    await callback.answer()
    await callback.message.answer(
        "✏️ <b>Редагування даних</b>\n\n"
        "Введи <b>назва міста</b> для доставки:\n"
        "(або /cancel для скасування)",
        parse_mode="HTML"
    )
    await state.set_state(ProfileEditStates.waiting_for_city)


@router.message(ProfileEditStates.waiting_for_city)
async def process_city(message: Message, session: AsyncSession, state: FSMContext):
    """Process city input."""
    user_id = message.from_user.id
    
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer("❌ Редагування скасовано.")
        return
    
    city = sanitize_user_input(message.text, max_length=100)
    if len(city) < 2:
        await message.answer("❌ Занадто коротка назва міста. Спробуй ще раз:")
        return
    
    await state.update_data(delivery_city=city)
    
    # Get current address from user
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    current_address = user.last_address if user else None
    
    text = "✏️ Тепер введи <b>адресу</b> (вулиця, номер будинку, квартира або номер відділення НП):\n"
    if current_address:
        text += f"\nПоточна адреса: {current_address}\n"
    text += "\n(або /cancel для скасування)"
    
    await message.answer(text, parse_mode="HTML")
    await state.set_state(ProfileEditStates.waiting_for_address)


@router.message(ProfileEditStates.waiting_for_address)
async def process_address(message: Message, session: AsyncSession, state: FSMContext):
    """Process address input."""
    user_id = message.from_user.id
    
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer("❌ Редагування скасовано.")
        return
    
    address = sanitize_user_input(message.text, max_length=500)
    if len(address) < 5:
        await message.answer("❌ Занадто коротка адреса. Спробуй ще раз:")
        return
    
    await state.update_data(last_address=address)
    
    # Get current phone from user
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    current_phone = user.phone if user else None
    
    text = "✏️ Тепер введи <b>номер телефону</b> у форматі +380XXXXXXXXX:\n"
    if current_phone:
        text += f"\nПоточний телефон: {current_phone}\n"
    text += "\n(або /cancel для скасування)"
    
    await message.answer(text, parse_mode="HTML")
    await state.set_state(ProfileEditStates.waiting_for_phone)


@router.message(ProfileEditStates.waiting_for_phone)
async def process_phone(message: Message, session: AsyncSession, state: FSMContext):
    """Process phone input and save all data."""
    user_id = message.from_user.id
    
    if message.text == "❌ Скасувати":
        await state.clear()
        await message.answer("❌ Редагування скасовано.")
        return
    
    phone = sanitize_user_input(message.text, max_length=20)
    
    # Basic phone validation
    # Remove spaces and dashes for validation
    clean_phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    
    if len(clean_phone) < 10:
        await message.answer("❌ Занадто короткий номер телефону. Спробуй ще раз:")
        return
    
    # Get data from state
    data = await state.get_data()
    delivery_city = data.get('delivery_city')
    last_address = data.get('last_address')
    
    # Update user in database
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    
    if user:
        user.delivery_city = delivery_city
        user.last_address = last_address
        user.phone = phone
        await session.commit()
        
        await message.answer(
            "✅ <b>Дані оновлено!</b> 🎉\n\n"
            f"🏙️ Місто: {delivery_city}\n"
            f"📍 Адреса: {last_address}\n"
            f"📞 Телефон: {phone}\n\n"
            "Тепер ти можеш швидко оформити замовлення!",
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Помилка: користувач не знайдений.")
    
    await state.clear()
