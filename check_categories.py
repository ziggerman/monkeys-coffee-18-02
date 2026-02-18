import asyncio
import sys
# Add project root to path
sys.path.append('/Users/nikolas/Desktop/BARISTA GOD/monkeys-coffee-18-02')

from src.database.session import init_db, async_session
from src.database.models import Category
from sqlalchemy import select

async def main():
    await init_db()
    async with async_session() as session:
        result = await session.execute(select(Category))
        categories = result.scalars().all()
        print(f"Total categories: {len(categories)}")
        for c in categories:
            print(f"ID: {c.id} | Name: {c.name_ua} | Slug: {c.slug} | Order: {c.sort_order} | Active: {c.is_active}")

if __name__ == "__main__":
    asyncio.run(main())
