import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.database.models import Product, Base
from src.utils.constants import ProductCategory

async def seed_shop():
    engine = create_async_engine("sqlite+aiosqlite:///coffee_shop.db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    products = [
        Product(
            name_ua="Фільтр-пакети Hario V60-02 (100 шт)",
            category="equipment",
            description="🐒 *Японська якість для вашого фільтру.* \n\nКислородно-відбілені паперові фільтри для пуровера Hario V60 розміру 02. Забезпечують чистий смак без паперового присмаку.",
            price_300g=320,  # Single price field for equipment
            price_1kg=0,
            image_url=None,
            is_active=True,
            profile="equipment"
        ),
        Product(
            name_ua="Пуровер Hario V60-02 (Пластик)",
            category="equipment",
            description="🐒 *Класика, з якої починається ранок.* \n\nЛегкий та міцний пластиковий пуровер. Завдяки матеріалу відмінно тримає температуру під час заварювання.",
            price_300g=450,
            price_1kg=0,
            image_url=None,
            is_active=True,
            profile="equipment"
        ),
        Product(
            name_ua="Мірна ложка Monkey Spoon",
            category="equipment",
            description="🐒 *Спеціальний девайс для точного дозування.* \n\nЗручна ложка, яка допоможе відміряти саме ту кількість зерен, яка потрібна для ідеальної чашки.",
            price_300g=150,
            price_1kg=0,
            image_url=None,
            is_active=True,
            profile="equipment"
        )
    ]
    
    async with async_session() as session:
        for p in products:
            session.add(p)
        await session.commit()
    
    print("✅ Shop seeded with equipment!")

if __name__ == "__main__":
    asyncio.run(seed_shop())
