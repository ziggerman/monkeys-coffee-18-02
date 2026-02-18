from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from src.utils.image_constants import MODULE_ORDERS, ASSETS_DIR
import os
import traceback

router = Router()

@router.message(Command("debug_img"))
async def debug_image_handler(message: Message):
    """Debug command to test image sending and path resolution."""
    response = "🔍 <b>Image Debugger</b>\n\n"
    
    # Check Path
    response += f"📂 <b>Current CWD:</b> {os.getcwd()}\n"
    response += f"🖼 <b>Assets Dir:</b> {ASSETS_DIR}\n"
    response += f"✅ <b>Assets Dir Exists:</b> {ASSETS_DIR.exists()}\n\n"
    
    target_image = MODULE_ORDERS
    response += f"🎯 <b>Target:</b> {target_image.name}\n"
    response += f"📍 <b>Path:</b> {target_image}\n"
    response += f"✅ <b>Exists:</b> {target_image.exists()}\n"
    
    if target_image.exists():
        response += f"📏 <b>Size:</b> {target_image.stat().st_size} bytes\n"
    
    await message.answer(response, parse_mode="HTML")
    
    # Attempt 1: FSInputFile with Path object
    try:
        await message.answer("🚀 Attempt 1: FSInputFile(Path object)...")
        photo = FSInputFile(target_image)
        await message.answer_photo(photo, caption="✅ Success: Path object")
    except Exception as e:
        await message.answer(f"❌ Failed Attempt 1: {str(e)}\n\nTraceback:\n{traceback.format_exc()}")

    # Attempt 2: FSInputFile with string path
    try:
        await message.answer("🚀 Attempt 2: FSInputFile(String path)...")
        photo = FSInputFile(str(target_image))
        await message.answer_photo(photo, caption="✅ Success: String path")
    except Exception as e:
        await message.answer(f"❌ Failed Attempt 2: {str(e)}")


@router.message(Command("test_all_images"))
async def test_all_images_handler(message: Message):
    """Iterate through all constants in image_constants and try to send them."""
    import src.utils.image_constants as ic
    from pathlib import Path
    
    await message.answer("🧪 <b>Starting Full Image Audit...</b>", parse_mode="HTML")
    
    items = []
    # Get all Path objects from image_constants
    for name, value in vars(ic).items():
        if isinstance(value, Path) and "assets" in str(value):
            items.append((name, value))
            
    total = len(items)
    success = 0
    failed = 0
    
    for name, path in items:
        status_msg = f"Testing <b>{name}</b>...\nPath: {path.name}\n"
        
        if not path.exists():
            status_msg += "❌ FILE NOT FOUND\n"
            failed += 1
            await message.answer(status_msg, parse_mode="HTML")
            continue
            
        try:
            photo = FSInputFile(path)
            # Send silently to avoid spamming user notifications
            await message.answer_photo(photo, caption=f"✅ <b>{name}</b> OK", parse_mode="HTML")
            success += 1
        except Exception as e:
            status_msg += f"❌ SEND FAILED: {str(e)}\n"
            failed += 1
            await message.answer(status_msg, parse_mode="HTML")
            
    summary = f"""
🏁 <b>Audit Complete</b>
Total: {total}
✅ Success: {success}
❌ Failed: {failed}
"""
    await message.answer(summary, parse_mode="HTML")
