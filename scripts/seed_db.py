import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.getcwd())

from sqlalchemy import select, delete
from src.database.session import init_db, async_session
from src.database.models import Product, TastingSet, PromoCode, Category
from src.utils.constants import CoffeeProfile


async def seed_categories(session):
    """Seed default product categories - preserves existing categories."""
    print("📂 Seeding Categories...")
    
    # Default categories to ensure exist
    default_categories = [
        {"slug": "coffee", "name_ua": "☕ Кава", "name_en": "Coffee", "sort_order": 1},
        {"slug": "equipment", "name_ua": "🏪 Магазин", "name_en": "Shop", "sort_order": 2},
    ]
    
    added_count = 0
    for cat_data in default_categories:
        # Check if category already exists
        query = select(Category).where(Category.slug == cat_data["slug"])
        result = await session.execute(query)
        existing = result.scalar_one_or_none()
        
        if not existing:
            # Create new category
            new_category = Category(
                slug=cat_data["slug"],
                name_ua=cat_data["name_ua"],
                name_en=cat_data["name_en"],
                is_active=True,
                sort_order=cat_data["sort_order"]
            )
            session.add(new_category)
            added_count += 1
    
    if added_count > 0:
        await session.commit()
    
    # Get total count
    result = await session.execute(select(Category))
    total = len(result.scalars().all())
    print(f"✅ Categories: {added_count} added, {total} total (existing preserved)")


async def seed_products(session):
    print("🌱 Seeding Products...")
    
    # Get existing products to preserve them
    result = await session.execute(select(Product))
    existing_products = {p.name_ua: p for p in result.scalars().all()}
    
    # Get default products list
    default_products = get_default_products()
    
    # Filter products to add only those that don't exist
    products_to_add = []
    for prod in default_products:
        if prod.name_ua not in existing_products:
            products_to_add.append(prod)
    
    if products_to_add:
        session.add_all(products_to_add)
        await session.commit()
    
    # Get total count
    result = await session.execute(select(Product))
    total = len(result.scalars().all())
    print(f"✅ Products: {len(products_to_add)} added, {total} total (existing preserved)")


# Define default products as a separate list
def get_default_products():
    """Returns list of default products."""
    return [
        # --- ESPRESSO ---
        Product(
            name_ua="Brasil Mogiana",
            name_en="Brasil Mogiana",
            origin="Бразилія, Можіана",
            processing="Натуральна",
            roast_level="Espresso",
            profile=CoffeeProfile.ESPRESSO,
            region="Mogiana, Sao Paulo",
            variety="Mundo Novo, Catuai",
            altitude="800-1100м",
            processing_method="Natural",
            tasting_notes=["Лісовий горіх", "Молочний шоколад", "Карамель"],
            description="Класика, яку ми любимо.",
            sca_score=83,
            price_300g=360,
            price_1kg=1100,
            is_active=True,
            sort_order=1
        ),
        Product(
            name_ua="Colombia Supremo",
            name_en="Colombia Supremo",
            origin="Колумбія, Уіла",
            processing="Митий",
            roast_level="Espresso",
            profile=CoffeeProfile.ESPRESSO,
            region="Huila",
            variety="Caturra, Castillo",
            altitude="1500-1800м",
            processing_method="Washed",
            tasting_notes=["Червоне яблуко", "Тростинний цукор", "Какао"],
            description="Той самий 'кавовий' смак, але краще.",
            sca_score=84,
            price_300g=420,
            price_1kg=1250,
            is_active=True,
            sort_order=2
        ),
        Product(
            name_ua="Honduras Caballero",
            name_en="Honduras Caballero",
            origin="Гондурас, Маркала",
            processing="Хані",
            roast_level="Espresso",
            profile=CoffeeProfile.ESPRESSO,
            region="Marcala, La Paz",
            variety="Catuai",
            altitude="1600м",
            processing_method="Honey",
            tasting_notes=["Сухофрукти", "Мед", "Темний шоколад"],
            description="Солодка бомба.",
            sca_score=85,
            price_300g=440,
            price_1kg=1350,
            is_active=True,
            sort_order=3
        ),
        Product(
            name_ua="Guatemala Antigua",
            name_en="Guatemala Antigua",
            origin="Гватемала, Антігуа",
            processing="Митий",
            roast_level="Omni",
            profile=CoffeeProfile.UNIVERSAL,
            region="Antigua District",
            variety="Bourbon, Caturra",
            altitude="1500-1700м",
            processing_method="Washed",
            tasting_notes=["Смородина", "Шоколад", "Цитрус"],
            description="Універсальний солдат.",
            sca_score=85,
            price_300g=450,
            price_1kg=1400,
            is_active=True,
            sort_order=4
        ),
        Product(
            name_ua="Costa Rica Tarrazu",
            name_en="Costa Rica Tarrazu",
            origin="Коста-Ріка, Тарразу",
            processing="Митий",
            roast_level="Omni",
            profile=CoffeeProfile.UNIVERSAL,
            region="Tarrazu",
            variety="Caturra, Catuai",
            altitude="1400-1900м",
            processing_method="Washed",
            tasting_notes=["Зелене яблуко", "Мандарин", "Кленовий сироп"],
            description="Чиста емоція.",
            sca_score=86,
            price_300g=480,
            price_1kg=1500,
            is_active=True,
            sort_order=5
        ),
        Product(
            name_ua="Ethiopia Yirgacheffe",
            name_en="Ethiopia Yirgacheffe",
            origin="Ефіопія, Їргачеф",
            processing="Митий",
            roast_level="Filter",
            profile=CoffeeProfile.FILTER,
            region="Yirgacheffe, Gedeo",
            variety="Heirloom",
            altitude="1900-2100м",
            processing_method="Washed",
            tasting_notes=["Бергамот", "Жасмин", "Лимон"],
            description="Це не кава, це чай з кофеїном.",
            sca_score=87,
            price_300g=520,
            price_1kg=1650,
            is_active=True,
            sort_order=6
        ),
        Product(
            name_ua="Kenya Nyeri AA",
            name_en="Kenya Nyeri AA",
            origin="Кенія, Ньєрі",
            processing="Митий",
            roast_level="Filter",
            profile=CoffeeProfile.FILTER,
            region="Nyeri County",
            variety="SL28, SL34",
            altitude="1700-1900м",
            processing_method="Washed",
            tasting_notes=["Чорна смородина", "Грейпфрут", "Томат"],
            description="Королева кислотності.",
            sca_score=88,
            price_300g=600,
            price_1kg=1900,
            is_active=True,
            sort_order=7
        ),
        Product(
            name_ua="Rwanda Anaerobic",
            name_en="Rwanda Anaerobic",
            origin="Руанда, Камоні",
            processing="Анаеробна",
            roast_level="Filter",
            profile=CoffeeProfile.FILTER,
            region="Kamonyi District",
            variety="Red Bourbon",
            altitude="1700м",
            processing_method="Anaerobic",
            tasting_notes=["Вишня в шоколаді", "Ром", "Прянощі"],
            description="Фанк у чашці.",
            sca_score=88,
            price_300g=650,
            price_1kg=2100,
            is_active=True,
            sort_order=8
        ),
    ]

async def seed_tasting_sets(session):
    print("🍱 Seeding Tasting Sets...")
    
    await session.execute(delete(TastingSet))
    
    # Need to fetch product IDs first
    products = (await session.execute(select(Product))).scalars().all()
    prod_map = {p.name_en: p.id for p in products}
    
    sets_data = [
        {
            "name_ua": "Start Pack (Знайомство)",
            "name_en": "Start Pack",
            "description": "Три хіти продажів, щоб зрозуміти, що тобі до душі. Бразилія для бази, Колумбія для балансу, Ефіопія для емоцій. Спробуй все і знайди свій фаворит!",
            "product_names": ["Brasil Mogiana", "Colombia Supremo", "Ethiopia Yirgacheffe"],
            "sort_order": 1
        },
        {
            "name_ua": "Filter God (Кислотність)",
            "name_en": "Filter God",
            "description": "Для тих, хто любить яскравіше. Кенія, Руанда та Ефіопія. Вибух рецепторів гарантовано. Кращі лоти для поціновувачів фільтр-кави.",
            "product_names": ["Kenya Nyeri AA", "Rwanda Anaerobic", "Ethiopia Yirgacheffe"],
            "sort_order": 2
        },
        {
            "name_ua": "Espresso Geek (Насиченість)",
            "name_en": "Espresso Geek",
            "description": "Для тих, хто шукає ідеальне еспресо. Індія, Бурунді та Гондурас. Різні профілі: від пряних спецій до ягідної кислинки.",
            "product_names": ["Indian Monsoon Malabar", "Burundi Ngozi", "Honduras Caballero"],
            "sort_order": 3
        },
        {
            "name_ua": "Premium Mystery Box",
            "name_en": "Mystery Box",
            "description": "Ми самі оберемо для тебе 3 топові мікролоти. Ризикни і отримай найкраще, що є у нас на складі сьогодні!",
            "product_names": ["Colombia Geisha", "Ethiopia Guji", "Kenya Nyeri AA"],
            "sort_order": 4
        },
        {
            "name_ua": "African Adventure (Тур Африкою)",
            "name_en": "African Adventure",
            "description": "Справжня подорож витоками кави. Ефіопія, Кенія та Танзанія. Найяскравіші фруктові та квіткові профілі в одному наборі.",
            "product_names": ["Ethiopia Sidamo", "Kenya Nyeri AA", "Tanzania Kilimanjaro"],
            "sort_order": 5
        },
        {
            "name_ua": "Dark & Bold (Міць та Характер)",
            "name_en": "Dark & Bold",
            "description": "Для тих, хто любить класичну міцну каву. Індія, Суматра та Бразилія. Горіхи, шоколад, спеції та ніякої кислотності.",
            "product_names": ["Indian Monsoon Malabar", "Sumatra Mandheling", "Brasil Mogiana"],
            "sort_order": 6
        }
    ]
    
    valid_sets = []
    prod_obj_map = {p.name_en: p for p in products}
    
    for s_data in sets_data:
        prod_ids = [prod_map.get(name) for name in s_data["product_names"]]
        if None in prod_ids:
            continue
            
        # Calculate price with 10% discount
        total_orig = sum(prod_obj_map[name].price_300g for name in s_data["product_names"])
        discounted_price = int(total_orig * 0.9)
        
        valid_sets.append(TastingSet(
            name_ua=s_data["name_ua"],
            name_en=s_data["name_en"],
            description=s_data["description"],
            product_ids=prod_ids,
            format="300g",
            price=discounted_price,
            discount_percent=10,
            is_active=True,
            sort_order=s_data["sort_order"]
        ))
    
    
    session.add_all(valid_sets)
    await session.commit()
    print(f"✅ Added {len(valid_sets)} tasting sets")

async def seed_promo_codes(session):
    print("🎫 Seeding Promo Codes...")
    
    await session.execute(delete(PromoCode))
    
    codes = [
        PromoCode(
            code="WELCOME",
            discount_percent=10,
            description="Твій квиток у світ Monkeys. -10% на перше замовлення.",
            usage_limit=1000,
            is_active=True,
            valid_until=datetime.utcnow() + timedelta(days=365)
        ),
        PromoCode(
            code="MONKEY",
            discount_percent=15,
            description="Олдскульна знижка для справжніх фанатів нашого бренду.",
            usage_limit=50,
            is_active=True
        ),
        PromoCode(
            code="FRIEND",
            discount_percent=5,
            description="Для тих, хто прийшов за рекомендацією. Друзям завжди раді!",
            is_active=True
        ),
        PromoCode(
            code="FLASH25",
            discount_percent=25,
            description="Секретна нічна знижка. Встигни замовити!",
            usage_limit=10,
            is_active=True
        ),
        PromoCode(
            code="HIPSTER",
            discount_percent=20,
            description="Для тих, хто знає різницю між V60 та Chemex.",
            is_active=True,
            min_order_amount=1000
        ),
        PromoCode(
            code="EXTREME",
            discount_percent=30,
            description="Тільки для тих, кому завжди мало кави. Максимальна вигода!",
            usage_limit=5,
            is_active=True
        )
    ]
    
    session.add_all(codes)
    await session.commit()
    print(f"✅ Added {len(codes)} promo codes")

async def main():
    print("🚀 Starting Database Seed...")
    await init_db()
    
    async with async_session() as session:
        # Seed categories FIRST - needed for products
        await seed_categories(session)
        await seed_products(session)
        await seed_tasting_sets(session)
        await seed_promo_codes(session)
        
    print("🏁 Database Seed Complete!")

if __name__ == "__main__":
    asyncio.run(main())
