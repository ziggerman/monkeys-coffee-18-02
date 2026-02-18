"""Shopping cart handler with smart discount calculations."""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User, PromoCode
from src.services.cart_service import CartService
from src.services.discount_engine import DiscountEngine
from src.keyboards.cart_kb import get_cart_keyboard, get_empty_cart_keyboard
from src.keyboards.main_menu import get_cancel_keyboard
from src.utils.formatters import format_currency, format_order_items, format_discount_info
from src.utils.constants import CallbackPrefix
from src.states.checkout_states import PromoCodeStates
from src.utils.image_constants import MODULE_CART

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("cart"))
# Primary exact matches (with and without emoji)
@router.message(F.text == "🛒 Мій Кошик")
@router.message(F.text == "Мій Кошик")
# Fallbacks: match any message containing the word 'Кошик' (case-insensitive)
@router.message(F.text.lower().contains("кошик"))
@router.callback_query(F.data == CallbackPrefix.CART_VIEW)
async def show_cart(event: Message | CallbackQuery, session: AsyncSession):
    """Display shopping cart with full discount breakdown."""
    user_id = event.from_user.id if isinstance(event, Message) else event.from_user.id
    
    # Get user for loyalty level
    user_query = select(User).where(User.id == user_id)
    user_result = await session.execute(user_query)
    user = user_result.scalar_one_or_none()
    
    if not user:
        text = "Помилка: користувач не знайдений"
        if isinstance(event, Message):
            await event.answer(text)
        else:
            await event.answer(text, show_alert=True)
        return
    
    # Get cart items
    cart_items = await CartService.get_cart_items(session, user_id)
    
    if not cart_items:
        text = """
🟠 <b>Твій Кошик</b> 🐒
Тут пусто, як у понеділок зранку без кави. 😴 Час це виправляти!
━━━━━━━━━━━━━━━━━━━━━━
🪵 <b>РЕКОМЕНДУЄМО:</b>
• <b>Дегустаційний сет</b> — спробуй одразу 4 лоти.
• <b>Кенія Gachatha</b> — наш абсолютний бестселер.
━━━━━━━━━━━━━━━━━━━━━━
"""
        keyboard = get_empty_cart_keyboard()
        
        if isinstance(event, Message):
            if MODULE_CART.exists():
                photo = FSInputFile(MODULE_CART)
                await event.answer_photo(photo, caption=text, reply_markup=keyboard, parse_mode="HTML")
            else:
                await event.answer(text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await event.message.delete()
            if MODULE_CART.exists():
                photo = FSInputFile(MODULE_CART)
                await event.message.answer_photo(photo, caption=text, reply_markup=keyboard, parse_mode="HTML")
            else:
                await event.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
            await event.answer()
        return
    
    # Get active volume discounts
    from src.database.models import VolumeDiscount
    query_dist = select(VolumeDiscount).where(VolumeDiscount.is_active == True)
    res_dist = await session.execute(query_dist)
    active_rules = res_dist.scalars().all()
    
    # Calculate discounts
    discount_breakdown = DiscountEngine.calculate_full_discount(cart_items, user, active_rules=active_rules)
    
    # Build cart display
    text = f"🟠 <b>ВАШ КОШИК</b> 🐒\n\n"
    
    # List items
    for idx, (cart_item, product) in enumerate(cart_items, 1):
        # Support three formats: 300g packs, 1kg bags, and single-unit equipment/items.
        if cart_item.format == "300g":
            price = product.price_300g
        elif cart_item.format == "unit":
            # For equipment, admin stores unit price in price_300g
            price = product.price_300g
        else:  # 1kg
            price = product.price_1kg
        item_total = price * cart_item.quantity
        text += f"{idx}. <b>{product.name_ua}</b>\n"
        text += f"└ {cart_item.format} × {cart_item.quantity} шт = {format_currency(item_total)}\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"🟠 <b>ДЕТАЛІ:</b>\n"
    text += f"• Вага: {discount_breakdown.total_weight_kg:.1f} кг\n"
    text += f"• Сума: {format_currency(discount_breakdown.subtotal)}\n"
    
    # Applied discounts
    if discount_breakdown.total_discount_percent > 0:
        text += "━━━━━━━━━━━━━━━━━━━━━━\n"
        text += "🟢 <b>ЗАСТОСОВАНО ЗНИЖКИ:</b>\n"
        if discount_breakdown.volume_discount_percent > 0:
            text += f"• Об'ємна (-{discount_breakdown.volume_discount_percent}%): -{format_currency(discount_breakdown.volume_discount_amount)}\n"
        if discount_breakdown.loyalty_discount_percent > 0:
            text += f"• Лояльність (-{discount_breakdown.loyalty_discount_percent}%): -{format_currency(discount_breakdown.loyalty_discount_amount)}\n"
        if discount_breakdown.promo_discount_percent > 0:
            text += f"• Промокод (-{discount_breakdown.promo_discount_percent}%): -{format_currency(discount_breakdown.promo_discount_amount)}\n"
        text += f"💰 Разом знижки: -{format_currency(discount_breakdown.total_discount_amount)}\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"<b>💳 ДО СПЛАТИ: {format_currency(discount_breakdown.final_total)}</b>"
    
    if discount_breakdown.total_discount_amount > 0:
        savings_pct = round((discount_breakdown.total_discount_amount / discount_breakdown.subtotal) * 100)
        text += f"\n🌿 Вигода: {format_currency(discount_breakdown.total_discount_amount)} ({savings_pct}%)"
    
    # Get dynamic image
    from src.utils.ui_utils import get_module_image
    # Use module-level MODULE_CART imported at top to avoid local shadowing
    photo = await get_module_image(session, "cart", MODULE_CART)
    
    keyboard = get_cart_keyboard(cart_items)
    
    if isinstance(event, Message):
        if photo:
            await event.answer_photo(photo, caption=text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await event.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await event.message.delete()
        if photo:
            await event.message.answer_photo(photo, caption=text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await event.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        await event.answer()


@router.callback_query(F.data.startswith(CallbackPrefix.CART_INCREASE))
async def increase_quantity(callback: CallbackQuery, session: AsyncSession):
    """Increase cart item quantity."""
    cart_item_id = int(callback.data.replace(CallbackPrefix.CART_INCREASE, ""))
    
    # Increase quantity
    await CartService.change_quantity(session, cart_item_id, 1)
    
    await callback.answer("✅ Кількість збільшено")
    
    # Refresh cart display
    await show_cart(callback, session)


@router.callback_query(F.data.startswith(CallbackPrefix.CART_DECREASE))
async def decrease_quantity(callback: CallbackQuery, session: AsyncSession):
    """Decrease cart item quantity."""
    cart_item_id = int(callback.data.replace(CallbackPrefix.CART_DECREASE, ""))
    
    # Decrease quantity
    result = await CartService.change_quantity(session, cart_item_id, -1)
    
    if result:
        await callback.answer("✅ Кількість зменшено")
    else:
        await callback.answer("✅ Товар видалено з кошика")
    
    # Refresh cart display
    await show_cart(callback, session)


@router.callback_query(F.data.startswith(CallbackPrefix.CART_REMOVE))
async def remove_from_cart(callback: CallbackQuery, session: AsyncSession):
    """Remove item from cart."""
    cart_item_id = int(callback.data.replace(CallbackPrefix.CART_REMOVE, ""))
    
    success = await CartService.remove_item(session, cart_item_id)
    
    if success:
        await callback.answer("✅ Товар видалено з кошика")
    else:
        await callback.answer("❌ Товар не знайдено", show_alert=True)
    
    # Refresh cart display
    await show_cart(callback, session)


@router.callback_query(F.data == CallbackPrefix.CART_PROMO)
async def enter_promo_code(callback: CallbackQuery, state: FSMContext):
    """Start promo code entry process."""
    await callback.message.answer(
        "🎫 Введіть промокод:\n\n"
        "Наприклад: FIRST25\n\n"
        "Або відправте /cancel щоб скасувати",
        reply_markup=get_cancel_keyboard()
    )
    
    await state.set_state(PromoCodeStates.waiting_for_code)
    await callback.answer()


@router.message(PromoCodeStates.waiting_for_code)
async def process_promo_code(message: Message, state: FSMContext, session: AsyncSession):
    """Process entered promo code."""
    text = message.text.strip()
    
    if text == "❌ Скасувати" or text == "/cancel" or text == "🪵 Скасувати":
        await state.clear()
        await message.answer("❌ Введення промокоду скасовано")
        await show_cart(message, session)
        return

    code = text.upper()
    
    # Validate and check promo code
    query = select(PromoCode).where(PromoCode.code == code)
    result = await session.execute(query)
    promo_code = result.scalar_one_or_none()
    
    if not promo_code:
        await message.answer("❌ Промокод не знайдено. Спробуйте інший або /cancel")
        return
    
    if not promo_code.is_valid():
        await message.answer("❌ Цей промокод більше не дійсний. Спробуйте інший або /cancel")
        return
    
    # Save promo code to state
    await state.update_data(promo_code=code)
    await state.clear()
    
    await message.answer(
        f"✅ Промокод <b>{code}</b> застосовано!\n"
        f"Знижка: {promo_code.discount_percent}%\n\n"
        f"Перегляньте кошик щоб побачити оновлену ціну.",
        parse_mode="HTML"
    )


# Checkout is handled in checkout.py

