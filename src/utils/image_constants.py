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


def get_category_image(category: str, session=None) -> Path | None:
    """Get category image path by category name.
    
    Args:
        category: Category slug
        session: Optional DB session to check Category.image_path
    
    Returns:
        Path to the category image or None
    """
    # First check if we have a DB session and category has custom image
    if session:
        from src.database.models import Category
        from sqlalchemy import select
        import asyncio
        
        async def get_db_image():
            query = select(Category).where(Category.slug == category)
            result = await session.execute(query)
            cat = result.scalar_one_or_none()
            if cat and cat.image_path:
                path = Path(cat.image_path)
                if path.exists():
                    return path
            return None
        
        # Try to get from DB
        try:
            # Check if we can use the session synchronously or need async
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in async context, this won't work directly
                # Fall through to static
                pass
            else:
                return asyncio.run(get_db_image())
        except:
            pass
    
    # Fallback to static map
    return CATEGORY_IMAGES.get(category)


async def get_category_image_async(category: str, session) -> Path | None:
    """Get category image path by category name (async version).
    
    Args:
        category: Category slug
        session: AsyncSession for DB access
    
    Returns:
        Path to the category image or None
    """
    from src.database.models import Category
    from sqlalchemy import select
    
    # Check DB first for custom category image
    query = select(Category).where(Category.slug == category)
    result = await session.execute(query)
    cat = result.scalar_one_or_none()
    
    if cat and cat.image_path:
        path = Path(cat.image_path)
        if path.exists():
            return path
    
    # Fallback to static map
    return CATEGORY_IMAGES.get(category)


def convert_image_to_png(input_path: Path, output_path: Path = None) -> Path:
    """Convert HEIC/HEIF or other image formats to PNG.
    
    Args:
        input_path: Path to the input image
        output_path: Path for output PNG (if None, uses same name with .png)
    
    Returns:
        Path to the converted PNG file
    """
    try:
        from PIL import Image
    except ImportError:
        # If PIL not available, just return original path
        return input_path
    
    try:
        with Image.open(input_path) as img:
            # Handle HEIC/HEIF files
            if img.format in ('HEIC', 'HEIF'):
                # Convert RGBA to RGB if necessary
                if img.mode == 'RGBA':
                    # Create white background for transparency
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])  # Use alpha as mask
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
            
            # Determine output path
            if output_path is None:
                output_path = input_path.with_suffix('.png')
            
            # Save as PNG
            img.save(output_path, 'PNG')
            return output_path
    except Exception as e:
        print(f"Error converting image {input_path}: {e}")
        return input_path
