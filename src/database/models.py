"""SQLAlchemy database models for Monkeys Coffee Roasters bot."""
from datetime import datetime
from typing import Optional, List
import secrets
import string

from sqlalchemy import (
    BigInteger, String, Integer, Float, Boolean, DateTime,
    Text, JSON, ForeignKey, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class User(Base):
    """User model with loyalty tracking."""
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram user ID
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Saved Delivery Details
    delivery_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    recipient_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Loyalty System
    loyalty_level: Mapped[int] = mapped_column(Integer, default=1)
    total_purchased_kg: Mapped[float] = mapped_column(Float, default=0.0)
    total_orders: Mapped[int] = mapped_column(Integer, default=0)
    
    # Referral System
    referral_code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    referred_by_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey('users.id'), nullable=True
    )
    referral_balance: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Active promo code (set when user applies a promo, cleared after order)
    active_promo_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_order_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    cart_items: Mapped[List["CartItem"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    orders: Mapped[List["Order"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    referred_by: Mapped[Optional["User"]] = relationship(
        remote_side=[id], foreign_keys=[referred_by_id]
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.referral_code:
            self.referral_code = self._generate_referral_code()
    
    @staticmethod
    def _generate_referral_code(length: int = 8) -> str:
        """Generate unique referral code."""
        chars = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    def __repr__(self):
        return f"<User {self.id} (@{self.username})>"


class Product(Base):
    """Coffee product model."""
    __tablename__ = 'products'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(50), default='coffee')
    name_ua: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Added missing field
    origin: Mapped[str] = mapped_column(String(255))  # e.g., "Кенія Kiambu AA"
    processing: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    roast_level: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Technical specs for detailed view
    region: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    variety: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    altitude: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    processing_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Profile and characteristics
    profile: Mapped[str] = mapped_column(String(50))  # espresso, filter, universal
    tasting_notes: Mapped[List[str]] = mapped_column(JSON)  # ["Полуниця", "Апельсин", "Мед"]
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sca_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Pricing
    price_300g: Mapped[int] = mapped_column(Integer, nullable=False)  # Price in UAH
    price_1kg: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Metadata
    roast_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_product_profile', 'profile'),
        Index('idx_product_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<Product {self.id}: {self.name_ua}>"


class CartItem(Base):
    """Shopping cart item."""
    __tablename__ = 'cart_items'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False
    )
    
    format: Mapped[str] = mapped_column(String(10))  # "300g" or "1kg"
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    
    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="cart_items")
    product: Mapped["Product"] = relationship()
    
    # Indexes
    __table_args__ = (
        Index('idx_cart_user', 'user_id'),
        Index('idx_cart_user_product', 'user_id', 'product_id', 'format', unique=True),
    )
    
    def __repr__(self):
        return f"<CartItem user={self.user_id} product={self.product_id} qty={self.quantity}>"


class Order(Base):
    """Order model with full tracking."""
    __tablename__ = 'orders'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey('users.id', ondelete='CASCADE'), nullable=False
    )
    
    # Order Status
    status: Mapped[str] = mapped_column(
        String(20), default='pending'
    )  # pending, paid, shipped, delivered, cancelled
    
    # Order Items (stored as JSON)
    items: Mapped[List[dict]] = mapped_column(JSON)  # [{product_id, name, format, qty, price}, ...]
    
    # Pricing Breakdown
    subtotal: Mapped[int] = mapped_column(Integer)  # Before discounts
    discount_volume: Mapped[int] = mapped_column(Integer, default=0)
    discount_loyalty: Mapped[int] = mapped_column(Integer, default=0)
    discount_promo: Mapped[int] = mapped_column(Integer, default=0)
    promo_code_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    delivery_cost: Mapped[int] = mapped_column(Integer)
    total: Mapped[int] = mapped_column(Integer)  # Final amount to pay
    
    # Delivery Information
    delivery_method: Mapped[str] = mapped_column(String(50))  # nova_poshta, ukrposhta, courier
    delivery_city: Mapped[str] = mapped_column(String(255))
    delivery_address: Mapped[str] = mapped_column(String(500))
    recipient_name: Mapped[str] = mapped_column(String(255))
    recipient_phone: Mapped[str] = mapped_column(String(20))
    
    # Coffee preferences
    grind_preference: Mapped[str] = mapped_column(String(50), default='beans')
    
    # Tracking
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="orders")
    
    # Indexes
    __table_args__ = (
        Index('idx_order_user', 'user_id'),
        Index('idx_order_status', 'status'),
        Index('idx_order_created', 'created_at'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.order_number:
            self.order_number = self._generate_order_number()
    
    @staticmethod
    def _generate_order_number() -> str:
        """Generate order number in format MC-XXXX."""
        import random
        return f"MC-{random.randint(1000, 9999)}"
    
    def __repr__(self):
        return f"<Order {self.order_number} user={self.user_id} total={self.total}>"


class PromoCode(Base):
    """Promotional code model."""
    __tablename__ = 'promo_codes'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    
    discount_percent: Mapped[int] = mapped_column(Integer)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Validity
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Usage limits
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    min_order_amount: Mapped[int] = mapped_column(Integer, default=0)  # Added missing field
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    def is_valid(self) -> bool:
        """Check if promo code is currently valid."""
        if not self.is_active:
            return False
        
        now = datetime.utcnow()
        
        if self.valid_from and now < self.valid_from:
            return False
        
        if self.valid_until and now > self.valid_until:
            return False
        
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False
        
        return True
    
    def __repr__(self):
        return f"<PromoCode {self.code} -{self.discount_percent}%>"


class TastingSet(Base):
    """Pre-configured tasting sets."""
    __tablename__ = 'tasting_sets'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_ua: Mapped[str] = mapped_column(String(255))
    name_en: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Added missing field
    description: Mapped[str] = mapped_column(Text)
    
    # Product composition
    product_ids: Mapped[List[int]] = mapped_column(JSON)  # List of product IDs
    format: Mapped[str] = mapped_column(String(10), default="300g")
    
    # Pricing
    price: Mapped[int] = mapped_column(Integer, nullable=False)  # Added missing field
    
    discount_percent: Mapped[int] = mapped_column(Integer, default=10)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<TastingSet {self.name_ua}>"
class ModuleImage(Base):
    """Dynamic module images managed by admin."""
    __tablename__ = 'module_images'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module_name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    file_id: Mapped[str] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class VolumeDiscount(Base):
    """Dynamic volume discount rules."""
    __tablename__ = 'volume_discounts'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    discount_type: Mapped[str] = mapped_column(String(20))  # 'packs' or 'weight'
    threshold: Mapped[float] = mapped_column(Float)
    discount_percent: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class ModuleContent(Base):
    """Dynamic text content for modules managed by admin."""
    __tablename__ = 'module_content'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # e.g. 'cart.empty_text'
    value: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(String(200))  # Admin-facing description
    category: Mapped[str] = mapped_column(String(50), default='general')  # cart, info, catalog
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ModuleContent {self.key}>"


class Category(Base):
    """Product categories managed by admin."""
    __tablename__ = 'categories'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)  # e.g. 'coffee', 'equipment'
    name_ua: Mapped[str] = mapped_column(String(100))
    name_en: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # Image support
    image_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Telegram file_id
    image_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Local path
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Category {self.slug}>"
