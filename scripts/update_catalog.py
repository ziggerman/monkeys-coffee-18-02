import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.getcwd())

from sqlalchemy import select, delete
from src.database.session import init_db, async_session
from src.database.models import Product, TastingSet, PromoCode
from src.utils.constants import CoffeeProfile

async def update_catalog():
    print("☕ Updating Coffee Catalog & Tasting Sets...")
    await init_db()
    
    async with async_session() as session:
        # Clear existing products and tasting sets
        await session.execute(delete(TastingSet))
        await session.execute(delete(Product))
        
        products_data = [
            {
                "name_ua": "#5 Blend 50/50",
                "name_en": "Blend 50/50",
                "origin": "Купаж Monkeys Coffee",
                "tasting_notes": ["Шоколад", "Сухофрукти", "Горіх"],
                "description": "Збалансований купаж 50/50. Класичний смак з нотками шоколаду, солодких сухофруктів та приємним горіховим післясмаком. Ідеально для еспресо та молочних напоїв.",
                "price_300g": 320,
                "price_1kg": 1060,
                "profile": CoffeeProfile.ESPRESSO,
                "is_active": True,
                "sort_order": 1
            },
            {
                "name_ua": "Colombia Tolima Supremo",
                "name_en": "Colombia Tolima Supremo",
                "origin": "Колумбія, Толіма",
                "tasting_notes": ["Зелене яблуко", "Вишня", "Ірис", "Шоколад"],
                "description": "Вишукана Колумбія з ясним профілем. Відчуйте свіжість зеленого яблука, соковиту вишню та солодкість ірису в поєднанні з шоколадною базою.",
                "price_300g": 390,
                "price_1kg": 1265,
                "profile": CoffeeProfile.UNIVERSAL, # Suits Filter & Espresso
                "is_active": True,
                "sort_order": 2
            },
            {
                "name_ua": "Burundi Gihere (Natural)",
                "name_en": "Burundi Gihere",
                "origin": "Бурунді, Гіере",
                "tasting_notes": ["Агрус", "Білий виноград", "Родзинки"],
                "description": "Натуральна обробка з Бурунді. Яскрава кислотність агрусу, елегантність білого винограду та глибока солодкість родзинок. Справжня насолода для цінителів.",
                "price_300g": 515,
                "price_1kg": 1710,
                "profile": CoffeeProfile.UNIVERSAL, # Others on Espresso/Universal
                "is_active": True,
                "sort_order": 3
            },
            {
                "name_ua": "Decaf Colombia",
                "name_en": "Decaf Colombia",
                "origin": "Колумбія (Be-Decaf)",
                "tasting_notes": ["Апельсин", "Шоколад", "Чорнослив"],
                "description": "Кава без кофеїну, яка не поступається смаком. Яскраві апельсинові ноти, насичений шоколад та оксамитовий чорнослив. Насолоджуйтесь у будь-який час.",
                "price_300g": 435,
                "price_1kg": 1445,
                "profile": CoffeeProfile.UNIVERSAL,
                "is_active": True,
                "sort_order": 4
            },
            {
                "name_ua": "Costa Rica Santa Anita",
                "name_en": "Costa Rica Santa Anita",
                "origin": "Коста-Ріка, Західна Долина",
                "tasting_notes": ["Цитрусові", "Ірис", "Тропічні фрукти", "Ваніль"],
                "description": "Багатий букет з Коста-Ріки. Гармонійне поєднання цитрусових, солодкого ірису, тропічних фруктів та ніжної ванілі.",
                "price_300g": 435,
                "price_1kg": 1445,
                "profile": CoffeeProfile.UNIVERSAL, # Suits Filter & Espresso
                "is_active": True,
                "sort_order": 5
            },
            {
                "name_ua": "Ethiopia Yirgacheffe",
                "name_en": "Ethiopia Yirgacheffe",
                "origin": "Ефіопія, Іргачефф",
                "tasting_notes": ["Сухофрукти", "Цитрус", "Чорний чай"],
                "description": "Класична Ефіопія. Тонкий аромат чорного чаю з легкими цитрусовими нотами та солодкістю сухофруктів. Дуже витончена чашка.",
                "price_300g": 355,
                "price_1kg": 1175,
                "profile": CoffeeProfile.UNIVERSAL, # Others on Espresso/Universal
                "is_active": True,
                "sort_order": 6
            },
            {
                "name_ua": "El Salvador Finca Lorena Anaerobic",
                "name_en": "El Salvador Finca Lorena",
                "origin": "Сальвадор, Серро-Верде",
                "tasting_notes": ["Жовта слива", "Яблуко", "Ожина"],
                "description": "Анаеробна ферментація надає цій каві неймовірної складності. Стигла жовта слива, соковите яблуко та лісова ожина в кожному ковтку.",
                "price_300g": 495,
                "price_1kg": 1675,
                "profile": CoffeeProfile.FILTER, # Filter Only
                "is_active": True,
                "sort_order": 7
            },
            {
                "name_ua": "Costa Rica Juventud",
                "name_en": "Costa Rica Juventud",
                "origin": "Коста-Ріка, Реші",
                "tasting_notes": ["Цитрус", "Смородина", "Какао"],
                "description": "Енергійний профіль. Свіжість цитрусу та смородини врівноважена м'якими нотами какао. Дуже питка та зрозуміла кава.",
                "price_300g": 410,
                "price_1kg": 1360,
                "profile": CoffeeProfile.UNIVERSAL,
                "is_active": True,
                "sort_order": 8
            }
        ]
        
        products = []
        for d in products_data:
            p = Product(**d)
            session.add(p)
            products.append(p)
        
        await session.flush() # To get IDs
        
        # Create Tasting Set from the 3 positions: Colombia, Santa Anita, Salvador
        set_ids = [p.id for p in products if p.name_ua in [
            "Colombia Tolima Supremo", 
            "Costa Rica Santa Anita", 
            "El Salvador Finca Lorena Anaerobic"
        ]]
        
        if len(set_ids) == 3:
            tasting_set = TastingSet(
                name_ua="Дегустаційний набір (3 позиції)",
                name_en="Tasting Set (3 positions)",
                description="Три особливі лоти для поціновувачів вишуканої кави: Колумбія, Коста-Ріка та Сальвадор. Вибух смаку у вашій чашці!",
                product_ids=set_ids,
                format="100g",
                price=550,
                discount_percent=10,
                is_active=True,
                sort_order=1
            )
            session.add(tasting_set)
            print("🍱 Added requested tasting set.")
        
        await session.commit()
        print(f"✅ Successfully updated catalog with {len(products)} products.")

if __name__ == "__main__":
    asyncio.run(update_catalog())
