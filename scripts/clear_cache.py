"""Script to clear cache - Telegram file_ids and local images."""
import asyncio
import sys
import os

sys.path.append(os.getcwd())

from sqlalchemy import select, update
from src.database.session import init_db, async_session
from src.database.models import Category, ModuleImage


async def clear_cache(clear_local_images: bool = False):
    """Clear Telegram cache - file_ids and optionally local images.
    
    Args:
        clear_local_images: If True, also clear local image paths
    """
    print("🧹 Starting cache clearing...")
    await init_db()
    
    async with async_session() as session:
        # 1. Clear Category image file_ids
        result = await session.execute(select(Category))
        categories = result.scalars().all()
        
        cat_count = 0
        for cat in categories:
            if cat.image_file_id:
                cat.image_file_id = None
                cat_count += 1
            if clear_local_images and cat.image_path:
                # Delete local file if exists
                if cat.image_path and os.path.exists(cat.image_path):
                    try:
                        os.remove(cat.image_path)
                        print(f"   🗑 Deleted: {cat.image_path}")
                    except Exception as e:
                        print(f"   ⚠️ Failed to delete {cat.image_path}: {e}")
                cat.image_path = None
        
        if cat_count > 0 or clear_local_images:
            await session.commit()
        
        print(f"✅ Cleared {cat_count} category file_ids")
        
        # 2. Clear ModuleImage file_ids
        result = await session.execute(select(ModuleImage))
        modules = result.scalars().all()
        
        mod_count = 0
        for mod in modules:
            if mod.file_id:
                mod.file_id = None
                mod_count += 1
        
        if mod_count > 0:
            await session.commit()
        
        print(f"✅ Cleared {mod_count} module image file_ids")
        
        # Summary
        print("\n" + "="*50)
        print("📋 Cache cleared successfully!")
        print(f"   - Category file_ids: {cat_count}")
        print(f"   - Module image file_ids: {mod_count}")
        print("   - FSM state: Will clear on bot restart")
        print("="*50)
        
        print("\n💡 Note: FSM state (button states) is stored in memory")
        print("   and will be automatically cleared when bot restarts.")
        print("   Just restart the bot to clear FSM cache.")


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Clear Telegram bot cache")
    parser.add_argument(
        "--all", 
        "-a", 
        action="store_true",
        help="Also clear local image files"
    )
    args = parser.parse_args()
    
    await clear_cache(clear_local_images=args.all)


if __name__ == "__main__":
    asyncio.run(main())
