"""Admin panel analytics service."""
from typing import Dict, List
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Order, User, Product
from config import LOYALTY_LEVELS


class AnalyticsService:
    """Service for admin analytics and statistics."""
    
    @staticmethod
    async def get_general_statistics(session: AsyncSession) -> Dict:
        """Get general business statistics.
        
        Returns:
            Dict with key metrics
        """
        # Total users
        user_count_query = select(func.count(User.id))
        user_count_result = await session.execute(user_count_query)
        total_users = user_count_result.scalar()
        
        # Total orders
        order_count_query = select(func.count(Order.id))
        order_count_result = await session.execute(order_count_query)
        total_orders = order_count_result.scalar()
        
        # Total revenue (paid orders)
        revenue_query = select(func.sum(Order.total)).where(
            Order.status.in_(['paid', 'shipped', 'delivered'])
        )
        revenue_result = await session.execute(revenue_query)
        total_revenue = revenue_result.scalar() or 0
        
        # Average order value
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # Orders by status
        pending_query = select(func.count(Order.id)).where(Order.status == 'pending')
        pending_result = await session.execute(pending_query)
        pending_orders = pending_result.scalar()
        
        paid_query = select(func.count(Order.id)).where(Order.status == 'paid')
        paid_result = await session.execute(paid_query)
        paid_orders = paid_result.scalar()
        
        shipped_query = select(func.count(Order.id)).where(Order.status == 'shipped')
        shipped_result = await session.execute(shipped_query)
        shipped_orders = shipped_result.scalar()
        
        delivered_query = select(func.count(Order.id)).where(Order.status == 'delivered')
        delivered_result = await session.execute(delivered_query)
        delivered_orders = delivered_result.scalar()
        
        # Active products
        active_products_query = select(func.count(Product.id)).where(Product.is_active == True)
        active_products_result = await session.execute(active_products_query)
        active_products = active_products_result.scalar()
        
        return {
            'total_users': total_users,
            'total_orders': total_orders,
            'total_revenue': int(total_revenue),
            'avg_order_value': int(avg_order_value),
            'pending_orders': pending_orders,
            'paid_orders': paid_orders,
            'shipped_orders': shipped_orders,
            'delivered_orders': delivered_orders,
            'active_products': active_products
        }
    
    @staticmethod
    async def get_discount_statistics(session: AsyncSession) -> Dict:
        """Get discount usage statistics.
        
        Returns:
            Dict with discount metrics
        """
        # Get all completed orders
        orders_query = select(Order).where(
            Order.status.in_(['paid', 'shipped', 'delivered'])
        )
        orders_result = await session.execute(orders_query)
        orders = orders_result.scalars().all()
        
        if not orders:
            return {
                'total_orders': 0,
                'total_discounts': 0,
                'volume_discounts': 0,
                'loyalty_discounts': 0,
                'promo_discounts': 0,
                'avg_discount_percent': 0,
                'orders_with_discounts': 0
            }
        
        total_discounts = sum(
            order.discount_volume + order.discount_loyalty + order.discount_promo
            for order in orders
        )
        
        volume_discounts = sum(order.discount_volume for order in orders)
        loyalty_discounts = sum(order.discount_loyalty for order in orders)
        promo_discounts = sum(order.discount_promo for order in orders)
        
        orders_with_discounts = sum(
            1 for order in orders
            if (order.discount_volume + order.discount_loyalty + order.discount_promo) > 0
        )
        
        total_subtotal = sum(order.subtotal for order in orders)
        avg_discount_percent = (total_discounts / total_subtotal * 100) if total_subtotal > 0 else 0
        
        return {
            'total_orders': len(orders),
            'total_discounts': int(total_discounts),
            'volume_discounts': int(volume_discounts),
            'loyalty_discounts': int(loyalty_discounts),
            'promo_discounts': int(promo_discounts),
            'avg_discount_percent': round(avg_discount_percent, 1),
            'orders_with_discounts': orders_with_discounts
        }
    
    @staticmethod
    async def get_loyalty_distribution(session: AsyncSession) -> Dict:
        """Get distribution of users across loyalty levels.
        
        Returns:
            Dict with user counts per level
        """
        distribution = {}
        
        for level in range(1, 5):
            query = select(func.count(User.id)).where(User.loyalty_level == level)
            result = await session.execute(query)
            count = result.scalar()
            
            level_info = LOYALTY_LEVELS[level]
            distribution[level] = {
                'name': level_info['name'],
                'count': count,
                'discount': level_info['discount']
            }
        
        # Get users close to next level
        close_to_level_2_query = select(func.count(User.id)).where(
            User.loyalty_level == 1,
            User.total_purchased_kg >= 3,
            User.total_purchased_kg < 5
        )
        close_to_level_2_result = await session.execute(close_to_level_2_query)
        close_to_level_2 = close_to_level_2_result.scalar()
        
        distribution['insights'] = {
            'close_to_level_2': close_to_level_2
        }
        
        return distribution
    
    @staticmethod
    async def get_sales_by_period(
        session: AsyncSession,
        days: int = 30
    ) -> Dict:
        """Get sales statistics for recent period.
        
        Args:
            session: Database session
            days: Number of days to analyze
            
        Returns:
            Dict with period statistics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Orders in period
        orders_query = select(Order).where(
            Order.created_at >= start_date,
            Order.status.in_(['paid', 'shipped', 'delivered'])
        )
        orders_result = await session.execute(orders_query)
        orders = orders_result.scalars().all()
        
        if not orders:
            return {
                'period_days': days,
                'total_orders': 0,
                'total_revenue': 0,
                'avg_order_value': 0,
                'total_kg_sold': 0
            }
        
        total_revenue = sum(order.total for order in orders)
        avg_order_value = total_revenue / len(orders)
        
        # Calculate total kg sold
        total_kg = 0
        for order in orders:
            for item in order.items:
                if item['format'] == '300g':
                    total_kg += 0.3 * item['quantity']
                else:
                    total_kg += 1.0 * item['quantity']
        
        return {
            'period_days': days,
            'total_orders': len(orders),
            'total_revenue': int(total_revenue),
            'avg_order_value': int(avg_order_value),
            'total_kg_sold': round(total_kg, 1)
        }
    
    @staticmethod
    async def get_pending_orders_alerts(session: AsyncSession) -> List[Dict]:
        """Get alerts for orders requiring attention.
        
        Returns:
            List of alert dictionaries
        """
        alerts = []
        
        # Pending orders older than 24 hours
        day_ago = datetime.utcnow() - timedelta(hours=24)
        old_pending_query = select(Order).where(
            Order.status == 'pending',
            Order.created_at < day_ago
        )
        old_pending_result = await session.execute(old_pending_query)
        old_pending = old_pending_result.scalars().all()
        
        if old_pending:
            alerts.append({
                'type': 'old_pending',
                'count': len(old_pending),
                'message': f'{len(old_pending)} замовлень очікують оплати >24 год'
            })
        
        # Paid orders not shipped
        paid_not_shipped_query = select(func.count(Order.id)).where(
            Order.status == 'paid'
        )
        paid_not_shipped_result = await session.execute(paid_not_shipped_query)
        paid_not_shipped = paid_not_shipped_result.scalar()
        
        if paid_not_shipped > 0:
            alerts.append({
                'type': 'needs_shipping',
                'count': paid_not_shipped,
                'message': f'{paid_not_shipped} оплачених замовлень готові до відправки'
            })
        
        return alerts
