"""Promotions handler for referrals and promo codes."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User, PromoCode
from config import settings
from src.utils.image_constants import MODULE_PROMOTIONS

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "🎟️ Спецпропозиції")
@router.message(F.text == "⚡ Акції")
@router.callback_query(F.data == "promotions")
async def show_promotions(event: Message | CallbackQuery, session: AsyncSession, user: User = None):
    """Show promotions and referral program."""
    if not user:
        # Fallback if middleware somehow missed it
        user_id = event.from_user.id
        query = select(User).where(User.id == user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
    
    if not user:
        text = "Помилка: користувач не знайдений"
        if isinstance(event, Message):
            await event.answer(text)
        else:
            await event.answer(text, show_alert=True)
        return
    
    # Get active promo codes
    promo_query = select(PromoCode).where(PromoCode.is_active == True)
    promo_result = await session.execute(promo_query)
    promo_codes = promo_result.scalars().all()
    
    # Get active volume discounts
    from src.database.models import VolumeDiscount
    query_dist = select(VolumeDiscount).where(VolumeDiscount.is_active == True)
    res_dist = await session.execute(query_dist)
    active_rules = res_dist.scalars().all()
    
    from src.utils.constants import UIStyle
    
    bot_info = await event.bot.get_me()
    referral_link = f"t.me/{bot_info.username}?start=ref_{user.referral_code}"
    
    text = (
        f"🔴 <b>Акції та Плюшки</b> 🐒\n"
        f"<i>Твій доступ до кращих цін та бонусів.</i> 🎟️\n\n"
    )
    
    # Dynamic Volume Discounts
    if active_rules:
        text += f"📦 <b>ОПТОВІ ЗНИЖКИ</b>\n{UIStyle.DIVIDER}\n"
        for rule in active_rules:
            unit = "кг" if rule.discount_type == 'weight' else "пачок (300г)"
            text += f"• <b>{rule.threshold}+ {unit}</b> ➜ <b>-{rule.discount_percent}%</b>\n"
        text += "\n"
    else:
        # Legacy fallback or empty
        text += f"📦 <b>ОПТОВІ ЗНИЖКИ</b>\n{UIStyle.DIVIDER}\n"
        text += f"• <b>6+ пачок (300г)</b> ➜ <b>-25%</b>\n"
        text += f"• <b>2+ кг зерна</b> ➜ <b>-25%</b>\n\n"

    text += (
        f"🐒 <b>ПІДСАДИ ДРУГА</b>\n"
        f"{UIStyle.DIVIDER}\n"
        f"Кидай лінк другу — коли він зробить перше замовлення, ви обоє отримаєте по <b>100 грн</b> на рахунок. 🤝\n\n"
        f"🔗 <b>Твоє лінк:</b>\n"
        f"<code>{referral_link}</code>\n\n"
    )
    
    if user.referral_balance > 0:
        text += f"💰 <b>Доступно бонусів:</b> {user.referral_balance} грн\n\n"
    
    text += f"🎫 <b>СЕКРЕТНІ КОДИ</b>\n{UIStyle.DIVIDER}\n"
    
    if promo_codes:
        for promo in promo_codes[:5]:
            if promo.is_valid():
                text += f"• <code>{promo.code}</code> — мінус <b>{promo.discount_percent}%</b>\n"
                if promo.description:
                    text += f"  <i>({promo.description})</i>\n"
                text += "\n"
    else:
        text += "Зараз без кодів. Лови момент в сторіз! 📸\n\n"
    
    text += (
        f"{UIStyle.DIVIDER}\n"
        f"💡 <i>Акції не сумуються. Бот автоматично обере найвигіднішу для тебе ціну!</i>"
    )
    
    # Get dynamic image
    from src.utils.ui_utils import get_module_image
    from src.utils.image_constants import MODULE_PROMOTIONS
    photo = await get_module_image(session, "promotions", MODULE_PROMOTIONS)
    
    if isinstance(event, Message):
        if photo:
            await event.answer_photo(photo, caption=text, parse_mode="HTML")
        else:
            await event.answer(text, parse_mode="HTML")
    else:
        # Handle CallbackQuery
        try:
            if photo:
                from aiogram.types import InputMediaPhoto
                media = InputMediaPhoto(media=photo, caption=text, parse_mode="HTML")
                await event.message.edit_media(media=media)
            else:
                await event.message.edit_text(text, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Failed to edit promotions message: {e}")
            try:
                await event.message.delete()
            except Exception:
                pass
                
            if photo:
                await event.message.answer_photo(photo, caption=text, parse_mode="HTML")
            else:
                await event.message.answer(text, parse_mode="HTML")
        await event.answer()
