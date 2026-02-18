#!/usr/bin/env python3
"""Load demo data into the database for testing."""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import async_session, init_db
from src.database.models import Product, PromoCode, TastingSet


async def load_products(session: AsyncSession):
    """Load demo coffee products."""
    products = [
        Product(
            name_ua="Бразилія Сантос",
            name_en="Brazil Santos",
            origin="Бразилія, регіон Сантос",
            profile="espresso",
            tasting_notes=["Шоколад", "Горіхи", "Карамель"],
            description="Класичний бразильський кофе з м'яким смаком шоколаду та горіхів. Ідеально підходить для еспресо та напоїв на його основі.",
            price_300g=270,
            price_1kg=820,
            sca_score=84,
            processing="Натуральна обробка",
            roast_level="Середнє обсмаження",
            roast_date=datetime.now() - timedelta(days=3),
            is_active=True,
            sort_order=1
        ),
        Product(
            name_ua="Колумбія Супремо",
            name_en="Colombia Supremo",
            origin="Колумбія, Уїла",
            profile="espresso",
            tasting_notes=["Цитрус", "Карамель", "Мигдаль"],
            description="Збалансований колумбійський кофе з яскравою цитрусовою кислинкою та солодкою карамельною базою.",
            price_300g=290,
            price_1kg=880,
            sca_score=86,
            processing="Мита обробка",
            roast_level="Середнє обсмаження",
            roast_date=datetime.now() - timedelta(days=2),
            is_active=True,
            sort_order=2
        ),
        Product(
            name_ua="Ефіопія Сідамо",
            name_en="Ethiopia Sidamo",
            origin="Ефіопія, Сідамо",
            profile="filter",
            tasting_notes=["Чорниця", "Бергамот", "Жасмин"],
            description="Вишуканий ефіопський кофе з квітковими нотами та яскравою ягідною кислинкою. Ідеальний для альтернативних методів заварювання.",
            price_300g=310,
            price_1kg=940,
            sca_score=88,
            processing="Мита обробка",
            roast_level="Світле обсмаження",
            roast_date=datetime.now() - timedelta(days=1),
            is_active=True,
            sort_order=3
        ),
        Product(
            name_ua="Кенія АА",
            name_en="Kenya AA",
            origin="Кенія, Ньєрі",
            profile="filter",
            tasting_notes=["Чорна смородина", "Грейпфрут", "Вино"],
            description="Преміальний кенійський кофе з інтенсивною кислинкою чорної смородини та складним винним післясмаком.",
            price_300g=340,
            price_1kg=1050,
            sca_score=90,
            processing="Мита обробка",
            roast_level="Світле обсмаження",
            roast_date=datetime.now() - timedelta(days=2),
            is_active=True,
            sort_order=4
        ),
        Product(
            name_ua="Гватемала Антигуа",
            name_en="Guatemala Antigua",
            origin="Гватемала, Антігуа",
            profile="universal",
            tasting_notes=["Шоколад", "Спеції", "Апельсин"],
            description="Універсальний кофе з вулканічних ґрунтів Антігуа. Чудовий баланс солодкості, кислинки та тіла.",
            price_300g=300,
            price_1kg=900,
            sca_score=85,
            processing="Мита обробка",
            roast_level="Середнє обсмаження",
            roast_date=datetime.now() - timedelta(days=4),
            is_active=True,
            sort_order=5
        ),
        Product(
            name_ua="Коста-Ріка Тарразу",
            name_en="Costa Rica Tarrazu",
            origin="Коста-Ріка, Тарразу",
            profile="universal",
            tasting_notes=["Мед", "Яблуко", "Карамель"],
            description="М'який та збалансований кофе з медовою солодкістю та легкою яблучною кислинкою.",
            price_300g=285,
            price_1kg=860,
            sca_score=86,
            processing="Мед обробка",
            roast_level="Середнє обсмаження",
            roast_date=datetime.now() - timedelta(days=3),
            is_active=True,
            sort_order=6
        ),
    ]
    
    session.add_all(products)
    await session.commit()
    print(f"✅ Loaded {len(products)} products")


async def load_promo_codes(session: AsyncSession):
    """Load demo promo codes."""
    promo_codes = [
        PromoCode(
            code="FIRST25",
            discount_percent=25,
            description="Знижка 25% на перше замовлення",
            valid_from=datetime.now() - timedelta(days=30),
            valid_until=datetime.now() + timedelta(days=60),
            usage_limit=100,
            used_count=0,
            min_order_amount=0,
            is_active=True
        ),
        PromoCode(
            code="FRESHDROP",
            discount_percent=15,
            description="Свіжообсмажена кава - знижка 15%",
            valid_from=datetime.now() - timedelta(days=7),
            valid_until=datetime.now() + timedelta(days=23),
            usage_limit=50,
            used_count=0,
            min_order_amount=300,
            is_active=True
        ),
        PromoCode(
            code="BIGORDER",
            discount_percent=30,
            description="Великі замовлення - знижка 30%",
            valid_from=datetime.now(),
            valid_until=datetime.now() + timedelta(days=90),
            usage_limit=None,  # Unlimited
            used_count=0,
            min_order_amount=2000,
            is_active=True
        ),
    ]
    
    session.add_all(promo_codes)
    await session.commit()
    print(f"✅ Loaded {len(promo_codes)} promo codes")


async def load_tasting_sets(session: AsyncSession):
    """Load demo tasting sets."""
    tasting_sets = [
        TastingSet(
            name_ua="Набір Espresso Lovers",
            name_en="Espresso Lovers Set",
            description="Три класичних сорти для еспресо: Бразилія, Колумбія та Гватемала",
            product_ids=[1, 2, 5],  # IDs will be set after products are loaded
            price=750,
            discount_percent=10,
            is_active=True,
            sort_order=1
        ),
        TastingSet(
            name_ua="Набір Filter Coffee",
            name_en="Filter Coffee Set",
            description="Вишукані африканські сорти: Ефіопія та Кенія",
            product_ids=[3, 4],
            price=600,
            discount_percent=8,
            is_active=True,
            sort_order=2
        ),
    ]
    
    session.add_all(tasting_sets)
    await session.commit()
    print(f"✅ Loaded {len(tasting_sets)} tasting sets")


async def main():
    """Main function to load all demo data."""
    print("🔧 Initializing database...")
    await init_db()
    
    print("\n📦 Loading demo data...\n")
    
    async with async_session() as session:
        # Check if data already exists
        from sqlalchemy import select
        result = await session.execute(select(Product))
        existing_products = result.scalars().all()
        
        if existing_products:
            print("⚠️  Products already exist in database!")
            response = input("Do you want to clear and reload all data? (yes/no): ")
            if response.lower() != 'yes':
                print("Cancelled.")
                return
            
            # Clear existing data
            print("\n🗑️  Clearing existing data...")
            from sqlalchemy import text
            await session.execute(text("DELETE FROM tasting_sets"))
            await session.execute(text("DELETE FROM promo_codes"))
            await session.execute(text("DELETE FROM cart_items"))
            await session.execute(text("DELETE FROM orders"))
            await session.execute(text("DELETE FROM products"))
            await session.commit()
            print("✅ Cleared existing data")
        
        # Load new data
        await load_products(session)
        await load_promo_codes(session)
        await load_tasting_sets(session)
    
    print("\n" + "="*50)
    print("✅ Demo data loaded successfully!")
    print("="*50)
    print("\nYou can now:")
    print("  1. Start the bot: python bot.py")
    print("  2. Test with /start command")
    print("  3. Browse catalog and test features")
    print("\nDemo promo codes:")
    print("  • FIRST25 - 25% off (no minimum)")
    print("  • FRESHDROP - 15% off (min 300 UAH)")
    print("  • BIGORDER - 30% off (min 2000 UAH)")
    print()


if __name__ == "__main__":
    asyncio.run(main())
