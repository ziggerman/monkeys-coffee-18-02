
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from src.utils.image_constants import (
    MODULE_ORDERS, 
    MODULE_CART, 
    ASSETS_DIR,
    CATEGORY_UNIVERSAL
)

print(f"Current Working Directory: {os.getcwd()}")
print(f"ASSETS_DIR: {ASSETS_DIR}")
print(f"ASSETS_DIR exists: {ASSETS_DIR.exists()}")
print(f"ASSETS_DIR is dir: {ASSETS_DIR.is_dir()}")

print("-" * 20)
print(f"MODULE_ORDERS path: {MODULE_ORDERS}")
print(f"MODULE_ORDERS exists: {MODULE_ORDERS.exists()}")
print(f"MODULE_ORDERS absolute: {MODULE_ORDERS.absolute()}")

print("-" * 20)
print(f"MODULE_CART path: {MODULE_CART}")
print(f"MODULE_CART exists: {MODULE_CART.exists()}")

print("-" * 20)
print(f"CATEGORY_UNIVERSAL path: {CATEGORY_UNIVERSAL}")
print(f"CATEGORY_UNIVERSAL exists: {CATEGORY_UNIVERSAL.exists()}")

# List dir
print("-" * 20)
if ASSETS_DIR.exists():
    print("Files in ASSETS_DIR:")
    for f in ASSETS_DIR.iterdir():
        print(f" - {f.name}")
else:
    print("ASSETS_DIR does not exist!")
