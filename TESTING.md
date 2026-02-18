# Testing Checklist for Monkeys Coffee Bot

## 1. Environment Setup
- [ ] Create virtual environment: `python3 -m venv venv`
- [ ] Activate: `source venv/bin/activate`
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Configure `.env` with bot token and database URL
- [ ] Verify all imports work: `python -c "from bot import *"`

## 2. Database Setup
- [ ] Ensure PostgreSQL is running
- [ ] Create database: `createdb monkeys_coffee`
- [ ] Initialize tables: `python -c "from src.database.session import init_db; import asyncio; asyncio.run(init_db())"`
- [ ] Load demo data: `python load_demo_data.py`
- [ ] Verify data: Check products, promo codes, tasting sets loaded

## 3. Bot Startup
- [ ] Start bot: `python bot.py`
- [ ] Verify no errors in console
- [ ] Check "Bot started successfully! 🚀" message appears

## 4. User Flow Testing

### Registration & Start
- [ ] Send `/start` to bot
- [ ] Verify welcome message appears
- [ ] Check main menu keyboard shows up
- [ ] Verify user created in database

### Catalog Navigation
- [ ] Click "☕ Каталог кави"
- [ ] Select format (300g or 1kg)
- [ ] Select profile (Espresso, Filter, or Universal)
- [ ] Verify products display correctly
- [ ] Test pagination if more than 3 products
- [ ] Click "Додати до кошика" on a product
- [ ] Verify success message

### Shopping Cart
- [ ] Click "🛒 Кошик"
- [ ] Verify cart shows added items
- [ ] Test quantity controls (+ / -)
- [ ] Verify discounts calculate correctly
- [ ] Check progress bars display
- [ ] Try different quantities to see discount tiers
- [ ] Test "Видалити" button

### Discount Testing
- [ ] Add 3 x 300g items → Verify 10% discount
- [ ] Add 6 x 300g items → Verify 25% discount
- [ ] Add 2 x 1kg items → Verify 25% discount
- [ ] Check loyalty discount if user has level > 1
- [ ] Test promo code entry (use FIRST25 or FRESHDROP)
- [ ] Verify promo code overrides if higher

### Checkout Flow
- [ ] Click "Оформити замовлення" from cart
- [ ] Step 1: Select grind preference
- [ ] Step 2: Select delivery method
- [ ] Step 3: Enter city name
- [ ] Step 4a: Enter delivery address
- [ ] Step 4b: Enter recipient name
- [ ] Step 4c: Enter phone number
- [ ] Step 5: Review order summary
- [ ] Verify all data displays correctly
- [ ] Verify free delivery if >1500 UAH
- [ ] Click "Оплатити"
- [ ] Check placeholder payment message
- [ ] Verify cart cleared after order

### Order History
- [ ] Click "📦 Мої замовлення"
- [ ] Verify order appears in list
- [ ] Click on order to view details
- [ ] Check all information correct
- [ ] Test "Повторити замовлення" button
- [ ] Verify items added back to cart

### Loyalty System
- [ ] Click "🎯 Накопичувальні знижки"
- [ ] Verify loyalty level displays
- [ ] Check progress bars
- [ ] Verify statistics (orders, kg purchased)

### Promotions
- [ ] Click "🎁 Акції"
- [ ] Verify volume discounts displayed
- [ ] Check referral link shows
- [ ] Verify promo codes listed

## 5. Admin Panel Testing

### Access
- [ ] Add your Telegram ID to ADMIN_IDS in .env
- [ ] Restart bot
- [ ] Click "⚙️ Адмін-панель"
- [ ] Verify admin menu appears

### Order Management
- [ ] Click "📦 Управління замовленнями"
- [ ] Test "Очікують оплати" filter
- [ ] Click on an order
- [ ] Click "Підтвердити оплату"
- [ ] Verify status changes to paid
- [ ] Click "Відправити"
- [ ] Enter tracking number
- [ ] Verify order marked as shipped
- [ ] Test "Позначити доставленим"
- [ ] Verify status updates

### Analytics
- [ ] Click "📊 Аналітика та статистика"
- [ ] Test "Загальна статистика"
- [ ] Verify numbers make sense
- [ ] Check alerts appear for pending orders
- [ ] Test "Звіт по знижках"
- [ ] Verify discount breakdown
- [ ] Test "Рівні лояльності"
- [ ] Check distribution
- [ ] Test "Продажі за період"
- [ ] Verify sales data

### Product Management
- [ ] Click "☕ Управління товарами"
- [ ] Click "Список товарів"
- [ ] Verify all products listed
- [ ] Check status indicators

## 6. Error Handling

### Invalid Inputs
- [ ] Try entering invalid phone number in checkout
- [ ] Try entering very short city name
- [ ] Test /cancel during checkout
- [ ] Try accessing admin panel as non-admin

### Edge Cases
- [ ] Empty cart → Try checkout
- [ ] Apply promo code with empty cart
- [ ] Add same product multiple times
- [ ] Try to view non-existent order
- [ ] Test with cart having 10+ items

## 7. Performance & Stability

### Load Testing
- [ ] Add many items to cart (20+)
- [ ] Create multiple orders rapidly
- [ ] Switch between sections quickly
- [ ] Test concurrent users (if possible)

### Memory & Logs
- [ ] Monitor bot logs for errors
- [ ] Check database connections don't leak
- [ ] Verify FSM states clear properly
- [ ] No unhandled exceptions

## 8. Data Verification

### Database Checks
- [ ] Check users table populated correctly
- [ ] Verify orders have correct totals
- [ ] Check loyalty levels update on order completion
- [ ] Verify referral bonuses credited (if applicable)
- [ ] Check promo code usage counts increment

## 9. User Experience

### Message Quality
- [ ] All messages in Ukrainian
- [ ] No placeholder text visible
- [ ] Emoji usage appropriate
- [ ] Formatting clear and readable
- [ ] Button labels make sense

### Navigation
- [ ] Back buttons work everywhere
- [ ] Can return to main menu easily
- [ ] No dead ends in flow
- [ ] Inline keyboards respond quickly

## 10. Production Readiness

### Documentation
- [ ] README.md complete and accurate
- [ ] .env.example has all variables
- [ ] Code comments adequate
- [ ] No TODO or FIXME in critical code

### Security
- [ ] Admin access properly restricted
- [ ] User inputs sanitized
- [ ] No sensitive data in logs
- [ ] Database credentials not hardcoded

### Deployment Prep
- [ ] Requirements.txt complete
- [ ] .gitignore configured
- [ ] No test data in production code
- [ ] Error handling comprehensive

## Issues Found

### Critical (Must Fix)
- [ ] None yet

### Medium (Should Fix)
- [ ] None yet

### Low (Nice to Have)
- [ ] None yet

## Test Results Summary

**Date Tested:** _____________
**Tested By:** _____________
**Overall Status:** ☐ Pass ☐ Fail ☐ Partial

**Notes:**
