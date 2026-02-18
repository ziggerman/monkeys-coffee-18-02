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
        "cart.empty_text": {
            "value": "Тут пусто, як у понеділок зранку без кави. 😴 Час це виправляти!",
            "desc": "Текст порожнього кошика",
            "cat": "cart"
        },
        "cart.header": {
            "value": "🟠 <b>ВАШ КОШИК</b> 🐒\n\n",
            "desc": "Заголовок кошика",
            "cat": "cart"
        },
        "cabinet.caption": {
            "value": "🔴 <b>Твій Кабінет</b> 🐒\n\nЦе твоя база. Тут історія покупок і твоя статистика. ⚫",
            "desc": "Текст в кабінеті",
            "cat": "info"
        },
        "about.text": {
            "value": "⚫ <b>Інфо-Хаб</b> 🐒\n\nВсе, що ти хотів знати, а ми хотіли розповісти. ⚫",
            "desc": "Текст розділу Інфо",
            "cat": "info"
        },
        "catalog.espresso": {
            "value": "🟠 <b>Для еспресо</b>\n(щільність, шоколад, карамель, горіхи)",
            "desc": "Опис профілю Еспресо",
            "cat": "catalog"
        },
        "catalog.filter": {
            "value": "🟢 <b>Для фільтру</b>\n(кислинка, фрукти, ягоди, квіти)",
            "desc": "Опис профілю Фільтр",
            "cat": "catalog"
        },
         "catalog.guide": {
            "value": "🟠 <b>ЯК ОБРАТИ?</b>\n• Кавомашина/Молоко ➜ <b>Еспресо</b>\n• V60/Аеропрес/Фільтр ➜ <b>Фільтр</b>\n• Турка/Гейзер/Чашка ➜ <b>Універсальна</b>",
            "desc": "Гайд по вибору кави",
            "cat": "catalog"
        }
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
