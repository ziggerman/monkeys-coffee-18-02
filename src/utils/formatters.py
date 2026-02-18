"""Message formatting utilities."""
from typing import List, Dict, Any
from datetime import datetime


def format_currency(amount: int) -> str:
    """Format amount in UAH with thousand separators."""
    return f"{amount:,} грн".replace(",", " ")


def format_progress_bar(current: float, target: float, length: int = 12) -> str:
    """Generate visual progress bar.
    
    Args:
        current: Current value
        target: Target value
        length: Length of progress bar in characters
        
    Returns:
        Progress bar string like [████████░░░░]
    """
    if target == 0:
        return "[" + "░" * length + "]"
    
    filled = int((current / target) * length)
    filled = min(filled, length)
    
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}]"


def format_discount_info(
    volume_discount: int,
    loyalty_discount: int,
    promo_discount: int = 0
) -> str:
    """Format discount breakdown for display."""
    lines = []
    
    if volume_discount > 0:
        lines.append(f"✅ Об'ємна знижка {volume_discount}%")
    
    if loyalty_discount > 0:
        lines.append(f"✅ Накопичувальна {loyalty_discount}%")
    
    if promo_discount > 0:
        lines.append(f"✅ Промокод {promo_discount}%")
    
    return "\n".join(lines) if lines else "Знижок поки немає"


def format_tasting_notes(notes: List[str]) -> str:
    """Format tasting notes with emojis."""
    emoji_map = {
        "полуниця": "🍓",
        "апельсин": "🍊",
        "мед": "🍯",
        "чорний чай": "☕",
        "шоколад": "🍫",
        "карамель": "🍬",
        "горіхи": "🥜",
        "ягоди": "🫐",
        "квіти": "🌸",
        "цитрус": "🍋",
    }
    
    formatted = []
    for note in notes:
        note_lower = note.lower()
        emoji = next((e for k, e in emoji_map.items() if k in note_lower), "•")
        formatted.append(f"{emoji} {note}")
    
    return " · ".join(formatted)


def format_date(dt: datetime, format_type: str = "short") -> str:
    """Format datetime in Ukrainian locale.
    
    Args:
        dt: Datetime object
        format_type: 'short' (28.01.2025) or 'long' (28 січня 2025)
    """
    if format_type == "short":
        return dt.strftime("%d.%m.%Y")
    
    months_ua = [
        "січня", "лютого", "березня", "квітня", "травня", "червня",
        "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"
    ]
    
    return f"{dt.day} {months_ua[dt.month - 1]} {dt.year}"


def format_cart_summary(
    items_count: int,
    total_weight_kg: float,
    subtotal: int
) -> str:
    """Format cart summary for quick view."""
    return f"🛒 У кошику: {items_count} товарів ({total_weight_kg:.1f} кг) · {format_currency(subtotal)}"


def format_order_items(items: List[Dict[str, Any]]) -> str:
    """Format order items list."""
    lines = []
    for idx, item in enumerate(items, 1):
        name = item['name']
        format_str = item['format']
        qty = item['quantity']
        price = item['price']
        total = qty * price
        
        lines.append(
            f"{idx}. {name} ({format_str}) × {qty} = {format_currency(total)}"
        )
    
    return "\n".join(lines)


def pluralize_ua(count: int, forms: tuple) -> str:
    """Get correct Ukrainian plural form.
    
    Args:
        count: Number to pluralize
        forms: Tuple of (one, few, many) forms
            e.g., ("пачка", "пачки", "пачок")
    """
    if count % 10 == 1 and count % 100 != 11:
        return forms[0]
    elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
        return forms[1]
    else:
        return forms[2]


def format_weight(weight_kg: float) -> str:
    """Format weight for display."""
    if weight_kg < 1:
        grams = int(weight_kg * 1000)
        return f"{grams} г"
    else:
        return f"{weight_kg:.1f} кг"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to max length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


async def generate_product_description(
    name: str, 
    notes: List[str] = None, 
    origin: str = None, 
    roast: str = None, 
    processing: str = None,
    price_300g: int = 0,
    price_1kg: int = 0
) -> str:
    """Generate a concise, AI-powered or template-based coffee description."""
    import random
    from src.services.ai_service import ai_service
    
    # Safety checks
    if not name:
        name = "Кава"
    if not notes:
        notes = ["смачна кава"]
    
    notes_str = ", ".join(notes).lower() if isinstance(notes, list) else str(notes).lower()
    origin_part = f" (<b>{origin}</b>)" if origin else ""
    roast_lower = (roast or "").lower()
    
    # Try AI first (Professional Mode)
    from src.services.ai_service import logger as ai_logger
    ai_logger.info(f"Generating description for {name}...")
    
    ai_narrative = await ai_service.generate_professional_description(
        name=name,
        origin=origin or "Секретна локація",
        roast=roast or "Універсальна",
        notes=notes,
        processing=processing or "Класична"
    )
    
    if ai_narrative:
        ai_logger.info(f"AI description generated for {name}")
        base_text = ai_narrative
    else:
        # --- FALLBACK TEMPLATES (in case AI fails or no API key) ---
        ai_logger.warning(f"AI failed for {name}, using templates.")
        
        # 1. ESPRESSO
        espresso_templates = [
            f"🍫 <b>{name}</b>{origin_part}. Класичний густий смак з нотками <b>{notes_str}</b>. \n💡 <i>Порада:</i> Ідеально для капучино — буде солодко і без гіркоти! 🥛",
            f"🔥 <b>{name}</b>{origin_part}. Заряд енергії з відтінками <b>{notes_str}</b>. \n💡 <i>Порада:</i> Найкращий вибір для ранкової чашки або гейзера. 🦍⚙️",
            f"☕ <b>{name}</b>{origin_part}. Баланс шоколаду та <b>{notes_str}</b>. \n💡 <i>Порада:</i> Додай молока, щоб розкрити всю лагідність цього лоту. 🍫🍯"
        ]
        
        # 2. FILTER
        filter_templates = [
            f"🍋 <b>{name}</b>{origin_part}. Легка, як чай, з соковитими нотами <b>{notes_str}</b>. \n💡 <i>Порада:</i> Пий чорною, щоб відчути справжній фруктовий сік! ✨",
            f"🌸 <b>{name}</b>{origin_part}. Вишуканий профіль з ароматом <b>{notes_str}</b>. \n💡 <i>Порада:</i> Для тих, хто любить делікатну кислинку та свіжість. 🍓🍃",
            f"🌈 <b>{name}</b>{origin_part}. М'яка кава з цікавим поєднанням <b>{notes_str}</b>. \n💡 <i>Порада:</i> Дай їй трохи охолонути — стане ще солодшою! 🍋🌸"
        ]
        
        # 3. OMNI / UNIVERSAL
        universal_templates = [
            f"⚔️ <b>{name}</b>{origin_part}. Універсальний лот: нотки <b>{notes_str}</b> та ідеальний баланс. \n💡 <i>Порада:</i> Якщо не знаєш, що обрати — це твій безпрограшний варіант! ✅",
            f"⚖️ <b>{name}</b>{origin_part}. Золота середина: солодкість та <b>{notes_str}</b> без зайвої гіркоти. \n💡 <i>Порада:</i> Заварюй як зручно — вона завжди смакує добре. ✨☕",
            f"🐒 <b>{name}</b>{origin_part}. Гнучкий профіль з міксом <b>{notes_str}</b>. \n💡 <i>Порада:</i> М'яка і зрозуміла кава на будь-який час доби. ✌️☕"
        ]
        
        # Selection
        if "еспресо" in roast_lower or "espresso" in roast_lower:
            base_text = random.choice(espresso_templates)
        elif "фільтр" in roast_lower or "filter" in roast_lower:
            base_text = random.choice(filter_templates)
        else:
            base_text = random.choice(universal_templates)
        
    return base_text




