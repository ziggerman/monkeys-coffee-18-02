"""Service for managing dynamic module content."""
import logging
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import ModuleContent

logger = logging.getLogger(__name__)

class ContentService:
    """Service to handle dynamic text content."""
    
    # Default values to initialize if missing
    DEFAULTS = {
        # --- CART ---
        "cart.empty_text": {
            "value": "🛒 <b>Твій Кошик</b> 🐒\n\nПоки тут порожньо — але це легко виправити. ☕\n━━━━━━━━━━━━━━━━━━━━━━\n🔥 <b>ЧОМУ ВАРТО ВЗЯТИ ЗАРАЗ:</b>\n• <b>Свіжість</b> — смажимо 2-3 рази на тиждень\n• <b>-25% знижка</b> — від 2 кг в одному замовленні\n• <b>Безкоштовна доставка</b> — від 1500 грн\n━━━━━━━━━━━━━━━━━━━━━━\n💡 <i>Кожна пачка — це свіжообсмажене зерно, упаковане з любов'ю.</i>",
            "desc": "Текст порожнього кошика",
            "cat": "cart"
        },
        "cart.header": {
            "value": "🛒 <b>ВАШ КОШИК</b> 🐒\n\n",
            "desc": "Заголовок кошика",
            "cat": "cart"
        },
        # --- CATALOG ---
        "catalog.espresso": {
            "value": "🥤 <b>ЕСПРЕСО</b>\nНасичений, щільний, з оксамитовою крема.\nДля тих, хто любить каву такою, якою вона має бути.",
            "desc": "Опис профілю Еспресо",
            "cat": "catalog"
        },
        "catalog.filter": {
            "value": "🫖 <b>ФІЛЬТР</b>\nЧистий смак, яскрава кислинка, квіткові та фруктові ноти.\nІдеально для пуровера, аеропресу, кемексу.",
            "desc": "Опис профілю Фільтр",
            "cat": "catalog"
        },
        "catalog.guide": {
            "value": "🟠 <b>ЯК ОБРАТИ?</b>\n• Кавомашина/Молоко ➜ <b>Еспресо</b>\n• V60/Аеропрес/Фільтр ➜ <b>Фільтр</b>\n• Турка/Гейзер/Чашка ➜ <b>Універсальна</b>",
            "desc": "Гайд по вибору кави",
            "cat": "catalog"
        },
        # --- CABINET / INFO ---
        "cabinet.caption": {
            "value": "👤 <b>Твій Кабінет</b> 🐒\n\nТут зберігається історія твоїх замовлень, статус лояльності і все, що ти заробив з Monkeys. ☕\n━━━━━━━━━━━━━━━━━━━━━━\n📈 <b>ЧИМ БІЛЬШЕ КУПУЄШ — ТИМ БІЛЬШЕ БОНУСІВ:</b>\n• Від 2 кг — <b>-25%</b> на весь чек\n• Реферальна програма — 100 грн за кожного друга\n• Рівні лояльності — чим більше кави, тим краща ціна",
            "desc": "Текст в кабінеті",
            "cat": "info"
        },
        "about.text": {
            "value": "🐒 <b>Про нас</b>\n\nMonkeys Coffee Roasters — це команда людей, які серйозно захворіли на каву. Ми обсмажуємо тільки спешелті зерно SCA 80+, пряма з ростера до тебе. ☕",
            "desc": "Текст розділу Про нас",
            "cat": "info"
        },
        # --- START ---
        "start.welcome_new": {
            "value": "🟢 <b>Привіт, {name}!</b> 🐒\n\nТи завітав нас в світ справжньої кави. Тут немає компромісів — тільки зерно SCA 80+, свіже обсмажене і з душею. ☕\n━━━━━━━━━━━━━━━━━━━━━━\n🟠 <b>ЩО ТЕБЕ ЧЕКАЄ:</b>\n• <b>Свіжа кава</b> — обсмажуємо 2-3 рази на тиждень\n• <b>-25% знижка</b> — від 2 кг в одному чеку\n• <b>Безкоштовна доставка</b> — від 1500 грн\n• <b>Кешбек бонусами</b> — за кожне замовлення\n━━━━━━━━━━━━━━━━━━━━━━\n👇 Обирай свій перший сорт:",
            "desc": "Привітання нового користувача",
            "cat": "start"
        },
        "start.welcome_return": {
            "value": "🟢 <b>З поверненням, {name}!</b> 🐒\n\nЗапаси закінчуються? Чи просто хочеться чогось нового? ☕\nНаші ростери вже попрацювали — свіжа партія чекає.\n━━━━━━━━━━━━━━━━━━━━━━\n👇 Обирай, що будемо пити цього разу:",
            "desc": "Привітання повторного користувача",
            "cat": "start"
        },
        # --- PROMOTIONS ---
        "promotions.header": {
            "value": "⚡ <b>Акції та Плюшки</b> 🐒\n<i>Хороша кава має бути доступною — тому ми придумали купу способів заощадити.</i> ☕\n\n",
            "desc": "Заголовок розділу Акції",
            "cat": "promotions"
        },
        # --- LOYALTY ---
        "loyalty.header": {
            "value": "🔴 <b>Твоя Кавова Статистика</b> 🐒\n<i>Тут ми рахуємо кожну твою чашку.</i> ☕",
            "desc": "Заголовок розділу Бонуси",
            "cat": "loyalty"
        },
        # --- SUPPORT ---
        "support.header": {
            "value": "🔴 <b>Служба підтримки</b> 🐒\n\nМи завжди раді допомогти! Напишіть нам — відповімо протягом 1-3 годин у робочий час.",
            "desc": "Заголовок розділу Підтримка",
            "cat": "support"
        },
    }

    @staticmethod
    async def get_text(session: AsyncSession, key: str) -> str:
        """Get text content by key. Initialize with default if missing."""
        query = select(ModuleContent).where(ModuleContent.key == key)
        result = await session.execute(query)
        content = result.scalar_one_or_none()
        
        if content:
            return content.value
            
        # Initialize default if exists
        if key in ContentService.DEFAULTS:
            default = ContentService.DEFAULTS[key]
            new_content = ModuleContent(
                key=key,
                value=default["value"],
                description=default["desc"],
                category=default["cat"]
            )
            session.add(new_content)
            await session.commit()
            return default["value"]
            
        return ""

    @staticmethod
    async def update_text(session: AsyncSession, key: str, value: str) -> bool:
        """Update text content."""
        query = select(ModuleContent).where(ModuleContent.key == key)
        result = await session.execute(query)
        content = result.scalar_one_or_none()
        
        if content:
            content.value = value
            await session.commit()
            return True
        return False

    @staticmethod
    async def reset_to_default(session: AsyncSession, key: str) -> str | None:
        """Reset a content key to its default value."""
        if key not in ContentService.DEFAULTS:
            return None
        default_value = ContentService.DEFAULTS[key]["value"]
        query = select(ModuleContent).where(ModuleContent.key == key)
        result = await session.execute(query)
        content = result.scalar_one_or_none()
        if content:
            content.value = default_value
            await session.commit()
        return default_value

    @staticmethod
    async def get_all_content(session: AsyncSession):
        """Get all editable content grouped by category."""
        query = select(ModuleContent).order_by(ModuleContent.category, ModuleContent.key)
        result = await session.execute(query)
        items = result.scalars().all()
        
        # Ensure initialization of all defaults
        existing_keys = {item.key for item in items}
        new_items = []
        
        for key, default in ContentService.DEFAULTS.items():
            if key not in existing_keys:
                new_item = ModuleContent(
                    key=key,
                    value=default["value"],
                    description=default["desc"],
                    category=default["cat"]
                )
                session.add(new_item)
                new_items.append(new_item)
        
        if new_items:
            await session.commit()
            items.extend(new_items)
            
        return items
