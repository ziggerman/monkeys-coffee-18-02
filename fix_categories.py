import asyncio
import os
import sys

# Ensure current directory is in sys.path
sys.path.append(os.getcwd())
# Ensure src is importable
if 'src' not in sys.modules:
    sys.path.append(os.path.join(os.getcwd(), 'src'))

from sqlalchemy import select, delete, update
from src.database.session import get_session, init_db
from src.database.models import Category
from config import settings

async def main():
    print("🚀 Starting Category Fix Script...")
    print(f"📂 Database: {settings.database_url}")
    
    # Initialize DB (create tables if not exist, though they should)
    await init_db()
    
    async for session in get_session():
        # 1. Delete "Йо" and any other garbage
        print("🗑️ Deleting invalid categories...")
        # Delete everything that is NOT coffee or equipment
        stmt = delete(Category).where(Category.slug.notin_(['coffee', 'equipment']))
        result = await session.execute(stmt)
        print(f"   Deleted {result.rowcount} categories (including 'Йо' if it existed).")

        # 2. Setup Coffee
        print("☕ Setting up Coffee...")
        coffee = await session.scalar(select(Category).where(Category.slug == 'coffee'))
        if not coffee:
            coffee = Category(slug='coffee', name_ua='☕ Кава', name_en='Coffee', is_active=True, sort_order=1)
            session.add(coffee)
            print("   Created 'coffee' category.")
        else:
            coffee.name_ua = '☕ Кава'
            coffee.is_active = True
            coffee.sort_order = 1
            print("   Updated 'coffee' category.")

        # 3. Setup Shop
        print("🏪 Setting up Shop...")
        shop = await session.scalar(select(Category).where(Category.slug == 'equipment'))
        if not shop:
            shop = Category(slug='equipment', name_ua='🏪 Магазин', name_en='Shop', is_active=True, sort_order=2)
            session.add(shop)
            print("   Created 'equipment' category.")
        else:
            shop.name_ua = '🏪 Магазин'
            shop.is_active = True
            shop.sort_order = 2
            print("   Updated 'equipment' category.")
            
        await session.commit()
        
        # 4. Verify
        print("\n✅ Verification - Current Categories:")
        cats = await session.scalars(select(Category).order_by(Category.sort_order))
        for c in cats:
            print(f"   - [{c.id}] {c.name_ua} ({c.slug}) Active={c.is_active}")
            
    print("\n🎉 Done! Now restart your bot.")

if __name__ == "__main__":
    asyncio.run(main())
