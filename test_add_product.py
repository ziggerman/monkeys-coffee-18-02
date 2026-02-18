
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.session import async_session
from src.database.models import Product

async def test_add_product():
    async with async_session() as session:
        try:
            new_product = Product(
                name_ua="Тестова кава",
                origin="Тестова кава",
                price_300g=400,
                price_1kg=1200,
                profile="universal",
                tasting_notes=["Тест", "Кава"],
                description="Опис",
                is_active=True
            )
            session.add(new_product)
            await session.commit()
            print("Successfully added product!")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_add_product())
