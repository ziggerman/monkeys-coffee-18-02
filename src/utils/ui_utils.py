"""Utility functions for dynamic UI elements."""
import logging
from aiogram.types import FSInputFile, Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import ModuleImage
from src.utils.image_constants import ASSETS_DIR
from pathlib import Path

logger = logging.getLogger(__name__)

# In-memory cache for file_ids to avoid repeated DB queries and Telegram API calls
# Format: {module_name: {"file_id": str, "used": bool}}
_file_id_cache = {}


async def get_module_image(session: AsyncSession, module_name: str, default_path: Path) -> str | FSInputFile | None:
    """Get module image: priority to cached/DB file_id, fallback to local file.
    
    Uses caching to ensure the same file_id is reused, preventing Telegram media accumulation.
    """
    # Check in-memory cache first
    if module_name in _file_id_cache:
        cached = _file_id_cache[module_name]
        if cached.get("file_id"):
            logger.debug(f"Using cached file_id for {module_name}")
            return cached["file_id"]
    
    # 1. Check DB for existing file_id
    query = select(ModuleImage).where(ModuleImage.module_name == module_name)
    result = await session.execute(query)
    module_img = result.scalar_one_or_none()
    
    if module_img and module_img.file_id:
        # Cache it
        _file_id_cache[module_name] = {"file_id": module_img.file_id, "used": True}
        logger.debug(f"Using DB file_id for {module_name}")
        return module_img.file_id
        
    # 2. Fallback to local file (only if no cached file_id exists)
    if module_name not in _file_id_cache and default_path.exists():
        file_id = None
        # Try to get file_id from Telegram by sending the file once (only if not in cache)
        # This is expensive, so we skip it and just return the local file
        logger.debug(f"Using local file for {module_name}")
        return FSInputFile(default_path)
    
    return None


async def clear_module_image_cache(module_name: str = None) -> None:
    """Clear module image cache. If module_name is None, clear all."""
    global _file_id_cache
    if module_name:
        _file_id_cache.pop(module_name, None)
    else:
        _file_id_cache.clear()
    logger.info(f"Cleared module image cache: {module_name or 'all'}")
