"""Catalog handlers for browsing and adding products."""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Product, User
from src.keyboards.catalog_kb import (
    get_format_selection_keyboard,
    get_profile_filter_keyboard,
    get_product_list_keyboard,
    get_product_details_keyboard
)
from src.services.cart_service import CartService
from src.utils.formatters import format_tasting_notes, format_date, format_currency
from src.utils.constants import CallbackPrefix
from src.utils.image_constants import get_category_image, get_product_image, CATEGORY_UNIVERSAL, MODULE_CATALOG_MAP

router = Router()
logger = logging.getLogger(__name__)




@router.message(Command("catalog"))
@router.message(F.text == "☕ Каталог")
@router.message(F.text == "☕ Каталог кави")
@router.callback_query(F.data == "goto_catalog")
async def show_catalog_start(event: Message | CallbackQuery, session: AsyncSession):
    """Show catalog start - profile selection with dynamic image."""
    text = """
🟢 <b>Кавова Карта</b> 🐒
Оберіть профіль смаку:
━━━━━━━━━━━━━━━━━━━━━━
🟠 <b>Для еспресо</b>
(щільність, шоколад, карамель, горіхи)
🟢 <b>Для фільтру</b>
(кислинка, фрукти, ягоди, квіти)
🟢 <b>Універсальна</b>
(збалансована, для будь-якого методу)
━━━━━━━━━━━━━━━━━━━━━━
🟠 <b>ЯК ОБРАТИ?</b>
• Кавомашина/Молоко ➜ <b>Еспресо</b>
• V60/Аеропрес/Фільтр ➜ <b>Фільтр</b>
• Турка/Гейзер/Чашка ➜ <b>Універсальна</b>
👇 Тицьни на кнопку нижче
"""
    
    keyboard = get_profile_filter_keyboard()
    
    # Get dynamic image (Roast Map)
    from src.utils.ui_utils import get_module_image
    from src.utils.image_constants import MODULE_CATALOG_MAP, CATEGORY_UNIVERSAL
    
    photo = await get_module_image(session, "catalog_map", MODULE_CATALOG_MAP)
    
    # Fallback to universal category if no catalog map
    if not photo and CATEGORY_UNIVERSAL.exists():
        photo = FSInputFile(CATEGORY_UNIVERSAL)
    
    if isinstance(event, Message):
        if photo:
            await event.answer_photo(photo, caption=text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await event.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        try:
            await event.message.delete()
        except Exception as e:
            logger.warning(f"Delete failed in show_catalog_start: {e}")
            return
            
        if photo:
            await event.message.answer_photo(photo, caption=text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await event.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
        await event.answer()


@router.callback_query(F.data.startswith(CallbackPrefix.CATALOG_PROFILE))
async def select_profile(callback: CallbackQuery, session: AsyncSession):
    """Handle profile selection and show product list."""
    # Format: cat_prof:profile
    profile = callback.data.replace(CallbackPrefix.CATALOG_PROFILE, "")
    
    # Load products for selected profile
    if profile == "all":
        query = select(Product).where(
            Product.category == "coffee",
            Product.is_active == True
        ).order_by(Product.sort_order)
    elif profile == "equipment":
        query = select(Product).where(
            Product.category == "equipment",
            Product.is_active == True
        ).order_by(Product.sort_order)
    elif profile in ["espresso", "filter"]:
        # Show specific profile + universal ones
        from src.utils.constants import CoffeeProfile
        query = select(Product).where(
            ((Product.profile == profile) | (Product.profile == CoffeeProfile.UNIVERSAL)),
            Product.category == "coffee",
            Product.is_active == True
        ).order_by(Product.sort_order)
    else:
        query = select(Product).where(
            Product.profile == profile,
            Product.is_active == True
        ).order_by(Product.sort_order)
    
    result = await session.execute(query)
    products = result.scalars().all()
    
    if not products:
        await callback.answer("Пусто... Мабуть, все випили. Зазирни пізніше!", show_alert=True)
        return
    
    # Show first page
    await show_product_page(callback.message, products, 0, profile, session, callback.from_user.id, is_edit=True)
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
    
    text = f"<b>{profile_name}</b>\n{cart_text}Оберіть лот для деталей 👇"
    
    # Get interactive menu keyboard
    from src.keyboards.catalog_kb import get_product_list_keyboard
    keyboard = get_product_list_keyboard(page_products, page, total_pages, selected_profile)
    
    # Get category image
    image_path = get_category_image(selected_profile)
    logger.info(f"Selected profile: {selected_profile}, Image path: {image_path}, Exists: {image_path.exists() if image_path else 'None'}")
    
    if is_edit:
        # Try to edit media first to prevent flickering and duplicates
        try:
            if image_path and image_path.exists():
                logger.info("Attempting edit_media...")
                media = InputMediaPhoto(media=FSInputFile(image_path), caption=text, parse_mode="HTML")
                await message.edit_media(media=media, reply_markup=keyboard)
                logger.info("edit_media success")
            else:
                logger.info("Attempting edit_text...")
                await message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            # Only fallback to delete+send if edit failed (e.g. type mismatch)
            # But do NOT suppress "Message not found" if called explicitly, 
            # though here we are in a fallback.
            logger.warning(f"Edit details failed, falling back to delete+send: {e}")
            try:
                await message.delete()
            except Exception as e:
                # If delete fails (e.g. double click race), STOP. Do not send duplicate.
                logger.warning(f"Delete failed in fallback (preventing duplicate): {e}")
                return
                
            if image_path and image_path.exists():
                await message.answer_photo(FSInputFile(image_path), caption=text, reply_markup=keyboard, parse_mode="HTML")
            else:
                await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        # First show
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
    
    # Reload products
    logger.info(f"Changing page to {page} for profile {selected_profile}")
    if selected_profile == "all":
        query = select(Product).where(
            Product.category == "coffee",
            Product.is_active == True
        ).order_by(Product.sort_order)
    elif selected_profile == "equipment":
        query = select(Product).where(
            Product.category == "equipment",
            Product.is_active == True
        ).order_by(Product.sort_order)
    elif selected_profile in ["espresso", "filter"]:
        # Show specific profile + universal ones
        from src.utils.constants import CoffeeProfile
        query = select(Product).where(
            ((Product.profile == selected_profile) | (Product.profile == CoffeeProfile.UNIVERSAL)),
            Product.category == "coffee",
            Product.is_active == True
        ).order_by(Product.sort_order)
    else:
        query = select(Product).where(
            Product.profile == selected_profile,
            Product.is_active == True
        ).order_by(Product.sort_order)
    
    result = await session.execute(query)
    products = result.scalars().all()

    # If query returned nothing, inform user instead of deleting message
    if not products:
        await callback.answer("Пусто... Мабуть, все випили. Зазирни пізніше!", show_alert=True)
        return

    # Use robust delete + send (is_edit=False) to ensure Back button works
    # and to prevent double-menu issues (fail-fast on delete)
    try:
        await callback.message.delete()
    except Exception as e:
        # If delete fails (e.g. double click), stop here to prevent duplicate sending
        logger.warning(f"Delete failed in change_page (preventing duplicate): {e}")
        return

    # Show page (new message)
    await show_product_page(
        callback.message, 
        products, 
        page, 
        selected_profile, 
        session, 
        callback.from_user.id,
        is_edit=False
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
    
    if is_coffee:
        notes = format_tasting_notes(product.tasting_notes)
        roast_str = product.roast_level or "Невідомо"
        
        text = f"""
🟢 <b>{product.name_ua}</b> 🐒
{product.description or ''}
━━━━━━━━━━━━━━━━━━
🟠 <b>ПРОФІЛЬ СМАКУ:</b>
{notes}
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
    
    if image_path and image_path.exists():
        photo = FSInputFile(image_path)
        # We need to delete old message and send new photo message
        await callback.message.delete()
        await callback.message.answer_photo(photo, caption=text, reply_markup=keyboard, parse_mode="HTML")
    else:
        # Fallback to text edit if no image
        try:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        except Exception:
            # If we are coming from a photo message but don't have a new photo, 
            # we might need to delete and send text
            await callback.message.delete()
            await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
            
    await callback.answer()

