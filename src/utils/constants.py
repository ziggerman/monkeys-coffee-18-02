"""Utility constants and enums for the bot."""
from enum import Enum


class OrderStatus(str, Enum):
    """Order status values."""
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class DeliveryMethod(str, Enum):
    """Delivery method options."""
    NOVA_POSHTA = "nova_poshta"
    UKRPOSHTA = "ukrposhta"
    COURIER = "courier"


class GrindType(str, Enum):
    """Coffee grind preferences."""
    BEANS = "beans"
    FINE = "fine"
    MEDIUM = "medium"
    COARSE = "coarse"


class ProductFormat(str, Enum):
    """Product format options."""
    PACK_300G = "300g"
    KG_1 = "1kg"
    UNIT = "unit"


class ProductCategory(str, Enum):
    """Product category types."""
    COFFEE = "coffee"
    EQUIPMENT = "equipment"


class CoffeeProfile(str, Enum):
    """Coffee profile categories."""
    ESPRESSO = "espresso"
    FILTER = "filter"
    UNIVERSAL = "universal"


# Callback data prefixes for inline keyboards
class CallbackPrefix:
    """Callback data prefixes for routing."""
    # Catalog
    CATALOG_FORMAT = "cat_fmt:"
    CATALOG_PROFILE = "cat_prof:"
    CATALOG_PRODUCT = "cat_prod:"
    CATALOG_PAGE = "cat_page:"
    CATALOG_ADD = "cat_add:"
    
    # Cart
    CART_VIEW = "cart_view"
    CART_INCREASE = "cart_inc:"
    CART_DECREASE = "cart_dec:"
    CART_REMOVE = "cart_rm:"
    CART_CHECKOUT = "cart_checkout"
    CART_PROMO = "cart_promo"
    
    # Orders
    ORDER_VIEW = "order_view:"
    ORDER_REPEAT = "order_repeat:"
    ORDER_PAGE = "order_page:"
    
    # Loyalty
    LOYALTY_VIEW = "loyalty_view"
    
    # Promotions
    PROMO_REFERRAL = "promo_ref"
    PROMO_CODES = "promo_codes"
    
    # Tasting Sets
    SET_VIEW = "set_view:"
    SET_ADD = "set_add:"
    SET_CUSTOMIZE = "set_custom:"
    
    # Admin
    ADMIN_ORDERS = "adm_orders"
    ADMIN_PRODUCTS = "adm_products"
    ADMIN_ANALYTICS = "adm_analytics"
    ADMIN_ORDER_UPDATE = "adm_ord_upd:"


# Display names mapping
DELIVERY_METHOD_NAMES = {
    DeliveryMethod.NOVA_POSHTA: "Нова Пошта",
    DeliveryMethod.UKRPOSHTA: "Укрпошта",
    DeliveryMethod.COURIER: "Кур'єр",
}

GRIND_TYPE_NAMES = {
    GrindType.BEANS: "⚫ В зернах",
    GrindType.FINE: "☕ Дрібний помел",
    GrindType.MEDIUM: "☕ Середній помел",
    GrindType.COARSE: "☕ Грубий помел",
}

ORDER_STATUS_NAMES = {
    OrderStatus.PENDING: "🔴 Очікує оплати",
    OrderStatus.PAID: "⚫ Оплачено",
    OrderStatus.SHIPPED: "🚚 Відправлено",
    OrderStatus.DELIVERED: "✅ Доставлено",
    OrderStatus.CANCELLED: "❌ Скасовано",
}


class UIStyle:
    """Standard UI elements for the bot."""
    # Colors
    BLACK = "⚫"
    RED = "🔴"
    WHITE = "⚪"
    
    # Symbols
    SUCCESS = "✅"
    WARNING = "⚠️"
    ERROR = "❌"
    INFO = "ℹ️"
    
    # Navigation
    BACK = "←"
    NEXT = "➜"
    HOME = "🏠"
    CART = "🛒"
    
    # Dividers
    DIVIDER = "────────────────"
    BOLD_DIVIDER = "━━━━━━━━━━━━━━━━"
    
    # Brand
    MONKEY = "🐒"
    COFFEE = "☕"
    SPARKLES = "✨"
