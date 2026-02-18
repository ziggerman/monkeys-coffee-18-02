"""Image path constants for the bot."""
from pathlib import Path

# Base paths
ASSETS_DIR = Path(__file__).parent.parent.parent / "assets" / "images"

# Hero and banners
HERO_BANNER = ASSETS_DIR / "hero_banner.png"

# Category images
CATEGORY_ESPRESSO = ASSETS_DIR / "category_espresso.png"
CATEGORY_FILTER = ASSETS_DIR / "category_filter.png"
CATEGORY_UNIVERSAL = ASSETS_DIR / "category_universal.png"
CATEGORY_ALL = CATEGORY_UNIVERSAL  # Reuse universal for "all"
MODULE_TASTING_SETS = ASSETS_DIR / "module_tasting_sets.png"
MODULE_LOYALTY = ASSETS_DIR / "module_loyalty.png"
MODULE_SUPPORT = ASSETS_DIR / "module_support.png"
MODULE_ABOUT_US = ASSETS_DIR / "module_about_us.png"
MODULE_PROMOTIONS = ASSETS_DIR / "module_promotions.png"
MODULE_CABINET = ASSETS_DIR / "module_cabinet.png"
MODULE_RECIPES = ASSETS_DIR / "module_recipes.png"
MODULE_CART = ASSETS_DIR / "module_cart.png"
MODULE_CART = ASSETS_DIR / "module_cart.png"
MODULE_ORDERS = ASSETS_DIR / "module_orders.png"
MODULE_CATALOG_MAP = ASSETS_DIR / "module_catalog_map.png"

# Product images mapping (product_id -> image_path)
PRODUCT_IMAGES = {
    1: ASSETS_DIR / "product_brazil_santos.png",
    2: ASSETS_DIR / "product_colombia_supremo.png",
    3: ASSETS_DIR / "product_ethiopia_sidamo.png",
    4: ASSETS_DIR / "product_kenya_aa.png",
    5: ASSETS_DIR / "product_guatemala_antigua.png",
    6: ASSETS_DIR / "product_costa_rica.png",
}

# Category images mapping
CATEGORY_IMAGES = {
    "espresso": CATEGORY_ESPRESSO,
    "filter": CATEGORY_FILTER,
    "universal": CATEGORY_UNIVERSAL,
    "all": CATEGORY_ALL,
}


def get_product_image(product_id: int) -> Path | None:
    """Get product image path by product ID.
    Checks static map first, then falls back to product_{id}.png in assets.
    """
    if product_id in PRODUCT_IMAGES:
        return PRODUCT_IMAGES[product_id]
    
    # Try dynamic lookup
    dynamic_path = ASSETS_DIR / f"product_{product_id}.png"
    if dynamic_path.exists():
        return dynamic_path
        
    return None


def get_category_image(category: str) -> Path | None:
    """Get category image path by category name."""
    return CATEGORY_IMAGES.get(category)
