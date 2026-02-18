import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append("/Users/nikolas/Documents/MONKEYS COFFEE бот")

try:
    from src.utils.image_constants import HERO_BANNER, CATEGORY_UNIVERSAL
    
    print(f"HERO_BANNER path: {HERO_BANNER}")
    print(f"HERO_BANNER exists: {HERO_BANNER.exists()}")
    print(f"HERO_BANNER is absolute: {HERO_BANNER.is_absolute()}")
    
    if not HERO_BANNER.exists():
        print("Listing directory content of parent:")
        parent = HERO_BANNER.parent
        if parent.exists():
            for x in parent.iterdir():
                print(f" - {x.name}")
        else:
            print(f"Parent directory {parent} does not exist!")

except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
