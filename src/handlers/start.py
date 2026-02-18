"""Start command and main menu handler."""
import logging
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.keyboards.main_menu import get_main_menu_keyboard, get_admin_main_menu_keyboard
from config import settings
from config import settings
from src.utils.image_constants import HERO_BANNER, MODULE_ABOUT_US, MODULE_SUPPORT

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, user: User = None):
    """Handle /start command and referral codes."""
    user_id = message.from_user.id
    
    # Extract referral code if present
    referral_code = None
    if message.text and len(message.text.split()) > 1:
        args = message.text.split()[1]
        if args.startswith("ref_"):
            referral_code = args[4:]  # Remove 'ref_' prefix
    
    # User is now provided by middleware, but we double check
    if not user:
        query = select(User).where(User.id == user_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
    
    is_new_user = False
    
    # If user was just created by middleware in this session, 
    # it might not have 'referred_by_id' yet.
    # We check if they are "effectively new" (created very recently or no referrer set yet)
    if user and user.referred_by_id is None and referral_code:
        # Check if they have any orders. If no orders, we can still count them as "new" for referral
        from src.database.models import Order
        order_query = select(Order).where(Order.user_id == user_id)
        order_result = await session.execute(order_query)
        if not order_result.scalars().first():
            # Find referrer
            referrer_query = select(User).where(User.referral_code == referral_code)
            referrer_result = await session.execute(referrer_query)
            referrer = referrer_result.scalar_one_or_none()
            
            if referrer and referrer.id != user_id:
                user.referred_by_id = referrer.id
                is_new_user = True  # Mark as new for the welcome message
                logger.info(f"User {user_id} referred by {referrer.id}")
                await session.commit()

    # Determine which keyboard to show
    is_admin = user_id in settings.admin_id_list
    logger.info(f"User {user_id} admin check: {is_admin} (Admins: {settings.admin_id_list})")
    
    keyboard = get_admin_main_menu_keyboard() if is_admin else get_main_menu_keyboard()
    
    # Welcome message
    if is_new_user:
        welcome_text = f"""
🟢 <b>Привіт, {user.first_name}!</b> 🐒
Ласкаво просимо до <b>Monkeys Coffee Roasters</b>. Тут ми смажимо каву, яка змінює ранок. 🟢
━━━━━━━━━━━━━━━━━━━━━━
🟠 <b>НАШІ ПЕРЕВАГИ:</b>
• Спешелті зерно (SCA 80+)
• Знижки для тих, хто бере багато
• Кешбек у вигляді міцних бонусів
• Безкоштовна доставка від 1500 грн
━━━━━━━━━━━━━━━━━━━━━━
🟠 <b>ЯК ЕКОНОМИТИ:</b>
🟢 6+ пачок по 300г ➜ <b>-25%</b>
🟠 2+ кг ➜ <b>-25%</b>

Тисни на кнопки внизу, і погнали обирати! 👇
"""
        
        if referral_code:
            welcome_text += "\n🎁 <b>О, ти від друга!</b> Зараховано бонус 100 грн на перше замовлення."
    
    else:
        welcome_text = f"""
🟢 <b>З поверненням, {user.first_name}!</b> 🐒
Запаси закінчуються? Чи просто захотілось чогось новенького?
Наші ростери вже попрацювали, свіжа партія чекає. 🟢
Обирай, що будемо пити цього разу 👇
"""
    
    # Send with hero banner if available
    if HERO_BANNER.exists():
        photo = FSInputFile(HERO_BANNER)
        await message.answer_photo(photo, caption=welcome_text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.answer(welcome_text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "start")
async def callback_start(callback: CallbackQuery, session: AsyncSession, user: User = None):
    """Handle 'Back to Home' callback."""
    user_id = callback.from_user.id
    
    # Determine which keyboard to show
    is_admin = user_id in settings.admin_id_list
    keyboard = get_admin_main_menu_keyboard() if is_admin else get_main_menu_keyboard()
    
    welcome_text = f"🟢 <b>Головне Меню</b> 🐒\n\nПривіт, {callback.from_user.first_name}! Обирай свій шлях:"
    
    await callback.message.delete()
    await callback.message.answer(welcome_text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.message(F.text == "🏠 Головне меню")
async def show_main_menu(message: Message, session: AsyncSession):
    """Show main menu."""
    user_id = message.from_user.id
    is_admin = user_id in settings.admin_id_list
    
    keyboard = get_admin_main_menu_keyboard() if is_admin else get_main_menu_keyboard()
    
    await message.answer(
        "🟢 <b>Головне Меню</b> 🐒\n\nКуди попрямуємо?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(F.text == "📖 Корисна Інфо")
@router.message(F.text == "🐒 Про нас")
async def show_about(message: Message, session: AsyncSession):
    """Show about us information with dynamic image."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    about_text = (
        "🟢 <b>Monkeys Coffee Roasters</b> 🐒\n"
        "<i>Ми не просто смажимо каву, ми створюємо досвід.</i> ☕\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌍 <b>НАША ФІЛОСОФІЯ</b>\n"
        "Справжня кава має бути смачною. Крапка. Ми шукаємо найкраще зерно, "
        "щоб ви могли просто насолоджуватись моментом.\n\n"
        "🟠 <b>ЧОМУ МИ?</b>\n"
        "• <b>Свіжість:</b> Смажимо 2-3 рази на тиждень\n"
        "• <b>Якість:</b> Тільки зерно SCA 84+\n"
        "• <b>Прямий контакт:</b> Знаємо фермерів в обличчя\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📍 <b>ДЕ НАС ШУКАТИ?</b>\n"
        "• <b>Telegram:</b> @AndriyKhomenko\n\n"
        "🆘 Потрібна допомога? Тисніть кнопку нижче або в меню!"
    )
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📸 Наш Instagram", url="https://www.instagram.com/monkeyscoffeeroaster/"))
    kb.row(InlineKeyboardButton(text="🆘 Допомога та SOS", callback_data="support_main"))
    
    # Get dynamic image
    from src.utils.ui_utils import get_module_image
    from src.utils.image_constants import MODULE_ABOUT_US
    photo = await get_module_image(session, "about_us", MODULE_ABOUT_US)
    
    if photo:
        await message.answer_photo(
            photo, 
            caption=about_text, 
            reply_markup=kb.as_markup(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            about_text, 
            reply_markup=kb.as_markup(),
            parse_mode="HTML"
        )


@router.message(F.text == "🤝 Допомога та SOS")
@router.message(F.text == "Підтримка")
async def show_support(message: Message, session: AsyncSession):
    """Show support information with dynamic image."""
    support_text = """
🟢 <b>Підтримка Monkeys</b> 🐒
Щось пішло не так? Ми поруч! 🪵
━━━━━━━━━━━━━━━━━━━━━━
📱 <b>КОНТАКТИ:</b>
• Telegram: @AndriyKhomenko (відповідаємо швидко)
• Email: monkeyscoffeeraoster@gmail.com
❓ <b>ШВИДКІ ВІДПОВІДІ:</b>
🟠 <b>Де моя посилка?</b>
Як тільки відправимо — ТТН прилетить сюди.
🟠 <b>Як зберігати?</b>
Закрий пачку щільно, сховай в шафу. Ніякого холодильника.
━━━━━━━━━━━━━━━━━━━━━━
Потрібна допомога? Пиши в телеграм вище! 👆
"""
    
    # Get dynamic image
    from src.utils.ui_utils import get_module_image
    from src.utils.image_constants import MODULE_SUPPORT
    photo = await get_module_image(session, "support", MODULE_SUPPORT)
    
    if photo:
        await message.answer_photo(photo, caption=support_text, parse_mode="HTML")
    else:
        await message.answer(support_text, parse_mode="HTML")
