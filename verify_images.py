from pathlib import Path
import sys

# Add project root to path
sys.path.append(".")

try:
    from src.utils.image_constants import MODULE_CART, MODULE_ORDERS, ASSETS_DIR
    
    print(f"ASSETS_DIR: {ASSETS_DIR}")
    print(f"ASSETS_DIR exists: {ASSETS_DIR.exists()}")
    print(f"ASSETS_DIR absolute: {ASSETS_DIR.absolute()}")
    
    print(f"MODULE_CART: {MODULE_CART}")
    print(f"MODULE_CART exists: {MODULE_CART.exists()}")
    print(f"MODULE_CART absolute: {MODULE_CART.absolute()}")
    
    print(f"MODULE_ORDERS: {MODULE_ORDERS}")
    print(f"MODULE_ORDERS exists: {MODULE_ORDERS.exists()}")
    
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
