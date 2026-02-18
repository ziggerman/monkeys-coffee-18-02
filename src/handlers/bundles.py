"""Bundle constructor handler for creating custom coffee packages."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Product, User
from src.services.cart_service import CartService
from src.utils.formatters import format_currency
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from src.utils.image_constants import MODULE_TASTING_SETS
from aiogram.types import FSInputFile

router = Router()


class BundleStates(StatesGroup):
    """States for bundle construction."""
    selecting_profile = State()
    selecting_products = State()
    confirming_bundle = State()


@router.message(F.text == "📦 Створити набір")
@router.callback_query(F.data == "create_bundle")
async def start_bundle_constructor(event: Message | CallbackQuery, session: AsyncSession):
    """Start the smart bundle constructor."""
    text = """
🔴 <b>Розумний конструктор наборів</b> 🐒

Створіть свій ідеальний набір кави
та отримайте максимальну знижку! ⚫

━━━━━━━━━━━━━━━━━━
<b>Як це працює:</b>
1️⃣ Оберіть профіль смаку або змішайте
2️⃣ Виберіть сорти кави
3️⃣ Налаштуйте кількість
4️⃣ Отримайте оптимальну знижку!
━━━━━━━━━━━━━━━━━━

🔴 <b>Готові набори:</b>
⚫ <b>Базовий</b> (3 × 300г) ➜ <b>10%</b>
🔴 <b>Оптимальний</b> (4 × 300г) ➜ <b>15%</b>
⚫ <b>Максимум</b> (6 × 300г) ➜ <b>25%</b>

Оберіть дію:
"""
    
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="🌟 Базовий набір (3 шт)",
        callback_data="bundle_quick:3"
    ))
    
    builder.row(InlineKeyboardButton(
        text="🔥 Оптимальний (4 шт)",
        callback_data="bundle_quick:4"
    ))
    
    builder.row(InlineKeyboardButton(
        text="⭐ Максимум (6 шт)",
        callback_data="bundle_quick:6"
    ))
    
    builder.row(InlineKeyboardButton(
        text="🎨 Створити свій набір",
        callback_data="bundle_custom"
    ))
    
    builder.row(InlineKeyboardButton(
        text="← Назад",
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



@router.callback_query(F.data.startswith("bundle_quick:"))
async def create_quick_bundle(callback: CallbackQuery, session: AsyncSession):
    """Create a quick pre-configured bundle."""
    quantity = int(callback.data.split(":")[1])
    
    # Get products - mix of espresso and filter
    espresso_query = select(Product).where(
        Product.profile == "espresso", Product.is_active == True
    ).limit(quantity // 2 + quantity % 2)
    
    filter_query = select(Product).where(
        Product.profile == "filter", Product.is_active == True
    ).limit(quantity // 2)
    
    espresso_result = await session.execute(espresso_query)
    filter_result = await session.execute(filter_query)
    
    espresso_products = list(espresso_result.scalars().all())
    filter_products = list(filter_result.scalars().all())
    
    all_products = espresso_products + filter_products
    
    if len(all_products) < quantity:
        # Not enough products, fallback to any available
        universal_query = select(Product).where(
            Product.is_active == True
        ).limit(quantity - len(all_products))
        
        universal_result = await session.execute(universal_query)
        all_products.extend(universal_result.scalars().all())
    
    # Calculate bundle pricing
    total_price = sum(p.price_300g for p in all_products[:quantity])
    
    # Determine discount
    if quantity >= 6:
        discount = 25
    elif quantity >= 4:
        discount = 15
    elif quantity >= 3:
        discount = 10
    else:
        discount = 0
    
    discounted_price = total_price - (total_price * discount / 100)
    savings = total_price - discounted_price
    
    # Build bundle description
    from src.services.visual_ux_service import VisualUXService
    
    text = f"""
<b>📦 Ваш набір "{['', '', '', 'Базовий', 'Оптимальний', '', 'Максимум'][quantity]}"</b>

<b>Склад набору:</b>

"""
    
    for idx, product in enumerate(all_products[:quantity], 1):
        notes = ", ".join(product.tasting_notes[:2]) if product.tasting_notes else "класичний смак"
        text += f"{idx}. {product.name_ua}\n   {notes}\n\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Pricing visualization
    bar = VisualUXService.create_progress_bar(discount, 25, length=12)
    
    text += f"<b>💰 Вартість:</b>\n\n"
    text += f"Без знижки: <s>{format_currency(total_price)}</s>\n"
    text += f"Ваша ціна: <b>{format_currency(int(discounted_price))}</b>\n\n"
    text += f"Знижка:\n{bar}\n\n"
    text += f"<b>Економія: {format_currency(int(savings))}</b>\n\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    text += "Додати набір до кошика?"
    
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="✅ Додати до кошика",
        callback_data=f"bundle_add:{','.join(str(p.id) for p in all_products[:quantity])}"
    ))
    
    builder.row(InlineKeyboardButton(
        text="← Назад до наборів",
        callback_data="create_bundle"
    ))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("bundle_add:"))
async def add_bundle_to_cart(callback: CallbackQuery, session: AsyncSession):
    """Add bundle to cart."""
    product_ids = [int(pid) for pid in callback.data.split(":")[1].split(",")]
    user_id = callback.from_user.id
    
    added_count = 0
    for product_id in product_ids:
        await CartService.add_to_cart(
            session=session,
            user_id=user_id,
            product_id=product_id,
            format="300g",
            quantity=1
        )
        added_count += 1
    
    await callback.answer(
        f"✅ Набір додано! ({added_count} позицій)",
        show_alert=True
    )
    
    # Navigate to cart
    from src.handlers.cart import show_cart
    await show_cart(callback, session, FSMContext)


@router.callback_query(F.data == "bundle_custom")
async def start_custom_bundle(callback: CallbackQuery, state: FSMContext):
    """Start custom bundle creation."""
    text = """
🔴 <b>Власний набір</b> 🐒

Створіть унікальну комбінацію! ⚫

<b>Крок 1:</b> Оберіть профіль смаку

🔴 <b>Еспресо</b> - насичені, щільні
⚫ <b>Фільтр</b> - легкі, квіткові
⚫ <b>Універсал</b> - збалансовані
🔴 <b>Мікс</b> - все понемногу
"""
    
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(text="🔥 Еспресо", callback_data="bundle_profile:espresso"))
    builder.row(InlineKeyboardButton(text="🌸 Фільтр", callback_data="bundle_profile:filter"))
    builder.row(InlineKeyboardButton(text="🎯 Універсал", callback_data="bundle_profile:universal"))
    builder.row(InlineKeyboardButton(text="🌈 Мікс", callback_data="bundle_profile:mix"))
    builder.row(InlineKeyboardButton(text="← Назад", callback_data="create_bundle"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()
    await state.set_state(BundleStates.selecting_profile)


@router.callback_query(F.data.startswith("bundle_profile:"))
async def select_bundle_profile(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Select products for custom bundle based on profile."""
    profile = callback.data.split(":")[1]
    
    # Store profile in state
    await state.update_data(profile=profile)
    
    # Get products for this profile
    if profile == "mix":
        query = select(Product).where(Product.is_active == True).limit(10)
    else:
        query = select(Product).where(
            Product.profile == profile,
            Product.is_active == True
        )
    
    result = await session.execute(query)
    products = result.scalars().all()
    
    text = f"""
<b>🎨 Власний набір - Вибір кави</b>

Профіль: <b>{['', 'Еспресо', 'Фільтр', 'Універсал', 'Мікс'][['', 'espresso', 'filter', 'universal', 'mix'].index(profile) if profile in ['espresso', 'filter', 'universal', 'mix'] else 0]}</b>

Оберіть сорти (мінімум 3 для знижки 10%):
"""
    
    # This is a simplified version - full implementation would track selections
    builder = InlineKeyboardBuilder()
    
    for product in products[:6]:
        notes = ", ".join(product.tasting_notes[:2]) if product.tasting_notes else ""
        builder.row(InlineKeyboardButton(
            text=f"☐ {product.name_ua} - {format_currency(product.price_300g)}",
            callback_data=f"bundle_toggle:{product.id}"
        ))
    
    builder.row(InlineKeyboardButton(
        text="✅ Підтвердити вибір (0)",
        callback_data="bundle_confirm"
    ))
    
    builder.row(InlineKeyboardButton(
        text="← Назад",
        callback_data="bundle_custom"
    ))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
    await callback.answer()
    await state.set_state(BundleStates.selecting_products)
