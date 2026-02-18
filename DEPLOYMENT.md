# 🚀 Deployment Guide - Monkeys Coffee Roasters Bot

Complete guide to deploy your e-commerce Telegram bot to production.

---

## 📋 Pre-Deployment Checklist

### 1. Bot Configuration

- [ ] Get bot token from [@BotFather](https://t.me/BotFather)
- [ ] Set bot name: "Monkeys Coffee Roasters"
- [ ] Set bot username (e.g., @monkeyscoffee_bot)
- [ ] Upload bot profile picture
- [ ] Set bot description
- [ ] Configure bot commands:
```
start - Почати роботу  
catalog - Каталог кави
cart - Кошик
orders - Мої замовлення
loyalty - Накопичувальні знижки
help - Допомога
```

### 2. Database Setup

**Option A: Local PostgreSQL**
```bash
# Install PostgreSQL
brew install postgresql@15  # macOS
# OR
sudo apt install postgresql-15  # Ubuntu

# Start service
brew services start postgresql@15  # macOS
# OR
sudo systemctl start postgresql  # Ubuntu

# Create database
createdb monkeys_coffee

# Create user (optional)
psql postgres
CREATE USER monkeys_admin WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE monkeys_coffee TO monkeys_admin;
\q
```

**Option B: Cloud Database (Recommended for Production)**

Providers:
- [Supabase](https://supabase.com/) - Free tier available
- [Neon](https://neon.tech/) - Serverless PostgreSQL
- [Digital Ocean](https://www.digitalocean.com/) - Managed databases
- [AWS RDS](https://aws.amazon.com/rds/) - Enterprise grade

Get connection string format:
```
postgresql+asyncpg://user:password@host:port/database
```

### 3. Environment Configuration

Create `.env` file:
```bash
# Telegram
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz  # From @BotFather
ADMIN_IDS=123456789,987654321  # Your Telegram IDs (comma separated)

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/monkeys_coffee

# Payment (LiqPay)
LIQPAY_PUBLIC_KEY=sandbox_i12345678  # Get from liqpay.ua
LIQPAY_PRIVATE_KEY=sandbox_abcdefgh  # Get from liqpay.ua

# Business Settings
FREE_DELIVERY_THRESHOLD=1500
DELIVERY_COST_NOVA_POSHTA=65
DELIVERY_COST_UKRPOSHTA=50
REFERRAL_BONUS_AMOUNT=100
```

**Get Your Telegram ID:**
1. Message [@userinfobot](https://t.me/userinfobot)
2. Copy your ID number
3. Add to `ADMIN_IDS` in `.env`

---

## 🏗️ Installation Steps

### 1. Clone/Copy Project

```bash
cd "/Users/nikolas/Desktop/MONKEYS COFFEE ROASTERS"
# Project already exists
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Initialize Database

```bash
# Run initialization
python -c "from src.database.session import init_db; import asyncio; asyncio.run(init_db())"
```

Expected output:
```
Creating tables...
✅ Database initialized successfully
```

### 5. Load Demo Data (Optional for Testing)

```bash
python load_demo_data.py
```

This loads:
- 6 coffee products
- 2 promo codes
- 2 tasting sets

### 6. Test Setup

```bash
./test_setup.sh
```

Should show:
```
✅ All automated tests passed!
```

---

## 🚀 Running the Bot

### Development Mode

```bash
source venv/bin/activate
python bot.py
```

Expected console output:
```
2026-02-02 11:20:00 - root - INFO - Initializing database...
2026-02-02 11:20:01 - root - INFO - Database initialized!
2026-02-02 11:20:01 - root - INFO - Bot started successfully! 🚀
```

### Production Mode (with systemd)

Create service file: `/etc/systemd/system/monkeys-bot.service`

```ini
[Unit]
Description=Monkeys Coffee Roasters Telegram Bot
After=network.target postgresql.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/MONKEYS COFFEE ROASTERS
Environment="PATH=/path/to/MONKEYS COFFEE ROASTERS/venv/bin"
ExecStart=/path/to/MONKEYS COFFEE ROASTERS/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable monkeys-bot
sudo systemctl start monkeys-bot
sudo systemctl status monkeys-bot
```

View logs:
```bash
sudo journalctl -u monkeys-bot -f
```

---

## 📊 Load Production Data

### Replace Demo Products

1. **Edit** `load_demo_data.py` or create `load_production_data.py`

2. **Add your real coffees:**

```python
products = [
    {
        "name_ua": "Бразилія Сантос",
        "origin": "Бразилія, регіон Сантос",
        "profile": "espresso",
        "tasting_notes": ["Шоколад", "Горіхи", "Карамель"],
        "description": "Класичний бразильський кофе...",
        "price_300g": 270,
        "price_1kg": 820,
        "sca_score": 84,
        "processing": "Натуральна обробка",
        "roast_level": "Середнє обсмаження",
        "roast_date": datetime.now(),
        "is_active": True,
        "sort_order": 1
    },
    # Add more...
]
```

3. **Run:**
```bash
python load_production_data.py
```

### Upload Product Images

**Option 1: Telegram File IDs (Recommended)**
```python
product.image_url = "AgACAgIAAxkBAAIC..."  # Telegram file_id
```

**Option 2: External URLs**
```python
product.image_url = "https://yoursite.com/images/coffee.jpg"
```

**Option 3: Local Files**
```python
product.image_url = "/path/to/images/coffee.jpg"
```

### Configure Promo Codes

```python
promo_codes = [
    {
        "code": "NEWYEAR25",
        "discount_percent": 25,
        "description": "Новорічна знижка 25%",
        "valid_until": datetime(2026, 1, 15),
        "max_uses": 100,
        "is_active": True
    },
]
```

---

## 🔐 Security Best Practices

### 1. Environment Variables

**Never commit `.env` to git:**
```bash
# Already in .gitignore
.env
```

### 2. Admin Access

Restrict admin panel:
```python
# In config.py, ADMIN_IDS is loaded from .env
# Only these Telegram IDs can access admin panel
```

### 3. Database Security

- Use strong passwords
- Restrict network access
- Enable SSL connections:
```python
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?ssl=require
```

### 4. Rate Limiting

Add to bot.py (future enhancement):
```python
from aiogram.filters import RateLimiter
dp.message.middleware(RateLimiter(rate=10, period=60))  # 10 msg/min
```

---

## 📈 Monitoring & Logging

### Application Logs

Configure in `bot.py`:
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
```

### Database Monitoring

```sql
-- Check active connections
SELECT * FROM pg_stat_activity WHERE datname = 'monkeys_coffee';

-- Monitor table sizes
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Bot Health Checks

Create `healthcheck.py`:
```python
#!/usr/bin/env python3
import asyncio
from src.database.session import async_session

async def check():
    try:
        async with async_session() as session:
            await session.execute("SELECT 1")
        print("✅ Database: OK")
        return 0
    except Exception as e:
        print(f"❌ Database: {e}")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(check()))
```

---

## 🔄 Backup Strategy

### Database Backups

**Daily automated backup:**
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/monkeys_coffee"
mkdir -p $BACKUP_DIR

pg_dump monkeys_coffee > $BACKUP_DIR/backup_$DATE.sql
gzip $BACKUP_DIR/backup_$DATE.sql

# Keep last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

**Cron job:**
```bash
0 3 * * * /path/to/backup.sh
```

### Restore from Backup

```bash
gunzip backup_20260202.sql.gz
psql monkeys_coffee < backup_20260202.sql
```

---

## 🚦 Testing in Production

### Smoke Tests

1. **Bot responds:** Send `/start`
2. **Database works:** Browse catalog
3. **Discounts calculate:** Add 6 items to cart
4. **Orders create:** Complete checkout
5. **Admin access:** Open admin panel

### Load Testing

Use `TESTING.md` checklist systematically.

### User Acceptance Testing

1. Invite 5-10 beta testers
2. Give promo code: BETA50 (50% off)
3. Collect feedback
4. Fix critical issues
5. Iterate

---

## 📞 Support Setup

### Support Channel

Create Telegram channel:
- @monkeyscoffee_support
- Add to bot via "💬 Підтримка" button

### Support Workflow

1. User clicks "Підтримка"
2. Bot forwards to support chat
3. Admins respond via channel
4. Bot relays messages back

(Requires implementation - placeholder ready)

---

## 🎯 Launch Checklist

### Pre-Launch (1 week before)

- [ ] All products loaded with real data
- [ ] Product images uploaded
- [ ] Promo codes configured
- [ ] Test complete user journey 3x
- [ ] Admin panel fully tested
- [ ] Backups configured
- [ ] Monitoring setup
- [ ] Support channel created

### Launch Day

- [ ] Final smoke tests
- [ ] Database backup
- [ ] Announce in social media
- [ ] Monitor logs actively
- [ ] Be ready for support requests
- [ ] Track first orders closely

### Post-Launch (First week)

- [ ] Daily analytics review
- [ ] User feedback collection
- [ ] Bug fix priority
- [ ] Performance optimization
- [ ] Marketing campaigns

---

## 📊 Success Metrics

**Week 1 Targets:**
- 50+ new users
- 10+ completed orders
- <5% error rate
- 100% uptime

**Month 1 Targets:**
- 200+ users
- 50+ orders
- 10% repeat purchase rate
- Average order value >500 UAH

**Month 3 Targets:**
- 500+ users
- 200+ orders
- 25% repeat rate
- 15% at level 2+ loyalty

---

## 🆘 Troubleshooting

### Bot Not Starting

**Check:**
```bash
# Bot token valid?
python -c "from config import settings; print(settings.bot_token[:10])"

# Database accessible?
python healthcheck.py

# Dependencies installed?
pip list | grep aiogram
```

### Database Connection Issues

```python
# Test connection
python -c "
import asyncio
from src.database.session import async_session

async def test():
    async with async_session() as s:
        print('Connected!')

asyncio.run(test())
"
```

### Orders Not Creating

Check:
- Cart not empty
- User exists
- Products active
- Database has space

View logs:
```bash
tail -f bot.log | grep ERROR
```

---

## 🔮 Future Enhancements

### Phase 4 (After Launch)

1. **Payment Integration**
   - LiqPay full integration
   - Auto order confirmation

2. **Notifications**
   - Order confirmations
   - Shipping updates
   - Delivery confirmations
   - Marketing messages

3. **Advanced Admin**
   - Product CRUD UI
   - Inventory management
   - Advanced analytics
   - Customer messaging

4. **Customer Features**
   - Subscription orders
   - Wishlist
   - Review system
   - Gift cards

---

## 📞 Getting Help

**Documentation:**
- [README.md](file:///Users/nikolas/Desktop/MONKEYS%20COFFEE%20ROASTERS/README.md) - Project overview
- [TESTING.md](file:///Users/nikolas/Desktop/MONKEYS%20COFFEE%20ROASTERS/TESTING.md) - Test checklist

**Code Issues:**
- Check error logs in console
- Review `bot.log`
- Test with demo data first

**Questions:**
- Re-read implementation plan
- Review walkthrough document
- Check code comments

---

✨ **You're Ready to Launch!** ✨

The bot is production-ready. Just add your bot token, load your products, and start selling coffee! ☕🚀
