#!/usr/bin/env python3
"""Helper script to organize and copy UI images to the project."""
import os
import shutil
from pathlib import Path

# Paths
BRAIN_DIR = "/Users/nikolas/.gemini/antigravity/brain/73412149-4dec-47f8-8675-4f80bc6f57a9"
PROJECT_DIR = "/Users/nikolas/Documents/MONKEYS COFFEE бот"
ASSETS_DIR = os.path.join(PROJECT_DIR, "assets", "images")

# Image mappings
IMAGES = {
    "hero_banner_1771171375327.png": "hero_banner.png",
    "category_espresso_1771171390052.png": "category_espresso.png",
    "category_filter_1771171403395.png": "category_filter.png",
    "category_universal_1771171422203.png": "category_universal.png",
    "product_brazil_santos_1771171447699.png": "product_brazil_santos.png",
    "product_colombia_supremo_1771171461491.png": "product_colombia_supremo.png",
}


def setup_assets_directory():
    """Create assets directory if it doesn't exist."""
    Path(ASSETS_DIR).mkdir(parents=True, exist_ok=True)
    print(f"✅ Created assets directory: {ASSETS_DIR}")


def copy_images():
    """Copy images from brain directory to project assets."""
    copied = 0
    for source_name, dest_name in IMAGES.items():
        source_path = os.path.join(BRAIN_DIR, source_name)
        dest_path = os.path.join(ASSETS_DIR, dest_name)
        
        if os.path.exists(source_path):
            shutil.copy2(source_path, dest_path)
            print(f"✅ Copied: {dest_name}")
            copied += 1
        else:
            print(f"⚠️  Not found: {source_name}")
    
    print(f"\n📊 Total images copied: {copied}/{len(IMAGES)}")


def create_image_constants():
    """Create a constants file for image paths."""
    constants_content = '''"""Image path constants for the bot."""
from pathlib import Path

# Base paths
ASSETS_DIR = Path(__file__).parent.parent / "assets" / "images"

# Hero and banners
HERO_BANNER = ASSETS_DIR / "hero_banner.png"

# Category images
CATEGORY_ESPRESSO = ASSETS_DIR / "category_espresso.png"
CATEGORY_FILTER = ASSETS_DIR / "category_filter.png"
CATEGORY_UNIVERSAL = ASSETS_DIR / "category_universal.png"

# Product images mapping (product_id -> image_path)
PRODUCT_IMAGES = {
    1: ASSETS_DIR / "product_brazil_santos.png",
    2: ASSETS_DIR / "product_colombia_supremo.png",
    3: ASSETS_DIR / "product_ethiopia_sidamo.png",  # To be generated
    4: ASSETS_DIR / "product_kenya_aa.png",  # To be generated
    5: ASSETS_DIR / "product_guatemala_antigua.png",  # To be generated
    6: ASSETS_DIR / "product_costa_rica.png",  # To be generated
}

# Category images mapping
CATEGORY_IMAGES = {
    "espresso": CATEGORY_ESPRESSO,
    "filter": CATEGORY_FILTER,
    "universal": CATEGORY_UNIVERSAL,
}


def get_product_image(product_id: int) -> Path | None:
    """Get product image path by product ID."""
    return PRODUCT_IMAGES.get(product_id)


def get_category_image(category: str) -> Path | None:
    """Get category image path by category name."""
    return CATEGORY_IMAGES.get(category)
'''
    
    constants_path = os.path.join(PROJECT_DIR, "src", "utils", "image_constants.py")
    with open(constants_path, "w", encoding="utf-8") as f:
        f.write(constants_content)
    
    print(f"✅ Created image constants: {constants_path}")


def main():
    """Main function."""
    print("🎨 Setting up UI images for Monkeys Coffee Bot\n")
    
    setup_assets_directory()
    print()
    
    copy_images()
    print()
    
    create_image_constants()
    print()
    
    print("=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Generate remaining product images using prompts in ui_images_guide.md")
    print("2. Update bot handlers to use images (see examples in guide)")
    print("3. Import image constants: from src.utils.image_constants import *")
    print()


if __name__ == "__main__":
    main()
