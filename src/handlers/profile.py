"""Profile handler and repeat order logic."""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database.models import User, Order
from src.services.cart_service import CartService
from src.utils.formatters import format_currency, format_date
from src.utils.constants import CallbackPrefix

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "👤 Мій Кабінет")
async def show_profile(message: Message, session: AsyncSession):
    """Show user profile."""
    user_id = message.from_user.id
    
    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        return

    # Calculate total spent and orders count
    stats_query = select(Order).where(
        Order.user_id == user_id,
        Order.status == "paid"  # Only count paid orders
    )
    stats_result = await session.execute(stats_query)
    orders = stats_result.scalars().all()
    
    total_spent = sum(o.total for o in orders)
    orders_count = len(orders)
    
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
async def edit_profile_data(callback: CallbackQuery):
    """Stub for profile editing."""
    await callback.answer("🚧 Функція в розробці. Змініть дані при оформленні замовлення.", show_alert=True)
