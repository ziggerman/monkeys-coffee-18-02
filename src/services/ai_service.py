"""AI Service — GPT-4o primary, Gemini fallback, DALL-E for images."""
import asyncio
import logging
from pathlib import Path
from config import settings

logger = logging.getLogger(__name__)


class AIService:
    """Service for generating content using AI (GPT-4o primary, Gemini fallback, DALL-E for images)."""

    def __init__(self):
        # --- OpenAI (primary) ---
        self.openai_client = None
        openai_key = settings.openai_api_key
        
        if openai_key:
            try:
                from openai import AsyncOpenAI
                print(f"DEBUG: Initializing OpenAI client. Key starts with: {openai_key[:8]}...")
                logger.info(f"Initializing OpenAI client. Key starts with: {openai_key[:8]}...")
                self.openai_client = AsyncOpenAI(api_key=openai_key)
                print("DEBUG: OpenAI client initialized successfully (GPT-4o)")
                logger.info("OpenAI client initialized successfully (GPT-4o)")
            except Exception as e:
                print(f"DEBUG: OpenAI init failed: {e}")
                logger.error(f"OpenAI init failed: {e}", exc_info=True)
        else:
            print("DEBUG: OpenAI API Key is missing or empty in settings!")
            logger.warning("OpenAI API Key is missing or empty in settings!")

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
        
        # --- Assets directory for images ---
        from src.utils.image_constants import ASSETS_DIR
        self.assets_dir = ASSETS_DIR
        self.assets_dir.mkdir(parents=True, exist_ok=True)

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

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        save_path: Path = None
    ) -> tuple[str | None, str | None, Path | None]:
        """Generate image using DALL-E 3 and optionally save to disk.
        
        Args:
            prompt: Text description for image generation
            size: Image size (1024x1024, 1024x1792, or 1792x1024)
            save_path: Optional path to save the image
            
        Returns:
            Tuple of (image_url, error, local_path)
            - image_url: URL of generated image (if not saved locally)
            - error: Error message if generation failed
            - local_path: Path to saved image (if save_path provided)
        """
        if not self.openai_client:
            return None, "OpenAI client not initialized", None
        
        try:
            logger.info(f"Generating image with prompt: {prompt[:100]}...")
            
            response = await asyncio.wait_for(
                self.openai_client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size=size,
                    quality="standard",
                    n=1,
                ),
                timeout=60.0
            )
            
            image_data = response.data[0]
            image_url = image_data.url
            
            # Download and save if path provided
            local_path = None
            if save_path:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url) as resp:
                        if resp.status == 200:
                            content = await resp.read()
                            save_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(save_path, 'wb') as f:
                                f.write(content)
                            local_path = save_path
                            logger.info(f"Image saved to: {save_path}")
                        else:
                            logger.warning(f"Failed to download image: {resp.status}")
            
            return image_url, None, local_path
            
        except asyncio.TimeoutError:
            logger.warning("DALL-E image generation timed out")
            return None, "DALL-E Timeout", None
        except Exception as e:
            err = str(e)
            logger.warning(f"DALL-E error: {e}")
            if "429" in err or "quota" in err.lower() or "insufficient_quota" in err:
                return None, "DALL-E Quota Exceeded", None
            return None, f"DALL-E Error: {str(e)[:100]}", None

    async def generate_category_image(
        self,
        category_name: str,
        profile: str = None,
        save_path: Path = None
    ) -> tuple[str | None, str | None, Path | None]:
        """Generate a category banner image using DALL-E.
        
        Args:
            category_name: Name of the category (e.g., "Еспресо", "Фільтр")
            profile: Optional profile type (espresso/filter/universal)
            save_path: Path to save the image
            
        Returns:
            Tuple of (image_url, error, local_path)
        """
        # Build detailed prompt for coffee category - Ukrainian context
        # Map category names to appropriate prompts
        category_lower = category_name.lower().strip() if category_name else ""
        
        # Determine style based on category name or profile
        if profile == "espresso" or "еспресо" in category_lower or "espresso" in category_lower:
            prompt = (
                "Elegant coffee shop menu banner for espresso coffee section. "
                "Dark roasted coffee beans, professional espresso machine in background, "
                "rich dark brown and black colors with warm amber accents, "
                "professional photography, clean minimalist composition, "
                "soft studio lighting, high quality, no text, no words, Telegram bot menu style"
            )
        elif profile == "filter" or "фільтр" in category_lower or "filter" in category_lower or "альтернатива" in category_lower:
            prompt = (
                "Elegant coffee shop menu banner for filter coffee section. "
                "Light roasted coffee beans, pour-over dripper (V60, Chemex), "
                "bright golden yellow and light brown colors, morning natural light, "
                "clean fresh aesthetic, professional product photography, "
                "minimalist design, high quality, no text, no words, Telegram bot menu style"
            )
        elif profile == "universal" or "універсальн" in category_lower or "універсальн" in category_lower:
            prompt = (
                "Elegant coffee shop menu banner for versatile coffee selection. "
                "Mixed variety of coffee beans, different roast levels displayed together, "
                "balanced warm brown and orange tones, cozy coffee shop atmosphere, "
                "professional product shot, clean minimalist composition, "
                "high quality, no text, no words, Telegram bot menu style"
            )
        else:
            # Default coffee banner - use category name to make it relevant
            prompt = (
                f"Elegant coffee shop menu banner for {category_name} section. "
                "Professional product photography, warm coffee colors (brown, amber, golden), "
                "clean minimalist composition, soft studio lighting, "
                "high quality, no text, no words, Telegram bot menu style"
            )
        
        return await self.generate_image(prompt, save_path=save_path)

    async def generate_product_image(
        self,
        product_name: str,
        origin: str,
        roast_level: str,
        tasting_notes: list = None,
        save_path: Path = None
    ) -> tuple[str | None, str | None, Path | None]:
        """Generate a product image for a coffee bag using DALL-E.
        
        Args:
            product_name: Name of the coffee
            origin: Country/region of origin
            roast_level: Roast level (light/medium/dark)
            tasting_notes: List of flavor notes
            save_path: Path to save the image
            
        Returns:
            Tuple of (image_url, error, local_path)
        """
        # Build prompt for coffee bag product shot
        notes_str = ", ".join(tasting_notes) if tasting_notes else ""
        
        # Determine color tones based on roast
        if "light" in roast_level.lower() or "filter" in roast_level.lower():
            color_tones = "light golden brown, bright and vibrant"
        elif "dark" in roast_level.lower() or "espresso" in roast_level.lower():
            color_tones = "dark chocolate brown, deep rich tones"
        else:
            color_tones = "warm medium brown, balanced tones"
        
        prompt = (
            f"Professional coffee product photography, premium coffee bag/stand-up pouch on wooden table, "
            f"whole bean coffee, {color_tones}, natural lighting from window, "
            f"coffee accessories (scale, grinder) in background for context, "
            f"artisan coffee roaster style, clean minimalist composition, "
            f"high-end e-commerce product shot, no text or labels visible"
        )
        
        return await self.generate_image(prompt, save_path=save_path)

    async def generate_product_variation(
        self,
        input_image_path: Path,
        save_path: Path = None
    ) -> tuple[str | None, str | None, Path | None]:
        """Generate a variation of an existing product image using DALL-E 2.
        
        This uses DALL-E 2's image variation capability to create a new version
        of the uploaded coffee package photo with improved quality while
        maintaining the same packaging, labels, and product.
        
        Args:
            input_image_path: Path to the uploaded product image
            save_path: Path to save the generated variation
            
        Returns:
            Tuple of (image_url, error, local_path)
        """
        if not self.openai_client:
            return None, "OpenAI client not initialized", None
        
        try:
            logger.info(f"Generating image variation from: {input_image_path}")
            
            # Open the input image
            with open(input_image_path, "rb") as f:
                image_data = f.read()
            
            # DALL-E 2 supports image variations
            response = await asyncio.wait_for(
                self.openai_client.images.create_variation(
                    image=image_data,
                    model="dall-e-2",
                    size="1024x1024",
                    n=1,
                ),
                timeout=60.0
            )
            
            image_url = response.data[0].url
            
            # Download and save if path provided
            local_path = None
            if save_path:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url) as resp:
                        if resp.status == 200:
                            content = await resp.read()
                            save_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(save_path, 'wb') as f:
                                f.write(content)
                            local_path = save_path
                            logger.info(f"Image variation saved to: {save_path}")
                        else:
                            logger.warning(f"Failed to download image variation: {resp.status}")
            
            return image_url, None, local_path
            
        except asyncio.TimeoutError:
            logger.warning("DALL-E image variation timed out")
            return None, "DALL-E Variation Timeout", None
        except Exception as e:
            err = str(e)
            logger.warning(f"DALL-E variation error: {e}")
            if "429" in err or "quota" in err.lower() or "insufficient_quota" in err:
                return None, "DALL-E Quota Exceeded", None
            if "image" in err.lower() and "format" in err.lower():
                return None, "Invalid image format. Use PNG or JPEG.", None
            return None, f"DALL-E Error: {str(e)[:100]}", None

    async def enhance_product_image(
        self,
        input_image_path: Path,
        product_name: str = None,
        roast_level: str = None,
        save_path: Path = None
    ) -> tuple[str | None, str | None, Path | None]:
        """Enhance a product image using DALL-E (edit/variation).
        
        Takes a simple photo of a coffee package and creates a professional
        product shot while keeping the same packaging and labels.
        
        Args:
            input_image_path: Path to the uploaded product image
            product_name: Name of the coffee (for prompt guidance)
            roast_level: Roast level (for background style)
            save_path: Path to save the enhanced image
            
        Returns:
            Tuple of (image_url, error, local_path)
        """
        # Determine background style based on roast
        background_style = "warm coffee shop atmosphere"
        if roast_level:
            if "light" in roast_level.lower() or "filter" in roast_level.lower():
                background_style = "bright natural lighting, light and airy atmosphere"
            elif "dark" in roast_level.lower() or "espresso" in roast_level.lower():
                background_style = "dark moody atmosphere, warm amber lighting"
        
        # For now, use the variation endpoint which keeps the main subject
        return await self.generate_product_variation(input_image_path, save_path)


# Singleton instance
ai_service = AIService()

