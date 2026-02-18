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
async def show_cart(event: Message | CallbackQuery, session: AsyncSession, state: FSMContext = None):
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
        # Get dynamic text for empty cart
        from src.services.content_service import ContentService
        text = await ContentService.get_text(session, "cart.empty_text")
        
        if not text:
             text = """
🛒 <b>Твій Кошик</b> 🐒

Поки тут порожньо — але це легко виправити. ☕
━━━━━━━━━━━━━━━━━━━━━━
🔥 <b>ЧОМУ ВАРТО ВЗЯТИ ЗАРАЗ:</b>
• <b>Свіжість</b> — смажимо 2-3 рази на тиждень
• <b>-25% знижка</b> — від 2 кг в одному замовленні
• <b>Безкоштовна доставка</b> — від 1500 грн
━━━━━━━━━━━━━━━━━━━━━━
💡 <i>Кожна пачка — це свіжообсмажене зерно, упаковане з любов'ю.</i>
"""
        keyboard = get_empty_cart_keyboard()
        
        if isinstance(event, Message):
            from src.utils.message_manager import delete_previous, save_message
            await delete_previous(event, state)
            if MODULE_CART.exists():
                photo = FSInputFile(MODULE_CART)
                sent = await event.answer_photo(photo, caption=text, reply_markup=keyboard, parse_mode="HTML")
            else:
                sent = await event.answer(text, reply_markup=keyboard, parse_mode="HTML")
            await save_message(state, sent)
        else:
            # Callback: use edit_media
            try:
                if MODULE_CART.exists():
                    from aiogram.types import InputMediaPhoto
                    media = InputMediaPhoto(media=FSInputFile(MODULE_CART), caption=text, parse_mode="HTML")
                    await event.message.edit_media(media=media, reply_markup=keyboard)
                else:
                    await event.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            except Exception:
                if MODULE_CART.exists():
                    await event.message.answer_photo(FSInputFile(MODULE_CART), caption=text, reply_markup=keyboard, parse_mode="HTML")
                else:
                    await event.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
            await event.answer()
        return
    
    # Get active volume discounts
    from src.database.models import VolumeDiscount
    query_dist = select(VolumeDiscount).where(VolumeDiscount.is_active == True)
    res_dist = await session.execute(query_dist)
    active_rules = res_dist.scalars().all()
    
    # Load active promo code from user record
    promo_code_obj = None
    if user.active_promo_code:
        promo_query = select(PromoCode).where(PromoCode.code == user.active_promo_code)
        promo_result = await session.execute(promo_query)
        promo_code_obj = promo_result.scalar_one_or_none()
        # If promo is no longer valid, clear it
        if promo_code_obj and not promo_code_obj.is_valid():
            user.active_promo_code = None
            await session.commit()
            promo_code_obj = None
    
    # Calculate discounts
    discount_breakdown = DiscountEngine.calculate_full_discount(cart_items, user, promo_code_obj, active_rules=active_rules)

    
    # Build cart display
    from src.services.content_service import ContentService
    header = await ContentService.get_text(session, "cart.header")
    text = header if header else f"🟠 <b>ВАШ КОШИК</b> 🐒\n\n"
    
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
        # Handle CallbackQuery
        try:
            if photo:
                from aiogram.types import InputMediaPhoto
                media = InputMediaPhoto(media=photo, caption=text, parse_mode="HTML")
                await event.message.edit_media(media=media, reply_markup=keyboard)
            else:
                await event.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Failed to edit cart message: {e}")
            # Do NOT delete+send — that creates new photo messages in gallery
            # Just send a new message as fallback
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
    
    # Save promo code to user record in DB (persists across FSM state resets)
    user_query = select(User).where(User.id == message.from_user.id)
    user_result = await session.execute(user_query)
    user = user_result.scalar_one_or_none()
    if user:
        user.active_promo_code = code
        await session.commit()
    
    await state.clear()
    
    await message.answer(
        f"✅ Промокод <b>{code}</b> застосовано!\n"
        f"Знижка: <b>{promo_code.discount_percent}%</b>\n\n"
        f"Знижка відображається в кошику 👇",
        parse_mode="HTML"
    )
    # Refresh cart to show updated price
    await show_cart(message, session)



# Checkout is handled in checkout.py

