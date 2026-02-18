"""Visual UX service for enhanced user experience."""
from typing import List, Tuple, Optional
from src.database.models import Product, User
from src.services.discount_engine import DiscountBreakdown


class VisualUXService:
    """Service for creating visual UX elements."""
    
    @staticmethod
    def create_progress_bar(
        current: float,
        target: float,
        length: int = 10,
        filled_char: str = "█",
        empty_char: str = "░",
        show_percentage: bool = True
    ) -> str:
        """Create a visual progress bar.
        
        Args:
            current: Current value
            target: Target value
            length: Length of the bar in characters
            filled_char: Character for filled portion
            empty_char: Character for empty portion
            show_percentage: Whether to show percentage
            
        Returns:
            Formatted progress bar string
        """
        if target <= 0:
            percentage = 100
        else:
            percentage = min(100, (current / target) * 100)
        
        filled = int((percentage / 100) * length)
        empty = length - filled
        
        bar = filled_char * filled + empty_char * empty
        
        if show_percentage:
            return f"{bar} {percentage:.0f}%"
        return bar
    
    @staticmethod
    def create_savings_meter(
        current_discount: int,
        potential_discount: int,
        max_discount: int = 40
    ) -> str:
        """Create a visual savings meter showing current and potential savings.
        
        Args:
            current_discount: Current discount percentage
            potential_discount: Potential discount percentage
            max_discount: Maximum possible discount
            
        Returns:
            Formatted savings meter
        """
        meter_length = 15
        
        # Calculate positions
        current_pos = int((current_discount / max_discount) * meter_length)
        potential_pos = int((potential_discount / max_discount) * meter_length)
        
        meter = ['░'] * meter_length
        
        # Fill current discount
        for i in range(current_pos):
            meter[i] = '█'
        
        # Show potential with different character
        for i in range(current_pos, potential_pos):
            meter[i] = '▓'
        
        meter_str = ''.join(meter)
        
        return f"""
💰 Економія:
{meter_str}
Зараз: {current_discount}% | Можливо: {potential_discount}%
"""
    
    @staticmethod
    def create_discount_visualization(breakdown: DiscountBreakdown) -> str:
        """Create visual discount breakdown with bars."""
        from src.utils.formatters import format_currency
        
        lines = ["📊 <b>Розбивка знижок:</b>\n"]
        
        if breakdown.volume_discount_percent > 0:
            bar = VisualUXService.create_progress_bar(
                breakdown.volume_discount_percent,
                25,  # Max volume discount
                length=8,
                show_percentage=False
            )
            lines.append(
                f"📦 Об'єм: {bar} {breakdown.volume_discount_percent}%\n"
                f"   Економія: {format_currency(breakdown.volume_discount_amount)}\n"
            )
        
        if breakdown.promo_discount_percent > 0:
            bar = VisualUXService.create_progress_bar(
                breakdown.promo_discount_percent,
                50,  # Max promo discount
                length=8,
                show_percentage=False
            )
            lines.append(
                f"🎁 Промокод: {bar} {breakdown.promo_discount_percent}%\n"
                f"   Економія: {format_currency(breakdown.promo_discount_amount)}\n"
            )
        
        lines.append(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        lines.append(
            f"💵 <b>Загальна економія:</b> {format_currency(breakdown.total_discount_amount)}\n"
            f"✨ <b>Загальна знижка:</b> {breakdown.total_discount_percent}%"
        )
        
        return ''.join(lines)
    
    @staticmethod
    def create_discount_tier_ladder(
        current_packs: int,
        current_kg: float
    ) -> str:
        """Create a visual ladder showing discount tiers."""
        lines = ["🎯 <b>Рівні знижок:</b>\n\n"]
        
        # New simplified rules
        pack_marker = "✅" if current_packs >= 7 else "🔒"
        kg_marker = "✅" if current_kg >= 2.0 else "🔒"
        
        lines.append(f"{pack_marker} 📦 7+ пачок (300г): 25%\n")
        lines.append(f"{kg_marker} ⚖️ 2+ кг кави: 25%\n")
        
        if current_packs < 7 and current_kg < 2.0:
            lines.append(f"\n💡 <i>Додайте ще трохи для максимальної економії!</i>")
        else:
            lines.append(f"\n✨ <b>Максимальна знижка застосована!</b>")
            
        return ''.join(lines)

    @staticmethod
    def create_loyalty_progress(user: User) -> str:
        """Create visual statistics display (simplified from loyalty)."""
        current_kg = user.total_purchased_kg
        
        lines = [f"📊 <b>Твоя Кавова Статистика:</b>\n\n"]
        lines.append(f"Загалом випито кави: <b>{current_kg:.2f} кг</b>\n")
        
        # Show a fun progress bar towards a "Coffee Master" achievement
        achievements = [
            (5, "Кавовий Ентузіаст"),
            (10, "Кавовий Гік"),
            (25, "Майстер Ростерії"),
            (50, "Бог Кофеїну")
        ]
        
        next_ach = next((a for a in achievements if current_kg < a[0]), achievements[-1])
        
        bar = VisualUXService.create_progress_bar(
            current_kg,
            next_ach[0],
            length=12
        )
        
        lines.append(f"\nНаступна ціль: {next_ach[1]}\n{bar}\n")
        
        return ''.join(lines)
    
    @staticmethod
    def create_bundle_recommendation(
        cart_items: List[Tuple],
        user: User
    ) -> Optional[str]:
        """Create smart bundle recommendation based on cart.
        
        Args:
            cart_items: List of (CartItem, Product) tuples
            user: User object
            
        Returns:
            Formatted recommendation or None
        """
        from src.services.discount_engine import DiscountEngine
        
        breakdown = DiscountEngine.calculate_full_discount(cart_items, user)
        
        # Analyze cart composition
        total_packs = breakdown.total_packs_300g
        total_kg = breakdown.total_weight_kg
        
        recommendations = []
        
        # Pack-based recommendations
        if total_packs == 2:
            recommendations.append({
                'title': '🎁 Набір "Початківець"',
                'description': 'Додайте ще 1 пачку',
                'benefit': 'Отримайте знижку 10%',
                'savings': breakdown.potential_savings_packs
            })
        elif total_packs in [3, 5]:
            next_tier = 4 if total_packs == 3 else 6
            discount = 15 if next_tier == 4 else 25
            needed = next_tier - total_packs
            
            recommendations.append({
                'title': f'🎁 Набір "{"Середній" if next_tier == 4 else "Максимум"}"',
                'description': f'Додайте ще {needed} {"пачку" if needed == 1 else "пачки"}',
                'benefit': f'Отримайте знижку {discount}%',
                'savings': breakdown.potential_savings_packs
            })
        
        # Kg-based recommendations
        if 1.5 <= total_kg < 2.0:
            needed_kg = 2.0 - total_kg
            recommendations.append({
                'title': '🎁 Набір "2 кілограми"',
                'description': f'Додайте ще {needed_kg:.1f} кг',
                'benefit': 'Отримайте максимальну знижку 25%',
                'savings': breakdown.potential_savings_kg
            })
        
        if not recommendations:
            return None
        
        from src.utils.formatters import format_currency
        
        # Build recommendation display
        rec = recommendations[0]  # Show best recommendation
        
        return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ <b>Розумна пропозиція</b>

{rec['title']}

{rec['description']}
→ {rec['benefit']}

💰 Ваша економія: ~{format_currency(rec['savings'])}

<i>Ця пропозиція оптимізована спеціально
для вашого кошика!</i>
━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    @staticmethod
    def create_real_time_savings_display(
        subtotal: int,
        current_total: int,
        if_bought_separately: int
    ) -> str:
        """Create real-time savings comparison display.
        
        Args:
            subtotal: Original subtotal
            current_total: Final total after discounts
            if_bought_separately: Cost if items bought in separate orders
            
        Returns:
            Formatted savings display
        """
        from src.utils.formatters import format_currency
        
        immediate_savings = subtotal - current_total
        bundle_savings = if_bought_separately - current_total
        
        savings_percent = (immediate_savings / subtotal * 100) if subtotal > 0 else 0
        
        # Create visual comparison
        lines = ["💰 <b>Ваша економія в реальному часі:</b>\n\n"]
        
        # Immediate savings bar
        bar = VisualUXService.create_progress_bar(
            savings_percent,
            50,  # Theoretical max
            length=12
        )
        
        lines.append(f"Знижка зараз:\n{bar}\n\n")
        
        # Comparison table
        lines.append("📊 <b>Порівняння:</b>\n\n")
        lines.append(f"Без знижки:     {format_currency(subtotal)}\n")
        lines.append(f"Ваша ціна:      {format_currency(current_total)} ✨\n")
        lines.append(f"━━━━━━━━━━━━━━━━━━━━━\n")
        lines.append(f"<b>Економія:        {format_currency(immediate_savings)}</b>\n\n")
        
        if bundle_savings > immediate_savings:
            lines.append(
                f"💡 <i>Якби купували окремо: {format_currency(if_bought_separately)}</i>\n"
                f"<i>Додаткова економія: {format_currency(bundle_savings - immediate_savings)}</i>\n"
            )
        
        return ''.join(lines)
    
    @staticmethod
    def create_interactive_calculator(
        base_price: int,
        formats: List[str] = ["300g", "1kg"]
    ) -> str:
        """Create interactive discount calculator display.
        
        Args:
            base_price: Base price for 300g
            formats: Available formats
            
        Returns:
            Formatted calculator
        """
        from src.utils.formatters import format_currency
        
        lines = ["🧮 <b>Калькулятор знижок:</b>\n\n"]
        
        # Price per format
        price_1kg = int(base_price * 3.0)  # Approximate conversion
        
        # Calculate different quantities
        calculations = [
            (1, 0, "1 пачка (300г)"),
            (2, 0, "2 пачки (600г)"),
            (3, 10, "3 пачки (900г)"),
            (4, 15, "4 пачки (1.2 кг)"),
            (6, 25, "6 пачок (1.8 кг)"),
            (0, 25, "2 кг (1 упаковка)", price_1kg * 2, True),
        ]
        
        for qty, discount, label, *args in calculations:
            if args and args[0]:  # Custom price provided
                price = args[0]
                is_kg = True
            else:
                price = base_price * qty
                is_kg = False
            
            if discount > 0:
                discounted = price - (price * discount / 100)
                savings = price - discounted
                
                lines.append(
                    f"{'📦' if not is_kg else '⚖️'} {label}\n"
                    f"   Ціна: <s>{format_currency(price)}</s> → {format_currency(int(discounted))}\n"
                    f"   Знижка: <b>{discount}%</b> (економія {format_currency(int(savings))})\n\n"
                )
            else:
                lines.append(
                    f"{'📦' if not is_kg else '⚖️'} {label}\n"
                    f"   Ціна: {format_currency(price)}\n\n"
                )
        
        lines.append(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 <i>Чим більше купуєте, тим більше економите!</i>"
        )
        
        return ''.join(lines)
    
    @staticmethod
    def create_catalog_item_with_savings(
        product: Product,
        user_loyalty_discount: int = 0
    ) -> str:
        """Create enhanced catalog item display with savings preview.
        
        Args:
            product: Product object
            user_loyalty_discount: User's loyalty discount percentage
            
        Returns:
            Formatted product display
        """
        from src.utils.formatters import format_currency
        
        lines = []
        
        # Product header
        lines.append(f"<b>{product.name_ua}</b>\n")
        lines.append(f"📍 {product.origin}\n")
        
        # Tasting notes
        if product.tasting_notes:
            notes = ", ".join(product.tasting_notes[:3])
            lines.append(f"🌸 {notes}\n\n")
        
        # Pricing with savings preview
        lines.append("<b>💰 Ціни:</b>\n")
        
        # 300g price
        price_300g = product.price_300g
        if user_loyalty_discount > 0:
            discounted_300g = price_300g - (price_300g * user_loyalty_discount / 100)
            lines.append(
                f"300г: <s>{format_currency(price_300g)}</s> → "
                f"{format_currency(int(discounted_300g))} "
                f"(-{user_loyalty_discount}%)\n"
            )
        else:
            lines.append(f"300г: {format_currency(price_300g)}\n")
        
        # 1kg price
        price_1kg = product.price_1kg
        if user_loyalty_discount > 0:
            discounted_1kg = price_1kg - (price_1kg * user_loyalty_discount / 100)
            lines.append(
                f"1 кг: <s>{format_currency(price_1kg)}</s> → "
                f"{format_currency(int(discounted_1kg))} "
                f"(-{user_loyalty_discount}%)\n"
            )
        else:
            lines.append(f"1 кг: {format_currency(price_1kg)}\n")
        
        # Savings preview for volume
        lines.append("\n<b>🎁 При купівлі:</b>\n")
        
        # Calculate example savings
        three_pack_price = price_300g * 3
        three_pack_with_discount = three_pack_price * 0.9  # 10% off
        three_pack_savings = three_pack_price - three_pack_with_discount
        
        if user_loyalty_discount > 0:
            three_pack_with_loyalty = three_pack_with_discount - (three_pack_with_discount * user_loyalty_discount / 100)
            total_savings = three_pack_price - three_pack_with_loyalty
            
            lines.append(
                f"3 пачки: {format_currency(int(three_pack_with_loyalty))} "
                f"(економія {format_currency(int(total_savings))})\n"
            )
        else:
            lines.append(
                f"3 пачки: {format_currency(int(three_pack_with_discount))} "
                f"(економія {format_currency(int(three_pack_savings))})\n"
            )
        
        # Quality indicator
        if product.sca_score:
            score_bar = VisualUXService.create_progress_bar(
                product.sca_score,
                100,
                length=10,
                filled_char="⭐",
                empty_char="☆",
                show_percentage=False
            )
            lines.append(f"\n{score_bar} SCA {product.sca_score}")
        
        return ''.join(lines)
