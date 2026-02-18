import logging
import google.generativeai as genai
from config import settings

logger = logging.getLogger(__name__)

class AIService:
    """Service for generating content using AI."""
    
    def __init__(self):
        self.api_key = settings.gemini_api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Use gemini-flash-latest (1.5 Flash) for stability
            self.primary_model = genai.GenerativeModel('models/gemini-flash-latest')
            self.fallback_model = genai.GenerativeModel('models/gemini-2.0-flash-lite')
        else:
            self.primary_model = None
            self.fallback_model = None

    async def generate_description_narrative(
        self, 
        name: str, 
        origin: str, 
        roast: str, 
        notes: list, 
        processing: str
    ) -> str:
        """Generate a punchy, cheeky 'Monkeys' style coffee narrative."""
        if not self.primary_model:
            return None

        prompt = f"""
Ти — копірайтер бренду "MONKEYS COFFEE ROASTERS". Твій стиль: зухвалий, енергійний, професійний, але з гуримом (🐒🔥).
Твоє завдання — написати логічний (1-2 речення) та вибуховий опис для нової кави та додати одну лаконічну пораду (💡 Порада).

Дані лоту:
- Назва: {name}
- Походження/Регіон: {origin}
- Обсмажка: {roast}
- Нотки смаку: {", ".join(notes) if isinstance(notes, list) else notes}
- Обробка: {processing}

Вимоги:
1. Використовуй емодзі (🐒, ☕, ⚡, 🤟).
2. Опис має бути коротким — максимум 2 речення.
3. Порада має бути практичною (метод заварювання, як заварювати, чи додавати молоко, коли пити).
4. Мова: Українська.
5. Не використовуй технічну інфу (обсмажка/обробка) в тексті розповіді, вона буде додана окремо. Зосередься на емоції та смаку.
6. Вкажи назву лоту в тексті та зроби її жирною (<b>Назва</b>).

Приклад структури:
🔥 <b>Назва</b>. Зухвалий опис смаку з емоцією.
💡 Порада: Коротка порада по справі.
"""
        # Try primary model
        try:
            response = await self.primary_model.generate_content_async(prompt)
            text = response.text.strip() if response and hasattr(response, 'text') else None
            if text and len(text) > 10:
                return text
        except Exception as e:
            logger.warning(f"Primary AI model failed: {e}. Trying fallback...")
            
        # Try fallback model
        try:
            response = await self.fallback_model.generate_content_async(prompt)
            text = response.text.strip() if response and hasattr(response, 'text') else None
            return text if text and len(text) > 10 else None
        except Exception as e:
            logger.error(f"All AI models failed: {e}")
            return None

    async def generate_professional_description(
        self, 
        name: str, 
        origin: str, 
        roast: str, 
        notes: list, 
        processing: str
    ) -> str:
        """Generate a professional, educational, and engaging coffee description."""
        if not self.primary_model:
            return None

        prompt = f"""
Ти — професійний шеф-бариста та обсмажчик кави в "Monkeys Coffee Roasters".
Твоя місія — закохати людину в цю каву ще до того, як вона її скуштує.
Твій стиль: Експертний, але зрозумілий (пояснюєш складне просто), теплий, надихаючий.

Дані лоту:
- Назва: {name}
- Регіон/Походження: {origin}
- Обсмажка: {roast}
- Нотки смаку (дескриптори): {", ".join(notes) if isinstance(notes, list) else notes}
- Обробка: {processing}

ЗАВДАННЯ:
Напиши опис цього лоту, який складатиметься з 3-х коротких, але змістовних блоків:

1. 📖 **Історія та Характер** (2-3 речення):
   Опиши загальне враження від кави. Яка вона за характером? (Яскрава, щільна, делікатна, зухвала?). Чому цей регіон/обробка круті? Поясни "на пальцях" для новачка, що він відчує.

2. 👅 **Смаковий Профіль** (1-2 речення):
   Детальніше про смак. Як розкриваються дескриптори? Що відчувається на післясмаку? Використовуй епітети (соковитий, оксамитовий, іскристий).

3. 💡 **Порада Баристи** (1-2 речення):
   Як це краще заварити? (Пуровер, еспресо, гейзер, чашка?). В який час доби краще пити? З чим смакує?

ВАЖЛИВО:
- Мова: Українська.
- Використовуй емодзі для структурування (але в міру).
- Не використовуй занадто складні терміни без пояснень.
- Опис має виглядати як рекомендація кращого друга, який шарить в каві.
- Виділяй ключові слова **жирним**.

Формат виводу (приклад):
☕ **[Назва]** — це справжня візитівка [Регіон]. Вона...

👅 **Смак:** Тут ви знайдете...

💡 **Порада:** Ідеально підійде для...
"""
        # Try primary model
        try:
            response = await self.primary_model.generate_content_async(prompt)
            text = response.text.strip() if response and hasattr(response, 'text') else None
            if text and len(text) > 20:
                return text
        except Exception as e:
            logger.warning(f"Primary AI model failed (professional): {e}. Trying fallback...")
            
        # Try fallback model
        try:
            response = await self.fallback_model.generate_content_async(prompt)
            text = response.text.strip() if response and hasattr(response, 'text') else None
            return text if text and len(text) > 20 else None
        except Exception as e:
            logger.error(f"All AI models failed (professional): {e}")
            return None


# Singleton instance
ai_service = AIService()
