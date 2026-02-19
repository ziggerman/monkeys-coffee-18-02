"""Main bot entry point."""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from src.database.session import init_db, async_session
from sqlalchemy import select

# Import handlers
from src.handlers import start, catalog, cart, loyalty, promotions, checkout, orders, profile, admin, admin_categories, admin_discounts, support, tasting_sets, info, bundles, debug_utils, unhandled, navigation
from src.utils.bot_commands import setup_bot_commands

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def on_startup():
    """Execute on bot startup."""
    logger.info("Initializing database...")
    await init_db()
    
    # CLEAR WEBHOOK to ensure polling works!
    # This fixes issues if the bot was ever used with a webhook.
    from aiogram.methods import DeleteWebhook
    try:
         # We need the bot instance here, but on_startup is called by main...
         # We will move this to main() before start_polling
         pass
    except Exception as e:
        logger.error(f"Error clearing webhook: {e}")
        
    logger.info("Database initialized!")


async def main():
    """Main bot function."""
    # Create bot instance
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Create dispatcher with FSM storage
    dp = Dispatcher(storage=MemoryStorage())
    
    # Register routers
    # GLOBAL NAVIGATION (Must be first to catch commands/states)
    dp.include_router(navigation.router)
    
    dp.include_router(admin.router)
    dp.include_router(admin_categories.router)
    dp.include_router(admin_discounts.router)
    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(checkout.router)
    dp.include_router(cart.router)
    dp.include_router(tasting_sets.router)
    dp.include_router(orders.router)
    dp.include_router(loyalty.router)
    dp.include_router(promotions.router)
    dp.include_router(bundles.router)
    dp.include_router(support.router)
    dp.include_router(info.router)
    
    # Catalog (contains search catch-all, must be last of main features)
    dp.include_router(catalog.router)
    
    dp.include_router(debug_utils.router)
    
    # Catch-all for unhandled updates (MUST BE LAST)
    dp.include_router(unhandled.router)
    
    # Middleware to inject database session and handle user registration
    @dp.update.middleware()
    async def db_session_middleware(handler, event, data):
        async with async_session() as session:
            data['session'] = session
            
            # Get Telegram user info
            tg_user = None
            if hasattr(event, "from_user") and event.from_user:
                tg_user = event.from_user
            elif hasattr(event, "message") and event.message and event.message.from_user:
                tg_user = event.message.from_user
            elif hasattr(event, "callback_query") and event.callback_query and event.callback_query.from_user:
                tg_user = event.callback_query.from_user
                
            if tg_user:
                logger.info(f"Update from ID: {tg_user.id} ({tg_user.full_name}) | Admin list: {settings.admin_id_list}")
                from src.database.models import User
                # Get or create user
                query = select(User).where(User.id == tg_user.id)
                result = await session.execute(query)
                user = result.scalar_one_or_none()
                
                
                if not user:
                    user = User(
                        id=tg_user.id,
                        username=tg_user.username,
                        first_name=tg_user.first_name,
                        last_name=tg_user.last_name
                    )
                    session.add(user)
                    await session.commit()
                    await session.refresh(user)
                    logger.info(f"Auto-registered new user: {tg_user.id}")
                else:
                    # Sync info if changed
                    if (user.username != tg_user.username or 
                        user.first_name != tg_user.first_name or 
                        user.last_name != tg_user.last_name):
                        user.username = tg_user.username
                        user.first_name = tg_user.first_name
                        user.last_name = tg_user.last_name
                        await session.commit()
                
                data['user'] = user

            # DEBUG LOGGING FOR ALL MESSAGES
            if hasattr(event, "message") and event.message and event.message.text:
                state = data.get('state')
                current_state = await state.get_state() if state else "Unknown"
                logger.info(f"📨 MESSAGE RECEIVED: '{event.message.text}' | User: {tg_user.id if tg_user else 'None'} | State: {current_state}")
            elif hasattr(event, "callback_query") and event.callback_query:
                state = data.get('state')
                current_state = await state.get_state() if state else "Unknown"
                logger.info(f"🔘 CALLBACK RECEIVED: '{event.callback_query.data}' | User: {tg_user.id if tg_user else 'None'} | State: {current_state}")

            return await handler(event, data)
    
    # Run startup
    await on_startup()
    
    # Set bot commands
    await setup_bot_commands(bot)
    
    # Start polling
    logger.info("Bot started successfully! 🚀")
    
    # FORCE DELETE WEBHOOK
    logger.info("Deleting webhook to force polling...")
    await bot.delete_webhook(drop_pending_updates=True)
    
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
