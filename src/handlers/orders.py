"""Order history and management handler."""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.order_service import OrderService
from src.services.payment_service import payment_service
from src.keyboards.checkout_kb import get_payment_keyboard
from src.utils.formatters import format_currency, format_date, format_order_items
from src.utils.constants import ORDER_STATUS_NAMES
from src.utils.image_constants import MODULE_ORDERS

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("orders"))
@router.message(F.text == "📋 Замовлення")
@router.callback_query(F.data == "my_orders")
async def show_order_history(event: Message | CallbackQuery, session: AsyncSession):
    """Show user's order history."""
    if isinstance(event, Message):
        user_id = event.from_user.id
        message = event
    else:
        user_id = event.from_user.id
        message = event.message

    orders = await OrderService.get_user_orders(session, user_id, limit=10)
    
    if not orders:
        text = """
🔴 <b>Мої замовлення</b> 🐒

У вас поки немає замовлень.

Час замовити першу порцію свіжої кави! ⚫

Перегляньте наш каталог та оберіть улюблені сорти.
"""
        if isinstance(event, Message):
            if MODULE_ORDERS.exists():
                photo = FSInputFile(MODULE_ORDERS)
                await message.answer_photo(photo, caption=text, parse_mode="HTML")
            else:
                await message.answer(text, parse_mode="HTML")
        else:
            await message.delete()
            try:
                await message.delete()
            except Exception as e:
                logger.warning(f"Failed to delete empty orders message: {e}")
                
            if MODULE_ORDERS.exists():
                photo = FSInputFile(MODULE_ORDERS)
                await message.answer_photo(photo, caption=text, parse_mode="HTML")
            else:
                await message.answer(text, parse_mode="HTML")
            await event.answer()
        return
    
    text = f"<b>📦 Мої замовлення</b>\n\n"
    text += f"Всього замовлень: {len(orders)}\n\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    builder = InlineKeyboardBuilder()
    
    for order in orders[:5]:  # Show last 5 orders
        status_emoji = {
            "pending": "⏳",
            "paid": "✅",
            "shipped": "🚚",
            "delivered": "📦",
            "cancelled": "❌"
        }.get(order.status, "📋")
        
        order_date = format_date(order.created_at, "short")
        status_name = ORDER_STATUS_NAMES.get(order.status, order.status)
        
        text += f"{status_emoji} <b>Замовлення #{order.order_number}</b>\n"
        text += f"Дата: {order_date}\n"
        text += f"Статус: {status_name}\n"
        text += f"Сума: {format_currency(order.total)}\n"
        
        if order.tracking_number:
            text += f"ТТН: <code>{order.tracking_number}</code>\n"
        
        text += "\n"
        
        # Add button for details
        builder.row(InlineKeyboardButton(
            text=f"📋 #{order.order_number} - {format_currency(order.total)}",
            callback_data=f"order_view:{order.id}"
        ))
    
    if len(orders) > 5:
        text += f"\n... та ще {len(orders) - 5} замовлень\n"
    
    if isinstance(event, Message):
        if MODULE_ORDERS.exists():
            photo = FSInputFile(MODULE_ORDERS)
            await message.answer_photo(photo, caption=text, reply_markup=builder.as_markup(), parse_mode="HTML")
        else:
            await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        await message.delete()
        if MODULE_ORDERS.exists():
            photo = FSInputFile(MODULE_ORDERS)
            await message.answer_photo(photo, caption=text, reply_markup=builder.as_markup(), parse_mode="HTML")
        else:
            await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        await event.answer()


@router.callback_query(F.data.startswith("order_view:"))
async def show_order_details(callback: CallbackQuery, session: AsyncSession):
    """Show detailed order information."""
    order_id = int(callback.data.split(":")[1])
    
    from src.database.models import Order
    from sqlalchemy import select
    
    query = select(Order).where(Order.id == order_id)
    result = await session.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        await callback.answer("❌ Замовлення не знайдено", show_alert=True)
        return
    
    # Verify ownership
    if order.user_id != callback.from_user.id:
        await callback.answer("❌ Це не ваше замовлення", show_alert=True)
        return
    
    status_name = ORDER_STATUS_NAMES.get(order.status, order.status)
    order_date = format_date(order.created_at, "long")
    
    text = f"""
🔴 <b>Замовлення #{order.order_number}</b> 🐒

━━━━━━━━━━━━━━━━━━
🔴 <b>ДЕТАЛІ ЛОТУ:</b>

{format_order_items(order.items)}

Товарів на: {format_currency(order.subtotal)}

━━━━━━━━━━━━━━━━━━
⚫ <b>ЗНИЖКИ ТА БОНУСИ:</b>

"""
    
    if order.discount_volume > 0:
        text += f"Об'ємна знижка: -{format_currency(order.discount_volume)}\n"
    
    if order.discount_loyalty > 0:
        text += f"Накопичувальна: -{format_currency(order.discount_loyalty)}\n"
    
    if order.discount_promo > 0:
        text += f"Промокод {order.promo_code_used}: -{format_currency(order.discount_promo)}\n"
    
    total_discount = order.discount_volume + order.discount_loyalty + order.discount_promo
    
    if total_discount > 0:
        text += f"\nРазом знижки: -{format_currency(total_discount)}\n"
    else:
        text += "Знижок немає\n"
    
    text += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"Доставка: {format_currency(order.delivery_cost)}\n"
    
    text += f"\n<b>💳 РАЗОМ: {format_currency(order.total)}</b>\n"
    
    text += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"<b>📍 Доставка:</b>\n"
    text += f"{order.delivery_city}\n"
    text += f"{order.delivery_address}\n\n"
    
    text += f"<b>👤 Отримувач:</b>\n"
    text += f"{order.recipient_name}\n"
    text += f"{order.recipient_phone}\n"
    
    if order.tracking_number:
        text += f"\n<b>📦 Трекінг:</b>\n"
        text += f"ТТН: <code>{order.tracking_number}</code>\n"
        
        if order.delivery_method == "nova_poshta":
            text += "\n🔗 Відстежити: https://novaposhta.ua/tracking/"
    
    # Status timeline
    text += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    text += "<b>📅 Історія:</b>\n\n"
    
    text += f"✅ Створено: {format_date(order.created_at, 'short')}\n"
    
    if order.paid_at:
        text += f"✅ Оплачено: {format_date(order.paid_at, 'short')}\n"
    
    if order.shipped_at:
        text += f"✅ Відправлено: {format_date(order.shipped_at, 'short')}\n"
    
    if order.delivered_at:
        text += f"✅ Доставлено: {format_date(order.delivered_at, 'short')}\n"
    
    # Action buttons
    builder = InlineKeyboardBuilder()
    
    if order.status == "pending":
        builder.row(InlineKeyboardButton(
            text="💳 Продовжити оплату",
            callback_data=f"order_pay:{order.id}"
        ))
        builder.row(InlineKeyboardButton(
            text="❌ Скасувати замовлення",
            callback_data=f"order_cancel:{order.id}"
        ))
    
    if order.status == "delivered":
        builder.row(InlineKeyboardButton(
            text="🔄 Повторити замовлення",
            callback_data=f"order_repeat:{order.id}"
        ))
    
    builder.row(InlineKeyboardButton(
        text="← Назад до замовлення",
        callback_data="orders_list"
    ))
    
    # Was editing text, but we might be coming from a photo message. Use delete+send to be safe.
    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning(f"Failed to delete message for order details: {e}")

    await callback.message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "orders_list")
async def back_to_orders_list(callback: CallbackQuery, session: AsyncSession):
    """Go back to orders list."""
    # Re-create orders list message
    user_id = callback.from_user.id
    
    orders = await OrderService.get_user_orders(session, user_id, limit=10)
    
    text = f"<b>📦 Мої замовлення</b>\n\n"
    text += f"Всього замовлень: {len(orders)}\n\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    builder = InlineKeyboardBuilder()
    
    for order in orders[:5]:
        status_emoji = {
            "pending": "⏳",
            "paid": "✅",
            "shipped": "🚚",
            "delivered": "📦",
            "cancelled": "❌"
        }.get(order.status, "📋")
        
        order_date = format_date(order.created_at, "short")
        status_name = ORDER_STATUS_NAMES.get(order.status, order.status)
        
        text += f"{status_emoji} <b>Замовлення #{order.order_number}</b>\n"
        text += f"Дата: {order_date}\n"
        text += f"Статус: {status_name}\n"
        text += f"Сума: {format_currency(order.total)}\n\n"
        
        builder.row(InlineKeyboardButton(
            text=f"📋 #{order.order_number} - {format_currency(order.total)}",
            callback_data=f"order_view:{order.id}"
        ))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("order_repeat:"))
async def repeat_order(callback: CallbackQuery, session: AsyncSession):
    """Add previous order items to cart."""
    order_id = int(callback.data.split(":")[1])
    
    from src.database.models import Order
    from sqlalchemy import select
    from src.services.cart_service import CartService
    
    query = select(Order).where(Order.id == order_id)
    result = await session.execute(query)
    order = result.scalar_one_or_none()
    
    if not order or order.user_id != callback.from_user.id:
        await callback.answer("❌ Замовлення не знайдено", show_alert=True)
        return
    
    # Add items from order to cart
    added_count = 0
    for item in order.items:
        try:
            await CartService.add_to_cart(
                session,
                user_id=callback.from_user.id,
                product_id=item['product_id'],
                format=item['format'],
                quantity=item['quantity']
            )
            added_count += 1
        except Exception as e:
            logger.error(f"Error adding item to cart: {e}")
    
    if added_count > 0:
        await callback.answer(
            f"✅ Додано {added_count} товарів до кошика!\n"
            f"Перейдіть в кошик для оформлення.",
            show_alert=True
        )
    else:
        await callback.answer("❌ Не вдалося додати товари", show_alert=True)


@router.callback_query(F.data.startswith("order_pay:"))
async def process_order_payment(callback: CallbackQuery, session: AsyncSession):
    """Show payment information for an existing order."""
    order_id = int(callback.data.split(":")[1])
    
    from src.database.models import Order
    from sqlalchemy import select
    from config import settings
    
    query = select(Order).where(Order.id == order_id)
    result = await session.execute(query)
    order = result.scalar_one_or_none()
    
    if not order or order.user_id != callback.from_user.id:
        await callback.answer("❌ Замовлення не знайдено", show_alert=True)
        return
    
    if order.status != "pending":
        await callback.answer("❌ Це замовлення вже оплачене або скасоване", show_alert=True)
        return
    
    # Generate LiqPay link
    payment_url = payment_service.get_payment_url(
        order_id=order.order_number,
        amount=order.total,
        description=f"Оплата замовлення #{order.order_number} у Monkeys Coffee"
    )
    
    text = f"""
<b>💳 Оплата замовлення #{order.order_number}</b>

Сума до сплати: <b>{format_currency(order.total)}</b>

Натисніть кнопку нижче, щоб перейти до миттєвої оплати через LiqPay. 
🚀
"""
    
    keyboard = get_payment_keyboard(payment_url)
    
    builder = InlineKeyboardBuilder()
    builder.attach(InlineKeyboardBuilder.from_markup(keyboard))
    builder.row(InlineKeyboardButton(
        text="← Назад до замовлення",
        callback_data=f"order_view:{order.id}"
    ))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("order_cancel:"))
async def process_order_cancel(callback: CallbackQuery, session: AsyncSession):
    """Cancel a pending order."""
    order_id = int(callback.data.split(":")[1])
    
    from src.database.models import Order
    from sqlalchemy import select
    
    query = select(Order).where(Order.id == order_id)
    result = await session.execute(query)
    order = result.scalar_one_or_none()
    
    if not order or order.user_id != callback.from_user.id:
        await callback.answer("❌ Замовлення не знайдено", show_alert=True)
        return
    
    if order.status != "pending":
        await callback.answer("❌ Тільки нові замовлення можна скасувати самостійно", show_alert=True)
        return
    
    # Update status to cancelled
    await OrderService.update_order_status(session, order_id, "cancelled")
    
    await callback.answer("✅ Замовлення скасовано", show_alert=True)
    
    # Return to updated orders list
    await show_order_history(callback, session)
