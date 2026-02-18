"""Notification service for automated customer engagement."""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot

from src.database.models import User, Order, Product
from src.utils.formatters import format_currency, format_date
from config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending automated notifications to users."""
    
    def __init__(self, bot: Bot):
        """Initialize notification service with bot instance."""
        self.bot = bot
    
    async def send_order_confirmation(
        self,
        session: AsyncSession,
        order_id: int
    ):
        """Send order confirmation notification after successful payment.
        
        Args:
            session: Database session
            order_id: ID of the paid order
        """
        query = select(Order).where(Order.id == order_id)
        result = await session.execute(query)
        order = result.scalar_one_or_none()
        
        if not order:
            logger.error(f"Order {order_id} not found for confirmation")
            return
        
        text = f"""
✅ <b>Замовлення #{order.order_number} підтверджено!</b>

Дякуємо за покупку!

<b>Деталі замовлення:</b>
💰 Сума: {format_currency(order.total)}
📦 Доставка: {order.delivery_method}
📍 Адреса: {order.delivery_city}, {order.delivery_address}

<b>Наступні кроки:</b>
1️⃣ Ми обсмажимо вашу каву протягом 1-2 днів
2️⃣ Відправимо замовлення
3️⃣ Надішлемо трекінг-номер

⏱️ <b>Очікуваний час доставки:</b> 2-4 дні

Слідкуйте за статусом в розділі "📦 Мої замовлення"

Дякуємо, що обрали Monkeys Coffee! 🐒☕
"""
        
        try:
            await self.bot.send_message(
                chat_id=order.user_id,
                text=text,
                parse_mode="HTML"
            )
            logger.info(f"Sent order confirmation for order {order_id}")
        except Exception as e:
            logger.error(f"Failed to send order confirmation: {e}")
    
    async def send_shipping_notification(
        self,
        session: AsyncSession,
        order_id: int
    ):
        """Send notification when order is shipped.
        
        Args:
            session: Database session
            order_id: ID of the shipped order
        """
        query = select(Order).where(Order.id == order_id)
        result = await session.execute(query)
        order = result.scalar_one_or_none()
        
        if not order or not order.tracking_number:
            return
        
        tracking_link = ""
        if "nova" in order.delivery_method.lower():
            tracking_link = f"\n🔗 Відстежити: https://novaposhta.ua/tracking/?&cargo_number={order.tracking_number}"
        
        text = f"""
📦 <b>Замовлення #{order.order_number} відправлено!</b>

Ваша кава вже в дорозі! 🚚

<b>Трекінг-номер:</b> <code>{order.tracking_number}</code>{tracking_link}

<b>Доставка:</b> {order.delivery_method}
<b>Адреса:</b> {order.delivery_city}, {order.delivery_address}

⏱️ <b>Очікувані строки:</b>
• Нова Пошта: 1-3 дні
• Укрпошта: 3-7 днів

💡 <b>Після отримання:</b>
Дайте каві "відпочити" 1-2 дні після обсмаження
для найкращого розкриття смаку!

Смачної кави! ☕
"""
        
        try:
            await self.bot.send_message(
                chat_id=order.user_id,
                text=text,
                parse_mode="HTML"
            )
            logger.info(f"Sent shipping notification for order {order_id}")
        except Exception as e:
            logger.error(f"Failed to send shipping notification: {e}")
    
    async def send_replenishment_reminders(
        self,
        session: AsyncSession
    ) -> int:
        """Send coffee replenishment reminders to users.
        
        Targets users who:
        - Made their last order 20-25 days ago
        - Haven't ordered in the last 3 days
        
        Returns:
            Number of reminders sent
        """
        # Calculate date range
        reminder_start = datetime.utcnow() - timedelta(days=25)
        reminder_end = datetime.utcnow() - timedelta(days=20)
        recent_cutoff = datetime.utcnow() - timedelta(days=3)
        
        # Find users with last order in reminder window
        query = select(User).join(Order).where(
            and_(
                Order.status.in_(['paid', 'shipped', 'delivered']),
                Order.created_at >= reminder_start,
                Order.created_at <= reminder_end
            )
        ).distinct()
        
        result = await session.execute(query)
        users = result.scalars().all()
        
        sent_count = 0
        
        for user in users:
            # Check if user has ordered recently
            recent_order_query = select(Order).where(
                and_(
                    Order.user_id == user.id,
                    Order.created_at >= recent_cutoff,
                    Order.status.in_(['paid', 'shipped', 'delivered'])
                )
            )
            recent_result = await session.execute(recent_order_query)
            recent_order = recent_result.scalar_one_or_none()
            
            if recent_order:
                continue  # Skip if already ordered recently
            
            # Get user's last order for personalization
            last_order_query = select(Order).where(
                and_(
                    Order.user_id == user.id,
                    Order.status.in_(['paid', 'shipped', 'delivered'])
                )
            ).order_by(Order.created_at.desc()).limit(1)
            
            last_order_result = await session.execute(last_order_query)
            last_order = last_order_result.scalar_one_or_none()
            
            if not last_order:
                continue
            
            # Personalize based on last order
            days_ago = (datetime.utcnow() - last_order.created_at).days
            
            # Get most ordered product
            favorite_product = None
            if last_order.items:
                product_counts = {}
                for item in last_order.items:
                    product_id = item.get('product_id')
                    product_counts[product_id] = product_counts.get(product_id, 0) + item.get('quantity', 0)
                
                if product_counts:
                    favorite_id = max(product_counts, key=product_counts.get)
                    product_query = select(Product).where(Product.id == favorite_id)
                    product_result = await session.execute(product_query)
                    favorite_product = product_result.scalar_one_or_none()
            
            text = f"""
☕ <b>Час поповнити запаси кави!</b>

Привіт! Минуло вже {days_ago} днів з вашого
останнього замовлення.

"""
            
            if favorite_product:
                text += f"""💚 <b>Ваша улюблена кава:</b>
{favorite_product.name_ua}

Вона чекає на вас в каталозі!

"""
            
            text += f"""🎁 <b>Ексклюзивна пропозиція:</b>

Використайте промокод <b>COMEBACK15</b>
для знижки 15% на наступне замовлення!

Діє 7 днів.

━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 <b>Чому варто замовити зараз?</b>

✓ Свіжеобсмажена кава (2-3 дні)
✓ Безкоштовна доставка від 1500 грн
✓ Накопичувальна знижка {user.loyalty_level * 5}%

Ваш рівень: {['Новачок', 'Любитель кави', 'Кавовий експерт', 'Монкі-майстер'][user.loyalty_level - 1]}

Замовляйте зараз! 🐒☕
"""
            
            try:
                await self.bot.send_message(
                    chat_id=user.id,
                    text=text,
                    parse_mode="HTML"
                )
                sent_count += 1
                logger.info(f"Sent replenishment reminder to user {user.id}")
            except Exception as e:
                logger.error(f"Failed to send replenishment reminder to user {user.id}: {e}")
        
        return sent_count
    
    async def send_volume_discount_suggestions(
        self,
        session: AsyncSession
    ) -> int:
        """Send suggestions to users close to volume discount tiers.
        
        Targets users who have items in cart but haven't reached next discount tier.
        
        Returns:
            Number of suggestions sent
        """
        from src.services.discount_engine import DiscountEngine
        from src.services.cart_service import CartService
        
        # Find users with active carts
        query = select(User).join(User.cart_items).distinct()
        result = await session.execute(query)
        users = result.scalars().all()
        
        sent_count = 0
        
        for user in users:
            # Get cart breakdown
            cart_items = await CartService.get_cart_items(session, user.id)
            
            if not cart_items:
                continue
            
            breakdown = DiscountEngine.calculate_full_discount(cart_items, user)
            
            # Check if close to next tier
            should_send = False
            suggestion = ""
            
            # Check pack-based discounts
            if breakdown.total_packs_300g == 2:
                should_send = True
                suggestion = """
🎯 <b>Ще 1 пачка = -10%!</b>

У вас в кошику 2 пачки по 300г.
Додайте ще одну - отримаєте знижку 10%!

💰 Економія: ~{} грн
""".format(format_currency(breakdown.potential_savings_packs))
            
            elif breakdown.total_packs_300g in [3, 5]:
                next_tier = 4 if breakdown.total_packs_300g == 3 else 6
                next_discount = 15 if next_tier == 4 else 25
                needed = next_tier - breakdown.total_packs_300g
                
                should_send = True
                suggestion = f"""
🎯 <b>Ще {needed} пачки = -{next_discount}%!</b>

У вас в кошику {breakdown.total_packs_300g} пачки.
Додайте ще {needed} - отримаєте знижку {next_discount}%!

💰 Економія: ~{format_currency(breakdown.potential_savings_packs)}
"""
            
            # Check kg-based discounts
            elif 1.5 <= breakdown.total_weight_kg < 2.0:
                needed_kg = 2.0 - breakdown.total_weight_kg
                should_send = True
                suggestion = f"""
🎯 <b>Ще {needed_kg:.1f} кг = -25%!</b>

У вас в кошику {breakdown.total_weight_kg:.1f} кг кави.
Додайте ще трохи - активуєте максимальну знижку 25%!

💰 Економія: ~{format_currency(breakdown.potential_savings_kg)}
"""
            
            if should_send:
                text = f"""
💡 <b>Підказка по вашому кошику</b>

{suggestion}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>Поточний кошик:</b>
Товарів на: {format_currency(breakdown.subtotal)}
Поточна знижка: {breakdown.volume_discount_percent + breakdown.loyalty_discount_percent}%

<b>Після додавання:</b>
Знижка збільшиться до максимуму!

Переглянути кошик → /cart
Каталог → /start

Не упустіть вигоду! 🐒
"""
                
                try:
                    await self.bot.send_message(
                        chat_id=user.id,
                        text=text,
                        parse_mode="HTML"
                    )
                    sent_count += 1
                    logger.info(f"Sent volume discount suggestion to user {user.id}")
                except Exception as e:
                    logger.error(f"Failed to send suggestion to user {user.id}: {e}")
        
        return sent_count
    
    async def send_fresh_roast_announcements(
        self,
        session: AsyncSession,
        product_ids: Optional[List[int]] = None
    ) -> int:
        """Send personalized fresh roast announcements.
        
        Args:
            session: Database session
            product_ids: Optional list of newly roasted product IDs
            
        Returns:
            Number of announcements sent
        """
        # Get recently roasted products (last 3 days)
        if not product_ids:
            recent_roast_date = datetime.utcnow() - timedelta(days=3)
            query = select(Product).where(
                and_(
                    Product.roast_date >= recent_roast_date,
                    Product.is_active == True
                )
            )
            result = await session.execute(query)
            products = result.scalars().all()
        else:
            query = select(Product).where(
                and_(
                    Product.id.in_(product_ids),
                    Product.is_active == True
                )
            )
            result = await session.execute(query)
            products = result.scalars().all()
        
        if not products:
            return 0
        
        # Get all active users who have ordered before
        user_query = select(User).join(Order).where(
            Order.status.in_(['paid', 'shipped', 'delivered'])
        ).distinct()
        user_result = await session.execute(user_query)
        users = user_result.scalars().all()
        
        sent_count = 0
        
        for user in users:
            # Personalize based on user's order history
            orders_query = select(Order).where(
                and_(
                    Order.user_id == user.id,
                    Order.status.in_(['paid', 'shipped', 'delivered'])
                )
            )
            orders_result = await session.execute(orders_query)
            user_orders = orders_result.scalars().all()
            
            # Find user's favorite profile
            profile_counts = {}
            for order in user_orders:
                for item in order.items:
                    profile = item.get('profile', 'universal')
                    profile_counts[profile] = profile_counts.get(profile, 0) + 1
            
            favorite_profile = max(profile_counts, key=profile_counts.get) if profile_counts else None
            
            # Filter products for this user
            relevant_products = products
            if favorite_profile:
                relevant_products = [p for p in products if p.profile == favorite_profile]
                if not relevant_products:
                    relevant_products = products  # Fallback to all
            
            # Build announcement
            text = "🔥 <b>Свіжа кава тільки-но з ростера!</b>\n\n"
            
            if favorite_profile and len(relevant_products) < len(products):
                profile_names = {
                    'espresso': 'еспресо',
                    'filter': 'фільтр',
                    'universal': 'універсальну каву'
                }
                text += f"Ми знаємо, що ви любите {profile_names.get(favorite_profile, 'цю каву')}!\n\n"
            
            text += "Щойно обсмажені:\n\n"
            
            for product in relevant_products[:3]:  # Max 3 products
                roast_date = format_date(product.roast_date, "short")
                notes = ", ".join(product.tasting_notes[:3])
                
                text += f"""<b>{product.name_ua}</b>
📍 {product.origin}
🌸 {notes}
📅 Обсмажено: {roast_date}
💰 Від {format_currency(product.price_300g)}

"""
            
            text += f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ <b>Чому варто замовити зараз?</b>

• Максимум аромату (перші 3 тижні)
• Гарантована свіжість
• Ваша накопичувальна знижка: {user.loyalty_level * 5}%

🎁 <b>Бонус:</b> Безкоштовна доставка від 1500 грн!

Замовляйте, поки тепла! ☕🔥
"""
            
            try:
                await self.bot.send_message(
                    chat_id=user.id,
                    text=text,
                    parse_mode="HTML"
                )
                sent_count += 1
                logger.info(f"Sent fresh roast announcement to user {user.id}")
            except Exception as e:
                logger.error(f"Failed to send announcement to user {user.id}: {e}")
        
        return sent_count
    
    async def send_loyalty_upgrade_notification(
        self,
        user_id: int,
        new_level: int,
        total_kg: float
    ):
        """Send notification when user reaches new loyalty level.
        
        Args:
            user_id: User ID
            new_level: New loyalty level achieved
            total_kg: Total kg purchased
        """
        level_names = ["", "Новачок", "Любитель кави", "Кавовий експерт", "Монкі-майстер"]
        level_emojis = ["", "🌱", "☕", "🎓", "🐒"]
        
        from config import LOYALTY_LEVELS
        
        level_info = LOYALTY_LEVELS[new_level]
        
        text = f"""
🎉 <b>Вітаємо! Новий рівень лояльності!</b>

{level_emojis[new_level]} <b>{level_names[new_level]}</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ви придбали {total_kg:.1f} кг нашої кави!

<b>Ваші переваги:</b>

💰 Постійна знижка: <b>{level_info['discount']}%</b>
✨ Накопичується з об'ємними знижками
🎁 Ексклюзивні пропозиції
"""
        
        if new_level < 4:
            next_level = LOYALTY_LEVELS[new_level + 1]
            needed_kg = next_level['threshold_kg'] - total_kg
            
            text += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━

<b>Наступний рівень:</b>
{level_emojis[new_level + 1]} {level_names[new_level + 1]}

Знижка: {next_level['discount']}%
Залишилось: {needed_kg:.1f} кг
"""
        else:
            text += """

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 <b>Ви досягли максимального рівня!</b>

Дякуємо за вашу відданість!
"""
        
        text += "\n\nПродовжуйте насолоджуватись найкращою кавою! 🐒☕"
        
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=text,
                parse_mode="HTML"
            )
            logger.info(f"Sent loyalty upgrade notification to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send loyalty upgrade: {e}")
    
    async def send_abandoned_cart_reminder(
        self,
        session: AsyncSession
    ) -> int:
        """Send reminders to users with abandoned carts.
        
        Targets users who:
        - Have items in cart
        - Haven't modified cart in 24-48 hours
        - Haven't placed order in last 7 days
        
        Returns:
            Number of reminders sent
        """
        from src.services.cart_service import CartService
        
        # This would require tracking cart last_modified timestamp
        # For now, simplified version
        
        cutoff_recent = datetime.utcnow() - timedelta(days=7)
        
        query = select(User).join(User.cart_items).distinct()
        result = await session.execute(query)
        users = result.scalars().all()
        
        sent_count = 0
        
        for user in users:
            # Check if user has recent orders
            recent_order_query = select(Order).where(
                and_(
                    Order.user_id == user.id,
                    Order.created_at >= cutoff_recent
                )
            )
            recent_result = await session.execute(recent_order_query)
            recent_order = recent_result.scalar_one_or_none()
            
            if recent_order:
                continue  # Skip if already ordered
            
            cart_items = await CartService.get_cart_items(session, user.id)
            
            if not cart_items:
                continue
            
            from src.services.discount_engine import DiscountEngine
            breakdown = DiscountEngine.calculate_full_discount(cart_items, user)
            
            text = f"""
🛒 <b>Ви забули про свій кошик!</b>

У вас залишилось {len(cart_items)} товарів
на суму {format_currency(breakdown.subtotal)}

"""
            
            if breakdown.total_discount_percent > 0:
                text += f"""💰 <b>Ваша знижка: {breakdown.total_discount_percent}%</b>
Економія: {format_currency(breakdown.total_discount_amount)}

"""
            
            text += """━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎁 <b>Доповніть для більшої знижки!</b>

"""
            
            if breakdown.total_packs_300g < 6:
                text += f"Ще {6 - breakdown.total_packs_300g} пачки = знижка 25%\n"
            
            text += """
Завершити замовлення → /cart

Не втрачайте своїх переваг! 🐒☕
"""
            
            try:
                await self.bot.send_message(
                    chat_id=user.id,
                    text=text,
                    parse_mode="HTML"
                )
                sent_count += 1
                logger.info(f"Sent abandoned cart reminder to user {user.id}")
            except Exception as e:
                logger.error(f"Failed to send abandoned cart reminder: {e}")
        
        return sent_count
