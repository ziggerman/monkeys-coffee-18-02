#!/bin/bash

# Quick test script for Monkeys Coffee Bot

echo "🧪 Testing Monkeys Coffee Bot..."
echo ""

# Check Python version
echo "1️⃣ Checking Python version..."
python3 --version
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment exists"
fi
echo ""

# Activate venv and check dependencies
echo "2️⃣ Checking dependencies..."
source venv/bin/activate

# Try importing main modules
python3 << 'EOF'
try:
    import aiogram
    import sqlalchemy
    import pydantic
    print("✅ Core dependencies installed")
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Run: pip install -r requirements.txt")
    exit(1)
EOF

if [ $? -ne 0 ]; then
    exit 1
fi
echo ""

# Check .env file
echo "3️⃣ Checking configuration..."
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found"
    echo "   Copy .env.example to .env and configure it"
    exit 1
else
    echo "✅ .env file exists"
fi
echo ""

# Test imports
echo "4️⃣ Testing Python imports..."
python3 << 'EOF'
try:
    from config import settings
    from src.database import models
    from src.services import discount_engine, cart_service, loyalty_service, order_service
    from src.handlers import start, catalog, cart, checkout, orders, admin
    print("✅ All modules import successfully")
except Exception as e:
    print(f"❌ Import error: {e}")
    exit(1)
EOF

if [ $? -ne 0 ]; then
    echo "Fix import errors before proceeding"
    exit 1
fi
echo ""

# Test config loading
echo "5️⃣ Testing configuration loading..."
python3 << 'EOF'
try:
    from config import settings
    assert settings.bot_token, "BOT_TOKEN not set"
    assert settings.database_url, "DATABASE_URL not set"
    print(f"✅ Configuration loaded")
    print(f"   Database: {settings.database_url.split('@')[0]}@...")
    print(f"   Admins: {len(settings.admin_id_list)} configured")
except Exception as e:
    print(f"❌ Configuration error: {e}")
    exit(1)
EOF

if [ $? -ne 0 ]; then
    exit 1
fi
echo ""

# Test discount engine
echo "6️⃣ Testing discount calculation logic..."
python3 << 'EOF'
from src.services.discount_engine import DiscountEngine
from dataclasses import dataclass

# Mock objects for testing
@dataclass
class MockProduct:
    price_300g: int = 270
    price_1kg: int = 820

@dataclass
class MockCartItem:
    format: str
    quantity: int

@dataclass
class MockUser:
    loyalty_level: int = 1

# Test volume discount (6 packs)
cart_items = [
    (MockCartItem(format="300g", quantity=6), MockProduct())
]
user = MockUser()

result = DiscountEngine.calculate_full_discount(cart_items, user)

assert result.total_packs_300g == 6
assert result.volume_discount_percent == 25, f"Expected 25%, got {result.volume_discount_percent}%"
assert result.final_total < result.subtotal, "Discount not applied"

print(f"✅ Discount engine working correctly")
print(f"   6 packs → {result.volume_discount_percent}% discount")
print(f"   Subtotal: {result.subtotal} → Final: {result.final_total}")
EOF

if [ $? -ne 0 ]; then
    echo "Fix discount engine before proceeding"
    exit 1
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All automated tests passed!"
echo ""
echo "Next steps:"
echo "1. Ensure PostgreSQL is running"
echo "2. Create database: createdb monkeys_coffee"
echo "3. Initialize DB: python -c \"from src.database.session import init_db; import asyncio; asyncio.run(init_db())\""
echo "4. Load demo data: python load_demo_data.py"
echo "5. Start bot: python bot.py"
echo ""
echo "Then follow TESTING.md for manual testing"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
