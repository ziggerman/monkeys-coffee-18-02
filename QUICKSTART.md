# 🚀 Quick Start Guide

Get your Monkeys Coffee bot running in **5 minutes**!

---

## Step 1: Get Bot Token (2 min)

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` command
3. Choose a name: `Monkeys Coffee Roasters`
4. Choose username: `monkeyscoffee_bot` (or any available)
5. Copy the bot token (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

## Step 2: Get Your Telegram ID (30 sec)

1. Message [@userinfobot](https://t.me/userinfobot)
2. Copy your ID number (e.g., `123456789`)

## Step 3: Configure Environment (1 min)

Edit `.env` file in the project directory:

```bash
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
ADMIN_IDS=YOUR_TELEGRAM_ID_HERE
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/monkeys_coffee
```

**Don't have PostgreSQL?** See [Local Database Setup](#local-database-setup) below.

## Step 4: Install & Initialize (1 min)

```bash
# Activate virtual environment
source venv/bin/activate

# Dependencies already installed? Skip to next command
# If not: pip install -r requirements.txt

# Initialize database
python -c "from src.database.session import init_db; import asyncio; asyncio.run(init_db())"

# Load demo data
python load_demo_data.py
```

## Step 5: Start Bot! (30 sec)

```bash
python bot.py
```

You should see:
```
2026-02-02 11:20:00 - root - INFO - Initializing database...
2026-02-02 11:20:01 - root - INFO - Database initialized!
2026-02-02 11:20:01 - root - INFO - Bot started successfully! 🚀
```

## Step 6: Test It!

1. Find your bot on Telegram (search for `@monkeyscoffee_bot`)
2. Send `/start`
3. Browse catalog → Add items to cart → See discounts!
4. Try checkout flow (complete order simulation)
5. Access admin panel from main menu

---

## 🎯 What to Test First

### Customer Flow (5 min)
1. ✅ `/start` - Registration
2. ✅ Browse catalog (☕ Каталог кави)
3. ✅ Add 7 items (300g) → See 25% discount
4. ✅ Add 2kg total → See 25% discount
5. ✅ Try promo code: `FIRST25`
6. ✅ Complete checkout
7. ✅ View order history

### Admin Flow (3 min)
1. ✅ Open admin panel (⚙️ Адмін-панель)
2. ✅ View orders
3. ✅ Check analytics
4. ✅ See alerts

---

## 💡 Demo Features

### Products Loaded:
- 🇧🇷 Бразилія Сантос (270/820 UAH)
- 🇨🇴 Колумбія Супремо (290/880 UAH)
- 🇪🇹 Ефіопія Сідамо (310/940 UAH)
- 🇰🇪 Кенія АА (340/1050 UAH)
- 🇬🇹 Гватемала Антигуа (300/900 UAH)
- 🇨🇷 Коста-Ріка Тарразу (285/860 UAH)

### Promo Codes:
- `FIRST25` - 25% off everything
- `FRESHDROP` - 15% off (min 300 UAH)
- `BIGORDER` - 30% off (min 2000 UAH)

### Discount Tiers:
- 7+ packs of 300g = 25% off
- 2+ kg total = 25% off

---

## 🔧 Troubleshooting

### "Database connection failed"

**Option 1: Use SQLite (Quick)**
Change `.env`:
```bash
DATABASE_URL=sqlite+aiosqlite:///./monkeys_coffee.db
```

Then:
```bash
pip install aiosqlite
python -c "from src.database.session import init_db; import asyncio; asyncio.run(init_db())"
```

**Option 2: Install PostgreSQL**
See [Local Database Setup](#local-database-setup) below.

### "Module not found"

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "Bot doesn't respond"

1. Check bot token is correct in `.env`
2. Make sure bot is started (green "Bot started successfully! 🚀")
3. Try `/start` command in Telegram

### "Admin panel doesn't show"

Make sure your Telegram ID is in `.env`:
```bash
ADMIN_IDS=123456789
```

---

## 🗄️ Local Database Setup

### macOS (Homebrew)

```bash
# Install PostgreSQL
brew install postgresql@15

# Start service
brew services start postgresql@15

# Create database
createdb monkeys_coffee

# Update .env
DATABASE_URL=postgresql+asyncpg://$(whoami)@localhost:5432/monkeys_coffee
```

### Ubuntu/Debian

```bash
# Install
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql

# Create database
sudo -u postgres createdb monkeys_coffee
sudo -u postgres createuser $(whoami)

# Update .env
DATABASE_URL=postgresql+asyncpg://$(whoami)@localhost:5432/monkeys_coffee
```

### Windows

1. Download PostgreSQL from [postgresql.org](https://www.postgresql.org/download/windows/)
2. Install with default settings
3. Remember the password you set
4. Open pgAdmin and create database `monkeys_coffee`
5. Update `.env`:
```
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/monkeys_coffee
```

---

## 📊 Testing Checklist

After starting, verify:

- [ ] Bot responds to `/start`
- [ ] Catalog shows 6 products
- [ ] Can add items to cart
- [ ] Discounts calculate correctly
- [ ] Can complete checkout
- [ ] Admin panel accessible (if admin)
- [ ] Analytics show data

**Full testing guide:** See `TESTING.md`

---

## 🎉 You're Live!

Your e-commerce coffee bot is running! 

**Next steps:**
1. Replace demo products with your real coffee
2. Add product images
3. Configure payment gateway (LiqPay)
4. Share bot link with customers

**Need help?** Check:
- `README.md` - Full documentation
- `DEPLOYMENT.md` - Production setup
- `TESTING.md` - Complete test checklist

---

**Enjoy selling coffee with your bot! ☕🚀**
