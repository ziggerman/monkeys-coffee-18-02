
import asyncio
import sys
import os

# Add current directory to python path
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.db import get_session
from src.database.models import Category
from sqlalchemy import select

async def check_categories():
    print("Checking categories...")
    async for session in get_session():
        result = await session.execute(select(Category))
        categories = result.scalars().all()
        print(f'Found {len(categories)} categories:')
        for c in categories:
            print(f'- {c.slug} ({c.name_ua}) [Active: {c.is_active}]')
        break

if __name__ == "__main__":
    asyncio.run(check_categories())
