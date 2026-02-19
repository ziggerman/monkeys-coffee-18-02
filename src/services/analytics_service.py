"""Admin panel analytics service."""
from typing import Dict, List
from datetime import datetime, timedelta
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from src.database.models import Order, User, Product
from config import LOYALTY_LEVELS


class AnalyticsService:
    """Service for admin analytics and statistics."""
    
    @staticmethod
    async def get_general_statistics(session: AsyncSession) -> Dict:
        """Get general business statistics (Optimized).
        
        Returns:
            Dict with key metrics
        """
        # Execute queries in parallel
        # Execute queries sequentially (Session is not thread-safe for concurrent use)
        # 0: Total users
        total_users_result = await session.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar() or 0

        # 1: Total orders & revenue (paid+)
        paid_stats_result = await session.execute(
            select(func.count(Order.id), func.sum(Order.total))
            .where(Order.status.in_(['paid', 'shipped', 'delivered']))
        )
        paid_stats = paid_stats_result.one()
        paid_orders_count = paid_stats[0] or 0
        total_revenue = paid_stats[1] or 0

        # 2: Order status breakdown
        status_result = await session.execute(
            select(Order.status, func.count(Order.id)).group_by(Order.status)
        )
        status_counts = {row[0]: row[1] for row in status_result.all()}

        # 3: Active products
        active_products_result = await session.execute(
             select(func.count(Product.id)).where(Product.is_active == True)
        )
        active_products = active_products_result.scalar() or 0
        
        total_orders = sum(status_counts.values())
        
        # Calculate derived metrics
        avg_order_value = total_revenue / paid_orders_count if paid_orders_count > 0 else 0
        
        return {
            'total_users': total_users,
            'total_orders': total_orders,
            'total_revenue': int(total_revenue),
            'avg_order_value': int(avg_order_value),
            'pending_orders': status_counts.get('pending', 0),
            'paid_orders': status_counts.get('paid', 0),
            'shipped_orders': status_counts.get('shipped', 0),
            'delivered_orders': status_counts.get('delivered', 0),
            'active_products': active_products
        }
    
    @staticmethod
    async def get_discount_statistics(session: AsyncSession) -> Dict:
        """Get discount usage statistics (Optimized).
        
        Returns:
            Dict with discount metrics
        """
        # Aggregate all stats in one query
        query = select(
            func.count(Order.id),
            func.sum(Order.discount_volume),
            func.sum(Order.discount_loyalty),
            func.sum(Order.discount_promo),
            func.sum(Order.subtotal),
            # Count orders that had ANY discount using CASE for compatibility
            func.sum(case(
                ((Order.discount_volume + Order.discount_loyalty + Order.discount_promo) > 0, 1),
                else_=0
            ))
        ).where(
            Order.status.in_(['paid', 'shipped', 'delivered'])
        )
        
        result = await session.execute(query)
        stats = result.one()
        
        total_orders = stats[0] or 0
        volume_discounts = stats[1] or 0
        loyalty_discounts = stats[2] or 0
        promo_discounts = stats[3] or 0
        total_subtotal = stats[4] or 0
        orders_with_discounts = stats[5] or 0
        
        total_discounts = volume_discounts + loyalty_discounts + promo_discounts
        avg_discount_percent = (total_discounts / total_subtotal * 100) if total_subtotal > 0 else 0
        
        return {
            'total_orders': total_orders,
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
        """Get sales statistics for recent period (Optimized).
        
        Args:
            session: Database session
            days: Number of days to analyze
            
        Returns:
            Dict with period statistics
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        filter_condition = [
            Order.created_at >= start_date,
            Order.status.in_(['paid', 'shipped', 'delivered'])
        ]
        
        # Parallel queries:
        # 1. Aggregates (Count, Revenue)
        # 2. Items for KG calculation (only fetched column)
        # Execute queries sequentially
        
        stats_result = await session.execute(
            select(func.count(Order.id), func.sum(Order.total))
            .where(*filter_condition)
        )
        
        items_result = await session.execute(
            select(Order.items).where(*filter_condition)
        )
        
        # Process Aggregates
        stats = stats_result.one()
        total_orders = stats[0] or 0
        total_revenue = stats[1] or 0
        
        # Process KG
        items_rows = items_result.all()
        total_kg = 0
        
        for row in items_rows:
            # row[0] is the items dict/list
            order_items = row[0]
            if not order_items:
                continue
                
            for item in order_items:
                if item.get('format') == '300g':
                    total_kg += 0.3 * item.get('quantity', 0)
                else:
                    total_kg += 1.0 * item.get('quantity', 0)
        
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        return {
            'period_days': days,
            'total_orders': total_orders,
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
