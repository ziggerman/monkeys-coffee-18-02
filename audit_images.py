
import os
import imghdr
from pathlib import Path

ASSETS_DIR = Path("assets/images")

print(f"Auditing images in {ASSETS_DIR}...")

if not ASSETS_DIR.exists():
    print(f"Directory {ASSETS_DIR} does not exist.")
    exit(1)

errors_found = False

for file_path in ASSETS_DIR.iterdir():
    if not file_path.is_file():
        continue
    
    if file_path.name.startswith("."):
        continue

    # 1. Check if file is empty
    if file_path.stat().st_size == 0:
        print(f"❌ [EMPTY] {file_path.name} is 0 bytes.")
        errors_found = True
        continue

    # 2. Check actual image type
    try:
        real_type = imghdr.what(file_path)
        ext = file_path.suffix.lower().replace(".", "")
        
        # Map common extensions
        if ext == "jpg": ext = "jpeg"
        
        if real_type is None:
            print(f"❌ [UNKNOWN] {file_path.name}: Could not determine image type.")
            errors_found = True
        elif real_type != ext:
            if real_type == "jpeg" and ext == "png":
                 print(f"⚠️ [MISMATCH] {file_path.name}: Extension is .png but content is JPEG.")
                 errors_found = True
            elif real_type == "png" and ext == "jpeg":
                 print(f"⚠️ [MISMATCH] {file_path.name}: Extension is .jpg but content is PNG.")
                 errors_found = True
            else:
                 print(f"ℹ️ [OK-ISH] {file_path.name}: is {real_type}, ext is {ext}.")
        else:
             print(f"✅ [OK] {file_path.name}")
             
    except Exception as e:
        print(f"❌ [ERROR] {file_path.name}: {e}")
        errors_found = True

if not errors_found:
    print("\n🎉 All images look good!")
else:
    print("\n⚠️ Issues found. See above.")
