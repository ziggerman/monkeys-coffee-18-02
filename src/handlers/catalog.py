"""Catalog handlers for browsing and adding products."""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Product, User, Category
from src.keyboards.catalog_kb import (
    get_format_selection_keyboard,
    get_profile_filter_keyboard,
    get_category_keyboard,
    get_product_list_keyboard,
    get_product_details_keyboard
)
from src.services.cart_service import CartService
from src.utils.formatters import format_tasting_notes, format_date, format_currency
from src.utils.constants import CallbackPrefix
from src.utils.image_constants import get_category_image, get_category_image_async, get_product_image, CATEGORY_UNIVERSAL, MODULE_CATALOG_MAP

router = Router()
logger = logging.getLogger(__name__)




@router.message(Command("catalog"))
@router.message(F.text == "☕ Каталог")
@router.message(F.text == "☕ Каталог кави")
@router.callback_query(F.data == "goto_catalog")
async def show_catalog_start(event: Message | CallbackQuery, session: AsyncSession, state: FSMContext):
    """Show catalog start - profile selection with dynamic image."""
    from src.services.content_service import ContentService
    
    # Fetch all pieces in parallel or sequence
    t_espresso = await ContentService.get_text(session, "catalog.espresso")
    t_filter = await ContentService.get_text(session, "catalog.filter")
    t_guide = await ContentService.get_text(session, "catalog.guide")
    
    text = """
☕ <b>Кавова Карта Monkeys</b> 🐒
<i>Свіжообсмажена кава — пряма з ростера до тебе.</i>
━━━━━━━━━━━━━━━━━━━━━━
🥤 <b>ЕСПРЕСО</b>
Насичений, щільний, з оксамитовою крема.
Для тих, хто любить каву такою, якою вона має бути.

🫖 <b>ФІЛЬТР</b>
Чистий смак, яскрава кислинка, квіткові та фруктові ноти.
Ідеально для пуровера, аеропресу, кемексу.

⚗️ <b>УНІВЕРСАЛЬНА</b>
Збалансована кава для будь-якого методу заварювання.
Підходить і для еспресо-машини, і для фільтра.
━━━━━━━━━━━━━━━━━━━━━━
� <i>Обсмажуємо 2-3 рази на тиждень. Тільки зерно SCA 80+.</i>
👇 Обирай свій профіль:
"""
    
    # Always use hardcoded profile keyboard (Еспресо / Фільтр / Універсальна / Весь Арсенал / Магазин)
    keyboard = get_profile_filter_keyboard()
    
    # Get dynamic image (Roast Map)
    from src.utils.ui_utils import get_module_image
    from src.utils.image_constants import MODULE_CATALOG_MAP, CATEGORY_UNIVERSAL
    
    photo = await get_module_image(session, "catalog_map", MODULE_CATALOG_MAP)
    
    # Fallback to universal category if no catalog map
    if not photo and CATEGORY_UNIVERSAL.exists():
        photo = FSInputFile(CATEGORY_UNIVERSAL)
    
    if isinstance(event, Message):
        from src.utils.message_manager import delete_previous, save_message
        await state.clear() # Clear any active flows
        await delete_previous(event, state)
        if photo:
            sent = await event.answer_photo(photo, caption=text, reply_markup=keyboard, parse_mode="HTML")
        else:
            sent = await event.answer(text, reply_markup=keyboard, parse_mode="HTML")
        await save_message(state, sent)
    else:
        # Handle CallbackQuery
        try:
            if photo:
                media = InputMediaPhoto(media=photo, caption=text, parse_mode="HTML")
                await event.message.edit_media(media=media, reply_markup=keyboard)
            else:
                await event.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Edit failed in show_catalog_start: {e}")
            if photo:
                await event.message.answer_photo(photo, caption=text, reply_markup=keyboard, parse_mode="HTML")
            else:
                await event.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        await event.answer()


@router.callback_query(F.data.startswith(CallbackPrefix.CATALOG_PROFILE))
async def select_profile(callback: CallbackQuery, session: AsyncSession):
    """Handle profile/category selection and show product list."""
    # Format: cat_prof:slug
    slug = callback.data.replace(CallbackPrefix.CATALOG_PROFILE, "")
    
    # Check if this slug is a known coffee sub-profile (espresso/filter/universal)
    # These filter within the 'coffee' category by Product.profile
    COFFEE_PROFILES = {"espresso", "filter", "universal"}
    
    if slug == "all":
        # All coffee products (any category that is NOT equipment)
        # First try to get all non-equipment categories from DB
        cat_query = select(Category).where(
            Category.is_active == True,
            Category.slug != "equipment"
        )
        cat_result = await session.execute(cat_query)
        non_equip_cats = [c.slug for c in cat_result.scalars().all()]
        
        if non_equip_cats:
            query = select(Product).where(
                Product.category.in_(non_equip_cats),
                Product.is_active == True
            ).order_by(Product.sort_order)
        else:
            # Fallback: hardcoded 'coffee' category
            query = select(Product).where(
                Product.category == "coffee",
                Product.is_active == True
            ).order_by(Product.sort_order)
    elif slug in COFFEE_PROFILES:
        # Sub-profile filter within coffee: show matching profile + universal
        from src.utils.constants import CoffeeProfile
        # Try to find products with this profile in any non-equipment category
        query = select(Product).where(
            ((Product.profile == slug) | (Product.profile == CoffeeProfile.UNIVERSAL)),
            Product.category != "equipment",
            Product.is_active == True
        ).order_by(Product.sort_order)
    else:
        # Dynamic category slug — filter directly by Product.category == slug
        query = select(Product).where(
            Product.category == slug,
            Product.is_active == True
        ).order_by(Product.sort_order)
    
    result = await session.execute(query)
    products = result.scalars().all()
    
    if not products:
        await callback.answer("Пусто... Мабуть, все випили. Зазирни пізніше!", show_alert=True)
        return
    
    # Show first page
    await show_product_page(callback.message, products, 0, slug, session, callback.from_user.id, is_edit=True)
    await callback.answer()



async def show_product_page(
    message,
    products: list,
    page: int,
    selected_profile: str,
    session: AsyncSession,
    user_id: int,
    is_edit: bool = False
):
    """Show a page of products (Interactive Menu)."""
    total_products = len(products)
    # Increase items per page for list view (e.g. 5)
    ITEMS_PER_PAGE = 5
    total_pages = (total_products + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    start_idx = page * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, total_products)
    
    page_products = products[start_idx:end_idx]
    
    # Get cart count for display
    cart_count = await CartService.get_cart_count(session, user_id)
    cart_text = f"🟠 У кошику: {cart_count} лотів\n\n" if cart_count > 0 else ""
    
    profile_names = {
        "espresso": "🥤 Еспресо (Класика)",
        "filter": "🫖 Фільтр (Фанк)",
        "universal": "⚗️ Універсальна (База)",
        "all": "🫘 Весь Арсенал",
        "equipment": "📦 Магазин Аксесуарів"
    }
    
    profile_name = profile_names.get(selected_profile, selected_profile)
    
    # Breadcrumbs construction
    breadcrumb = f"☕ Каталог » {profile_name}"
    
    text = f"<b>{breadcrumb}</b>\n\n{cart_text}Оберіть лот для деталей 👇"
    
    # Get interactive menu keyboard
    from src.keyboards.catalog_kb import get_product_list_keyboard
    keyboard = get_product_list_keyboard(page_products, page, total_pages, selected_profile)
    
    # Get category image (from DB first, then static fallback)
    image_path = await get_category_image_async(selected_profile, session)
    if not image_path:
        image_path = get_category_image(selected_profile)
    logger.info(f"Selected profile: {selected_profile}, Image path: {image_path}, Exists: {image_path.exists() if image_path else 'None'}")
    
    if is_edit:
        # Always try edit_media first — never delete+send for callbacks (causes gallery accumulation)
        try:
            if image_path and image_path.exists():
                media = InputMediaPhoto(media=FSInputFile(image_path), caption=text, parse_mode="HTML")
                await message.edit_media(media=media, reply_markup=keyboard)
            else:
                await message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Edit failed in show_product_page: {e}")
            # Only fallback to delete+send if edit truly failed AND delete succeeds
            try:
                await message.delete()
            except Exception as del_e:
                logger.warning(f"Delete also failed (preventing duplicate): {del_e}")
                return  # Stop — do not send duplicate
            if image_path and image_path.exists():
                await message.answer_photo(FSInputFile(image_path), caption=text, reply_markup=keyboard, parse_mode="HTML")
            else:
                await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        # First show (from a Message, not a callback) — always send new
        if image_path and image_path.exists():
            await message.answer_photo(FSInputFile(image_path), caption=text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")



@router.callback_query(F.data.startswith(CallbackPrefix.CATALOG_PAGE))
async def change_page(callback: CallbackQuery, session: AsyncSession):
    """Handle pagination (switches pages in List View)."""
    # Format: cat_page:page:profile
    parts = callback.data.replace(CallbackPrefix.CATALOG_PAGE, "").split(":")
    page = int(parts[0])
    selected_profile = parts[1]
    
    # Reload products using same logic as select_profile
    logger.info(f"Changing page to {page} for slug {selected_profile}")
    COFFEE_PROFILES = {"espresso", "filter", "universal"}
    
    if selected_profile == "all":
        cat_query = select(Category).where(
            Category.is_active == True,
            Category.slug != "equipment"
        )
        cat_result = await session.execute(cat_query)
        non_equip_cats = [c.slug for c in cat_result.scalars().all()]
        
        if non_equip_cats:
            query = select(Product).where(
                Product.category.in_(non_equip_cats),
                Product.is_active == True
            ).order_by(Product.sort_order)
        else:
            query = select(Product).where(
                Product.category == "coffee",
                Product.is_active == True
            ).order_by(Product.sort_order)
    elif selected_profile in COFFEE_PROFILES:
        from src.utils.constants import CoffeeProfile
        query = select(Product).where(
            ((Product.profile == selected_profile) | (Product.profile == CoffeeProfile.UNIVERSAL)),
            Product.category != "equipment",
            Product.is_active == True
        ).order_by(Product.sort_order)
    else:
        # Dynamic category slug
        query = select(Product).where(
            Product.category == selected_profile,
            Product.is_active == True
        ).order_by(Product.sort_order)

    
    result = await session.execute(query)
    products = result.scalars().all()

    # If query returned nothing, inform user instead of deleting message
    if not products:
        await callback.answer("Пусто... Мабуть, все випили. Зазирни пізніше!", show_alert=True)
        return

    # Use is_edit=True for show_product_page
    await show_product_page(
        callback.message, 
        products, 
        page, 
        selected_profile, 
        session, 
        callback.from_user.id,
        is_edit=True
    )
    await callback.answer()


@router.callback_query(F.data.startswith(CallbackPrefix.CATALOG_ADD))
async def add_to_cart_from_catalog(callback: CallbackQuery, session: AsyncSession):
    """Add product to cart."""
    parts = callback.data.replace(CallbackPrefix.CATALOG_ADD, "").split(":")
    product_id = int(parts[0])
    product_format = parts[1]
    
    # Add to cart
    await CartService.add_to_cart(
        session,
        user_id=callback.from_user.id,
        product_id=product_id,
        format=product_format,
        quantity=1
    )
    
    # Get product name for feedback
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    product = result.scalar_one_or_none()
    
    if product:
        await callback.answer(
            f"✅ {product.name_ua} ({product_format}) додано!",
            show_alert=False
        )
    else:
        await callback.answer("✅ Додано!")


@router.callback_query(F.data.startswith(CallbackPrefix.CATALOG_PRODUCT))
async def show_product_details(callback: CallbackQuery, session: AsyncSession):
    """Show detailed product view (Detail View)."""
    # Format: cat_prod:product_id:page:profile
    data = callback.data.replace(CallbackPrefix.CATALOG_PRODUCT, "")
    parts = data.split(":")
    
    product_id = int(parts[0])
    # Extract back navigation context if available
    back_page = int(parts[1]) if len(parts) > 1 else 0
    back_profile = parts[2] if len(parts) > 2 else "all"
    
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        await callback.answer("Товар не знайдено", show_alert=True)
        return

    is_coffee = product.category == 'coffee'
    
    # Breadcrumbs
    # We try to reconstruct based on back_profile
    profile_names = {
        "espresso": "Еспресо",
        "filter": "Фільтр",
        "universal": "Універсальна",
        "all": "Весь Арсенал",
        "equipment": "Магазин"
    }
    prof_name = profile_names.get(back_profile, back_profile)
    breadcrumb = f"☕ Каталог » {prof_name} » {product.name_ua}"

    if is_coffee:
        notes = format_tasting_notes(product.tasting_notes)
        roast_str = product.roast_level or "Невідомо"
        
        text = f"""
🟢 <b>{product.name_ua}</b> 🐒
<i>{breadcrumb}</i>
{product.description or ''}
━━━━━━━━━━━━━━━━━━
⚙️ <b>ДЕТАЛІ ЛОТУ:</b>
• <b>Обсмажка:</b> {roast_str}
• <b>Обробка:</b> {product.processing_method or 'Митий'}
• <b>Сорт:</b> {product.variety or 'Арабіка'}
• <b>Регіон:</b> {product.region or 'Секретна плантація'}
━━━━━━━━━━━━━━━━━━
💰 <b>ВАРТІСТЬ:</b>
🟢 300г — <b>{format_currency(product.price_300g)}</b>
🟠 1кг — <b>{format_currency(product.price_1kg)}</b>
"""
    else:
        text = f"""
📦 <b>{product.name_ua}</b> 🐒
<i>{breadcrumb}</i>
{product.description or ''}
━━━━━━━━━━━━━━━━━━
⚙️ <b>ХАРАКТЕРИСТИКИ:</b>
Якісний аксесуар для поціновувачів кави. Покращуйте свій щоденний ритуал разом з нами.
━━━━━━━━━━━━━━━━━━
💰 <b>ВАРТІСТЬ:</b>
💳 Ціна — <b>{format_currency(product.price_300g)}</b>
"""
    
    # Pass context to keyboard so "Back" works
    keyboard = get_product_details_keyboard(product.id, back_page, back_profile)
    
    # Try to get product image
    image_path = get_product_image(product.id)
    
    # Always use edit_media to avoid creating new messages (which accumulate in gallery)
    try:
        if image_path and image_path.exists():
            media = InputMediaPhoto(
                media=FSInputFile(image_path),
                caption=text,
                parse_mode="HTML"
            )
            await callback.message.edit_media(media=media, reply_markup=keyboard)
        else:
            try:
                await callback.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="HTML")
            except Exception:
                await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"edit_media failed in show_product_details: {e}")
        try:
            await callback.message.delete()
        except Exception:
            pass
        if image_path and image_path.exists():
            await callback.message.answer_photo(FSInputFile(image_path), caption=text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        
    await callback.answer()



@router.message(F.text & ~F.text.startswith("/"))
async def handle_search_query(message: Message, session: AsyncSession):
    """Global product search by text."""
    # Ignore specific menu commands that might have slipped through
    if message.text in ["☕ Каталог", "☕ Каталог кави", "🏪 Каталог", "🛒 Мій Кошик", "👤 Мій Кабінет", "🆘 Допомога та SOS", "🏠 Головне меню"]:
        return

    query_text = message.text.strip()
    if len(query_text) < 3:
        # Too short, ignore or suggest typing more
        return

    # Search by name (UA)
    stmt = select(Product).where(
        Product.name_ua.ilike(f"%{query_text}%"),
        Product.is_active == True
    )
    result = await session.execute(stmt)
    products = result.scalars().all()

    if not products:
        # Optional: Reply that nothing was found? 
        # Better to be silent if it's just random chat, but for a bot, a reply is usually expected.
        # Let's reply only if it looks like a search (no spaces, or short phrase)
        if len(query_text.split()) < 4:
             await message.answer(f"🔍 За запитом «{query_text}» нічого не знайдено.")
        return

    if len(products) == 1:
        # Found exactly one - show details
        product = products[0]
        # Reuse existing detail view logic but we need to mock a callback or call logic directly
        # Easiest is to send the detail message directly
        
        is_coffee = product.category == 'coffee'
        if is_coffee:
            roast_str = product.roast_level or "Невідомо"
            text = f"""
🟢 <b>{product.name_ua}</b> 🐒
{product.description or ''}
━━━━━━━━━━━━━━━━━━
⚙️ <b>ДЕТАЛІ ЛОТУ:</b>
• <b>Обсмажка:</b> {roast_str}
• <b>Обробка:</b> {product.processing_method or 'Митий'}
• <b>Сорт:</b> {product.variety or 'Арабіка'}
• <b>Регіон:</b> {product.region or 'Секретна плантація'}
━━━━━━━━━━━━━━━━━━
💰 <b>ВАРТІСТЬ:</b>
🟢 300г — <b>{format_currency(product.price_300g)}</b>
🟠 1кг — <b>{format_currency(product.price_1kg)}</b>
"""
        else:
            text = f"""
📦 <b>{product.name_ua}</b> 🐒
{product.description or ''}
━━━━━━━━━━━━━━━━━━
💰 <b>ВАРТІСТЬ:</b>
💳 Ціна — <b>{format_currency(product.price_300g)}</b>
"""
        
        keyboard = get_product_details_keyboard(product.id, back_page=0, back_profile="all")
        image_path = get_product_image(product.id)
        
        if image_path and image_path.exists():
            await message.answer_photo(FSInputFile(image_path), caption=text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
            
    else:
        # Multiple found - show list
        await message.answer(f"🔍 Знайдено {len(products)} товарів за запитом «{query_text}»:")
        
        # Show first page of results using existing pagination would be complex because 'slug' is needed.
        # We will show a simplified list for search results.
        
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        
        for product in products[:10]: # Limit to 10
             builder.row(InlineKeyboardButton(
                text=f"{product.name_ua}",
                callback_data=f"{CallbackPrefix.CATALOG_PRODUCT}{product.id}:0:all"
            ))
            
        await message.answer("Оберіть товар:", reply_markup=builder.as_markup())
