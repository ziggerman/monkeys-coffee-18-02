"""Info and Cabinet menu handler."""
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram.types import InlineKeyboardButton
from src.utils.image_constants import MODULE_CABINET
from src.utils.constants import CallbackPrefix

router = Router()


@router.message(F.text == "👤 Мій Кабінет")
async def show_cabinet_menu(message: Message, session: AsyncSession):
    """Show cabinet menu."""
    # Get dynamic text
    from src.services.content_service import ContentService
    text = await ContentService.get_text(session, "cabinet.caption")
    
    if not text:
        text = """
🔴 <b>Твій Кабінет</b> 🐒

Це твоя база. Тут історія покупок і твоя статистика. ⚫
"""
    
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="📋 Мої замовлення",
        callback_data="my_orders"
    ))
    
    builder.row(InlineKeyboardButton(
        text="📈 Моя Статистика",
        callback_data="loyalty_program"
    ))
    
    # Get dynamic image
    from src.utils.ui_utils import get_module_image
    from src.utils.image_constants import MODULE_CABINET
    photo = await get_module_image(session, "cabinet", MODULE_CABINET)
    
    if photo:
        await message.answer_photo(photo, caption=text, reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.message(F.text == "🎟️ Спецпропозиції")
async def show_offers_menu(message: Message, session: AsyncSession):
    """Show offers menu."""
    text = """
🔴 <b>Акції та Плюшки</b> 🐒

Ми любимо дарувати подарунки. Зазирни, що є цікавого сьогодні. ⚫
"""
    
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="🎟️ Акції та знижки",
        callback_data="promotions"
    ))
    
    builder.row(InlineKeyboardButton(
        text="☕ Дегустаційні набори",
        callback_data="tasting_sets"
    ))
    
    # Get dynamic image
    from src.utils.ui_utils import get_module_image
    from src.utils.image_constants import MODULE_PROMOTIONS
    photo = await get_module_image(session, "promotions", MODULE_PROMOTIONS)
    
    if photo:
        await message.answer_photo(photo, caption=text, reply_markup=builder.as_markup(), parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")


@router.message(F.text == "📖 Корисна Інфо")
async def show_info_menu(message: Message, session: AsyncSession):
    """Show info menu."""
    from src.services.content_service import ContentService
    text = await ContentService.get_text(session, "about.text")
    
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="⚫ Рецепти приготування",
        callback_data="recipes_menu"
    ))
    
    builder.row(InlineKeyboardButton(
        text="👥 Про нас",
        callback_data="about_us"
    ))
    
    builder.row(InlineKeyboardButton(
        text="🆘 Підтримка та контакти",
        callback_data="support_main"
    ))
    
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
