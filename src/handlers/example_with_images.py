"""Example handlers showing how to use the generated UI images."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from src.utils.image_constants import (
    HERO_BANNER,
    get_category_image,
    get_product_image
)
from src.keyboards.main_menu import get_main_menu
from src.keyboards.catalog_kb import get_profile_filter_keyboard, get_product_details_keyboard
from src.database.models import Product
from src.utils.formatters import format_tasting_notes, format_currency

router = Router()


@router.message(Command("start"))
async def cmd_start_with_image(message: Message):
    """Start command with hero banner image."""
    if HERO_BANNER.exists():
        photo = FSInputFile(HERO_BANNER)
        
        text = """
🐵 <b>Вітаю в MONKEYS COFFEE!</b>

Свіжообсмажена кава прямо до твоїх рук.

🌟 Що ми пропонуємо:
• Преміальна кава з усього світу
• Свіже обсмаження щотижня
• Доставка по всій Україні
• Програма лояльності

Обирай, замовляй, насолоджуйся ☕
"""
        
        await message.answer_photo(
            photo=photo,
            caption=text,
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
    else:
        # Fallback if image not found
        await message.answer(
            "🐵 <b>Вітаю в MONKEYS COFFEE!</b>\n\nСвіжообсмажена кава прямо до твоїх рук.",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )


@router.message(F.text == "☕ Каталог кави")
async def show_catalog_with_image(message: Message):
    """Show catalog start with category images."""
    text = """
<b>☕ Кавова Карта</b>

Оберіть профіль смаку, який вам до вподоби:

🍫 <b>Для еспресо</b>
(щільність, шоколад, карамель, горіхи)

🍋 <b>Для фільтру</b>
(кислинка, фрукти, ягоди, квіти)

⚖️ <b>Універсальна</b>
(збалансована, для будь-якого методу)

💡 <b>Як обрати? (Гід для новачків):</b>
• <b>Кавомашина / Напої з молоком</b> → беріть <b>Еспресо</b>.
• <b>Чорна кава / V60 / Chemex / Аеропрес</b> → беріть <b>Фільтр</b>.
• <b>Турка / Гейзер / Заварювання в чашці</b> → <b>Універсальна</b>.

Тицьни на кнопку нижче 👇
"""
    
    # Use espresso category image as default catalog image
    category_image = get_category_image("espresso")
    
    if category_image and category_image.exists():
        photo = FSInputFile(category_image)
        await message.answer_photo(
            photo=photo,
            caption=text,
            reply_markup=get_profile_filter_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            text,
            reply_markup=get_profile_filter_keyboard(),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("cat_prod:"))
async def show_product_with_image(callback: CallbackQuery, session: AsyncSession):
    """Show product details with product image."""
    from sqlalchemy import select
    
    # Parse callback data: cat_prod:product_id:page:profile
    data = callback.data.replace("cat_prod:", "")
    parts = data.split(":")
    
    product_id = int(parts[0])
    back_page = int(parts[1]) if len(parts) > 1 else 0
    back_profile = parts[2] if len(parts) > 2 else "all"
    
    # Get product from database
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        await callback.answer("Товар не знайдено", show_alert=True)
        return
    
    # Format product details
    notes = format_tasting_notes(product.tasting_notes)
    roast_str = product.roast_level or "Невідомо"
    
    text = f"""
<b>{product.name_ua}</b>

{product.description or ''}

🌟 <b>ПРОФІЛЬ СМАКУ:</b>
{notes}

⚙️ <b>ДЕТАЛІ ЛОТУ:</b>
• <b>Обсмажка:</b> {roast_str}
• <b>Обробка:</b> {product.processing_method or 'Митий'}
• <b>Сорт:</b> {product.variety or 'Арабіка'}
• <b>Регіон:</b> {product.region or 'Секретна плантація'}
• <b>Висота:</b> {product.altitude or 'High'}

💰 <b>ВАРТІСТЬ:</b>
📦 300г — <b>{format_currency(product.price_300g)}</b>
🏭 1кг — <b>{format_currency(product.price_1kg)}</b>
"""
    
    keyboard = get_product_details_keyboard(product.id, back_page, back_profile)
    
    # Get product image
    product_image = get_product_image(product_id)
    
    if product_image and product_image.exists():
        photo = FSInputFile(product_image)
        await callback.message.answer_photo(
            photo=photo,
            caption=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        # Delete the old message
        await callback.message.delete()
    else:
        # Fallback to text-only if image not found
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    await callback.answer()


# Example: Promotional message with category image
async def send_promo_message(user_id: int, bot):
    """Send promotional message with image."""
    from src.utils.image_constants import CATEGORY_FILTER
    
    text = """
🎉 <b>СПЕЦІАЛЬНА ПРОПОЗИЦІЯ!</b>

Знижка 25% на всі фільтр-кави цього тижня!

🍋 Спробуй яскраві африканські сорти:
• Ефіопія Сідамо - чорниця та жасмин
• Кенія АА - чорна смородина та грейпфрут

Використай промокод: <code>FILTER25</code>

⏰ Пропозиція діє до кінця тижня!
"""
    
    if CATEGORY_FILTER.exists():
        photo = FSInputFile(CATEGORY_FILTER)
        await bot.send_photo(
            chat_id=user_id,
            photo=photo,
            caption=text,
            parse_mode="HTML"
        )
    else:
        await bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode="HTML"
        )
