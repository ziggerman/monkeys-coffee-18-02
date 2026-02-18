from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault

async def setup_bot_commands(bot: Bot):
    """Set up bot commands for the command menu."""
    commands = [
        BotCommand(command="start", description="🟢 Головна ☕"),
        BotCommand(command="catalog", description="🟢 Каталог кави 🫘"),
        BotCommand(command="cart", description="🟠 Кошик покупок 🛍️"),
        BotCommand(command="orders", description="📦 Мої замовлення"),
        BotCommand(command="loyalty", description="🎯 Бонусна карта"),
        BotCommand(command="support", description="💬 Допомога та SOS"),
    ]
    
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())
