"""Checkout handler with FSM flow."""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, PreCheckoutQuery, LabeledPrice, SuccessfulPayment
)
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload # Додано для правильного завантаження товарів

from src.database.models import User, PromoCode, VolumeDiscount, Order
from src.services.cart_service import CartService
from src.services.order_service import OrderService
from src.services.discount_engine import DiscountEngine
from src.keyboards.checkout_kb import (
    get_grind_selection_keyboard,
    get_delivery_method_keyboard,
    get_order_confirmation_keyboard,
    get_payment_keyboard,
    get_cancel_keyboard,
    get_profile_confirmation_keyboard,
    get_use_saved_keyboard
)
from src.keyboards.main_menu import get_main_menu_keyboard, get_admin_main_menu_keyboard
from src.states.checkout_states import CheckoutStates
from src.services.payment_service import payment_service
from src.utils.formatters import format_currency, format_order_items
from src.utils.validators import validate_phone, validate_city_name, validate_address, sanitize_user_input
from src.utils.constants import DELIVERY_METHOD_NAMES, GRIND_TYPE_NAMES, ORDER_STATUS_NAMES, DeliveryMethod
from config import settings
from src.handlers.cart import show_cart # Імпорт для повернення в кошик

router = Router()
logger = logging.getLogger(__name__)


# ==========================================
# 🔄 ДОПОМІЖНА ФУНКЦІЯ ГЕНЕРАЦІЇ ЗАМОВЛЕННЯ
# ==========================================
async def _generate_and_send_order_preview(message: Message, state: FSMContext, session: AsyncSession, user_id: int):
    """Спільна логіка створення замовлення для швидкого та повного чекауту."""
    data = await state.get_data()
    
    # Отримуємо користувача
    user_query = select(User).where(User.id == user_id)
    user_result = await session.execute(user_query)
    user = user_result.scalar_one_or_none()
    
    if not user:
        await message.bot.send_message(chat_id=user_id, text="❌ Помилка: користувач не знайдений")
        await state.clear()
        return
    
    cart_items = await CartService.get_cart_items(session, user_id)
    if not cart_items:
        await message.bot.send_message(chat_id=user_id, text="❌ Кошик порожній!")
        await state.clear()
        return
    
    # Знижки — читаємо промокод з user.active_promo_code (зберігається в БД)
    promo_code_used = user.active_promo_code or data.get('promo_code')
    promo_code_obj = None
    if promo_code_used:
        promo_query = select(PromoCode).where(PromoCode.code == promo_code_used.upper())
        promo_result = await session.execute(promo_query)
        promo_code_obj = promo_result.scalar_one_or_none()

    
    query_dist = select(VolumeDiscount).where(VolumeDiscount.is_active == True)
    res_dist = await session.execute(query_dist)
    active_rules = res_dist.scalars().all()
    
    discount_breakdown = DiscountEngine.calculate_full_discount(cart_items, user, promo_code_obj, active_rules=active_rules)
    
    # Доставка
    delivery_cost = OrderService._calculate_delivery_cost(
        data['delivery_method'],
        discount_breakdown.final_total
    )
    is_free_delivery = delivery_cost == 0 and discount_breakdown.final_total >= settings.free_delivery_threshold
    
    # Створення замовлення (pending)
    try:
        order = await OrderService.create_order_from_cart(
            session,
            user,
            delivery_method=data['delivery_method'],
            delivery_city=data['delivery_city'],
            delivery_address=data['delivery_address'],
            recipient_name=data['recipient_name'],
            recipient_phone=data['recipient_phone'],
            grind_preference=data['grind_preference'],
            promo_code_used=promo_code_used
        )
        # Clear the promo code after it's been applied to the order
        if user.active_promo_code:
            user.active_promo_code = None
            await session.commit()
    except ValueError as e:
        await message.bot.send_message(chat_id=user_id, text=f"❌ Помилка створення замовлення: {e}")
        await state.clear()
        return

    
    # Формування тексту підтвердження
    text = f"""
<b>📋 ПІДТВЕРДЖЕННЯ #{order.order_number}</b> 🐒
━━━━━━━━━━━━━━━━━━━━━━
<b>📦 ТОВАРИ:</b>
{format_order_items(order.items)}
💸 Товарів на: {format_currency(order.subtotal)}
━━━━━━━━━━━━━━━━━━━━━━
<b>🎯 ЗНИЖКИ:</b>
"""
    if discount_breakdown.volume_discount_percent > 0:
        text += f"✅ Об'ємна: -{format_currency(order.discount_volume)}\n"
    if discount_breakdown.loyalty_discount_percent > 0:
        text += f"✅ Лояльність: -{format_currency(order.discount_loyalty)}\n"
    if discount_breakdown.promo_discount_percent > 0:
        text += f"✅ Промокод: -{format_currency(order.discount_promo)}\n"
    
    total_discount = order.discount_volume + order.discount_loyalty + order.discount_promo
    if total_discount > 0:
        text += f"💰 Разом знижки: -{format_currency(total_discount)}\n"
    else:
        text += "Знижок немає\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━━━\n"
    
    delivery_method = data['delivery_method']
    clean_dm = delivery_method.replace("DeliveryMethod.", "").lower()
    delivery_name = DELIVERY_METHOD_NAMES.get(clean_dm, delivery_method)
    
    delivery_status = f"{format_currency(delivery_cost)} ✅ БЕЗКОШТОВНО!" if is_free_delivery else format_currency(delivery_cost)
    
    text += f"<b>🚚 ДОСТАВКА:</b> {delivery_name} — {delivery_status}\n"
    text += f"📍 {data.get('delivery_city')}, {data.get('delivery_address')}\n"
    text += f"👤 {data.get('recipient_name')} ({data.get('recipient_phone')})\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"<b>💳 РАЗОМ: {format_currency(order.total)}</b>\n"
    
    if total_discount > 0:
        savings_pct = int((total_discount / order.subtotal) * 100)
        text += f"\n⚫ Ви економите: {format_currency(total_discount)} ({savings_pct}%)\n"
    
    text += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"<b>📍 Доставка:</b>\n{data['delivery_city']}\n"
    
    is_post = clean_dm in ["nova_poshta", "ukrposhta"]
    address_label = "Відділення:" if is_post else "Адреса:"
    text += f"<b>{address_label}</b> {data['delivery_address']}\n\n"
    text += f"<b>👤 Отримувач:</b>\n{data['recipient_name']}\n{data['recipient_phone']}\n\n"
    
    grind_name = GRIND_TYPE_NAMES.get(data['grind_preference'], data['grind_preference'])
    text += f"<b>☕ Помел:</b> {grind_name}\n"
    text += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    payment_url = payment_service.get_payment_url(
        order_id=order.order_number,
        amount=order.total,
        description=f"Оплата замовлення #{order.order_number} у Monkeys Coffee"
    )
    
    
    keyboard = get_order_confirmation_keyboard(order.id, payment_url=payment_url)
    
    # 🧹 Clear Reply Keyboard because we are switching to Inline flow
    from aiogram.types import ReplyKeyboardRemove
    clearing_msg = await message.bot.send_message(
        chat_id=user_id,
        text="⏳ Формуємо замовлення...",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Використовуємо bot.send_message замість message.answer для 100% надійності після видалення
    await message.bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard, parse_mode="HTML")
    
    # Delete the "Clearing" message to keep chat clean
    try:
        await clearing_msg.delete()
    except Exception:
        pass
        
    await state.set_state(CheckoutStates.confirming_order)
    await state.update_data(order_id=order.id)


@router.callback_query(F.data == "checkout_cancel_inline")
async def handle_checkout_cancel_inline(callback: CallbackQuery, state: FSMContext):
    """Handle inline cancel button during checkout."""
    await callback.message.delete()
    await state.clear()
    
    user_id = callback.from_user.id
    is_admin = user_id in settings.admin_id_list
    keyboard = get_admin_main_menu_keyboard() if is_admin else get_main_menu_keyboard()
    
    await callback.message.answer(
        "❌ Оформлення замовлення скасовано.\n\nТовари залишилися в кошику. Ви можете продовжити покупки.",
        reply_markup=keyboard
    )


# ==========================================
# 🚦 FSM ХЕНДЛЕРИ ОФОРМЛЕННЯ
# ==========================================

@router.callback_query(F.data == "cart_checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    user_id = callback.from_user.id
    
    cart_items = await CartService.get_cart_items(session, user_id)
    if not cart_items:
        await callback.answer("❌ Кошик порожній!", show_alert=True)
        return
    
    await state.clear()
    
    user_query = select(User).where(User.id == user_id)
    result = await session.execute(user_query)
    user = result.scalar_one_or_none()
    
    if user and user.delivery_city and user.last_address:
        text = f"""
🔴 <b>Твій профайл (Швидке оформлення)</b> 🐒

Привіт! Ми тебе пам'ятаємо. Використати ці дані?

🏠 <b>Місто:</b> {user.delivery_city}
📍 <b>Адреса/Відділення:</b> {user.last_address}
👤 <b>Отримувач:</b> {user.recipient_name or user.first_name}
📞 <b>Телефон:</b> {user.phone or 'Не вказано'}

👇 Як діємо?
"""
        await callback.message.answer(text, reply_markup=get_profile_confirmation_keyboard(), parse_mode="HTML")
        await state.set_state(CheckoutStates.confirming_saved_data)
        await state.update_data(
            is_fast_checkout=True,
            delivery_city=user.delivery_city,
            delivery_address=user.last_address,
            recipient_name=user.recipient_name or user.first_name,
            recipient_phone=user.phone
        )
    else:
        await state.update_data(is_fast_checkout=False)
        text = """
    🔴 <b>Оформлення (Фінішна пряма)</b> 🐒
    <b>Крок 1: Як нам помолоти?</b>
    Кава живе довше в зерні, але якщо треба — оберіть відповідний інструмент і ми підберемо помел:
    🫘 <b>В зернах</b> — Якщо хочеш сам мелити.
    ☕ <b>Ріжкова кавоварка</b> — Для еспресо/портофільтра.
    🥣 <b>Чашка</b> — Маленькі чашки, швидке заварювання.
    🔷 <b>Гейзерка</b> — Moka/гейзерні кавоварки.
    🫖 <b>Турка</b> — Для традиційної турки (дуже дрібний помел).
    🫖 <b>Фільтр</b> — Пуровер, V60, Chemex.
    👇 Твоє рішення?
    """
        await callback.message.answer(text, reply_markup=get_grind_selection_keyboard(), parse_mode="HTML")
        await state.set_state(CheckoutStates.waiting_for_grind)
    
    await callback.answer()


@router.callback_query(CheckoutStates.confirming_saved_data, F.data == "checkout_data_ok")
async def process_confirm_saved_data(callback: CallbackQuery, state: FSMContext):
    text = """
🔴 <b>Чудово! Дані підтверджено.</b> 🐒

<b>Крок 1: Як нам помолоти?</b>
"""
    await callback.message.edit_text(text, reply_markup=get_grind_selection_keyboard(), parse_mode="HTML")
    await state.set_state(CheckoutStates.waiting_for_grind)
    await callback.answer()


@router.callback_query(CheckoutStates.confirming_saved_data, F.data == "checkout_data_edit")
async def process_edit_saved_data(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_fast_checkout=False)
    text = """
🔴 <b>Оформлення 🐒</b>
Добре, введемо нові дані.

<b>Крок 1: Як нам помолоти?</b>
"""
    await callback.message.edit_text(text, reply_markup=get_grind_selection_keyboard(), parse_mode="HTML")
    await state.set_state(CheckoutStates.waiting_for_grind)
    await callback.answer()


@router.callback_query(CheckoutStates.waiting_for_grind, F.data.startswith("grind:"))
async def process_grind_selection(callback: CallbackQuery, state: FSMContext):
    grind = callback.data.split(":")[1]
    await state.update_data(grind_preference=grind)
    grind_name = GRIND_TYPE_NAMES.get(grind, grind)
    
    text = f"""
🔴 <b>Оформлення замовлення</b> 🐒
⚫ Помел: {grind_name}

<b>Крок 2: Спосіб доставки</b>
Оберіть зручний для вас варіант:
🔴 <b>Нова Пошта</b> — 65 грн
🔴 <b>Укрпошта</b> — 50 грн
🔴 <b>Кур'єр по Києву</b> — 100 грн
💡 <i>Безкоштовна доставка від 1500 грн!</i>
"""
    await callback.message.edit_text(text, reply_markup=get_delivery_method_keyboard(), parse_mode="HTML")
    await state.set_state(CheckoutStates.waiting_for_delivery_method)
    await callback.answer()


@router.callback_query(CheckoutStates.waiting_for_delivery_method, F.data.startswith("delivery:"))
async def process_delivery_method(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    delivery_method = callback.data.split(":")[1]
    await state.update_data(delivery_method=delivery_method)
    
    data = await state.get_data()
    
    # 💥 РОЗГАЛУЖЕННЯ
    if data.get("is_fast_checkout"):
        try:
            await callback.message.delete()
        except Exception:
            pass
        await _generate_and_send_order_preview(callback.message, state, session, callback.from_user.id)
        await callback.answer()
        return

    clean_dm = delivery_method.replace("DeliveryMethod.", "").lower()
    delivery_name = DELIVERY_METHOD_NAMES.get(clean_dm, delivery_method)
    saved_city = data.get('delivery_city')
    
    text = f"""
🔴 <b>Оформлення</b> 🐒
⚫ Доставка: {delivery_name}

<b>Крок 3: Куди везти? (Місто)</b>
Напиши назву міста або обери збережене:
"""
    keyboard = get_use_saved_keyboard(saved_city) if saved_city else get_cancel_keyboard()
    
    # ✅ ФІКС: Видаляємо повідомлення і надсилаємо нове. 
    # Не можна робити edit_text, бо ми змінюємо Inline клавіатуру на Reply клавіатуру!
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(CheckoutStates.waiting_for_city)
    await callback.answer()


@router.message(CheckoutStates.waiting_for_city, F.text)
async def process_city(message: Message, state: FSMContext):
    if message.text == "❌ Скасувати":
        await cancel_checkout(message, state)
        return
    
    # 1. Відрізаємо емодзі будиночка
    city_input = message.text.replace("🏠 ", "") if message.text.startswith("🏠 ") else message.text
    
    # 2. Очищаємо текст
    city = sanitize_user_input(city_input, max_length=100)
    
    # 3. Валідуємо (сюди вже потрапляє чисте місто без емодзі)
    if not validate_city_name(city):
        await message.answer("❌ Некоректна назва міста. Спробуйте ще раз або /cancel")
        return
    
    await state.update_data(delivery_city=city)
    
    data = await state.get_data()
    delivery_method = data.get('delivery_method', "")
    clean_dm = delivery_method.replace("DeliveryMethod.", "").lower()
    
    is_post = clean_dm in ["nova_poshta", "ukrposhta"]
    step_title = "Номер відділення" if is_post else "Адреса доставки"
    instruction = "Введіть номер відділення:" if is_post else "Введіть адресу доставки:"
    
    if clean_dm == "nova_poshta":
        address_example = "Відділення №12\nабо\nвул. Хрещатик, 15 (поштомат)"
    elif clean_dm == "ukrposhta":
        address_example = "Відділення №5"
    else:
        address_example = "вул. Хрещатик, 15, кв. 42"
    
    text = f"""
<b>🛍️ Оформлення замовлення</b>
✅ Місто: {city}

<b>Крок 4a: {step_title}</b>
{instruction}

<b>Приклад:</b>
<code>{address_example}</code>
Або відправте /cancel щоб скасувати
"""
    await message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
    await state.set_state(CheckoutStates.waiting_for_address)


@router.message(CheckoutStates.waiting_for_address, F.text)
async def process_address(message: Message, state: FSMContext):
    if message.text == "❌ Скасувати":
        await cancel_checkout(message, state)
        return
    
    address = sanitize_user_input(message.text, max_length=500)
    if not validate_address(address):
        await message.answer("❌ Некоректна адреса. Спробуйте ще раз або /cancel")
        return
    
    await state.update_data(delivery_address=address)
    
    text = """
<b>🛍️ Оформлення замовлення</b>

<b>Крок 4b: Отримувач</b>
Введіть ПІБ отримувача:

<b>Приклад:</b> <code>Іван Петренко</code>
Або відправте /cancel щоб скасувати
"""
    await message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
    await state.set_state(CheckoutStates.waiting_for_recipient_name)


@router.message(CheckoutStates.waiting_for_recipient_name, F.text)
async def process_recipient_name(message: Message, state: FSMContext):
    if message.text == "❌ Скасувати":
        await cancel_checkout(message, state)
        return
    
    recipient_name = sanitize_user_input(message.text, max_length=255)
    if len(recipient_name) < 3:
        await message.answer("❌ Занадто коротке ім'я. Спробуйте ще раз або /cancel")
        return
    
    await state.update_data(recipient_name=recipient_name)
    
    text = """
<b>🛍️ Оформлення замовлення</b>

<b>Крок 4c: Телефон отримувача</b>
Введіть номер телефону:

<b>Приклад:</b> <code>+380991234567</code> або <code>0991234567</code>
Або відправте /cancel щоб скасувати
"""
    await message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
    await state.set_state(CheckoutStates.waiting_for_recipient_phone)


@router.message(CheckoutStates.waiting_for_recipient_phone, F.text)
async def process_recipient_phone(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "❌ Скасувати":
        await cancel_checkout(message, state)
        return
    
    phone_input = message.text.replace("🏠 ", "") if message.text.startswith("🏠 ") else message.text
    phone = validate_phone(phone_input)
    if not phone:
        await message.answer(
            "❌ Некоректний номер телефону.\nФормат: +380XXXXXXXXX або 0XXXXXXXXX\nСпробуйте ще раз або /cancel"
        )
        return
    
    await state.update_data(recipient_phone=phone)
    await _generate_and_send_order_preview(message, state, session, message.from_user.id)


@router.callback_query(F.data == "checkout_edit")
async def handle_checkout_edit(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    order_id = data.get('order_id')
    
    if order_id:
        try:
            # ✅ ФІКС: selectinload потрібен, щоб асинхронна сесія могла витягнути товари
            query = select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
            result = await session.execute(query)
            order = result.scalar_one_or_none()
            
            if order and order.status == "pending":
                await CartService.restore_cart_from_pending_order(session, callback.from_user.id, order.items)
                await session.delete(order)
                await session.commit()
        except Exception as e:
            logger.error(f"Error restoring cart from order {order_id}: {e}")
    
    await state.clear()
    await show_cart(callback, session)


async def cancel_checkout(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    is_admin = user_id in settings.admin_id_list
    keyboard = get_admin_main_menu_keyboard() if is_admin else get_main_menu_keyboard()
    
    await message.answer(
        "❌ Оформлення замовлення скасовано.\n\nТовари залишилися в кошику. Ви можете продовжити покупки.",
        reply_markup=keyboard
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    if await state.get_state() is None:
        await message.answer("Немає активних процесів для скасування")
        return
    await cancel_checkout(message, state)


@router.callback_query(F.data.startswith("checkout_tg_pay:"))
async def process_tg_payment(callback: CallbackQuery, session: AsyncSession):
    order_id = int(callback.data.split(":")[1])
    
    query = select(Order).where(Order.id == order_id)
    result = await session.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        await callback.answer("❌ Замовлення не знайдено", show_alert=True)
        return
    if order.status != "pending":
        await callback.answer(f"❌ Замовлення вже має статус: {order.status}", show_alert=True)
        return
    if not settings.payment_provider_token:
        await callback.answer("⚠️ Оплата Apple/Google Pay наразі недоступна.", show_alert=True)
        return

    final_amount = int(order.total * 100)
    prices = [LabeledPrice(label=f"Замовлення #{order.order_number}", amount=final_amount)]

    try:
        await callback.message.answer_invoice(
            title=f"Замовлення #{order.order_number}",
            description="Свіжосмажена кава від Monkeys Coffee 🐒☕",
            payload=f"order_{order.id}",
            provider_token=settings.payment_provider_token,
            currency="UAH",
            prices=prices,
            max_tip_amount=100000,
            suggested_tip_amounts=[2000, 5000, 10000],
            start_parameter=f"pay_{order.order_number}",
            photo_url="https://monkeyscoffee.com.ua/logo.png",
            is_flexible=False
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error sending invoice: {e}")
        await callback.answer("❌ Помилка при створенні рахунку. Спробуйте LiqPay.", show_alert=True)


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def on_successful_payment(message: Message, session: AsyncSession):
    payment_info = message.successful_payment
    payload = payment_info.invoice_payload
    
    if not payload or not payload.startswith("order_"):
        return

    try:
        order_internal_id = int(payload.split("_")[1])
    except (ValueError, IndexError):
        return
    
    query = select(Order).where(Order.id == order_internal_id)
    result = await session.execute(query)
    order = result.scalar_one_or_none()
    
    if not order:
        return

    order.status = "paid"
    await session.commit()
    
    await CartService.clear_cart(session, message.from_user.id)
    await session.commit()

    
    # Restore Main Menu
    is_admin = message.from_user.id in settings.admin_id_list
    keyboard = get_admin_main_menu_keyboard() if is_admin else get_main_menu_keyboard()

    await message.answer(
        f"✅ <b>Оплата отримана!</b> 🐒\n\n"
        f"Дякуємо за замовлення <b>#{order.order_number}</b>.\n"
        f"Ми вже починаємо готувати вашу каву до відправки. ☕✨\n\n"
        f"Ви отримаєте сповіщення з трек-номером!",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    for admin_id in settings.admin_id_list:
        try:
            await message.bot.send_message(
                admin_id,
                f"💰 <b>НОВА ОПЛАТА (Apple/Google Pay)</b> ✅\n\n"
                f"Замовлення: #{order.order_number}\n"
                f"Сума: {payment_info.total_amount / 100} {payment_info.currency}\n"
                f"Користувач: {message.from_user.full_name} (@{message.from_user.username})"
            )
        except Exception:
            pass