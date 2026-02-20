"""Admin panel handler."""
import logging
import asyncio
from aiogram import Router, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, or_, cast, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload



from src.database.models import Order, Product, User, PromoCode
from src.services.order_service import OrderService
from src.services.analytics_service import AnalyticsService
from src.keyboards.admin_kb import (
    get_admin_panel_keyboard,
    get_order_management_keyboard,
    get_order_action_keyboard,
    get_admin_product_list_keyboard,
    get_product_action_keyboard,
    get_product_edit_fields_keyboard,
    get_product_delete_confirm_keyboard,
    get_admin_users_keyboard,
    get_analytics_keyboard,
    get_roast_level_keyboard,
    get_processing_method_keyboard,
    get_skip_image_keyboard,
    get_skip_image_keyboard,
    get_product_category_keyboard,
    get_back_keyboard,
    get_inline_cancel_keyboard,
    get_product_edit_description_keyboard,
    get_apply_ai_text_keyboard
)
from src.keyboards.main_menu import get_cancel_keyboard, get_admin_main_menu_keyboard
from src.states.admin_states import AdminStates
from src.utils.formatters import (
    format_currency, format_date, format_order_items,
    generate_product_description
)
from src.utils.constants import ORDER_STATUS_NAMES, UIStyle
from config import settings

router = Router()
logger = logging.getLogger(__name__)

# Global dictionary to track active AI generation tasks for admins
# Format: {user_id: asyncio.Task}
active_ai_tasks = {}


from src.utils.admin_utils import is_admin


@router.message(StateFilter("*"), F.text == "❌ Скасувати")
@router.message(StateFilter("*"), Command("cancel"))
async def admin_global_cancel(message: Message, state: FSMContext):
    """Global cancel for admins to escape stuck states."""
    if not is_admin(message.from_user.id):
        return  # Pass to other routers
    
    # Cancel any active AI task
    if message.from_user.id in active_ai_tasks:
        task = active_ai_tasks.pop(message.from_user.id)
        if not task.done():
            task.cancel()
    
    await state.clear()
    await message.answer(
        "❌ Процес скасовано",
        reply_markup=get_admin_main_menu_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin_product_back:"))
async def process_product_back(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Handle 'Back' navigation in product addition flow."""
    target = callback.data.split(":")[1]
    logger.info(f"Back navigation triggered to: {target} for user {callback.from_user.id}")
    
    data = await state.get_data()
    category = data.get("category", "coffee")

    if target in ["coffee", "equipment", "merch", "other", "tea", "cocoa", "accessories"]:
        # Back from Step 1 (Name) to Category selection
        await start_product_add(callback, state, session)
        return

    if target == "name":
        # Back to Step 1 (Name)
        await state.set_state(AdminStates.waiting_for_product_name)
        await callback.message.edit_text(
            f"📝 <b>Крок 1/8: Назва товару (UA)</b>\nПоточна: {data.get('name_ua', '---')}\n\nВведіть нову назву:",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
    elif target == "origin":
        # Back to Step 2 (Origin)
        await state.set_state(AdminStates.waiting_for_product_origin)
        await callback.message.edit_text(
            f"🌍 <b>Крок 2/8: Походження</b>\nПоточне: {data.get('origin', '---')}\n\nВведіть нове значення:",
            reply_markup=get_roast_level_keyboard(category=category),
            parse_mode="HTML"
        )
    elif target == "roast":
        # Back to Step 3 (Roast)
        await state.set_state(AdminStates.waiting_for_product_roast_level)
        await callback.message.edit_text(
            f"🔥 <b>Крок 3/8: Ступінь обсмаження</b>\nПоточне: {data.get('roast_level', '---')}\n\nОберіть нове:",
            reply_markup=get_roast_level_keyboard(category="origin"),
            parse_mode="HTML"
        )
    elif target == "processing":
        # Back to Step 4 (Processing)
        await ask_processing_method(callback.message, state)
    elif target == "notes":
        # Back to Step 5 (Notes)
        await ask_tasting_notes(callback.message, state)
    elif target == "price_300g":
        # Back to Step 6 (Price 300g)
        await state.set_state(AdminStates.waiting_for_product_price_300g)
        await callback.message.edit_text(
            f"💰 <b>Крок 6/8: Ціна за 300г</b>\nПоточна: {data.get('price_300g', '---')}\n\nВведіть нову:",
            reply_markup=get_roast_level_keyboard(category="notes"),
            parse_mode="HTML"
        )
    elif target == "price_1kg":
        # Back to Step 7 (Price 1kg)
        await state.set_state(AdminStates.waiting_for_product_price_1kg)
        await callback.message.edit_text(
            f"💰 <b>Крок 7/8: Ціна за 1кг</b>\nПоточна: {data.get('price_1kg', '---')}\n\nВведіть нову:",
            reply_markup=get_roast_level_keyboard(category="price_300g"),
            parse_mode="HTML"
        )
    
    await callback.answer()


@router.message(Command("admin"))
@router.message(F.text == "⚙️ Адмін-панель")
async def show_admin_panel(message: Message, session: AsyncSession):
    """Show admin panel main menu."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас немає доступу до адмін-панелі")
        return
    
    stats = await AnalyticsService.get_general_statistics(session)
    
    text = f"""
<b>Адмін-Панель</b>

━━━━━━━━━━━━━━━━━━
<b>ОГЛЯД ПОКАЗНИКІВ:</b>
• Користувачів: {stats['total_users']}
• Всього замовлень: {stats['total_orders']}
• Активних лотів: {stats['active_products']}
• Виручка: {format_currency(stats['total_revenue'])}

<b>ЗАРАЗ В РОБОТІ:</b>
• Очікують оплату: {stats['pending_orders']}
• Потребують відправки: {stats['paid_orders']}

━━━━━━━━━━━━━━━━━━━━

Оберіть розділ для управління:
"""
    
    keyboard = get_admin_panel_keyboard()
    
    await message.answer(
        text, 
        reply_markup=keyboard, 
        parse_mode="HTML"
    )


@router.message(Command("state"))
async def cmd_check_state(message: Message, state: FSMContext):
    """Debug command to check current FSM state."""
    if not is_admin(message.from_user.id):
        return
    current_state = await state.get_state()
    data = await state.get_data()
    await message.answer(f"🔍 <b>Поточний стан:</b> {current_state}\n📦 <b>Дані:</b> {data}")


@router.callback_query(F.data == "admin_main")
async def show_admin_main(callback: CallbackQuery, session: AsyncSession):
    """Show admin panel main menu from callback."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    stats = await AnalyticsService.get_general_statistics(session)
    
    text = f"""
<b>Адмін-Панель</b>

━━━━━━━━━━━━━━━━━━
<b>ОГЛЯД ПОКАЗНИКІВ:</b>
• Користувачів: {stats['total_users']}
• Всього замовлень: {stats['total_orders']}
• Активних лотів: {stats['active_products']}
• Виручка: {format_currency(stats['total_revenue'])}

<b>ЗАРАЗ В РОБОТІ:</b>
• Очікують оплату: {stats['pending_orders']}
• Потребують відправки: {stats['paid_orders']}

━━━━━━━━━━━━━━━━━━━━

Оберіть розділ для управління:
"""
    
    keyboard = get_admin_panel_keyboard()
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_users_main")
async def show_user_management(callback: CallbackQuery):
    """Show user management sub-menu."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    text = "<b>Управління користувачами</b>\n\nОберіть дію:"
    keyboard = get_admin_users_keyboard()
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# ========== ORDER MANAGEMENT ==========

@router.callback_query(F.data == "admin_orders")
async def show_order_management(callback: CallbackQuery):
    """Show order management menu."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    text = """
<b>Управління замовленнями</b>

Фільтруйте замовлення за статусом:

━━━━━━━━━━━━━━━━━━
<b>Очікують оплати</b> - нові замовлення
<b>Оплачені</b> - готові до відправки
<b>Відправлені</b> - в дорозі до клієнта
<b>Всі замовлення</b> - повний список
━━━━━━━━━━━━━━━━━━
"""
    
    keyboard = get_order_management_keyboard()
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_orders_"))
async def show_orders_by_status(callback: CallbackQuery, session: AsyncSession):
    """Show orders filtered by status."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    status_filter = callback.data.replace("admin_orders_", "")
    
    # Build query
    query = select(Order).options(selectinload(Order.user)).order_by(Order.created_at.desc()).limit(20)
    
    if status_filter == "pending":
        query = query.where(Order.status == "pending")
        title = "⏳ Очікують оплати"
    elif status_filter == "paid":
        query = query.where(Order.status == "paid")
        title = "✅ Оплачені (не відправлені)"
    elif status_filter == "shipped":
        query = query.where(Order.status == "shipped")
        title = "🚚 Відправлені"
    else:
        title = "📦 Всі замовлення"
    
    result = await session.execute(query)
    orders = result.scalars().all()
    
    if not orders:
        text = f"<b>{title}</b>\n\nНемає замовлень з таким статусом"
        await callback.message.edit_text(text, reply_markup=get_order_management_keyboard(), parse_mode="HTML")
        await callback.answer()
        return
    
    text = f"<b>{title}</b>\n\n"
    text += f"Знайдено: {len(orders)} замовлень\n\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Build query (Imports moved to top)
    
    builder = InlineKeyboardBuilder()
    
    for order in orders[:10]:  # Show max 10
        status_emoji = {
            "pending": "⏳",
            "paid": "✅",
            "shipped": "🚚",
            "delivered": "📦",
            "cancelled": "❌"
        }.get(order.status, "📋")
        
        order_date = format_date(order.created_at, "short")
        status_name = ORDER_STATUS_NAMES.get(order.status, order.status)
        
        text += f"{status_emoji} <b>#{order.order_number}</b>\n"
        text += f"Дата: {order_date}\n"
        
        client_info = f"@{order.user.username}" if order.user and order.user.username else f"ID: {order.user_id}"
        text += f"Клієнт: <b>{client_info}</b>\n"
        text += f"Сума: {format_currency(order.total)}\n"
        text += f"Статус: {status_name}\n\n"
        
        builder.row(InlineKeyboardButton(
            text=f"📋 #{order.order_number} - {format_currency(order.total)}",
            callback_data=f"admin_order:{order.id}"
        ))
    
    if len(orders) > 10:
        text += f"\n... та ще {len(orders) - 10} замовлень\n"
    
    builder.row(InlineKeyboardButton(
        text="← Назад",
        callback_data="admin_orders"
    ))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_order:"))
async def show_order_details_admin(callback: CallbackQuery, session: AsyncSession):
    """Show detailed order information for admin."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    order_id = int(callback.data.split(":")[1])
    
    query = select(Order).options(selectinload(Order.user)).where(Order.id == order_id)
    result = await session.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        await callback.answer("❌ Замовлення не знайдено", show_alert=True)
        return
    
    status_name = ORDER_STATUS_NAMES.get(order.status, order.status)
    order_date = format_date(order.created_at, "long")
    
    client_info = f"@{order.user.username}" if order.user and order.user.username else f"<code>{order.user_id}</code>"
    
    text = f"""
<b>📋 Замовлення #{order.order_number}</b> ⚫

━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>Статус:</b> {status_name}
<b>Дата:</b> {order_date}
<b>Клієнт:</b> {client_info}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>📦 ТОВАРИ:</b>

{format_order_items(order.items)}

Товарів на: {format_currency(order.subtotal)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>🎯 ЗНИЖКИ:</b>

"""
    
    if order.discount_volume > 0:
        text += f"Об'ємна: -{format_currency(order.discount_volume)}\n"
    if order.discount_loyalty > 0:
        text += f"Накопичувальна: -{format_currency(order.discount_loyalty)}\n"
    if order.discount_promo > 0:
        text += f"Промокод {order.promo_code_used}: -{format_currency(order.discount_promo)}\n"
    
    total_discount = order.discount_volume + order.discount_loyalty + order.discount_promo
    if total_discount == 0:
        text += "Без знижок\n"
    
    text += f"\nДоставка: {format_currency(order.delivery_cost)}\n"
    text += f"\n<b>💰 РАЗОМ: {format_currency(order.total)}</b>\n"
    
    text += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"<b>📍 Доставка:</b>\n"
    text += f"{order.delivery_method}\n"
    text += f"{order.delivery_city}\n"
    text += f"{order.delivery_address}\n\n"
    
    text += f"<b>👤 Отримувач:</b>\n"
    text += f"{order.recipient_name}\n"
    text += f"{order.recipient_phone}\n"
    
    if order.tracking_number:
        text += f"\n<b>📦 ТТН:</b> <code>{order.tracking_number}</code>\n"
    
    text += f"\n<b>☕ Помел:</b> {order.grind_preference}\n"
    
    keyboard = get_order_action_keyboard(order.id, order.status)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_order_paid:"))
async def mark_order_paid(callback: CallbackQuery, session: AsyncSession):
    """Mark order as paid."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    order_id = int(callback.data.split(":")[1])
    
    try:
        order = await OrderService.mark_order_paid(session, order_id)
        await callback.answer("✅ Замовлення підтверджено як оплачене!", show_alert=True)
        
        # Refresh order view
        await show_order_details_admin(callback, session)
    except Exception as e:
        logger.error(f"Error marking order paid: {e}")
        await callback.answer("❌ Помилка оновлення статусу", show_alert=True)


@router.callback_query(F.data.startswith("admin_order_ship:"))
async def start_shipping_order(callback: CallbackQuery, state: FSMContext):
    """Start shipping process - request tracking number."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    order_id = int(callback.data.split(":")[1])
    
    await state.update_data(order_id=order_id)
    await state.update_data(order_id=order_id)
    await state.set_state(AdminStates.waiting_for_tracking_number)
    logger.info(f"Set state waiting_for_tracking_number for user {callback.from_user.id} | Order: {order_id}")
    
    await callback.message.answer(
        "📦 <b>Відправка замовлення</b>\n\n"
        "Введіть номер ТТН (трекінг-номер):\n\n"
        "Наприклад: <code>59000123456789</code>\n\n"
        "Або /cancel для скасування",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_tracking_number)
async def process_tracking_number(message: Message, state: FSMContext, session: AsyncSession):
    """Process entered tracking number."""
    """Process entered tracking number."""
    tracking_number = message.text.strip()
    logger.info(f"Received tracking number: {tracking_number} from {message.from_user.id}")
    
    data = await state.get_data()
    order_id = data.get('order_id')
    
    try:
        order = await OrderService.update_order_status(
            session,
            order_id,
            "shipped",
            tracking_number=tracking_number
        )
        
        await message.answer(
            f"✅ Замовлення #{order.order_number} відправлено!\n"
            f"ТТН: <code>{tracking_number}</code>",
            reply_markup=get_admin_main_menu_keyboard(),
            parse_mode="HTML"
        )
        
        await state.clear()
    except Exception as e:
        logger.error(f"Error updating order: {e}")
        await message.answer("❌ Помилка оновлення. Спробуйте ще раз або /cancel", reply_markup=get_cancel_keyboard())


@router.callback_query(F.data.startswith("admin_order_delivered:"))
async def mark_order_delivered(callback: CallbackQuery, session: AsyncSession):
    """Mark order as delivered."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    order_id = int(callback.data.split(":")[1])
    
    try:
        order = await OrderService.update_order_status(session, order_id, "delivered")
        await callback.answer("✅ Замовлення позначено як доставлене!", show_alert=True)
        await show_order_details_admin(callback, session)
    except Exception as e:
        logger.error(f"Error marking delivered: {e}")
        await callback.answer("❌ Помилка оновлення", show_alert=True)


@router.callback_query(F.data.startswith("admin_order_cancel:"))
async def cancel_order(callback: CallbackQuery, session: AsyncSession):
    """Cancel order."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    order_id = int(callback.data.split(":")[1])
    
    try:
        order = await OrderService.update_order_status(session, order_id, "cancelled")
        await callback.answer("✅ Замовлення скасовано", show_alert=True)
        await show_order_details_admin(callback, session)
    except Exception as e:
        logger.error(f"Error canceling order: {e}")
        await callback.answer("❌ Помилка оновлення", show_alert=True)


# ========== ANALYTICS ==========

@router.callback_query(F.data == "admin_analytics")
async def show_analytics_menu(callback: CallbackQuery):
    """Show analytics menu."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    text = """
<b>📊 Аналітика та статистика</b>

Оберіть тип звіту:

📊 <b>Загальна статистика</b>
   Ключові показники бізнесу

🎯 <b>Звіт по знижках</b>
   Використання знижок, ефективність

👥 <b>Рівні лояльності</b>
   Розподіл користувачів

💰 <b>Продажі за період</b>
   Виручка та динаміка
"""
    
    keyboard = get_analytics_keyboard()
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_stats_general")
async def show_general_statistics(callback: CallbackQuery, session: AsyncSession):
    """Show general business statistics."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    stats = await AnalyticsService.get_general_statistics(session)
    
    text = """
<b>📊 Загальна статистика</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>👥 КОРИСТУВАЧІ:</b>

Зареєстровано: {total_users}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>📦 ЗАМОВЛЕННЯ:</b>

Всього: {total_orders}
⏳ Очікують: {pending_orders}
✅ Оплачені: {paid_orders}
🚚 Відправлені: {shipped_orders}
📦 Доставлені: {delivered_orders}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>💰 ФІНАНСИ:</b>

Виручка: {total_revenue}
Середній чек: {avg_order_value}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>☕ ТОВАРИ:</b>

Активних: {active_products}
""".format(
        total_users=stats['total_users'],
        total_orders=stats['total_orders'],
        pending_orders=stats['pending_orders'],
        paid_orders=stats['paid_orders'],
        shipped_orders=stats['shipped_orders'],
        delivered_orders=stats['delivered_orders'],
        total_revenue=format_currency(stats['total_revenue']),
        avg_order_value=format_currency(stats['avg_order_value']),
        active_products=stats['active_products']
    )
    
    # Check for alerts
    alerts = await AnalyticsService.get_pending_orders_alerts(session)
    if alerts:
        text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        text += "<b>⚠️ УВАГА:</b>\n\n"
        for alert in alerts:
            text += f"• {alert['message']}\n"
    
    keyboard = get_analytics_keyboard()
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_stats_discounts")
async def show_discount_statistics(callback: CallbackQuery, session: AsyncSession):
    """Show discount usage statistics."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    stats = await AnalyticsService.get_discount_statistics(session)
    
    text = f"""
<b>🎯 Статистика знижок</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━
Проаналізовано: {stats['total_orders']} замовлень

<b>Використання знижок:</b>
Замовлень зі знижками: {stats['orders_with_discounts']}
Середня знижка: {stats['avg_discount_percent']}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>Розподіл по типах:</b>

📦 Об'ємні знижки: {format_currency(stats['volume_discounts'])}
🎯 Накопичувальні: {format_currency(stats['loyalty_discounts'])}
🎫 Промокоди: {format_currency(stats['promo_discounts'])}

<b>Всього знижок:</b> {format_currency(stats['total_discounts'])}
"""
    
    keyboard = get_analytics_keyboard()
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_stats_loyalty")
async def show_loyalty_distribution(callback: CallbackQuery, session: AsyncSession):
    """Show loyalty level distribution."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    distribution = await AnalyticsService.get_loyalty_distribution(session)
    
    text = "<b>👥 Розподіл користувачів по рівнях</b>\n\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for level in range(1, 5):
        level_data = distribution[level]
        text += f"<b>Рівень {level}: {level_data['name']}</b>\n"
        text += f"Знижка: {level_data['discount']}%\n"
        text += f"Користувачів: {level_data['count']}\n\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"<b>💡 Інсайти:</b>\n\n"
    text += f"Близько до рівня 2: {distribution['insights']['close_to_level_2']} клієнтів"
    
    keyboard = get_analytics_keyboard()
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_stats_sales")
async def show_sales_statistics(callback: CallbackQuery, session: AsyncSession):
    """Show sales statistics."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    # Get stats for last 30 days
    stats = await AnalyticsService.get_sales_by_period(session, 30)
    
    text = f"""
<b>💰 Продажі за останні 30 днів</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━

Замовлень: {stats['total_orders']}
Виручка: {format_currency(stats['total_revenue'])}

Середній чек: {format_currency(stats['avg_order_value'])}
Продано кави: {stats['total_kg_sold']} кг

━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>Розрахункові показники:</b>
• Замовлень/день: ~{round(stats['total_orders'] / 30, 1)}
• Виручка/день: ~{format_currency(stats['total_revenue'] // 30)}
"""
    
    keyboard = get_analytics_keyboard()
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# ========== PRODUCT MANAGEMENT (Basic) ==========

@router.callback_query(F.data == "admin_products")
async def show_product_management(callback: CallbackQuery, session: AsyncSession):
    """Show product management menu."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    await show_products_list(callback, session)


# ========== PRODUCT MANAGEMENT (Full) ==========

@router.callback_query(F.data == "admin_product_add")
async def start_product_add(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Start product addition flow by asking for category."""
    logger.info(f"Admin product add started by user {callback.from_user.id}")
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    from src.database.models import Category
    from src.keyboards.admin_kb import get_product_category_keyboard
    
    query = select(Category).where(Category.is_active == True).order_by(Category.sort_order.asc())
    result = await session.execute(query)
    categories = result.scalars().all()
    
    # DEBUG LOG
    logger.info(f"Start Product Add: Found {len(categories)} active categories: {[c.slug for c in categories]}")
    
    await state.clear()
    await state.set_state(AdminStates.waiting_for_product_category)
    await callback.message.answer(
        "📂 <b>Крок 0: Оберіть категорію товару</b>",
        reply_markup=get_product_category_keyboard(categories),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(StateFilter("*"), F.data.startswith("admin_cat:"))
async def process_product_category(callback: CallbackQuery, state: FSMContext):
    """Process category selection and ask for name."""
    # Ensure state is cleared if user jumps here from elsewhere (or restart)
    await state.clear()
    
    category = callback.data.split(":")[1]
    logger.info(f"Category selected: {category} for user {callback.from_user.id}")
    await state.update_data(category=category)
    
    await state.set_state(AdminStates.waiting_for_product_name)
    await callback.message.edit_text(
        "📝 <b>Крок 1/8: Назва товару (UA)</b>\n"
        "Введіть повну назву (наприклад: <i>V60 Drip Set</i> чи <i>Ethiopia Sidamo</i>):",
        reply_markup=get_inline_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(Command("init_categories"))
async def cmd_init_categories(message: Message, session: AsyncSession):
    """Restore default categories: Coffee and Shop ONLY."""
    if not is_admin(message.from_user.id):
        return

    from src.database.models import Category
    from sqlalchemy import update
    
    logger.info("CMD_INIT_CATEGORIES: Starting update...")
    
    # Deactivate ALL categories first
    result = await session.execute(update(Category).values(is_active=False))
    logger.info(f"CMD_INIT_CATEGORIES: Deactivated {result.rowcount} categories.")
    
    # 1. COFFEE
    coffee_query = select(Category).where(Category.slug == "coffee")
    coffee = await session.scalar(coffee_query)
    if coffee:
        coffee.is_active = True
        coffee.name_ua = "☕ Кава"
        coffee.sort_order = 1
        logger.info("CMD_INIT_CATEGORIES: Activated existing 'coffee'.")
    else:
        session.add(Category(slug="coffee", name_ua="☕ Кава", name_en="Coffee", is_active=True, sort_order=1))
        logger.info("CMD_INIT_CATEGORIES: Created 'coffee'.")
        
    # 2. SHOP (Equipment/Merch) -> mapped to 'equipment' slug but named "Магазин"
    shop_query = select(Category).where(Category.slug == "equipment")
    shop = await session.scalar(shop_query)
    if shop:
        shop.is_active = True
        shop.name_ua = "🏪 Магазин"
        shop.sort_order = 2
        logger.info("CMD_INIT_CATEGORIES: Activated existing 'equipment' as 'Магазин'.")
    else:
        session.add(Category(slug="equipment", name_ua="🏪 Магазин", name_en="Shop", is_active=True, sort_order=2))
        logger.info("CMD_INIT_CATEGORIES: Created 'equipment' as 'Магазин'.")
    
    await session.commit()
    logger.info("CMD_INIT_CATEGORIES: Committed changes.")
    await message.answer("✅ Категорії оновлено: тільки 'Кава' та 'Магазин'. Всі інші приховані.")


@router.message(AdminStates.waiting_for_product_name, F.text, ~F.text.startswith("/"))
async def process_product_name(message: Message, state: FSMContext):
    """Process product name and branch based on category."""
    logger.info(f"Product name entered: {message.text} for user {message.from_user.id}")
    await state.update_data(name_ua=message.text)
    data = await state.get_data()
    
    category = data.get("category")
    
    # Simple products (skip coffee specifics)
    simple_categories = ["equipment", "merch", "other", "tea", "cocoa", "accessories"]
    
    if category in simple_categories:
        # Skip coffee-specific steps, go to price
        logger.info(f"Simple category detected: {category}. Moving to price.")
        await state.set_state(AdminStates.waiting_for_product_price_300g)
        await message.answer(
            "💰 <b>Крок 2/3: Ціна (грн)</b>\n"
            "Введіть вартість за одиницю товару:",
            reply_markup=get_back_keyboard(target="name"), 
            parse_mode="HTML"
        )
    else:
        # Proceed to coffee origin (Step 2/8)
        logger.info(f"Coffee category detected. Moving to origin.")
        await state.set_state(AdminStates.waiting_for_product_origin)
        await message.answer(
            "🌍 <b>Крок 2/8: Походження / Регіон</b>\n"
            "Наприклад: <i>Ефіопія, Їргачефф</i> або <i>Колумбія, Уїла</i>",
            reply_markup=get_back_keyboard(target="name"),
            parse_mode="HTML"
        )

@router.message(AdminStates.waiting_for_product_origin, F.text, ~F.text.startswith("/"))
async def process_product_origin(message: Message, state: FSMContext):
    """Process origin and ask for roast level."""
    logger.info(f"Product origin entered: {message.text} for user {message.from_user.id}")
    await state.update_data(origin=message.text)
    await state.set_state(AdminStates.waiting_for_product_roast_level)
    await message.answer(
        "🔥 <b>Крок 3/8: Ступінь обсмаження</b>\n"
        "Оберіть зі списку або введіть свій варіант:",
        reply_markup=get_roast_level_keyboard(category="origin"),
        parse_mode="HTML"
    )
@router.callback_query(AdminStates.waiting_for_product_roast_level, F.data.startswith("admin_roast:"))
async def process_roast_level_selection(callback: CallbackQuery, state: FSMContext):
    """Process roast level selection from keyboard."""
    logger.info(f"Roast level selected: {callback.data} for user {callback.from_user.id}")
    roast_code = callback.data.split(":")[1]
    
    roast_map = {
        "roast_light": "Світле (Light)",
        "roast_medium": "Середнє (Medium)",
        "roast_dark": "Темне (Dark)",
        "roast_espresso": "Еспресо (Espresso)",
        "roast_filter": "Фільтр (Filter)",
        "roast_omni": "Омні (Omni)"
    }
    
    roast_level = roast_map.get(roast_code, "Середнє")
    
    # AUTOMATIC PROFILE MAPPING
    # Default to universal
    profile = "universal"
    if roast_code == "roast_espresso":
        profile = "espresso"
    elif roast_code == "roast_filter":
        profile = "filter"
    elif roast_code == "roast_light":
        profile = "filter"
    elif roast_code == "roast_dark":
        profile = "espresso"

    await state.update_data(roast_level=roast_level, profile=profile)
    
    # Move to next step (Step 4/8)
    await ask_processing_method(callback.message, state)
    await callback.answer()


@router.message(AdminStates.waiting_for_product_roast_level, F.text, ~F.text.startswith("/"))
async def process_roast_level_text(message: Message, state: FSMContext):
    """Process custom roast level text."""
    await state.update_data(roast_level=message.text)
    await ask_processing_method(message, state)


async def ask_processing_method(message: Message, state: FSMContext):
    """Ask for processing method."""
    await state.set_state(AdminStates.waiting_for_product_processing)
    await message.answer(
        "⚙️ <b>Крок 4/8: Метод обробки</b>\n"
        "Оберіть зі списку або введіть свій варіант:",
        reply_markup=get_processing_method_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(AdminStates.waiting_for_product_processing, F.data.startswith("admin_proc:"))
async def process_processing_selection(callback: CallbackQuery, state: FSMContext):
    """Process processing method selection."""
    logger.info(f"Processing selected: {callback.data} for user {callback.from_user.id}")
    proc_code = callback.data.split(":")[1]
    
    proc_map = {
        "proc_washed": "Мита (Washed)",
        "proc_natural": "Натуральна (Natural)",
        "proc_honey": "Хані (Honey)",
        "proc_anaerobic": "Анаеробна (Anaerobic)",
        "proc_experimental": "Експериментальна"
    }
    
    processing = proc_map.get(proc_code, "Мита")
    await state.update_data(processing_method=processing)
    
    # Move to next step
    await ask_tasting_notes(callback.message, state)
    await callback.answer()


@router.message(AdminStates.waiting_for_product_processing, F.text, ~F.text.startswith("/"))
async def process_processing_text(message: Message, state: FSMContext):
    """Process custom processing method."""
    await state.update_data(processing_method=message.text)
    await ask_tasting_notes(message, state)


async def ask_tasting_notes(message: Message, state: FSMContext):
    """Ask for tasting notes."""
    await state.set_state(AdminStates.waiting_for_product_tasting_notes)
    await message.answer(
        "📝 <b>Крок 5/8: Дискриптори (нотки смаку)</b>\n"
        "Введіть через кому. Наприклад: <i>шоколад, горіхи, карамель</i>",
        reply_markup=get_back_keyboard(target="processing"),
        parse_mode="HTML"
    )


@router.message(AdminStates.waiting_for_product_tasting_notes, F.text, ~F.text.startswith("/"))
async def process_product_tasting_notes(message: Message, state: FSMContext):
    """Process tasting notes and ask for price (300g)."""
    notes = [x.strip() for x in message.text.split(",")]
    await state.update_data(tasting_notes=notes)
    await state.set_state(AdminStates.waiting_for_product_price_300g)
    await message.answer(
        "💰 <b>Крок 6/8: Ціна за 300г (грн)</b>\n"
        "Просто введіть число, наприклад: <i>450</i>",
        reply_markup=get_back_keyboard(target="tasting_notes"),
        parse_mode="HTML"
    )


@router.message(AdminStates.waiting_for_product_price_300g, F.text, ~F.text.startswith("/"))
async def process_product_price_300g(message: Message, state: FSMContext):
    """Process price and either ask for 1kg or move to summary."""
    logger.info(f"Price 300g entered: {message.text} for user {message.from_user.id}")
    try:
        price = int(message.text)
        await state.update_data(price_300g=price)
        data = await state.get_data()
        
        if data.get("category") == "equipment":
            # For equipment, 300g field is "unit price", 1kg is 0
            await state.update_data(price_1kg=0)
            await state.set_state(AdminStates.waiting_for_product_image)
            await message.answer(
                "🖼️ <b>Крок 3/3: Зображення товару</b>\n\n"
                "Надішліть фото або натисніть кнопку нижче, щоб пропустити:",
                reply_markup=get_skip_image_keyboard(),
                parse_mode="HTML"
            )
            # No AI description for auto-gen for non-coffee for now, simple fallback
            await state.update_data(description=f"📦 <b>{data.get('name_ua')}</b>. Якісний аксесуар для вашої кавової рутини.")
        else:
            await state.set_state(AdminStates.waiting_for_product_price_1kg)
            await message.answer(
                "💰 <b>Крок 7/8: Ціна за 1кг (грн)</b>\n"
                "Наприклад: <i>1200</i>",
                reply_markup=get_back_keyboard(target="price_300g"),
                parse_mode="HTML"
            )
    except ValueError:
        await message.answer("❌ Будь ласка, введіть числове значення.")


@router.message(AdminStates.waiting_for_product_price_1kg, F.text, ~F.text.startswith("/"))
async def process_product_price_1kg(message: Message, state: FSMContext):
    """Start background generation and immediately ask for photo."""
    logger.info(f"Price 1kg entered: {message.text} for user {message.from_user.id}")
    try:
        price_1kg = int(message.text)
        data = await state.get_data()
        
        # Start background AI generation task
        user_id = message.from_user.id
        
        # Cancel previous if exists (just in case)
        if user_id in active_ai_tasks:
            active_ai_tasks[user_id].cancel()
            
        async def background_gen_task():
            try:
                logger.info(f"Starting background AI generation for {data['name_ua']} (User: {user_id})")
                desc = await generate_product_description(
                    name=data['name_ua'], 
                    notes=data.get('tasting_notes', []),
                    origin=data.get('origin'),
                    roast=data.get('roast_level'),
                    processing=data.get('processing_method'),
                    price_300g=data.get('price_300g', 0),
                    price_1kg=price_1kg
                )
                logger.info(f"Background AI generation successful for {data['name_ua']}")
                return desc
            except asyncio.CancelledError:
                logger.warning(f"AI generation cancelled for {data['name_ua']}")
                raise
            except Exception as e:
                logger.error(f"Background AI generation failed for {data['name_ua']}: {e}")
                return f"☕ <b>{data.get('name_ua')}</b>. Свіжосмажена кава від Monkeys Coffee. Смачного!"

        active_ai_tasks[user_id] = asyncio.create_task(background_gen_task())
        
        await state.update_data(price_1kg=price_1kg)
        await state.set_state(AdminStates.waiting_for_product_image)
        
        await message.answer(
            "🖼️ <b>Крок 8/8: Зображення товару</b>\n\n"
            "Надішліть фото або натисніть кнопку нижче, щоб пропустити:",
            reply_markup=get_skip_image_keyboard(),
            parse_mode="HTML"
        )
    except ValueError:
        await message.answer("❌ Будь ласка, введіть числове значення.")

@router.callback_query(AdminStates.waiting_for_product_image, F.data == "admin_product_skip_image")
async def process_product_skip_image(callback: CallbackQuery, state: FSMContext):
    """Handle skipping image upload and await background description."""
    loading_msg = await callback.message.answer("🦍 *Зачекайте, Мавпа дописує опис...*", parse_mode="Markdown")
    
    user_id = callback.from_user.id
    description = None
    
    if user_id in active_ai_tasks:
        try:
            # Wait for background task with timeout
            logger.info(f"Awaiting AI task for user {user_id}...")
            description = await asyncio.wait_for(active_ai_tasks[user_id], timeout=35.0)
        except asyncio.TimeoutError:
            logger.warning(f"Background task for {user_id} timed out after 35s")
            description = f"🔥 <b>{(await state.get_data()).get('name_ua')}</b>. Досконалий лот для справжніх поціновувачів кави."
        except Exception as e:
            logger.error(f"Error awaiting background task: {e}")
            description = f"☕ <b>{(await state.get_data()).get('name_ua')}</b>. Смачного!"
        finally:
            active_ai_tasks.pop(user_id, None)
    
    if not description:
        # Check if description was pre-set (for non-coffee models)
        current_data = await state.get_data()
        description = current_data.get('description')
            
    if not description:
        description = "☕ Кава."
            
    await state.update_data(description=description)
    await loading_msg.delete()
    await show_product_preview(callback.message, state)
    await callback.answer()

@router.message(AdminStates.waiting_for_product_image, F.photo | F.document)
async def process_product_image_upload(message: Message, state: FSMContext):
    """Handle photo upload and await background description."""
    file_id = message.photo[-1].file_id if message.photo else message.document.file_id
    await state.update_data(photo_file_id=file_id)
    
    loading_msg = await message.answer("🦍 *Зберігаю фото та дописую опис...*", parse_mode="Markdown")
    
    user_id = message.from_user.id
    description = None
    
    if user_id in active_ai_tasks:
        try:
            description = await asyncio.wait_for(active_ai_tasks[user_id], timeout=30.0)
        except asyncio.TimeoutError:
            description = f"🔥 <b>{(await state.get_data()).get('name_ua')}</b>. Смак, що надихає!"
        except Exception as e:
            description = "☕ Смачна кава."
        finally:
            active_ai_tasks.pop(user_id, None)

    if not description:
        # Check if description was pre-set (for non-coffee models)
        current_data = await state.get_data()
        description = current_data.get('description')

    if not description:
        description = "☕ Кава."

    await state.update_data(description=description)
    await loading_msg.delete()
    await show_product_preview(message, state)




async def show_product_preview(message: Message, state: FSMContext):
    """Show product preview before saving."""
    data = await state.get_data()
    await state.set_state(AdminStates.waiting_for_product_confirm_generated)
    
    price_300g_formatted = format_currency(data.get('price_300g', 0))
    price_1kg_formatted = format_currency(data.get('price_1kg', 0))
    is_coffee = data.get('category', 'coffee') == 'coffee'
    
    preview_parts = [
        "<b>🧐 ПЕРЕГЛЯД ТОВАРУ:</b>",
        data.get('description', ''),
        UIStyle.DIVIDER,
        "💰 <b>ЦІНИ:</b>"
    ]
    
    if is_coffee:
        preview_parts.append(f"• 300г: <b>{price_300g_formatted}</b>")
        preview_parts.append(f"• 1кг: <b>{price_1kg_formatted}</b>")
    else:
        preview_parts.append(f"• Ціна: <b>{price_300g_formatted}</b>")
        
    preview_parts.append(UIStyle.DIVIDER)
    preview_parts.append('Все вірно? Тисніть <b>"✅ Зберегти"</b> або напишіть свій опис.')
    
    preview_text = "\n".join(preview_parts)
    
    from aiogram.utils.keyboard import ReplyKeyboardBuilder
    from aiogram.types import KeyboardButton
    
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="✅ Зберегти"))
    builder.row(KeyboardButton(text="❌ Скасувати"))
    
    # If photo exists, send it with preview
    if data.get('photo_file_id'):
        await message.answer_photo(
            data['photo_file_id'], 
            caption=preview_text, 
            reply_markup=builder.as_markup(resize_keyboard=True), 
            parse_mode="HTML"
        )
    else:
        await message.answer(
            preview_text, 
            reply_markup=builder.as_markup(resize_keyboard=True), 
            parse_mode="HTML"
        )


@router.message(AdminStates.waiting_for_product_confirm_generated)
async def finalize_product_add(message: Message, state: FSMContext, session: AsyncSession):
    """Finalize product addition with custom or generated description."""
    logger.info(f"Finalize product add triggered by user {message.from_user.id} with text: {message.text}")
    try:
        # DEBUG: Check if handler is called
        # await message.answer("DEBUG: Entering finalize_product_add")
        
        data = await state.get_data()
        
        # Validate required data
        if not data or 'name_ua' not in data:
            await message.answer("❌ Помилка: втрачені дані сесії. Спробуйте знову.")
            await state.clear()
            return

        # If user sent new text instead of clicking "Save", use it as description
        description = data.get('description', '')
        if message.text != "✅ Зберегти":
            description = message.text
        
        category = data.get('category', 'coffee')
        profile = "equipment" if category == "equipment" else "universal"
        
        new_product = Product(
            category=category,
            name_ua=data.get('name_ua', 'Unknown'),
            origin=data.get('origin', 'Unknown'),
            region=data.get('origin', 'Unknown'), # Map origin to region for display in catalog
            roast_level=data.get('roast_level', 'Medium'),
            processing_method=data.get('processing_method', 'Washed'),
            processing=data.get('processing_method', 'Washed'), # Backwards compatibility
            price_300g=data.get('price_300g', 0),
            price_1kg=data.get('price_1kg', 0),
            profile=profile,
            tasting_notes=data.get('tasting_notes', []),
            description=description,
            is_active=True
        )
        
        session.add(new_product)
        await session.commit()
        
        await message.answer(
            f"✅ <b>Товар успішно додано!</b>\n\n"
            f"Лот <b>{data.get('name_ua')}</b> тепер у каталозі.",
            parse_mode="HTML",
            reply_markup=get_admin_main_menu_keyboard()
        )
        
        # Save photo if exists
        if data.get('photo_file_id'):
            from src.utils.image_constants import ASSETS_DIR, convert_image_to_png
            ASSETS_DIR.mkdir(parents=True, exist_ok=True)
            photo_path = ASSETS_DIR / f"product_{new_product.id}.png"
            
            # Use bot to download
            from aiogram import Bot
            bot = message.bot
            file = await bot.get_file(data['photo_file_id'])
            await bot.download_file(file.file_path, photo_path)
            
            # Update product with path relative to assets if needed, but get_product_image handles it
            new_product.image_url = str(photo_path)
            await session.commit()
            
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error adding product: {e}", exc_info=True)
        await message.answer(f"❌ Сталася помилка при збереженні товару: {str(e)}")
        await state.clear()


@router.callback_query(F.data.startswith("admin_product_activate:"))
@router.callback_query(F.data.startswith("admin_product_deactivate:"))
async def toggle_product_status(callback: CallbackQuery, session: AsyncSession):
    """Toggle product active status."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    parts = callback.data.split(":")
    product_id = int(parts[1])
    
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        await callback.answer("❌ Товар не знайдено", show_alert=True)
        return
    
    product.is_active = not product.is_active
    await session.commit()
    
    status = "активовано" if product.is_active else "деактивовано"
    await callback.answer(f"✅ Товар {status}!")
    await show_products_list(callback, session)


@router.callback_query(F.data == "admin_products_list")
async def show_products_list(callback: CallbackQuery, session: AsyncSession):
    """Show products list with management actions."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    query = select(Product).order_by(Product.sort_order)
    result = await session.execute(query)
    products = result.scalars().all()
    
    text = "<b>☕ СПИСОК ТОВАРІВ</b>\n\nОберіть лот для перегляду та редагування:"
    
    keyboard = get_admin_product_list_keyboard(products)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_product_toggle_status:"))
async def admin_toggle_product_status(callback: CallbackQuery, session: AsyncSession):
    """Toggle product active status (shortcut)."""
    product_id = int(callback.data.split(":")[1])
    
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    product = result.scalar_one_or_none()
    
    if product:
        product.is_active = not product.is_active
        await session.commit()
        await callback.answer(f"✅ Статус {product.name_ua} змінено")
        await show_products_list(callback, session)
    else:
        await callback.answer("❌ Товар не знайдено", show_alert=True)


@router.callback_query(F.data == "admin_users_list")
async def show_users_list(callback: CallbackQuery, session: AsyncSession):
    """Show users list."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    query = select(User).order_by(User.created_at.desc()).limit(20)
    result = await session.execute(query)
    users = result.scalars().all()
    
    text = "<b>👥 Список користувачів (Останні 20)</b>\n\n"
    
    builder = InlineKeyboardBuilder()
    
    for user in users:
        username = f"@{user.username}" if user.username else str(user.id)
        # Handle potential None values for older records or manual insertions
        total_orders = user.total_orders or 0
        total_kg = user.total_purchased_kg or 0.0
        loyalty = user.loyalty_level or 1
        
        text += f"• <b>{user.first_name or ''} {user.last_name or ''}</b> ({username})\n"
        text += f"  Замовлень: {total_orders} | Куплено: {total_kg:.1f}кг\n"
        text += f"  Лояльність: Рівень {loyalty}\n\n"
    
    builder.row(InlineKeyboardButton(text="🔍 Пошук", callback_data="admin_users_search"))
    builder.row(InlineKeyboardButton(text="← Назад", callback_data="admin_users_main"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_users_search")
async def start_user_search(callback: CallbackQuery, state: FSMContext):
    """Start user search flow."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    await state.set_state(AdminStates.waiting_for_user_search)
    await callback.message.answer(
        "🔍 <b>Пошук користувача</b>\n\n"
        "Введіть <b>ID</b>, <b>Username</b> або <b>прізвище</b> користувача:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_user_search)
async def process_user_search(message: Message, state: FSMContext, session: AsyncSession):
    """Process user search query."""
    search_query = message.text.strip()
    
    # Search by ID, username, or name
    # Search by ID, username, or name (Imports moved to top)
    query = select(User).where(
        or_(
            cast(User.id, String).ilike(f"%{search_query}%"),
            User.username.ilike(f"%{search_query}%"),
            User.first_name.ilike(f"%{search_query}%"),
            User.last_name.ilike(f"%{search_query}%")
        )
    ).limit(10)
    
    result = await session.execute(query)
    users = result.scalars().all()
    
    if not users:
        await message.answer("❌ Користувачів не знайдено. Спробуйте ще раз або /cancel")
        return
    
    text = f"🔍 <b>Результати пошуку: '{search_query}'</b>\n\n"
    
    builder = InlineKeyboardBuilder()
    for user in users:
        username = f"@{user.username}" if user.username else str(user.id)
        total_orders = user.total_orders or 0
        total_kg = user.total_purchased_kg or 0.0
        
        text += f"• <b>{user.first_name or ''} {user.last_name or ''}</b> ({username})\n"
        text += f"  Замовлень: {total_orders} | Куплено: {total_kg:.1f}кг\n\n"
    
    builder.row(InlineKeyboardButton(text="← Назад до користувачів", callback_data="admin_users_main"))
    
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await state.clear()


@router.callback_query(F.data == "admin_promos_list")
async def show_promos_list(callback: CallbackQuery, session: AsyncSession):
    """Show promo codes list."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    from src.database.models import PromoCode
    query = select(PromoCode).order_by(PromoCode.created_at.desc())
    result = await session.execute(query)
    promos = result.scalars().all()
    
    text = "<b>🎫 Список промокодів</b>\n\n"
    
    builder = InlineKeyboardBuilder()
    
    for promo in promos:
        status = "✅" if promo.is_active else "🚫"
        text += f"{status} <b>{promo.code}</b> (-{promo.discount_percent}%)\n"
        text += f"   Використано: {promo.used_count}/{promo.usage_limit or '∞'}\n"
        text += f"   Мін. сума: {format_currency(promo.min_order_amount)}\n\n"
        
        # Add toggle button
        toggle_text = "🚫 Деактивувати" if promo.is_active else "✅ Активувати"
        builder.row(InlineKeyboardButton(
            text=f"{promo.code}: {toggle_text}",
            callback_data=f"admin_promo_toggle:{promo.id}"
        ))
    
    builder.row(InlineKeyboardButton(text="← Назад", callback_data="admin_analytics"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_promo_toggle:"))
async def toggle_promo_status(callback: CallbackQuery, session: AsyncSession):
    """Toggle promo code active status."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    promo_id = int(callback.data.split(":")[1])
    
    from src.database.models import PromoCode
    query = select(PromoCode).where(PromoCode.id == promo_id)
    result = await session.execute(query)
    promo = result.scalar_one_or_none()
    
    if not promo:
        await callback.answer("❌ Промокод не знайдено", show_alert=True)
        return
    
    promo.is_active = not promo.is_active
    await session.commit()
    
    await show_promos_list(callback, session)


# ========== DETAILED PRODUCT MANAGEMENT ==========

@router.callback_query(F.data.startswith("admin_product_view:"))
async def admin_view_product(callback: CallbackQuery, session: AsyncSession):
    """Show detailed product info and actions in admin panel."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    product_id = int(callback.data.split(":")[1])
    
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        await callback.answer("❌ Товар не знайдено", show_alert=True)
        return
    
    status = "✅ Активний" if product.is_active else "🚫 Вимкнено"
    
    text = f"""
<b>☕ {product.name_ua}</b>

<b>Статус:</b> {status}
<b>Походження:</b> {product.origin}
<b>Профіль:</b> {product.profile}

<b>💰 Ціни:</b>
• 300г: {format_currency(product.price_300g)}
• 1кг: {format_currency(product.price_1kg)}

<b>🌟 Нотатки:</b>
{", ".join(product.tasting_notes) if product.tasting_notes else "Не вказано"}

<b>📖 Опис:</b>
{product.description or "Відсутній"}
"""
    
    keyboard = get_product_action_keyboard(product_id, product.is_active)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_product_edit:"))
async def admin_product_edit(callback: CallbackQuery):
    """Show edit field selection for a product."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    product_id = int(callback.data.split(":")[1])
    
    text = "⚙️ <b>Редагування товару</b>\n\nОберіть поле, яке хочете змінити:"
    keyboard = get_product_edit_fields_keyboard(product_id)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_product_edit_field:"))
async def admin_product_edit_field(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Start FSM for editing a specific product field."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    parts = callback.data.split(":")
    product_id = int(parts[1])
    field = parts[2]
    
    field_names = {
        "name_ua": "Назва (UA)",
        "origin": "Походження",
        "category": "Категорія",
        "price_300g": "Ціна за 300г",
        "price_1kg": "Ціна за 1кг",
        "profile": "Профіль (espresso, filter, universal)",
        "roast_level": "Ступінь обсмаження",
        "processing_method": "Метод обробки",
        "tasting_notes": "Нотатки смаку (через кому)",
        "description": "Опис товару"
    }
    
    await state.update_data(product_id=product_id, edit_field=field)
    
    # Use specific keyboards for enum fields
    keyboard = get_cancel_keyboard()
    if field == "roast_level":
        keyboard = get_roast_level_keyboard()
    elif field == "processing_method":
        keyboard = get_processing_method_keyboard()
    elif field == "profile":
        from src.keyboards.admin_kb import get_profile_keyboard
        keyboard = get_profile_keyboard()
    elif field == "category":
        from src.database.models import Category
        # get_product_category_keyboard is already imported at top level
        
        query = select(Category).where(Category.is_active == True).order_by(Category.sort_order.asc())
        result = await session.execute(query)
        categories = result.scalars().all()
        keyboard = get_product_category_keyboard(categories)
    elif field == "description":
        # Use simple cancel keyboard OR AI generate keyboard
        keyboard = get_product_edit_description_keyboard(product_id)
        
    elif field == "image":
        # Show image options: AI generate, Upload, or Cancel
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="🤖 Згенерувати з AI",
            callback_data=f"admin_product_ai_img:{product_id}"
        ))
        builder.row(InlineKeyboardButton(
            text="✨ Покращити фото",
            callback_data=f"admin_product_enhance_img:{product_id}"
        ))
        builder.row(InlineKeyboardButton(
            text="📤 Завантажити своє",
            callback_data=f"admin_product_up_img:{product_id}"
        ))
        builder.row(InlineKeyboardButton(
            text="🔙 Назад",
            callback_data=f"admin_product_edit:{product_id}"
        ))
        
        await callback.message.edit_text(
            "🖼️ <b>Зображення товару</b>\n\n"
            "Оберіть дію:\n\n"
            "🤖 <b>Згенерувати</b> — створити нове фото з нуля\n"
            "✨ <b>Покращити</b> — покращити існуюче фото (зберігає упаковку)",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await callback.answer()
        return
        
    await state.set_state(AdminStates.waiting_for_product_edit_value)
    
    await callback.message.answer(
        f"📝 <b>Зміна поля: {field_names.get(field, field)}</b>\n\n"
        f"Введіть нове значення або оберіть зі списку:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_product_ai_gen:"))
async def process_admin_product_ai_gen(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Generate product description using AI."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return

    product_id = int(callback.data.split(":")[1])
    
    # Send loading state
    loading_msg = await callback.message.answer("🤖 <b>AI генерує опис...</b>\n<i>Це займе кілька секунд.</i>", parse_mode="HTML")
    await callback.answer()
    
    try:
        query = select(Product).where(Product.id == product_id)
        result = await session.execute(query)
        product = result.scalar_one_or_none()
        
        if not product:
            await loading_msg.delete()
            await callback.message.answer("❌ Товар не знайдено.")
            return

        # Use the narrative generator for punchy descriptions
        from src.services.ai_service import ai_service
        description, error = await ai_service.generate_description_narrative(
            name=product.name_ua,
            origin=product.origin or "Невідомо",
            roast=product.roast_level or "Середнє",
            notes=product.tasting_notes or [],
            processing=product.processing_method or "Мита"
        )
        
        await loading_msg.delete()
        
        if description:
            # Store generated text in state to apply later
            await state.update_data(ai_generated_description=description)
            
            await callback.message.answer(
                f"🤖 <b>AI згенерував варіант:</b>\n\n{description}\n\n"
                "Застосувати цей опис чи спробувати ще?",
                reply_markup=get_apply_ai_text_keyboard(product_id),
                parse_mode="HTML"
            )
        else:
            error_msg = error or "Невідома помилка"
            await callback.message.answer(f"⚠️ AI не зміг згенерувати опис.\n\n<b>Причина:</b> {error_msg}", parse_mode="HTML")
            
    except Exception as e:
        logger.error(f"Error generating description: {e}")
        try:
            await loading_msg.delete()
        except:
            pass
        await callback.message.answer(f"❌ Помилка: {e}")


@router.callback_query(F.data.startswith("admin_product_ai_apply:"))
async def process_admin_product_ai_apply(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Apply the AI generated description."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return

    product_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    description = data.get("ai_generated_description")
    
    if not description:
        await callback.answer("❌ Немає згенерованого опису", show_alert=True)
        return
        
    # Update product
    try:
        query = select(Product).where(Product.id == product_id)
        result = await session.execute(query)
        product = result.scalar_one_or_none()
        
        if product:
            product.description = description
            await session.commit()
            await callback.answer("✅ Опис оновлено!")
            await callback.message.answer(f"✅ <b>Опис товару оновлено:</b>\n\n{description}", parse_mode="HTML")
            
            # Return to product card
            await admin_product_view(callback, session)
        else:
            await callback.message.answer("❌ Товар не знайдено")
            
    except Exception as e:
        logger.error(f"Error applying description: {e}")
        await callback.answer("❌ Помилка збереження", show_alert=True)


@router.callback_query(AdminStates.waiting_for_product_edit_value, F.data.startswith("admin_roast:"))
async def process_product_edit_roast(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Process roast level edit selection."""
    roast_code = callback.data.split(":")[1]
    roast_map = {
        "roast_light": "Світле (Light)",
        "roast_medium": "Середнє (Medium)",
        "roast_dark": "Темне (Dark)",
        "roast_espresso": "Еспресо (Espresso)",
        "roast_filter": "Фільтр (Filter)",
        "roast_omni": "Омні (Omni)"
    }
    value = roast_map.get(roast_code, "Середнє")
    await save_product_edit(callback, state, session, value)


@router.callback_query(AdminStates.waiting_for_product_edit_value, F.data.startswith("admin_proc:"))
async def process_product_edit_processing(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Process processing method edit selection."""
    proc_code = callback.data.split(":")[1]
    proc_map = {
        "proc_washed": "Мита (Washed)",
        "proc_natural": "Натуральна (Natural)",
        "proc_honey": "Хані (Honey)",
        "proc_anaerobic": "Анаеробна (Anaerobic)",
        "proc_experimental": "Експериментальна"
    }
    value = proc_map.get(proc_code, "Мита")
    await save_product_edit(callback, state, session, value)


@router.callback_query(AdminStates.waiting_for_product_edit_value, F.data.startswith("admin_profile:"))
async def process_product_edit_profile(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Process profile edit selection."""
    profile_code = callback.data.split(":")[1]
    profile_map = {
        "profile_espresso": "espresso",
        "profile_filter": "filter",
        "profile_universal": "universal"
    }
    value = profile_map.get(profile_code, "universal")
    await save_product_edit(callback, state, session, value)


@router.callback_query(AdminStates.waiting_for_product_edit_value, F.data.startswith("admin_cat:"))
async def process_product_edit_category(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Process category edit selection."""
    category_slug = callback.data.split(":")[1]
    await save_product_edit(callback, state, session, category_slug)


@router.message(AdminStates.waiting_for_product_edit_value, F.photo)
async def process_product_edit_image(message: Message, state: FSMContext, session: AsyncSession):
    """Process updated product image."""
    data = await state.get_data()
    product_id = data.get('product_id')
    
    photo = message.photo[-1]
    
    from src.utils.image_constants import ASSETS_DIR, convert_image_to_png
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    photo_path = ASSETS_DIR / f"product_{product_id}.png"
    
    from aiogram import Bot
    bot = message.bot
    file = await bot.get_file(photo.file_id)
    await bot.download_file(file.file_path, photo_path)
    
    # Update DB
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    product = result.scalar_one_or_none()
    if product:
        product.image_url = str(photo_path)
        await session.commit()
        await message.answer(f"✅ Зображення для <b>{product.name_ua}</b> оновлено!", parse_mode="HTML")
        await admin_view_product_after_edit(message, product)
    
    await state.clear()


async def admin_view_product_after_edit(message: Message, product: Product):
    """Helper to show product after edit."""
    status = "✅ Активний" if product.is_active else "🚫 Вимкнено"
    text = f"""
<b>☕ {product.name_ua}</b>

<b>Статус:</b> {status}
<b>Походження:</b> {product.origin}
<b>Профіль:</b> {product.profile}

<b>💰 Ціни:</b>
• 300г: {format_currency(product.price_300g)}
• 1кг: {format_currency(product.price_1kg)}

<b>🌟 Нотатки:</b>
{", ".join(product.tasting_notes) if product.tasting_notes else "Не вказано"}

<b>📖 Опис:</b>
{product.description or "Відсутній"}
"""
    from src.keyboards.admin_kb import get_product_action_keyboard
    keyboard = get_product_action_keyboard(product.id, product.is_active)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.message(AdminStates.waiting_for_product_edit_value)
async def process_product_edit_value_text(message: Message, state: FSMContext, session: AsyncSession):
    """Save the updated field value for a product (text input)."""
    await save_product_edit(message, state, session, message.text)


async def save_product_edit(event, state: FSMContext, session: AsyncSession, value: str):
    """Common logic to save edited product field."""
    data = await state.get_data()
    product_id = data.get('product_id')
    field = data.get('edit_field')
    
    # Handle message vs callback
    message = event if isinstance(event, Message) else event.message
    
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        await message.answer("❌ Товар не знайдено")
        await state.clear()
        return
    
    try:
        if field in ["price_300g", "price_1kg"]:
            setattr(product, field, int(value))
        elif field == "tasting_notes":
            setattr(product, field, [x.strip() for x in value.split(",")])
        else:
            setattr(product, field, value)
            
        await session.commit()
        await message.answer(f"✅ Поле <b>{field}</b> оновлено до: <code>{value}</code>", parse_mode="HTML")
        
        # Show updated product
        status = "✅ Активний" if product.is_active else "🚫 Вимкнено"
        text = f"""
<b>☕ {product.name_ua}</b>

<b>Статус:</b> {status}
<b>Походження:</b> {product.origin}
<b>Профіль:</b> {product.profile}

<b>💰 Ціни:</b>
• 300г: {format_currency(product.price_300g)}
• 1кг: {format_currency(product.price_1kg)}

<b>🌟 Нотатки:</b>
{", ".join(product.tasting_notes) if product.tasting_notes else "Не вказано"}

<b>📖 Опис:</b>
{product.description or "Відсутній"}
"""
        keyboard = get_product_action_keyboard(product.id, product.is_active)
        await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        
        await state.clear()
    except ValueError:
        await message.answer("❌ Помилка: Введіть правильне числове значення.")
    except Exception as e:
        logger.error(f"Error updating product: {e}")
        await message.answer("❌ Сталася помилка при оновленні.")


@router.callback_query(F.data.startswith("admin_prod_del:"))
async def admin_product_delete(callback: CallbackQuery, session: AsyncSession):
    """Ask for confirmation before deleting a product."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    product_id = int(callback.data.split(":")[1])
    
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        await callback.answer("❌ Товар не знайдено", show_alert=True)
        return
    
    text = f"❗ <b>ВИДАЛЕННЯ ТОВАРУ</b>\n\nВи впевнені, що хочете видалити <b>{product.name_ua}</b>?\n\nЦю дію неможливо скасувати!"
    keyboard = get_product_delete_confirm_keyboard(product_id)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_prod_conf_del:"))
async def admin_product_delete_confirm(callback: CallbackQuery, session: AsyncSession):
    """Delete a product from the database."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    product_id = int(callback.data.split(":")[1])
    
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    product = result.scalar_one_or_none()
    
    if product:
        name = product.name_ua
        await session.delete(product)
        await session.commit()
        await callback.answer(f"🗑 {name} видалено", show_alert=True)
    else:
        await callback.answer("❌ Товар вже було видалено")


        
@router.callback_query(F.data == "admin_content_main")
async def show_content_management(callback: CallbackQuery):
    """Show content & discounts management menu."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    from src.keyboards.admin_kb import get_content_management_keyboard
    
    text = "🖼️ <b>Контент та Знижки</b>\n\nТут ви можете керувати візуалом та правилами оптових знижок:"
    await callback.message.edit_text(text, reply_markup=get_content_management_keyboard(), parse_mode="HTML")
    await callback.answer()


# ---------- IMAGE MANAGEMENT ----------

MODULE_LABELS = {
    "promotions": "⚡ Акції / Спецпропозиції",
    "cabinet": "👤 Мій Кабінет / Бонуси",
    "cart": "🛒 Кошик",
    "about_us": "🐒 Про нас",
    "support": "💬 Підтримка",
    "catalog_map": "🗺️ Карта обсмаження"
}

@router.callback_query(F.data == "admin_content_images")
async def show_image_management(callback: CallbackQuery):
    """Show module image management list."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    from src.keyboards.admin_kb import get_image_management_keyboard
    
    text = "🖼️ <b>Керування зображеннями</b>\n\nОберіть розділ, для якого хочете змінити обкладинку:"
    await callback.message.edit_text(text, reply_markup=get_image_management_keyboard(MODULE_LABELS), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_img_mod:"))
async def start_module_image_update(callback: CallbackQuery, state: FSMContext):
    """Ask admin to upload new image for a module."""
    module_key = callback.data.split(":")[1]
    
    await state.set_state(AdminStates.waiting_for_module_image)
    await state.update_data(target_module=module_key)
    
    text = f"📥 <b>Оновлення: {MODULE_LABELS.get(module_key, module_key)}</b>\n\nБудь ласка, надішліть нове зображення для цього розділу:"
    await callback.message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.message(AdminStates.waiting_for_module_image, F.photo)
async def process_module_image(message: Message, state: FSMContext, session: AsyncSession):
    """Save the uploaded module image file_id."""
    data = await state.get_data()
    module_name = data.get('target_module')
    file_id = message.photo[-1].file_id  # Best quality
    
    from src.database.models import ModuleImage
    
    # Update or create
    query = select(ModuleImage).where(ModuleImage.module_name == module_name)
    result = await session.execute(query)
    module_img = result.scalar_one_or_none()
    
    if module_img:
        module_img.file_id = file_id
    else:
        new_img = ModuleImage(module_name=module_name, file_id=file_id)
        session.add(new_img)
    
    await session.commit()
    await state.clear()
    
    await message.answer(
        f"✅ Зображення для розділу <b>{MODULE_LABELS.get(module_name, module_name)}</b> успішно оновлено!",
        reply_markup=get_admin_main_menu_keyboard(),
        parse_mode="HTML"
    )




# ========== SMART EDITOR (CONTENT MANAGEMENT) ==========

@router.callback_query(F.data == "admin_content_main")
async def show_content_management_menu(callback: CallbackQuery):
    """Show content management menu."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    text = """
<b>🎛 Конструктор та Контент</b>

Тут ви можете змінювати тексти, банери та налаштовувати знижки.

<b>📝 Тексти:</b> Заголовки, описи, повідомлення.
<b>🖼️ Зображення:</b> Банери в меню.
<b>⚡ Знижки:</b> Правила оптових знижок.
"""
    from src.keyboards.admin_kb import get_content_management_keyboard
    keyboard = get_content_management_keyboard()
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_content_texts")
async def show_text_editor_menu(callback: CallbackQuery, session: AsyncSession):
    """Show list of editable texts."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    from src.services.content_service import ContentService
    items = await ContentService.get_all_content(session)
    
    text = "<b>📝 Редактор Текстів</b>\n\nОберіть елемент для редагування:"
    
    from src.keyboards.admin_kb import get_content_editor_keyboard
    keyboard = get_content_editor_keyboard(items)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_edit_text:"))
async def edit_text_value_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Start editing a specific text value."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    key = callback.data.replace("admin_edit_text:", "")
    
    from src.services.content_service import ContentService
    value = await ContentService.get_text(session, key)
    
    await state.update_data(edit_text_key=key)
    await state.set_state(AdminStates.waiting_for_text_content)
    
    text = (
        f"✏️ <b>Редагування: {key}</b>\n\n"
        f"Поточне значення:\n"
        f"<code>{value}</code>\n\n"
        f"👇 Введіть новий текст (підтримується HTML):"
    )
    
    from src.keyboards.admin_kb import get_text_edit_action_keyboard
    keyboard = get_text_edit_action_keyboard(key)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.message(AdminStates.waiting_for_text_content)
async def process_text_content_preview(message: Message, state: FSMContext):
    """Show preview of the edited text."""
    new_text = message.text
    
    await state.update_data(new_text_value=new_text)
    await state.set_state(AdminStates.waiting_for_text_content_confirm)
    
    preview_text = f"<b>👁️ Попередній перегляд:</b>\n\n{new_text}\n\n━━━━━━━━━━━━━━━━\nЗберегти зміни?"
    
    from src.keyboards.admin_kb import get_confirm_save_keyboard
    await message.answer(preview_text, reply_markup=get_confirm_save_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "admin_text_save")
async def confirm_text_save(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Save the text content."""
    current_state = await state.get_state()
    logger.info(f"CONFIRM SAVE TRIGGERED. User: {callback.from_user.id}. State: {current_state}")
    
    # Check if we have the data we need, regardless of strict state match
    data = await state.get_data()
    key = data.get('edit_text_key')
    new_value = data.get('new_text_value')
    
    if not key or not new_value:
        await callback.answer("❌ Помилка: втрачено дані сесії. Спробуйте знову.", show_alert=True)
        logger.error(f"Missing key/value in state data: {data}")
        return

    from src.services.content_service import ContentService
    await ContentService.update_text(session, key, new_value)
    
    await state.clear()
    await callback.message.edit_text(f"✅ Текст для <b>{key}</b> успішно оновлено!", reply_markup=None, parse_mode="HTML")
    
    # Return to updated list
    await show_text_editor_menu(callback, session)


@router.callback_query(F.data == "admin_text_edit_continue")
async def continue_text_edit(callback: CallbackQuery, state: FSMContext):
    """Go back to editing state."""
    logger.info(f"CONTINUE EDIT TRIGGERED. State: {await state.get_state()}")
    await state.set_state(AdminStates.waiting_for_text_content)
    
    # Ensure key is preserved
    data = await state.get_data()
    if not data.get('edit_text_key'):
         await callback.answer("❌ Помилка: втрачено ключ редагування.", show_alert=True)
         return

    await callback.message.edit_text("👇 Продовжуйте редагування (надішліть виправлений текст):", reply_markup=get_cancel_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_text_cancel")
async def cancel_text_edit(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Cancel editing."""
    logger.info(f"CANCEL EDIT TRIGGERED. State: {await state.get_state()}")
    await state.clear()
    await callback.answer("❌ Скасовано")
    await show_text_editor_menu(callback, session)


@router.callback_query(F.data == "admin_text_edit_continue")
async def edit_text_continue_manual(callback: CallbackQuery, state: FSMContext):
    """Switch to manual editing after AI generation (or instead of saving)."""
    current_state = await state.get_state()
    logger.info(f"MANUAL EDIT TRIGGERED. Old State: {current_state}")
    
    await state.set_state(AdminStates.waiting_for_text_content)
    
    # Get the text we were previewing, if any, to show it as a starting point?
    # Or just ask to enter new text.
    data = await state.get_data()
    generated_text = data.get('new_text_value', '')
    
    msg_text = "👇 <b>Введіть новий варіант тексту</b>"
    if generated_text:
        msg_text += f"\n\nПопередній варіант:\n<code>{generated_text}</code>"
        
    await callback.message.answer(msg_text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "admin_text_save")
async def save_ai_generated_text(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Save the AI generated text."""
    data = await state.get_data()
    key = data.get('edit_text_key')
    new_text = data.get('new_text_value')
    
    if not key or not new_text:
        await callback.answer("❌ Помилка: немає даних для збереження", show_alert=True)
        return

    from src.services.content_service import ContentService
    await ContentService.update_text(session, key, new_text)
    
    await callback.answer("✅ Збережено!")
    await show_text_editor_menu(callback, session)
    await state.clear()


# ========== AI GENERATION FOR SMART EDITOR ==========

# Context-aware prompts for each content key
AI_PROMPTS = {
    "cart.empty_text": "Напиши мотивуючий текст для порожнього кошика кавового магазину Monkeys Coffee Roasters. Структура: 1) Короткий емоційний вступ (2 рядки). 2) Заклик до дії. 3) Нагадування про бонуси (знижка -25% від 2кг, безкоштовна доставка від 1500 грн). Тільки українська. Використовуй HTML теги <b> та <i>. Зроби текст чистим і читабельним.",
    "catalog.espresso": "Напиши опис профілю Еспресо. Структура: 1) Що це таке? (1 речення). 2) Смакові особливості (булітами). 3) Для кого підходить. Тільки українська. HTML форматування.",
    "catalog.filter": "Напиши опис профілю Фільтр. Структура: 1) Що це таке? (1 речення). 2) Смакові особливості (булітами). 3) Для кого підходить. Тільки українська. HTML форматування.",
    "catalog.guide": "Напиши гайд по вибору кави. Структуруй булітами: • Еспресо (для чого) • Фільтр (для чого) • Універсальна. Тільки українська. HTML форматування.",
    "cabinet.caption": "Напиши текст для розділу 'Мій Кабінет'. Структура: Привітання, Твій статус, Твої бонуси (булітами). Тільки українська. HTML форматування.",
    "about.text": "Напиши про Monkeys Coffee Roasters. Структура: Хто ми (1 абзац), Наші цінності (булітами), Наша місія. Тільки українська. HTML форматування.",
    "start.welcome_new": "Привітання нового клієнта. Структура: Вітаємо {name}! (заголовок), Хто ми (1 речення), Що пропонуємо (булітами: свіжа кава, швидка доставка). Тільки українська. HTML форматування.",
    "start.welcome_return": "Привітання постійного клієнта. Стиль: Стриманий, професійний. Структура: З поверненням {name}! (заголовок), Новинки (маркований список). Тільки українська. HTML форматування.",
    "promotions.header": "Заголовок 'Акції'. Стиль: Діловий, чіткий. Перерахуй основні плюшки списком: Опт (від 2кг), Рефералка, Накопичувальна. Тільки українська. HTML форматування.",
    "loyalty.header": "Заголовок 'Лояльність'. Стиль: Лаконічний. Поясни рівні лояльності списком. Тільки українська. HTML форматування.",
    "support.header": "Заголовок 'Підтримка'. Коротке, ввічливе повідомлення. Тільки українська. HTML форматування.",
    "cart.header": "Заголовок Кошика. Стиль: Мінімалістичний, спонукаючий. Тільки українська. HTML форматування.",
}

DEFAULT_AI_PROMPT = "Напиши короткий, професійний та структурований текст для Telegram бота Monkeys Coffee Roasters. Використовуй заголовки (<b>) та списки. Уникай зайвих емодзі. Мова: українська."


@router.callback_query(F.data.startswith("admin_ai_gen_text:"))
async def ai_generate_text_for_editor(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Generate AI text for a content key and show preview."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return

    key = callback.data.replace("admin_ai_gen_text:", "")
    await state.update_data(edit_text_key=key)

    loading_msg = await callback.message.answer("🤖 <b>AI генерує текст...</b>\n<i>Зачекайте кілька секунд.</i>", parse_mode="HTML")
    await callback.answer()

    prompt = AI_PROMPTS.get(key, DEFAULT_AI_PROMPT)

    try:
        from src.services.ai_service import ai_service
        
        # New clean method with GPT-4o support
        generated, error_msg = await ai_service.generate_smart_editor_text(key, prompt)
        
        await loading_msg.delete()

        if generated:
            await state.update_data(new_text_value=generated)
            await state.set_state(AdminStates.waiting_for_text_content_confirm)
            
            # DEBUG LOG
            logger.info(f"AI generated text. State set to: {await state.get_state()}. Data: {await state.get_data()}")
            
            preview = f"🤖 <b>AI згенерував текст:</b>\n\n{generated}\n\n━━━━━━━━━━━━━━━━\nЗберегти або відредагувати?"
            from src.keyboards.admin_kb import get_confirm_save_keyboard
            await callback.message.answer(preview, reply_markup=get_confirm_save_keyboard(), parse_mode="HTML")
        else:
            # AI unavailable — show current value for manual editing
            error_details = error_msg or "Невідома помилка"
            
            from src.services.content_service import ContentService
            current = await ContentService.get_text(session, key)
            await state.set_state(AdminStates.waiting_for_text_content)
            await callback.message.answer(
                f"⚠️ <b>AI недоступний</b> ({error_details}).\n\n"
                f"Поточний текст:\n<code>{current}</code>\n\n"
                f"👇 Введіть новий текст вручну:",
                parse_mode="HTML",
                reply_markup=get_cancel_keyboard()
            )
    except Exception as e:
        logger.error(f"AI generation for editor failed: {e}")
        try:
            await loading_msg.delete()
        except:
            pass
        await callback.message.answer(f"❌ Критична помилка: {str(e)}", reply_markup=get_cancel_keyboard())


@router.callback_query(F.data.startswith("admin_reset_text:"))
async def reset_text_to_default(callback: CallbackQuery, session: AsyncSession):
    """Reset a content key to its default value."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return

    key = callback.data.replace("admin_reset_text:", "")

    from src.services.content_service import ContentService
    default_value = await ContentService.reset_to_default(session, key)

    if default_value:
        await callback.answer("✅ Скинуто до стандартного значення!", show_alert=True)
        # Refresh the edit screen
        value = await ContentService.get_text(session, key)
        from src.keyboards.admin_kb import get_text_edit_action_keyboard
        text = (
            f"✏️ <b>Редагування: {key}</b>\n\n"
            f"Поточне значення:\n"
            f"<code>{value}</code>\n\n"
            f"👇 Введіть новий текст або скористайтесь AI:"
        )
        await callback.message.edit_text(text, reply_markup=get_text_edit_action_keyboard(key), parse_mode="HTML")
    else:
        await callback.answer("⚠️ Стандартне значення не знайдено", show_alert=True)


@router.callback_query(F.data.startswith("admin_text_"))
async def debug_text_callbacks(callback: CallbackQuery, state: FSMContext):
    """Debug handler for text callbacks that didn't match."""
    current_state = await state.get_state()
    logger.warning(f"⚠️ UNHANDLED TEXT CALLBACK: {callback.data} | State: {current_state}")
    await callback.answer(f"Debug: Unhandled | State: {current_state}", show_alert=True)


# ========== PRODUCT IMAGE AI GENERATION ==========

@router.callback_query(F.data.startswith("admin_product_ai_img:"))
async def generate_product_image_ai(callback: CallbackQuery, session: AsyncSession):
    """Generate product image using AI (DALL-E)."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    product_id = int(callback.data.split(":")[1])
    
    # Get product info
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        await callback.answer("❌ Товар не знайдено", show_alert=True)
        return
    
    # Send loading message
    loading_msg = await callback.message.answer(
        "🤖 <b>AI генерує зображення...</b>\n"
        "<i>Це може зайняти 10-30 секунд.</i>",
        parse_mode="HTML"
    )
    
    try:
        from src.services.ai_service import ai_service
        from src.utils.image_constants import ASSETS_DIR, convert_image_to_png
        
        # Generate image
        save_path = ASSETS_DIR / f"product_{product.id}.png"
        image_url, error, local_path = await ai_service.generate_product_image(
            product_name=product.name_ua,
            origin=product.origin or "Unknown",
            roast_level=product.roast_level or "Medium",
            tasting_notes=product.tasting_notes,
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
            # Save to database
            product.image_url = str(local_path)
            await session.commit()
            
            await callback.message.answer_photo(
                FSInputFile(local_path),
                caption=f"✅ <b>Зображення для {product.name_ua} згенеровано!</b>\n\n"
                        f"Збережено локально.",
                parse_mode="HTML"
            )
        else:
            await callback.message.answer(
                f"⚠️ Зображення згенеровано, але не вдалося зберегти локально.\n"
                f"URL: {image_url}",
                parse_mode="HTML"
            )
            
    except Exception as e:
        logger.error(f"Error generating product image: {e}")
        await loading_msg.delete()
        await callback.message.answer(f"❌ Помилка: {str(e)}", parse_mode="HTML")
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin_product_up_img:"))
async def start_product_image_upload(callback: CallbackQuery, state: FSMContext):
    """Ask admin to upload image for product."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    product_id = int(callback.data.split(":")[1])
    await state.update_data(product_id=product_id)
    await state.set_state(AdminStates.waiting_for_product_edit_value)
    
    await callback.message.answer(
        "📤 <b>Завантаження зображення</b>\n\n"
        "Надішліть фото для товару:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_product_enhance_img:"))
async def start_product_image_enhance(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Ask admin to upload image to enhance (image-to-image)."""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ заборонено", show_alert=True)
        return
    
    product_id = int(callback.data.split(":")[1])
    
    # First check if product has existing image
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    product = result.scalar_one_or_none()
    
    if not product or not product.image_url:
        await callback.message.answer(
            "❌ <b>Спочатку додайте фото товару</b>\n\n"
            "Для покращення потрібно спочатку мати фото упаковки.\n"
            "Використайте '📤 Завантажити своє' спочатку.",
            parse_mode="HTML"
        )
        await callback.answer()
        return
    
    await state.update_data(product_id=product_id, enhance_mode=True)
    await state.set_state(AdminStates.waiting_for_product_edit_value)
    
    await callback.message.answer(
        "✨ <b>Покращення зображення</b>\n\n"
        "Надішліть нове фото упаковки кави, яке ви хочете покращити.\n\n"
        "AI покращить якість фото, змінить фон, але збереже вашу упаковку, назву та лейбли.",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_product_edit_value, F.photo)
async def process_product_image_enhance(message: Message, state: FSMContext, session: AsyncSession):
    """Process uploaded image for AI enhancement (image-to-image)."""
    data = await state.get_data()
    product_id = data.get('product_id')
    enhance_mode = data.get('enhance_mode', False)
    
    if not enhance_mode:
        # Regular image upload - handled by other handler
        await process_product_edit_image(message, state, session)
        return
    
    # Download the uploaded image first
    photo = message.photo[-1]
    from src.utils.image_constants import ASSETS_DIR, convert_image_to_png
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    temp_input_path = ASSETS_DIR / f"temp_enhance_{message.from_user.id}.png"
    
    from aiogram import Bot
    bot = message.bot
    file = await bot.get_file(photo.file_id)
    await bot.download_file(file.file_path, temp_input_path)
    
    # Convert HEIC/HEIF to PNG if needed
    temp_input_path = convert_image_to_png(temp_input_path)

    # Show loading message
    loading_msg = await message.answer(
        "✨ <b>AI покращує зображення...</b>\n\n"
        "<i>Це може зайняти 20-40 секунд.</i>\n\n"
        "AI збереже вашу упаковку та лейбли, але покращить фон та якість.",
        parse_mode="HTML"
    )
    
    try:
        # Get product info for roast level
        query = select(Product).where(Product.id == product_id)
        result = await session.execute(query)
        product = result.scalar_one_or_none()
        
        roast_level = product.roast_level if product else None
        
        # Generate enhanced image
        from src.services.ai_service import ai_service
        save_path = ASSETS_DIR / f"product_{product_id}.png"
        
        image_url, error, local_path = await ai_service.enhance_product_image(
            input_image_path=temp_input_path,
            product_name=product.name_ua if product else None,
            roast_level=roast_level,
            save_path=save_path
        )
        
        await loading_msg.delete()
        
        # Clean up temp file
        if temp_input_path.exists():
            temp_input_path.unlink()
        
        if error:
            await message.answer(
                f"❌ <b>Помилка покращення</b>\n\n{error}",
                parse_mode="HTML"
            )
            await state.clear()
            return
        
        if local_path:
            # Update product in DB
            if product:
                product.image_url = str(local_path)
                await session.commit()
            
            await message.answer_photo(
                FSInputFile(local_path),
                caption=f"✨ <b>Зображення для {product.name_ua if product else 'товару'} покращено!</b>\n\n"
                        f"✅ Упаковка та лейбли збережені\n"
                        f"✅ Якість покращена\n"
                        f"✅ Новий фон застосовано",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"⚠️ Зображення покращено, але не вдалося зберегти.\nURL: {image_url}",
                parse_mode="HTML"
            )
            
    except Exception as e:
        logger.error(f"Error enhancing product image: {e}")
        await loading_msg.delete()
        # Clean up temp file on error
        if temp_input_path.exists():
            temp_input_path.unlink()
        await message.answer(f"❌ Помилка: {str(e)}", parse_mode="HTML")
    
    await state.clear()


