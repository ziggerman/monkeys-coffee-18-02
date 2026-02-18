"""Utility functions for dynamic UI elements."""
from aiogram.types import FSInputFile, Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import ModuleImage
from src.utils.image_constants import ASSETS_DIR
from pathlib import Path

async def get_module_image(session: AsyncSession, module_name: str, default_path: Path) -> str | FSInputFile | None:
    """Get module image: priority to DB file_id, fallback to local file."""
    # 1. Check DB
    query = select(ModuleImage).where(ModuleImage.module_name == module_name)
    result = await session.execute(query)
    module_img = result.scalar_one_or_none()
    
    if module_img and module_img.file_id:
        return module_img.file_id
        
    # 2. Fallback to local
    if default_path.exists():
        return FSInputFile(default_path)
        
    return None
