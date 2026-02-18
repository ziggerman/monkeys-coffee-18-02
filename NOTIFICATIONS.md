# 📬 Automated Notifications System

Complete guide to the automated notification system for customer engagement.

---

## 🎯 Overview

The notification system automatically sends personalized messages to customers at optimal times to increase engagement, retention, and sales.

**Total notification types:** 8

**Powered by:** APScheduler + async delivery

---

## 📧 Notification Types

### 1. Order Confirmation (Instant)
**Trigger:** Order marked as paid  
**Purpose:** Confirm successful payment

**Content:**
- Order number
- Total amount
- Delivery details
- Next steps timeline
- Estimated delivery

**Example:**
```
✅ Замовлення #MK-2024-001 підтверджено!

Дякуємо за покупку!

💰 Сума: 1,215 грн
📦 Доставка: Нова Пошта
📍 Адреса: Київ, Відділення №5

Наступні кроки:
1️⃣ Обсмаження (1-2 дні)
2️⃣ Відправка
3️⃣ Трекінг-номер

Очікувані строки: 2-4 дні
```

### 2. Shipping Notification (Instant)
**Trigger:** Tracking number added  
**Purpose:** Notify about shipment

**Content:**
- Tracking number
- Carrier tracking link
- Delivery timeline
- Coffee freshness tip

**Example:**
```
📦 Замовлення #MK-2024-001 відправлено!

Ваша кава вже в дорозі! 🚚

Трекінг-номер: 59000000000000
🔗 Відстежити: [Nova Poshta link]

Очікувані строки: 1-3 дні

💡 Після отримання:
Дайте каві "відпочити" 1-2 дні для
найкращого розкриття смаку!
```

### 3. Replenishment Reminders (Daily at 10:00)
**Trigger:** Last order 20-25 days ago  
**Purpose:** Re-engage customers

**Personalization:**
- Days since last order
- Favorite product
- Current loyalty level
- Exclusive promo code

**Example:**
```
☕ Час поповнити запаси кави!

Минуло вже 23 дні з вашого
останнього замовлення.

💚 Ваша улюблена кава:
Бразилія Сантос

🎁 Ексклюзивна пропозиція:
Промокод COMEBACK15 (15% знижка)
Діє 7 днів.

Ваш рівень: Любитель кави
Знижка: 5%
```

### 4. Volume Discount Suggestions (Daily at 15:00)
**Trigger:** Cart close to discount tier  
**Purpose:** Increase average order value

**Scenarios:**
- 2 packs → Suggest 1 more for 10%
- 3 packs → Suggest 1 more for 15%
- 5 packs → Suggest 1 more for 25%
- 1.5-2.0 kg → Suggest reach 2kg for 25%

**Example:**
```
🎯 Ще 1 пачка = -10%!

У вас в кошику 2 пачки по 300г.
Додайте ще одну - отримаєте знижку 10%!

💰 Економія: ~162 грн

Поточний кошик: 1,620 грн
Знижка після додавання: 10%

Не упустіть вигоду! 🐒
```

### 5. Fresh Roast Announcements (Mon & Thu at 11:00)
**Trigger:** New products roasted  
**Purpose:** Drive immediate purchases

**Personalization:**
- Favorite coffee profile
- Purchase history
- Loyalty discount

**Example:**
```
🔥 Свіжа кава тільки-но з ростера!

Ми знаємо, що ви любите еспресо!

Щойно обсмажені:

Бразилія Сантос
📍 Бразилія, регіон Сантос
🌸 Шоколад, Горіхи, Карамель
📅 Обсмажено: 02.02.2026
💰 Від 270 грн

✨ Чому варто замовити зараз?
• Максимум аромату (перші 3 тижні)
• Ваша накопичувальна знижка: 5%

🎁 Безкоштовна доставка від 1500 грн!
```

### 6. Loyalty Upgrade Notification (Instant)
**Trigger:** User reaches new level  
**Purpose:** Celebrate achievement

**Content:**
- New level achieved
- Total kg purchased
- New benefits
- Progress to next level

**Example:**
```
🎉 Вітаємо! Новий рівень лояльності!

☕ Любитель кави

Ви придбали 5.2 кг нашої кави!

Ваші переваги:
💰 Постійна знижка: 5%
✨ Накопичується з об'ємними знижками

Наступний рівень:
🎓 Кавовий експерт
Знижка: 10%
Залишилось: 9.8 кг
```

### 7. Abandoned Cart Reminder (Daily at 18:00)
**Trigger:** Items in cart, no orders 7+ days  
**Purpose:** Recover lost sales

**Content:**
- Cart value
- Current discounts
- Suggestion to increase discount
- Quick checkout link

**Example:**
```
🛒 Ви забули про свій кошик!

У вас залишилось 3 товари
на суму 1,350 грн

💰 Ваша знижка: 10%
Економія: 150 грн

🎁 Доповніть для більшої знижки!
Ще 3 пачки = знижка 25%

Завершити замовлення → /cart
```

### 8. Order Delivery Confirmation (Future)
**Trigger:** Order marked as delivered  
**Purpose:** Request feedback

*This notification is prepared but not yet activated.*

---

## 📅 Schedule

| Time | Notification | Frequency |
|------|-------------|-----------|
| Instant | Order Confirmation | Per event |
| Instant | Shipping Notification | Per event |
| Instant | Loyalty Upgrade | Per event |
| 10:00 | Replenishment Reminders | Daily |
| 15:00 | Volume Suggestions | Daily |
| 18:00 | Abandoned Cart | Daily |
| 11:00 | Fresh Roast Announcements | Mon & Thu |

**Timezone:** UTC (configure in scheduler.py)

---

## 🎨 Personalization Features

### User History Analysis
- Order frequency
- Favorite products
- Preferred coffee profile
- Purchase patterns
- Loyalty level

### Dynamic Content
- User's name (if available)
- Current loyalty discount
- Days since last order
- Favorite product mentions
- Personalized recommendations

### Smart Filtering
- Don't spam recent customers
- Skip if already ordered
- Respect preferences
- Avoid over-notification

---

## 🔧 Configuration

### Enable/Disable Notifications

Edit `src/services/scheduler.py`:

```python
# Comment out to disable
scheduler.add_job(
    self._send_replenishment_reminders,
    trigger=CronTrigger(hour=10, minute=0),
    # ...
)
```

### Change Schedule Times

```python
# Change hour and minute
trigger=CronTrigger(hour=14, minute=30)  # 2:30 PM

# Change days
trigger=CronTrigger(day_of_week='mon,wed,fri', hour=10)

# Weekly
trigger=CronTrigger(day_of_week='sun', hour=12)
```

### Adjust Targeting Criteria

Edit `src/services/notification_service.py`:

```python
# Replenishment window (currently 20-25 days)
reminder_start = datetime.utcnow() - timedelta(days=25)
reminder_end = datetime.utcnow() - timedelta(days=20)

# Change to 30-35 days
reminder_start = datetime.utcnow() - timedelta(days=35)
reminder_end = datetime.utcnow() - timedelta(days=30)
```

---

## 📊 Expected Impact

### Engagement Metrics

**Replenishment Reminders:**
- Open rate: ~40%
- Click-through rate: ~15%
- Conversion rate: ~8-12%
- Revenue per reminder: 400-600 UAH

**Volume Suggestions:**
- Open rate: ~50%
- Conversion rate: ~20-25%
- Average order increase: +300-500 UAH

**Fresh Roast Announcements:**
- Open rate: ~35%
- Click-through rate: ~12%
- New order rate: ~5-8%

**Abandoned Cart:**
- Recovery rate: ~10-15%
- Revenue recovery: ~20-30%

### Overall Business Impact

**Month 1:**
- +15% repeat purchase rate
- +10% average order value
- +25% customer engagement

**Month 3:**
- +30% repeat purchase rate
- +20% average order value  
- +40% customer lifetime value

---

## 🛠️ Manual Triggers

### For Testing or Special Events

```python
from src.services.scheduler import TaskScheduler

# In admin panel or console:
await scheduler.trigger_replenishment_reminders()
await scheduler.trigger_volume_suggestions()
await scheduler.trigger_fresh_roast_announcements()

# With specific products:
await scheduler.trigger_fresh_roast_announcements(
    product_ids=[1, 2, 3]
)
```

---

## 📈 Monitoring

### Log Messages

All notifications log their activity:

```
2026-02-02 10:00:12 - Sent 23 replenishment reminders
2026-02-02 15:00:08 - Sent 15 volume discount suggestions
2026-02-02 11:00:05 - Sent 45 fresh roast announcements
```

### Performance Metrics

Track in database:
- Notification sent count
- User engagement (clicks)
- Conversion rates
- Opt-out rates

### Admin Dashboard (Future)

Planned features:
- Real-time notification stats
- A/B testing results
- Effectiveness by type
- ROI calculations

---

## 🚫 User Preferences (Future Enhancement)

### Opt-out Options

Allow users to control notifications:
- Frequency preferences
- Type preferences
- Quiet hours
- Complete opt-out

**Implementation:**
Add `notification_preferences` JSON field to User model.

---

## ✨ Best Practices

### 1. Timing
- Morning (10-11 AM) for informational
- Afternoon (3 PM) for upsells
- Evening (6 PM) for reminders
- Avoid late night (after 9 PM)

### 2. Frequency
- Max 1 notification per user per day
- Special events: up to 2
- Space automated messages 4-6 hours apart

### 3. Content
- Always personalized
- Clear value proposition
- Single call-to-action
- Ukrainian language
- Friendly emoji usage

### 4. Testing
- A/B test message variants
- Test timing variations
- Monitor unsubscribe rates
- Adjust based on feedback

---

## 🎯 Success Metrics

**KPIs to Track:**
- Notification delivery rate: >99%
- Open rate: >30%
- Click-through rate: >10%
- Conversion rate: >5%
- Unsubscribe rate: <1%

**Revenue Impact:**
- Additional revenue from notifications
- Customer lifetime value increase
- Repeat purchase rate
- Average order value growth

---

## 🚀 Future Enhancements

### Phase 1 (Implemented)
✅ Order confirmations
✅ Shipping notifications
✅ Replenishment reminders
✅ Volume suggestions
✅ Fresh roast announcements
✅ Loyalty upgrades
✅ Abandoned cart

### Phase 2 (Planned)
- [ ] Delivery confirmations
- [ ] Review requests
- [ ] Birthday messages
- [ ] Anniversary rewards
- [ ] Seasonal campaigns

### Phase 3 (Advanced)
- [ ] AI-powered send time optimization
- [ ] Predictive replenishment
- [ ] Dynamic content generation
- [ ] Multi-channel (email, SMS)
- [ ] Advanced segmentation

---

**Your automated notification system is ready to boost engagement and revenue! 🚀📬**
