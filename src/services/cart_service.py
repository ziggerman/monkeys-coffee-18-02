"""Cart service - business logic for shopping cart operations."""
from typing import List, Tuple, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import CartItem, Product, User
from src.utils.constants import ProductFormat


class CartService:
    """Service for cart operations."""
    
    @staticmethod
    async def get_cart_items(
        session: AsyncSession,
        user_id: int
    ) -> List[Tuple[CartItem, Product]]:
        """Get all cart items for user with product details.
        
        Returns:
            List of (CartItem, Product) tuples
        """
        query = (
            select(CartItem, Product)
            .join(Product, CartItem.product_id == Product.id)
            .where(CartItem.user_id == user_id)
            .order_by(CartItem.added_at)
        )
        
        result = await session.execute(query)
        return result.all()
    
    @staticmethod
    async def add_to_cart(
        session: AsyncSession,
        user_id: int,
        product_id: int,
        format: str,
        quantity: int = 1
    ) -> CartItem:
        """Add product to cart or update quantity if already exists.
        
        Args:
            session: Database session
            user_id: User ID
            product_id: Product ID
            format: Product format (300g or 1kg)
            quantity: Quantity to add
            
        Returns:
            CartItem (new or updated)
        """
        # Check if item already in cart
        query = select(CartItem).where(
            CartItem.user_id == user_id,
            CartItem.product_id == product_id,
            CartItem.format == format
        )
        result = await session.execute(query)
        cart_item = result.scalar_one_or_none()
        
        if cart_item:
            # Update quantity
            cart_item.quantity += quantity
        else:
            # Create new cart item
            cart_item = CartItem(
                user_id=user_id,
                product_id=product_id,
                format=format,
                quantity=quantity
            )
            session.add(cart_item)
        
        await session.commit()
        await session.refresh(cart_item)
        
        return cart_item
    
    @staticmethod
    async def update_quantity(
        session: AsyncSession,
        cart_item_id: int,
        new_quantity: int
    ) -> Optional[CartItem]:
        """Update cart item quantity.
        
        If quantity is 0 or negative, removes item.
        
        Returns:
            Updated CartItem or None if removed
        """
        query = select(CartItem).where(CartItem.id == cart_item_id)
        result = await session.execute(query)
        cart_item = result.scalar_one_or_none()
        
        if not cart_item:
            return None
        
        if new_quantity <= 0:
            await session.delete(cart_item)
            await session.commit()
            return None
        
        cart_item.quantity = new_quantity
        await session.commit()
        await session.refresh(cart_item)
        
        return cart_item
    
    @staticmethod
    async def get_cart_item(
        session: AsyncSession,
        cart_item_id: int
    ) -> Optional[CartItem]:
        """Get single cart item."""
        query = select(CartItem).where(CartItem.id == cart_item_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def change_quantity(
        session: AsyncSession,
        cart_item_id: int,
        delta: int
    ) -> Optional[CartItem]:
        """Change cart item quantity by delta (positive or negative)."""
        cart_item = await CartService.get_cart_item(session, cart_item_id)
        
        if not cart_item:
            return None
            
        new_quantity = cart_item.quantity + delta
        
        if new_quantity <= 0:
            await session.delete(cart_item)
            await session.commit()
            return None
            
        cart_item.quantity = new_quantity
        await session.commit()
        await session.refresh(cart_item)
        
        return cart_item
    
    @staticmethod
    async def remove_item(
        session: AsyncSession,
        cart_item_id: int
    ) -> bool:
        """Remove item from cart.
        
        Returns:
            True if removed, False if not found
        """
        query = select(CartItem).where(CartItem.id == cart_item_id)
        result = await session.execute(query)
        cart_item = result.scalar_one_or_none()
        
        if not cart_item:
            return False
        
        await session.delete(cart_item)
        await session.commit()
        
        return True
    
    @staticmethod
    async def clear_cart(
        session: AsyncSession,
        user_id: int
    ) -> int:
        """Clear all items from user's cart.
        
        Returns:
            Number of items removed
        """
        query = select(CartItem).where(CartItem.user_id == user_id)
        result = await session.execute(query)
        items = result.scalars().all()
        
        count = len(items)
        
        for item in items:
            await session.delete(item)
        
        await session.commit()
        
        return count
    
    @staticmethod
    async def get_cart_count(
        session: AsyncSession,
        user_id: int
    ) -> int:
        """Get total number of items in cart.
        
        Returns:
            Total item count (sum of quantities)
        """
        query = select(CartItem).where(CartItem.user_id == user_id)
        result = await session.execute(query)
        items = result.scalars().all()
        
        return sum(item.quantity for item in items)
    
    @staticmethod
    def calculate_cart_weight(cart_items: List[Tuple[CartItem, Product]]) -> float:
        """Calculate total weight of cart in kg."""
        total_kg = 0.0
        
        for cart_item, product in cart_items:
            if cart_item.format == "300g":
                total_kg += 0.3 * cart_item.quantity
            elif cart_item.format == "1kg":
                total_kg += 1.0 * cart_item.quantity
            else:
                # unit or unknown formats don't contribute to kg-based discounts
                total_kg += 0.0
        
        return total_kg
    
    @staticmethod
    async def restore_cart_from_pending_order(
        session: AsyncSession,
        user_id: int,
        order_items: List[dict]
    ) -> int:
        """Restore items from a pending order back to cart.
        
        Args:
            session: Database session
            user_id: User ID
            order_items: List of item dicts from order.items
            
        Returns:
            Number of items restored
        """
        count = 0
        for item in order_items:
            product_id = item.get('product_id')
            format = item.get('format')
            quantity = item.get('quantity', 1)
            
            if product_id and format:
                await CartService.add_to_cart(
                    session,
                    user_id,
                    product_id,
                    format,
                    quantity
                )
                count += 1
                
        return count
