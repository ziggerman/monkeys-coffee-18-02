"""Tasting sets handler - pre-configured coffee bundles."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import TastingSet, Product
from src.services.cart_service import CartService
from src.utils.formatters import format_currency
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from src.utils.image_constants import MODULE_TASTING_SETS
from src.utils.admin_utils import is_admin

router = Router()


@router.message(F.text == "🎁 Дегустаційні набори")
@router.callback_query(F.data == "tasting_sets")
async def show_tasting_sets(event: Message | CallbackQuery, session: AsyncSession, state: FSMContext = None):
    """Show available tasting sets."""
    # Get all active tasting sets
    query = select(TastingSet).where(
        TastingSet.is_active == True
    ).order_by(TastingSet.sort_order)
    
    result = await session.execute(query)
    tasting_sets = result.scalars().all()
    
    if not tasting_sets:
        text = """
<b>🎁 Дегустаційні набори</b> 🐒

Набори зараз в розробці — скоро будуть доступні. ☕

Тим часом — завітай до каталогу і обери свій сорт самостійно!

☕ Каталог → /start
"""
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="← Назад", callback_data="back_to_menu"))
        
        if isinstance(event, CallbackQuery):
            try:
                if MODULE_TASTING_SETS.exists():
                    from aiogram.types import InputMediaPhoto
                    media = InputMediaPhoto(media=FSInputFile(MODULE_TASTING_SETS), caption=text, parse_mode="HTML")
                    await event.message.edit_media(media=media, reply_markup=builder.as_markup())
                else:
                    await event.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
            except Exception:
                if MODULE_TASTING_SETS.exists():
                    await event.message.answer_photo(FSInputFile(MODULE_TASTING_SETS), caption=text, reply_markup=builder.as_markup(), parse_mode="HTML")
                else:
                    await event.message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
            await event.answer()
        else:
            if MODULE_TASTING_SETS.exists():
                photo = FSInputFile(MODULE_TASTING_SETS)
                await event.answer_photo(photo, caption=text, reply_markup=builder.as_markup(), parse_mode="HTML")
            else:
                await event.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        return
    
    text = """
⚫ <b>Дегустаційні набори</b> 🐒

Готові підбірки кращих сортів для різних смаків! ⚫

━━━━━━━━━━━━━━━━━━
🔴 <b>Переваги наборів:</b>
⚫ Спеціальна ціна (додаткова знижка)
⚫ Продуманий баланс смаків
⚫ Можливість спробувати різні сорти
⚫ Ідеально для подарунка
━━━━━━━━━━━━━━━━━━

<b>Доступні набори:</b>
"""
    
    # List all sets
    for idx, tasting_set in enumerate(tasting_sets, 1):
        # Get products in this set
        product_query = select(Product).where(
            Product.id.in_(tasting_set.product_ids)
        )
        product_result = await session.execute(product_query)
        products = list(product_result.scalars().all())
        
        # Calculate pricing
        original_price = sum(p.price_300g for p in products) if products else 0
        set_price = tasting_set.price
        savings = original_price - set_price
        savings_pct = int((savings / original_price * 100)) if original_price > 0 else 0
        
        # Build set description
        text += f"<b>{idx}. {tasting_set.name_ua}</b>\n"
        text += f"{tasting_set.description}\n\n"
        
        if products:
            text += "Включає:\n"
            for product in products:
                text += f"  • {product.name_ua}\n"
        
        text += f"\n"
        text += f"Ціна окремо: <s>{format_currency(original_price)}</s>\n"
        text += f"Ціна набору: <b>{format_currency(set_price)}</b>\n"
        text += f"💰 Економія: {format_currency(savings)} ({savings_pct}%)\n"
        text += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Build keyboard with all sets
    builder = InlineKeyboardBuilder()
    
    for tasting_set in tasting_sets:
        builder.row(InlineKeyboardButton(
            text=f"🛒 {tasting_set.name_ua}",
            callback_data=f"tasting_view:{tasting_set.id}"
        ))
    
    builder.row(InlineKeyboardButton(
        text="← Повернутись",
        callback_data="back_to_menu"
    ))
    
    if isinstance(event, CallbackQuery):
        try:
            if MODULE_TASTING_SETS.exists():
                from aiogram.types import InputMediaPhoto
                media = InputMediaPhoto(media=FSInputFile(MODULE_TASTING_SETS), caption=text, parse_mode="HTML")
                await event.message.edit_media(media=media, reply_markup=builder.as_markup())
            else:
                await event.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        except Exception as e:
            # Do NOT delete+send — just send new message as last resort
            if MODULE_TASTING_SETS.exists():
                photo = FSInputFile(MODULE_TASTING_SETS)
                await event.message.answer_photo(photo, caption=text, reply_markup=builder.as_markup(), parse_mode="HTML")
            else:
                await event.message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        await event.answer()
    else:
        from src.utils.message_manager import delete_previous, save_message
        await delete_previous(event, state)
        if MODULE_TASTING_SETS.exists():
            photo = FSInputFile(MODULE_TASTING_SETS)
            sent = await event.answer_photo(photo, caption=text, reply_markup=builder.as_markup(), parse_mode="HTML")
        else:
            sent = await event.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        await save_message(state, sent)




@router.callback_query(F.data.startswith("tasting_view:"))
async def view_tasting_set(callback: CallbackQuery, session: AsyncSession):
    """View detailed information about a tasting set."""
    set_id = int(callback.data.split(":")[1])
    
    # Get tasting set
    query = select(TastingSet).where(TastingSet.id == set_id)
    result = await session.execute(query)
    tasting_set = result.scalar_one_or_none()
    
    if not tasting_set:
        await callback.answer("❌ Набір не знайдено", show_alert=True)
        return
    
    # Get products
    product_query = select(Product).where(
        Product.id.in_(tasting_set.product_ids)
    )
    product_result = await session.execute(product_query)
    products = list(product_result.scalars().all())
    
    # Calculate pricing
    original_price = sum(p.price_300g for p in products) if products else 0
    set_price = tasting_set.price
    savings = original_price - set_price
    savings_pct = int((savings / original_price * 100)) if original_price > 0 else 0
    
    # Visual display with progress bar
    from src.services.visual_ux_service import VisualUXService
    savings_bar = VisualUXService.create_progress_bar(
        savings_pct,
        50,  # Max theoretical discount
        length=12
    )
    
    text = f"""
<b>🎁 {tasting_set.name_ua}</b>

{tasting_set.description}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>📦 Склад набору:</b>

"""
    
    for idx, product in enumerate(products, 1):
        notes = ", ".join(product.tasting_notes[:3]) if product.tasting_notes else "класична кава"
        text += f"{idx}. <b>{product.name_ua}</b> (300г)\n"
        text += f"   📍 {product.origin}\n"
        text += f"   🌸 {notes}\n"
        text += f"   💰 {format_currency(product.price_300g)}\n\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Pricing visualization
    text += "<b>💰 Вартість:</b>\n\n"
    text += f"При окремій купівлі: <s>{format_currency(original_price)}</s>\n"
    text += f"Ціна набору: <b>{format_currency(set_price)}</b>\n\n"
    
    text += f"Знижка набору:\n{savings_bar}\n\n"
    text += f"<b>Ваша економія: {format_currency(savings)} ({savings_pct}%)</b>\n\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Benefits
    text += "<b>✨ Чому цей набір?</b>\n\n"
    text += "• Професійна підбірка від Q-грейдерів\n"
    text += "• Збалансовані смаки\n"
    text += "• Спеціальна ціна\n"
    text += "• Свіжеобсмажена кава\n"
    text += "• Готовий до подарунку\n"
    
    # Build keyboard
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="🛒 Додати набір до кошика",
        callback_data=f"tasting_add:{set_id}"
    ))
    
    builder.row(InlineKeyboardButton(
        text="← Назад до наборів",
        callback_data="tasting_sets"
    ))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("tasting_add:"))
async def add_tasting_set_to_cart(callback: CallbackQuery, session: AsyncSession):
    """Add tasting set to cart."""
    set_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    
    # Get tasting set
    query = select(TastingSet).where(TastingSet.id == set_id)
    result = await session.execute(query)
    tasting_set = result.scalar_one_or_none()
    
    if not tasting_set:
        await callback.answer("❌ Набір не знайдено", show_alert=True)
        return
    
    # Add all products from the set to cart
    added_count = 0
    for product_id in tasting_set.product_ids:
        try:
            await CartService.add_to_cart(
                session=session,
                user_id=user_id,
                product_id=product_id,
                format="300g",  # Tasting sets are 300g format
                quantity=1
            )
            added_count += 1
        except Exception as e:
            continue
    
    if added_count > 0:
        await callback.answer(
            f"✅ Набір додано до кошика!\n"
            f"Додано {added_count} сортів кави",
            show_alert=True
        )
        
        # Show cart
        from src.handlers.cart import show_cart
        await show_cart(callback, session)
    else:
        await callback.answer("❌ Помилка додавання набору", show_alert=True)


@router.message(F.text == "🎁 Подарункові набори")
async def show_gift_sets(message: Message, session: AsyncSession):
    """Show gift-focused tasting sets with special presentation."""
    # Get tasting sets
    query = select(TastingSet).where(
        TastingSet.is_active == True
    ).order_by(TastingSet.sort_order)
    
    result = await session.execute(query)
    tasting_sets = result.scalars().all()
    
    text = """
<b>🎁 Подарункові набори кави</b>

Ідеальний подарунок для кавоманів!

━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>💝 Що входить в подарунок:</b>

✅ Спеціальна подарункова упаковка
✅ Картка з описом кожного сорту
✅ Поради по завар юванню
✅ Персональне привітання (за бажанням)
✅ Безкоштовна доставка від 1500 грн

━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>🌟 Популярні набори:</b>

"""
    
    for tasting_set in tasting_sets[:3]:  # Show top 3
        product_query = select(Product).where(
            Product.id.in_(tasting_set.product_ids)
        )
        product_result = await session.execute(product_query)
        products = list(product_result.scalars().all())
        
        original_price = sum(p.price_300g for p in products) if products else 0
        savings = original_price - tasting_set.price
        
        text += f"🎁 <b>{tasting_set.name_ua}</b>\n"
        text += f"   {len(products)} сортів × 300г = {len(products) * 0.3:.1f} кг\n"
        text += f"   Ціна: {format_currency(tasting_set.price)}\n"
        text += f"   Економія: {format_currency(savings)}\n\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    text += "Переглянути всі набори → 🎁 Дегустаційні набори"
    
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="🎁 Переглянути всі набори",
        callback_data="tasting_sets"
    ))
    
    if MODULE_TASTING_SETS.exists():
        photo = FSInputFile(MODULE_TASTING_SETS)
        await message.answer_photo(photo, caption=text, reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.callback_query(F.data == "back_to_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """Return to main menu."""
    from src.keyboards.main_menu import get_main_menu_keyboard, get_admin_main_menu_keyboard
    from config import settings
    
    text = """
<b>☕ Monkeys Coffee Roasters</b>

Вітаємо в головному меню!

Оберіть розділ:
"""
    is_admin_user = is_admin(callback.from_user.id)
    keyboard = get_admin_main_menu_keyboard() if is_admin_user else get_main_menu_keyboard()
    
    # Send NEW message to restore ReplyKeyboardMarkup (cannot be edited into existence)
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
