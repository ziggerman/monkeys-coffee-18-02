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

async def seed_products(session):
    print("🌱 Seeding Products...")
    
    # Clear existing products
    await session.execute(delete(Product))
    
    products = [
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
            description="Класика, яку ми любимо. Ідеальна база для твого ранкового капучино або щільного еспресо. Смак рівний, як автобан, солодкий, як перше побачення. Ніякої кислоти, тільки комфорт і затишок.",
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
            description="Той самий 'кавовий' смак, але краще. Соковита, чиста, з приємною фруктовою ноткою, яка не змушує кривитись. Баланс рівня 'Бог'. Підходить і під молоко, і під чорну каву.",
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
            description="Солодка бомба. Обробка 'Хані' додає тягучості і медових відтінків. Це кава, яка обіймає за плечі. Дуже тільна, густа чашка з довгим шоколадним післясмаком.",
            sca_score=85,
            price_300g=440,
            price_1kg=1350,
            is_active=True,
            sort_order=3
        ),
        Product(
            name_ua="Indian Monsoon Malabar",
            name_en="Indian Monsoon Malabar",
            origin="Індія, Малабар",
            processing="Монсунінг",
            roast_level="Espresso",
            profile=CoffeeProfile.ESPRESSO,
            region="Malabar Coast",
            variety="Kents, Catimor",
            altitude="1100-1200м",
            processing_method="Monsooned",
            tasting_notes=["Хлібна скоринка", "Спеції", "Тютюн"],
            description="Кава з характером. Витримується під мусонними вітрами. Смак густий, пряний, з нотами спецій і практично відсутньою кислотністю. Ідеально під молоко для тих, хто любить 'Old School'.",
            sca_score=82,
            price_300g=390,
            price_1kg=1150,
            is_active=True,
            sort_order=9
        ),
        Product(
            name_ua="Burundi Ngozi",
            name_en="Burundi Ngozi",
            origin="Бурунді, Нгозі",
            processing="Митий",
            roast_level="Espresso",
            profile=CoffeeProfile.ESPRESSO,
            region="Ngozi Province",
            variety="Red Bourbon",
            altitude="1700-1800м",
            processing_method="Washed",
            tasting_notes=["Чорний чай", "Лайм", "Червоні ягоди"],
            description="Для тих, хто любить еспресо з кислинкою. Яскрава, соковита, але при цьому щільна. Дуже цікаво розкривається в американо, перетворюючи його на фруктовий еліксир.",
            sca_score=85,
            price_300g=460,
            price_1kg=1450,
            is_active=True,
            sort_order=10
        ),

        # --- UNIVERSAL ---
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
            description="Універсальний солдат. Хочеш в турку — будь ласка. Хочеш в гейзер — супер. Просто в чашку? Теж вогонь. Смак глибокий, з легким ягідним післясмаком і вулканічним характером.",
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
            description="Чиста емоція. Яскрава, дзвінка, але не кисла 'вирви око'. Ідеальна для тих, хто вже втомився від звичайної кави, але ще не готовий до експериментів Ефіопії. Дуже солодкий фініш.",
            sca_score=86,
            price_300g=480,
            price_1kg=1500,
            is_active=True,
            sort_order=5
        ),
        Product(
            name_ua="Peru Cajamarca",
            name_en="Peru Cajamarca",
            origin="Перу, Кахамарка",
            processing="Митий",
            roast_level="Omni",
            profile=CoffeeProfile.UNIVERSAL,
            region="Cajamarca",
            variety="Typica, Caturra",
            altitude="1600-1900м",
            processing_method="Washed",
            tasting_notes=["Мигдаль", "Виноград", "Какао"],
            description="М'яка, як ковдра. Дуже збалансована кава на кожен день. Не набридає, легко п'ється, чудово пасує до сніданку. Делікатна горіхова солодкість у кожному ковтку.",
            sca_score=84,
            price_300g=410,
            price_1kg=1250,
            is_active=True,
            sort_order=11
        ),
        Product(
            name_ua="El Salvador Santa Ana",
            name_en="El Salvador Santa Ana",
            origin="Сальвадор, Санта Ана",
            processing="Хані",
            roast_level="Omni",
            profile=CoffeeProfile.UNIVERSAL,
            region="Apaneca-Ilamatepec",
            variety="Bourbon",
            altitude="1400-1600м",
            processing_method="Honey",
            tasting_notes=["Медова диня", "Горіхи", "Молочний шоколад"],
            description="Дуже солодка чашка. Обробка Хані робить свою справу, залишаючи на губах липку солодкість. Тіло середнє, післясмак довгий і приємний. Справжній 'comfort coffee'.",
            sca_score=85,
            price_300g=460,
            price_1kg=1400,
            is_active=True,
            sort_order=12
        ),

        # --- FILTER ---
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
            description="Це не кава, це чай з кофеїном. Легка, квіткова, неймовірно ароматна. Пити тільки чорною і тільки з насолодою. Якщо ви шукаєте гіркоту - вам не сюди. Есенція жасмину в чашці.",
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
            description="Королева кислотності. Соковита, як свіжовичавлений фреш. Для справжніх гіків і тих, хто любить яскравий смак. Будить краще, ніж будильник. Найяскравіша позиція в нашому меню.",
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
            description="Фанк у чашці. Ферментація робить дива: смак алкогольний, солодкий, дикий. Кава для вечірніх посиденьок або ранкового здивування. Справжній експеримент.",
            sca_score=88,
            price_300g=650,
            price_1kg=2100,
            is_active=True,
            sort_order=8
        ),
        Product(
            name_ua="Colombia Geisha",
            name_en="Colombia Geisha",
            origin="Колумбія, Уіла",
            processing="Митий",
            roast_level="Filter",
            profile=CoffeeProfile.FILTER,
            region="Huila, Pitalito",
            variety="Geisha",
            altitude="1800-1950м",
            processing_method="Washed",
            tasting_notes=["Жасмин", "Персик", "Лайм"],
            description="VIP-ложа у світі кави. Гейша — це завжди свято. Витончена, легка, квіткова. Якщо хочете вразити рецептори (або дівчину) — беріть її. Шовковисте тіло і неймовірна чистота.",
            sca_score=89,
            price_300g=850,
            price_1kg=2800,
            is_active=True,
            sort_order=13
        ),
        Product(
            name_ua="Ethiopia Guji",
            name_en="Ethiopia Guji",
            origin="Ефіопія, Гуджі",
            processing="Натуральна",
            roast_level="Filter",
            profile=CoffeeProfile.FILTER,
            region="Guji Zone",
            variety="Heirloom",
            altitude="2000-2200м",
            processing_method="Natural",
            tasting_notes=["Полуничне варення", "Чорниця", "Молочний шоколад"],
            description="Ягідний вибух. Натуральна обробка дає смак стиглих ягід і джему. Дуже солодка, дуже ароматна. Як десерт, тільки кава. Полуничний профіль, що збиває з ніг.",
            sca_score=86,
            price_300g=550,
            price_1kg=1750,
            is_active=True,
            sort_order=14
        ),
        Product(
            name_ua="Ethiopia Sidamo",
            name_en="Ethiopia Sidamo",
            origin="Ефіопія, Сідамо",
            processing="Митий",
            roast_level="Filter",
            profile=CoffeeProfile.FILTER,
            region="Sidamo District",
            variety="Heirloom",
            altitude="1900-2200м",
            processing_method="Washed",
            tasting_notes=["Чайне дерево", "Лимонна трава", "Персик"],
            description="Класика ефіопського митого профілю. Елегантна, легка, з чіткими чайними нотами. Це кава для тих, хто цінує чистоту і делікатність. Ідеальна для ранкового фільтра.",
            sca_score=85,
            price_300g=490,
            price_1kg=1550,
            is_active=True,
            sort_order=15
        ),
        Product(
            name_ua="Sumatra Mandheling",
            name_en="Sumatra Mandheling",
            origin="Індонезія, Суматра",
            processing="Гілінг-басах",
            roast_level="Espresso",
            profile=CoffeeProfile.ESPRESSO,
            region="Lake Toba",
            variety="Typica, Catimor",
            altitude="1100-1500м",
            processing_method="Wet-Hulled",
            tasting_notes=["Землисті ноти", "Спеції", "Темний цукор"],
            description="Важка артилерія. Специфічна обробка дає неймовірну густину і низьку кислотність. Смак дикий, насичений, з нотами вологого лісу і деревних спецій. Для тих, хто любить максимально 'чоловічу' каву.",
            sca_score=83,
            price_300g=430,
            price_1kg=1300,
            is_active=True,
            sort_order=16
        ),
        Product(
            name_ua="Tanzania Kilimanjaro",
            name_en="Tanzania Kilimanjaro",
            origin="Танзанія, Кіліманджаро",
            processing="Митий",
            roast_level="Filter",
            profile=CoffeeProfile.FILTER,
            region="Moshi",
            variety="N/K, Bourbon",
            altitude="1400-1800м",
            processing_method="Washed",
            tasting_notes=["Виноград", "Чорний чай", "Абрикос"],
            description="Кава з даху Африки. Яскрава кислотність, що нагадує біле вино, і солодкий фруктовий фініш. Дуже структурована чашка, яка змінюється в міру охолодження.",
            sca_score=84,
            price_300g=470,
            price_1kg=1450,
            is_active=True,
            sort_order=17
        ),
        Product(
            name_ua="PNG Sigri",
            name_en="PNG Sigri",
            origin="Папуа-Нова Гвінея",
            processing="Митий",
            roast_level="Omni",
            profile=CoffeeProfile.UNIVERSAL,
            region="Waghi Valley",
            variety="Typica",
            altitude="1500м",
            processing_method="Washed",
            tasting_notes=["Грецький горіх", "Зелений чай", "Персик"],
            description="Дивовижний баланс. Кава з тихоокеанського острова, яка поєднує в собі чистоту Латинської Америки і тільність Індонезії. Дуже м'яка, горіхова і солодка. Універсальна на 100%.",
            sca_score=85,
            price_300g=460,
            price_1kg=1400,
            is_active=True,
            sort_order=18
        ),
        Product(
            name_ua="Panama Geisha",
            name_en="Panama Geisha",
            origin="Панама, Бокет",
            processing="Митий",
            roast_level="Filter",
            profile=CoffeeProfile.FILTER,
            region="Boquete",
            variety="Geisha",
            altitude="1700-2000м",
            processing_method="Washed",
            tasting_notes=["Жасмин", "Бергамот", "Манго"],
            description="Еталон кави. Легендарна Гейша з Панами. Це не просто напій, це парфум у чашці. Неймовірна чистота, витонченість і довгий квітковий післясмак. Кава, за яку борються на аукціонах.",
            sca_score=91,
            price_300g=1200,
            price_1kg=3800,
            is_active=True,
            sort_order=19
        ),
        Product(
            name_ua="Yemen Haraaz",
            name_en="Yemen Haraaz",
            origin="Ємен, Харааз",
            processing="Натуральна",
            roast_level="Omni",
            profile=CoffeeProfile.UNIVERSAL,
            region="Haraaz Mountains",
            variety="Jaidy, Dawairy",
            altitude="1800-2400м",
            processing_method="Natural",
            tasting_notes=["Вино", "Табак", "Сухофрукти"],
            description="Найдавніша кава у світі. Вирощена на терасах єменських гір. Смак дикий, складний, з нотами вина та сушених фруктів. Це кава для тих, хто хоче доторкнутися до історії.",
            sca_score=87,
            price_300g=950,
            price_1kg=3000,
            is_active=True,
            sort_order=20
        ),
        Product(
            name_ua="Mexico Chiapas",
            name_en="Mexico Chiapas",
            origin="Мексика, Чіапас",
            processing="Митий",
            roast_level="Omni",
            profile=CoffeeProfile.UNIVERSAL,
            region="Chiapas Highlands",
            variety="Bourbon, Mundo Novo",
            altitude="1300-1700м",
            processing_method="Washed",
            tasting_notes=["Шоколадний батончик", "Горіхи", "Яблуко"],
            description="Комфортна база. Мексиканська кава відома своєю м'якістю і шоколадним профілем. Це ідеальна кава для офісу або спокійного ранку. Нічого зайвого, тільки якість.",
            sca_score=83,
            price_300g=380,
            price_1kg=1150,
            is_active=True,
            sort_order=21
        ),
        Product(
            name_ua="Bolivia Caranavi",
            name_en="Bolivia Caranavi",
            origin="Болівія, Каранаві",
            processing="Митий",
            roast_level="Filter",
            profile=CoffeeProfile.FILTER,
            region="Yungas",
            variety="Caturra",
            altitude="1500-1700м",
            processing_method="Washed",
            tasting_notes=["Шовковиця", "Жасмин", "Тростинний цукор"],
            description="Рідкісний гість. Болівійська кава — це завжди про витонченість. Солодка, чиста, з ніжними квітковими нотами. Справжній десерт у вашій воронці.",
            sca_score=86,
            price_300g=580,
            price_1kg=1850,
            is_active=True,
            sort_order=22
        ),
        Product(
            name_ua="Uganda Rwenzori",
            name_en="Uganda Rwenzori",
            origin="Уганда, гори Рувензорі",
            processing="Натуральна",
            roast_level="Espresso",
            profile=CoffeeProfile.ESPRESSO,
            region="Rwenzori Mountains",
            variety="SL14, SL28",
            altitude="1600-1800м",
            processing_method="Natural",
            tasting_notes=["Фінік", "Темний виноград", "Спеції"],
            description="Афганська міць. Рувензорі — це гори, де народжується кава з характером. Натуральна обробка дає тягучість і солодкість сухофруктів. Ідеально для міцного еспресо.",
            sca_score=84,
            price_300g=420,
            price_1kg=1250,
            is_active=True,
            sort_order=23
        ),
        Product(
            name_ua="China Yunnan",
            name_en="China Yunnan",
            origin="Китай, Юньнань",
            processing="Митий",
            roast_level="Omni",
            profile=CoffeeProfile.UNIVERSAL,
            region="Pu'er",
            variety="Catimor",
            altitude="1400-1600м",
            processing_method="Washed",
            tasting_notes=["Трав'яні ноти", "Чорний чай", "Персик"],
            description="Екзотичний Схід. Китайська арабіка дивує своїм чайним профілем та трав'янистою свіжістю. Дуже незвична кава для тих, хто вже спробував все.",
            sca_score=84,
            price_300g=440,
            price_1kg=1350,
            is_active=True,
            sort_order=24
        ),
        Product(
            name_ua="Malawi AA Plus",
            name_en="Malawi AA Plus",
            origin="Малаві",
            processing="Митий",
            roast_level="Filter",
            profile=CoffeeProfile.FILTER,
            region="Misuku Hills",
            variety="Geisha, Nyasaland",
            altitude="1800-2000м",
            processing_method="Washed",
            tasting_notes=["Чорниця", "Лайм", "Квітковий мед"],
            description="Алмаз Малаві. Дуже тільна, але при цьому яскрава кава. Має винні відтінки та багатий аромат. Це кава, яку хочеться розгадувати ковток за ковтком.",
            sca_score=87,
            price_300g=560,
            price_1kg=1750,
            is_active=True,
            sort_order=25
        ),
    ]
    
    session.add_all(products)
    await session.commit()
    print(f"✅ Added {len(products)} products")

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
        await seed_products(session)
        await seed_tasting_sets(session)
        await seed_promo_codes(session)
        
    print("🏁 Database Seed Complete!")

if __name__ == "__main__":
    asyncio.run(main())
