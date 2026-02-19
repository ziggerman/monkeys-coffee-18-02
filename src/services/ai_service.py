"""AI Service — GPT-4o primary, Gemini fallback."""
import asyncio
import logging
from config import settings

logger = logging.getLogger(__name__)


class AIService:
    """Service for generating content using AI (GPT-4o primary, Gemini fallback)."""

    def __init__(self):
        # --- OpenAI (primary) ---
        self.openai_client = None
        if settings.openai_api_key:
            try:
                from openai import AsyncOpenAI
                self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
                logger.info("OpenAI client initialized (GPT-4o)")
            except Exception as e:
                logger.warning(f"OpenAI init failed: {e}")

        # --- Gemini (fallback) ---
        self.gemini_models = []
        if settings.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.gemini_api_key)
                self.gemini_models = [
                    genai.GenerativeModel('models/gemini-flash-lite-latest'),
                    genai.GenerativeModel('models/gemini-2.0-flash-lite'),
                ]
                logger.info("Gemini fallback models initialized")
            except Exception as e:
                logger.warning(f"Gemini init failed: {e}")

    async def _call_openai(self, prompt: str, system: str = None, timeout: float = 20.0) -> tuple[str | None, str | None]:
        """Call GPT-4o with timeout and quota error handling. Returns (text, error)."""
        if not self.openai_client:
            return None, "OpenAI client not initialized"
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = await asyncio.wait_for(
                self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    max_tokens=800,
                    temperature=0.7,
                ),
                timeout=timeout
            )
            text = response.choices[0].message.content.strip()
            if text and len(text) > 10:
                return text, None
            return None, "Empty response from OpenAI"
        except asyncio.TimeoutError:
            logger.warning("OpenAI timed out")
            return None, "OpenAI Timeout"
        except Exception as e:
            err = str(e)
            logger.warning(f"OpenAI error: {e}")
            if "429" in err or "quota" in err.lower() or "insufficient_quota" in err:
                return None, "OpenAI Quota Exceeded"
            return None, f"OpenAI Error: {str(e)[:50]}"

    async def _call_gemini(self, prompt: str, timeout: float = 15.0) -> tuple[str | None, str | None]:
        """Call Gemini models with timeout and quota error handling. Returns (text, error)."""
        last_error = "Gemini Call Failed"
        
        for model in self.gemini_models:
            try:
                response = await asyncio.wait_for(
                    model.generate_content_async(prompt), timeout=timeout
                )
                text = response.text.strip() if response and hasattr(response, 'text') else None
                if text and len(text) > 10:
                    return text, None
            except asyncio.TimeoutError:
                logger.warning("Gemini model timed out")
                last_error = "Gemini Timeout"
            except Exception as e:
                err = str(e)
                logger.warning(f"Gemini error: {e}")
                if "429" in err or "quota" in err.lower() or "ResourceExhausted" in err:
                    last_error = "Gemini Quota Exceeded"
                else:
                    last_error = f"Gemini Error: {str(e)[:50]}"
                    
        return None, last_error

    async def generate_professional_description(
        self,
        name: str,
        origin: str,
        roast: str,
        notes: list,
        processing: str
    ) -> tuple[str | None, str | None]:
        """Generate a professional coffee description. GPT-4o → Gemini fallback. Returns (text, error)."""

        system = (
            "Ти — професійний шеф-бариста Monkeys Coffee. Пишеш коротко, "
            "експертно та зрозуміло як для новачків, так і для фанатів кави. "
            "Тільки українська. HTML: <b>, <i>."
        )

        notes_str = ", ".join(notes) if isinstance(notes, list) else str(notes)

        prompt = f"""Напиши короткий професійний опис кави ({name}, {origin}, {roast}, {processing}, ноти: {notes_str}).
        
Структура (HTML):
<b>{name}</b>
<i>[1 речення: характер лоту]</i>

<b>📋 Профіль:</b>
• <b>Тіло:</b> [1-3 слова]
• <b>Смак:</b> {notes_str}

Пиши без води, максимум 30-40 слів."""

        # Try GPT-4o first
        result, openai_error = await self._call_openai(prompt, system=system)
        if result:
            logger.info(f"GPT-4o generated description for {name}")
            return result, None

        # Fallback to Gemini
        full_prompt = f"{system}\n\n{prompt}"
        result, gemini_error = await self._call_gemini(full_prompt)
        if result:
            logger.info(f"Gemini generated description for {name}")
            return result, None

        # Return the most relevant error
        return None, openai_error or gemini_error

    async def generate_description_narrative(
        self,
        name: str,
        origin: str,
        roast: str,
        notes: list,
        processing: str
    ) -> tuple[str | None, str | None]:
        """Generate a short punchy narrative. GPT-4o → Gemini fallback. Returns (text, error)."""

        system = (
            "Ти — зухвалий копірайтер Monkeys Coffee Roasters. "
            "Стиль: енергійний, з гумором, з емодзі 🐒☕⚡. Пишеш тільки українською. "
            "Використовуй HTML теги <b> та <i>."
        )

        notes_str = ", ".join(notes) if isinstance(notes, list) else str(notes)

        prompt = f"""Напиши короткий (2-3 речення) вибуховий опис кави. Без порад, тільки смак та емоція.

Дані: {name}, {origin}, обсмажка: {roast}, нотки: {notes_str}, обробка: {processing}

Формат:
🔥 <b>{name}</b>. [Зухвалий опис смаку з емоцією — 2-3 речення. Обов'язково згадай нотки смаку!]"""

        result, openai_error = await self._call_openai(prompt, system=system)
        if result:
            return result, None

        full_prompt = f"{system}\n\n{prompt}"
        result, gemini_error = await self._call_gemini(full_prompt)
        
        if result:
            return result, None
            
        return None, openai_error or gemini_error

    async def generate_smart_editor_text(self, key: str, prompt: str) -> tuple[str | None, str | None]:
        """Generate text for Smart Editor content keys. GPT-4o → Gemini fallback. Returns (text, error)."""

        system = (
            "Ти — професійний редактор Monkeys Coffee Roasters. "
            "Твоя мета — писати чіткі, структуровані та продаючі тексти для Telegram-бота. "
            "Використовуй марковані списки, емодзі (помірно) та HTML-теги <b> для акцентів. "
            "Стиль: діловий, але дружній, без зайвого 'шуму' та води. "
            "Тільки українська мова."
        )

        # Try GPT-4o
        result, error = await self._call_openai(prompt, system=system)
        if result:
            return result, None
            
        # Fallback to Gemini
        full_prompt = f"{system}\n\n{prompt}"
        result, gemini_error = await self._call_gemini(full_prompt)
        
        if result:
            return result, None
            
        # Return the most relevant error (OpenAI if set, else Gemini)
        return None, error or gemini_error


# Singleton instance
ai_service = AIService()
