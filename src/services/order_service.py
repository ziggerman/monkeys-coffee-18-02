"""Order service - business logic for order creation and management."""
from typing import List, Tuple, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Order, User, CartItem, Product
from src.services.cart_service import CartService
from src.services.discount_engine import DiscountEngine
from src.services.loyalty_service import LoyaltyService
from config import settings


class OrderService:
    """Service for order operations."""
    
    @staticmethod
    async def create_order_from_cart(
        session: AsyncSession,
        user: User,
        delivery_method: str,
        delivery_city: str,
        delivery_address: str,
        recipient_name: str,
        recipient_phone: str,
        grind_preference: str,
        promo_code_used: Optional[str] = None
    ) -> Order:
        """Create order from user's cart.
        
        Args:
            session: Database session
            user: User object
            delivery_method: Delivery method selected
            delivery_city: Delivery city
            delivery_address: Delivery address
            recipient_name: Recipient name
            recipient_phone: Recipient phone
            grind_preference: Grind type selected
            promo_code_used: Optional promo code
            
        Returns:
            Created Order object
        """
        # Get cart items
        cart_items = await CartService.get_cart_items(session, user.id)
        
        if not cart_items:
            raise ValueError("Cart is empty")
        
        # Calculate discounts
        from src.database.models import PromoCode
        promo_code_obj = None
        if promo_code_used:
            promo_query = select(PromoCode).where(PromoCode.code == promo_code_used.upper())
            promo_result = await session.execute(promo_query)
            promo_code_obj = promo_result.scalar_one_or_none()
        
        discount_breakdown = DiscountEngine.calculate_full_discount(
            cart_items, user, promo_code_obj
        )
        
        # Calculate delivery cost
        delivery_cost = OrderService._calculate_delivery_cost(
            delivery_method, 
            discount_breakdown.final_total
        )
        
        # Prepare order items as JSON
        order_items = []
        for cart_item, product in cart_items:
            price = product.price_300g if cart_item.format == "300g" else product.price_1kg
            order_items.append({
                "product_id": product.id,
                "name": product.name_ua,
                "format": cart_item.format,
                "quantity": cart_item.quantity,
                "price": price,
                "total": price * cart_item.quantity
            })
        
        # Create order
        order = Order(
            user_id=user.id,
            status="pending",
            items=order_items,
            subtotal=discount_breakdown.subtotal,
            discount_volume=discount_breakdown.volume_discount_amount,
            discount_loyalty=discount_breakdown.loyalty_discount_amount,
            discount_promo=discount_breakdown.promo_discount_amount,
            promo_code_used=promo_code_used,
            delivery_cost=delivery_cost,
            total=discount_breakdown.final_total + delivery_cost,
            delivery_method=delivery_method,
            delivery_city=delivery_city,
            delivery_address=delivery_address,
            recipient_name=recipient_name,
            recipient_phone=recipient_phone,
            grind_preference=grind_preference
        )
        
        # Update user's persistent delivery details for next time
        user.delivery_city = delivery_city
        user.last_address = delivery_address
        user.recipient_name = recipient_name
        user.phone = recipient_phone
        
        session.add(order)
        
        # Update promo code usage if used
        if promo_code_obj:
            promo_code_obj.used_count += 1
        
        # Clear cart
        await CartService.clear_cart(session, user.id)
        
        await session.commit()
        await session.refresh(order)
        
        return order
    
    @staticmethod
    def _calculate_delivery_cost(delivery_method: str, order_total: int) -> int:
        """Calculate delivery cost based on method and order total.
        
        Args:
            delivery_method: Delivery method
            order_total: Order total amount
            
        Returns:
            Delivery cost in UAH
        """
        # Free delivery above threshold
        if order_total >= settings.free_delivery_threshold:
            return 0
        
        # Delivery costs by method
        if delivery_method == "nova_poshta":
            return settings.delivery_cost_nova_poshta
        elif delivery_method == "ukrposhta":
            return settings.delivery_cost_ukrposhta
        elif delivery_method == "courier":
            return 100  # Fixed courier cost
        
        return settings.delivery_cost_nova_poshta  # Default
    
    @staticmethod
    async def mark_order_paid(
        session: AsyncSession,
        order_id: int
    ) -> Order:
        """Mark order as paid and trigger post-payment actions.
        
        Args:
            session: Database session
            order_id: Order ID
            
        Returns:
            Updated Order object
        """
        query = select(Order).where(Order.id == order_id)
        result = await session.execute(query)
        order = result.scalar_one_or_none()
        
        if not order:
            raise ValueError("Order not found")
        
        order.status = "paid"
        order.paid_at = datetime.utcnow()
        
        # Update user statistics and loyalty level
        user_query = select(User).where(User.id == order.user_id)
        user_result = await session.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if user:
            # Calculate total kg purchased
            total_kg = 0
            for item in order.items:
                if item['format'] == '300g':
                    total_kg += 0.3 * item['quantity']
                else:
                    total_kg += 1.0 * item['quantity']
            
            # Update loyalty
            level_upgraded, new_level = await LoyaltyService.update_user_level(
                session, user, total_kg
            )
            
            # Update order count and last order date
            user.total_orders += 1
            user.last_order_at = datetime.utcnow()
            
            # Process referral bonus if first order
            if user.total_orders == 1 and user.referred_by_id:
                referrer_query = select(User).where(User.id == user.referred_by_id)
                referrer_result = await session.execute(referrer_query)
                referrer = referrer_result.scalar_one_or_none()
                
                if referrer:
                    # Add bonus to both users
                    user.referral_balance += settings.referral_bonus_amount
                    referrer.referral_balance += settings.referral_bonus_amount
        
        await session.commit()
        await session.refresh(order)
        
        return order
    
    @staticmethod
    async def get_user_orders(
        session: AsyncSession,
        user_id: int,
        limit: int = 10
    ) -> List[Order]:
        """Get user's order history.
        
        Args:
            session: Database session
            user_id: User ID
            limit: Maximum number of orders to return
            
        Returns:
            List of Order objects
        """
        query = (
            select(Order)
            .where(Order.user_id == user_id)
            .where(Order.status != "cancelled")
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_order_by_number(
        session: AsyncSession,
        order_number: str
    ) -> Optional[Order]:
        """Get order by order number.
        
        Args:
            session: Database session
            order_number: Order number (e.g., MC-1234)
            
        Returns:
            Order object or None
        """
        query = select(Order).where(Order.order_number == order_number)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_order_status(
        session: AsyncSession,
        order_id: int,
        new_status: str,
        tracking_number: Optional[str] = None
    ) -> Order:
        """Update order status.
        
        Args:
            session: Database session
            order_id: Order ID
            new_status: New status
            tracking_number: Optional tracking number
            
        Returns:
            Updated Order object
        """
        query = select(Order).where(Order.id == order_id)
        result = await session.execute(query)
        order = result.scalar_one_or_none()
        
        if not order:
            raise ValueError("Order not found")
        
        order.status = new_status
        
        if tracking_number:
            order.tracking_number = tracking_number
        
        if new_status == "shipped":
            order.shipped_at = datetime.utcnow()
        elif new_status == "delivered":
            order.delivered_at = datetime.utcnow()
        
        await session.commit()
        await session.refresh(order)
        
        return order
