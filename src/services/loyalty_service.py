"""Loyalty service - track and manage user loyalty levels."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database.models import User
from config import LOYALTY_LEVELS


class LoyaltyService:
    """Service for loyalty level management."""
    
    @staticmethod
    def get_level_info(level: int) -> dict:
        """Get loyalty level information.
        
        Returns:
            Dict with name, discount, threshold_kg
        """
        return LOYALTY_LEVELS.get(level, LOYALTY_LEVELS[1])
    
    @staticmethod
    def calculate_level(total_purchased_kg: float) -> int:
        """Calculate loyalty level based on total purchases.
        
        Args:
            total_purchased_kg: Total kg of coffee purchased
            
        Returns:
            Loyalty level (1-4)
        """
        if total_purchased_kg >= 50:
            return 4  # Монкі-майстер
        elif total_purchased_kg >= 15:
            return 3  # Кавовий експерт
        elif total_purchased_kg >= 5:
            return 2  # Любитель кави
        else:
            return 1  # Новачок
    
    @staticmethod
    async def update_user_level(
        session: AsyncSession,
        user: User,
        purchased_kg: float
    ) -> tuple[bool, int]:
        """Update user's total purchases and recalculate level.
        
        Args:
            session: Database session
            user: User object
            purchased_kg: Amount of kg purchased in this order
            
        Returns:
            (level_upgraded, new_level)
        """
        old_level = user.loyalty_level
        
        # Update total purchases
        user.total_purchased_kg += purchased_kg
        
        # Recalculate level
        new_level = LoyaltyService.calculate_level(user.total_purchased_kg)
        user.loyalty_level = new_level
        
        await session.commit()
        
        level_upgraded = new_level > old_level
        
        return level_upgraded, new_level
    
    @staticmethod
    def get_progress_to_next_level(user: User) -> dict:
        """Get progress information to next loyalty level.
        
        Returns:
            Dict with: current_level, next_level, current_kg, needed_kg, progress_percent
        """
        current_level = user.loyalty_level
        current_kg = user.total_purchased_kg
        
        if current_level >= 4:
            # Max level reached
            return {
                "current_level": current_level,
                "next_level": None,
                "current_kg": current_kg,
                "needed_kg": 0,
                "progress_percent": 100
            }
        
        next_level = current_level + 1
        next_threshold = LOYALTY_LEVELS[next_level]["threshold_kg"]
        current_threshold = LOYALTY_LEVELS[current_level]["threshold_kg"]
        
        needed_kg = next_threshold - current_kg
        progress_kg = current_kg - current_threshold
        total_range = next_threshold - current_threshold
        
        progress_percent = int((progress_kg / total_range) * 100) if total_range > 0 else 0
        
        return {
            "current_level": current_level,
            "next_level": next_level,
            "current_kg": current_kg,
            "needed_kg": needed_kg,
            "progress_percent": min(progress_percent, 100)
        }
    
    @staticmethod
    def format_loyalty_status(user: User) -> str:
        """Format user's loyalty status for display.
        
        Returns:
            Formatted loyalty status message
        """
        from src.utils.formatters import format_progress_bar
        
        current_info = LoyaltyService.get_level_info(user.loyalty_level)
        progress = LoyaltyService.get_progress_to_next_level(user)
        
        lines = [f"🎯 Ваш статус: {current_info['name']}\n"]
        
        # Show all 4 levels
        for level in range(1, 5):
            info = LOYALTY_LEVELS[level]
            
            if level < user.loyalty_level:
                # Completed level
                lines.append("┌─────────────────────────────┐")
                lines.append(f"│ Рівень {level}: {info['name']:<16} │")
                lines.append("│ ✅ Досягнуто                │")
                lines.append(f"│ Знижка: {info['discount']}%                   │")
                lines.append("└─────────────────────────────┘\n")
            
            elif level == user.loyalty_level:
                # Current level
                lines.append("┌─────────────────────────────┐")
                lines.append(f"│ Рівень {level}: {info['name']:<16} │")
                lines.append("│ ✅ Ви тут                   │")
                lines.append(f"│ Знижка: {info['discount']}%                   │")
                lines.append("└─────────────────────────────┘\n")
            
            else:
                # Future level
                if level == user.loyalty_level + 1:
                    # Next level - show progress
                    threshold = info['threshold_kg']
                    current = user.total_purchased_kg
                    bar = format_progress_bar(current, threshold, 12)
                    
                    lines.append("┌─────────────────────────────┐")
                    lines.append(f"│ Рівень {level}: {info['name']:<16} │")
                    lines.append(f"│ {bar} {current:.1f}/{threshold} кг     │")
                    lines.append(f"│ До рівня: {progress['needed_kg']:.1f} кг            │")
                    lines.append(f"│ Знижка: {info['discount']}% на всі покупки   │")
                    lines.append("└─────────────────────────────┘\n")
                else:
                    # Further levels
                    threshold = info['threshold_kg']
                    bar = format_progress_bar(0, 1, 12)
                    
                    lines.append("┌─────────────────────────────┐")
                    lines.append(f"│ Рівень {level}: {info['name']:<16} │")
                    lines.append(f"│ {bar} 0/{threshold} кг      │")
                    lines.append(f"│ Знижка: {info['discount']}%")
                    if level == 4:
                        lines.append(" + пріоритет     │")
                        lines.append("│ + доступ до спецлотів       │")
                    else:
                        lines.append("                   │")
                    lines.append("└─────────────────────────────┘\n")
        
        # Statistics
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("📊 Ваша статистика:")
        lines.append(f"Замовлень: {user.total_orders}")
        lines.append(f"Куплено кави: {user.total_purchased_kg:.1f} кг")
        
        if user.total_orders > 0:
            avg_check = user.total_purchased_kg / user.total_orders
            lines.append(f"Середній чек: {avg_check:.1f} кг")
        
        if user.created_at:
            from datetime import datetime
            days = (datetime.utcnow() - user.created_at).days
            lines.append(f"З нами: {days} днів")
        
        lines.append("\n💡 Знижки за об'єм працюють")
        lines.append("окремо і сумуються з рівнем!")
        
        return "\n".join(lines)
