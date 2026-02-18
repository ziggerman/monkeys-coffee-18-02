"""Configuration management for Monkeys Coffee Roasters bot."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file='config.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )
    
    # Telegram Bot
    bot_token: str
    admin_ids: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""
    payment_provider_token: str = ""
    
    # Database
    database_url: str
    
    # Payment
    liqpay_public_key: str = ""
    liqpay_private_key: str = ""
    
    # Application Settings
    free_delivery_threshold: int = 1500
    delivery_cost_nova_poshta: int = 65
    delivery_cost_ukrposhta: int = 50
    
    # Referral System
    referral_bonus_amount: int = 100
    
    # Notifications
    enable_notifications: bool = True
    replenishment_reminder_days: int = 18
    
    @property
    def admin_id_list(self) -> List[int]:
        """Parse admin IDs from comma-separated string."""
        if not self.admin_ids:
            return []
        
        # Filter out placeholder IDs and ensure valid integers
        ids = []
        for x in self.admin_ids.split(','):
            if x.strip():
                try:
                    uid = int(x.strip())
                    # Filter out common placeholders
                    if uid != 123456789:
                        ids.append(uid)
                except ValueError:
                    continue
        return ids


# Global settings instance
settings = Settings()


# Loyalty System Configuration
LOYALTY_LEVELS = {
    1: {"name": "Новачок", "discount": 0, "threshold_kg": 0},
    2: {"name": "Любитель кави", "discount": 5, "threshold_kg": 5},
    3: {"name": "Кавовий експерт", "discount": 10, "threshold_kg": 15},
    4: {"name": "Монкі-майстер", "discount": 15, "threshold_kg": 50},
}

# Volume Discount Tiers (for 300g packs)
VOLUME_DISCOUNTS_PACKS = {
    7: 25,   # 7+ packs = 25%
}

# Volume Discount for Kilograms
KG_DISCOUNT_THRESHOLD = 2  # 2+ kg = 25%
KG_DISCOUNT_PERCENT = 25

# Coffee Profiles
COFFEE_PROFILES = {
    "espresso": {"name": "🍫 Для еспресо", "emoji": "🍫"},
    "filter": {"name": "🍋 Для фільтру", "emoji": "🍋"},
    "universal": {"name": "⚖️ Універсальна", "emoji": "⚖️"},
}

# Product Formats
PRODUCT_FORMATS = {
    "300g": {"weight_kg": 0.3, "display": "300г"},
    "1kg": {"weight_kg": 1.0, "display": "1кг"},
}
