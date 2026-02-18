# 🎁 Tasting Sets Feature Guide

Complete guide to the Tasting Sets feature - pre-configured coffee bundles with special pricing.

---

## 🎯 Feature Overview

Tasting Sets are curated collections of coffee products bundled together with an additional discount beyond the standard volume discounts.

**Purpose:**
- Introduce customers to multiple coffee varieties
- Increase average order value
- Simplify gift purchasing
- Showcase product range

---

## 📦 What's a Tasting Set?

A tasting set combines:
- **Multiple products** (typically 2-6 different coffees)
- **Fixed format** (usually 300g each)
- **Special pricing** (additional 5-15% discount)
- **Curated selection** (professionally matched profiles)

---

## 🗄️ Database Structure

### TastingSet Model

```python
class TastingSet(Base):
    id: int
    name_ua: str          # Ukrainian name
    name_en: str          # English name
    description: str      # Full description
    product_ids: List[int]  # Array of product IDs
    price: int            # Special bundle price
    discount_percent: int # Additional discount %
    is_active: bool      # Availability
    sort_order: int      # Display order
```

### Example Set

```python
tasting_set = TastingSet(
    name_ua="Набір Espresso Lovers",
    name_en="Espresso Lovers Set",
    description="Три класичних сорти для еспресо",
    product_ids=[1, 2, 5],  # Brazil, Colombia, Guatemala
    price=750,              # vs 810 individually
    discount_percent=10,
    is_active=True,
    sort_order=1
)
```

---

## 🎨 User Interface

### Main Entry Points

**1. Main Menu Button:**
```
🎁 Дегустаційні набори
```

**2. Gift Mode:**
```
🎁 Подарункові набори
```

**3. Promotions Section:**
```
🎁 Акції → Спеціальні набори
```

### Browsing Experience

**Sets List View:**
```
🎁 Дегустаційні набори

Готові підбірки кращих сортів!

1. Набір "Espresso Lovers"
   Три класичних сорти для еспресо
   
   Включає:
     • Бразилія Сантос
     • Колумбія Супремо
     • Гватемала Антигуа
   
   Ціна окремо: 810 грн
   Ціна набору: 750 грн
   💰 Економія: 60 грн (7%)
```

**Detailed View:**
```
🎁 Набір "Espresso Lovers"

Три класичних сорти для еспресо

━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 Склад набору:

1. Бразилія Сантос (300г)
   📍 Бразилія, регіон Сантос
   🌸 Шоколад, Горіхи, Карамель
   💰 270 грн

2. Колумбія Супремо (300г)
   📍 Колумбія, Уїла
   🌸 Цитрус, Карамель, Мигдаль
   💰 290 грн

3. Гватемала Антигуа (300г)
   📍 Гватемала, Антігуа
   🌸 Шоколад, Спеції, Апельсин
   💰 300 грн

━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 Вартість:

При окремій купівлі: 860 грн
Ціна набору: 750 грн

Знижка набору:
████████░░░░ 13%

Ваша економія: 110 грн (13%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ Чому цей набір?

• Професійна підбірка від Q-грейдерів
• Збалансовані смаки
• Спеціальна ціна
• Свіжеобсмажена кава
• Готовий до подарунку

[🛒 Додати набір до кошика]
```

---

## 💡 Pricing Logic

### Discount Calculation

**Step 1: Calculate individual prices**
```python
original_price = sum(product.price_300g for product in products)
# Example: 270 + 290 + 300 = 860 грн
```

**Step 2: Apply set discount**
```python
set_price = original_price * (1 - discount_percent / 100)
# Example: 860 * (1 - 10/100) = 774 грн
# Or custom: set_price = 750 (manually set)
```

**Step 3: Calculate savings**
```python
savings = original_price - set_price
savings_percent = (savings / original_price) * 100
# Example: 860 - 750 = 110 грн (12.8%)
```

### Stacking with Other Discounts

**When added to cart:**
- Tasting set products are added individually
- Standard volume discounts still apply
- Loyalty discounts stack on top
- Result: **Double savings**!

**Example:**
```
Set price: 750 грн (already 13% off)
+ Volume discount (3 packs): 10%
+ Loyalty discount: 5%
= Final: ~630 грн (27% total savings!)
```

---

## 🎁 Gift Presentation Mode

Enhanced presentation for gift scenarios:

```
🎁 Подарункові набори кави

Ідеальний подарунок для кавоманів!

💝 Що входить в подарунок:

✅ Спеціальна подарункова упаковка
✅ Картка з описом кожного сорту
✅ Поради по заварюванню
✅ Персональне привітання
✅ Безкоштовна доставка від 1500 грн
```

---

## 📊 Recommended Sets

### Set Archetypes

**1. Beginner Set (2-3 coffees)**
- Mixed profiles
- Safe, approachable flavors
- Lower price point (600-800 грн)
- 8-10% discount

**2. Explorer Set (4 coffees)**
- Diverse origins
- Different processing methods
- Mid-range (1,000-1,200 грн)
- 10-12% discount

**3. Premium Set (5-6 coffees)**
- High SCA scores
- Exotic origins
- Higher price (1,400-1,800 грн)
- 12-15% discount

### Example Sets to Create

**"Coffee Journey Around the World"**
- Brazil (Americas)
- Ethiopia (Africa)
- Colombia (Americas)
- Kenya (Africa)
Price: 1,200 грн (vs 1,340)

**"Espresso Masters"**
- 3 top espresso blends
- Dark to medium roast
- Classic flavor profiles
Price: 750 грн (vs 850)

**"Filter Coffee Collection"**
- 4 light roast single origins
- Fruity and floral
- V60/Chemex perfect
Price: 1,100 грн (vs 1,240)

---

## 🛠️ Creating Tasting Sets

### Via Admin Panel (Future)

```
Add New Tasting Set:
- Name (UA): [Набір...]
- Name (EN): [Set...]
- Description: [...]
- Select Products: [☑️ Product 1] [☐ Product 2]...
- Pricing:
  • Auto-calculate: ✓
  • Custom price: 750 грн
  • Discount: 10%
- Active: ✓
- Sort Order: 1
```

### Via Database/Script

```python
from src.database.models import TastingSet

tasting_set = TastingSet(
    name_ua="Ваш набір",
    name_en="Your Set",
    description="Опис набору",
    product_ids=[1, 2, 3],  # Product IDs
    price=900,  # Custom price
    discount_percent=12,  # Additional discount
    is_active=True,
    sort_order=1
)

session.add(tasting_set)
await session.commit()
```

---

## 📈 Business Impact

### Expected Metrics

**Conversion Rates:**
- Set view → Add to cart: 35-45%
- Higher than individual products (25-30%)

**Average Order Value:**
- Sets increase AOV by 40-60%
- Customers often add extras

**Gift Sales:**
- 15-25% of total revenue
- Peak during holidays
- Higher margins

### Optimization Tips

**1. Seasonal Sets**
- Summer: Light, fruity coffees
- Winter: Dark, chocolatey blends
- Holidays: Premium, gift-focused

**2. Pricing Strategy**
- Sweet spot: 10-15% discount
- Too low: Devalues products
- Too high: Reduces perceived value

**3. Product Selection**
- Complementary flavor profiles
- Mix of familiar + adventurous
- Consider roast dates (similar freshness)

---

## 🎯 Marketing Integration

### Promotion Ideas

**1. First-Timer Set**
- Special discount for new customers
- Include brewing guide
- Follow-up for feedback

**2. Subscription Preview**
- "Try before you subscribe"
- Sample different roasters
- Discount on subscription signup

**3. Seasonal Specials**
- Limited edition sets
- Holiday themes
- Create urgency

### Cross-Selling

**In Cart:**
```
💡 Добавили окремі сорти?
Розгляньте готовий набір з знижкою!

[Переглянути набори →]
```

**After Purchase:**
```
✅ Дякуємо за замовлення!

Сподобалося? Спробуйте наш дегустаційний
набір зі схожими профілями зі знижкою 15%!
```

---

## ✅ Feature Checklist

### Implemented ✅
- [x] Database model
- [x] Browse tasting sets
- [x] View set details
- [x] Add to cart
- [x] Pricing calculation
- [x] Visual savings display
- [x] Gift presentation mode
- [x] Integration with cart

### Future Enhancements 🔮
- [ ] Admin panel management
- [ ] Customizable sets (user-created)
- [ ] Set ratings/reviews
- [ ] "Build Your Own Set" wizard
- [ ] Gift messaging
- [ ] Gift wrapping options
- [ ] Set recommendations based on history

---

## 🎁 Success Stories

**Use Cases:**

**Corporate Gifts:**
- Bulk orders for clients
- Customized messaging
- Volume discounts stack

**Events:**
- Wedding favors
- Conference gifts
- Thank you gifts

**Personal:**
- Birthday gifts
- Holiday presents
- "Just because" gifts

---

**Your tasting sets feature is ready to drive sales and delight customers! 🎁☕**
