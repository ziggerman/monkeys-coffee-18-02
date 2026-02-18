"""Discount calculation engine - the core business logic."""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from config import LOYALTY_LEVELS, VOLUME_DISCOUNTS_PACKS, KG_DISCOUNT_THRESHOLD, KG_DISCOUNT_PERCENT
from src.database.models import CartItem, Product, PromoCode, User


@dataclass
class DiscountBreakdown:
    """Discount calculation result."""
    volume_discount_percent: int
    loyalty_discount_percent: int
    promo_discount_percent: int
    total_discount_percent: int
    
    subtotal: int
    volume_discount_amount: int
    loyalty_discount_amount: int
    promo_discount_amount: int
    total_discount_amount: int
    final_total: int
    
    # Progress tracking
    total_packs_300g: int
    total_weight_kg: float
    next_pack_discount_tier: Optional[int]
    next_kg_discount_active: bool


class DiscountEngine:
    """Calculate discounts based on cart contents and user status."""
    
    @staticmethod
    def calculate_cart_metrics(cart_items: List[Tuple[CartItem, Product]]) -> Tuple[int, float, int]:
        """Calculate cart metrics: pack count, total weight, subtotal.
        
        Returns:
            (total_packs_300g, total_weight_kg, subtotal)
        """
        total_packs = 0
        total_weight = 0.0
        subtotal = 0
        
        for cart_item, product in cart_items:
            quantity = cart_item.quantity

            # 300g packs
            if cart_item.format == "300g":
                total_packs += quantity
                total_weight += 0.3 * quantity
                item_price = product.price_300g
            # single-unit equipment/items — price stored in price_300g by admin, no weight contribution
            elif cart_item.format == "unit":
                item_price = product.price_300g
            # 1kg bags
            elif cart_item.format == "1kg":
                total_weight += 1.0 * quantity
                item_price = product.price_1kg
            else:
                # Unknown format — be defensive and treat as zero-priced
                item_price = 0

            subtotal += item_price * quantity
        
        return total_packs, total_weight, subtotal
    
    @staticmethod
    def calculate_volume_discount(
        total_packs_300g: int, 
        total_weight_kg: float,
        active_rules: Optional[List['VolumeDiscount']] = None
    ) -> int:
        """Calculate volume discount percentage based on active rules.
        If active_rules is None, falls back to legacy config.
        """
        best_discount = 0
        
        if active_rules:
            for rule in active_rules:
                if not rule.is_active:
                    continue
                    
                if rule.discount_type == 'packs':
                    if total_packs_300g >= rule.threshold:
                        best_discount = max(best_discount, rule.discount_percent)
                elif rule.discount_type == 'weight':
                    if total_weight_kg >= rule.threshold:
                        best_discount = max(best_discount, rule.discount_percent)
            return best_discount

        # Fallback to legacy config
        for pack_threshold, discount in VOLUME_DISCOUNTS_PACKS.items():
            if total_packs_300g >= pack_threshold:
                best_discount = max(best_discount, discount)
        
        if total_weight_kg >= KG_DISCOUNT_THRESHOLD:
            best_discount = max(best_discount, KG_DISCOUNT_PERCENT)
            
        return best_discount
    @staticmethod
    def calculate_loyalty_discount(user: User) -> int:
        """Get loyalty discount. 
        
        DEPRECATED: Loyalty levels removed. Returns 0.
        """
        return 0
    
    @staticmethod
    def calculate_full_discount(
        cart_items: List[Tuple[CartItem, Product]],
        user: User,
        promo_code: Optional[PromoCode] = None,
        active_rules: Optional[List['VolumeDiscount']] = None
    ) -> DiscountBreakdown:
        """Calculate complete discount breakdown."""
        # Calculate cart metrics
        total_packs, total_kg, subtotal = DiscountEngine.calculate_cart_metrics(cart_items)
        
        # Calculate volume discount
        volume_discount = DiscountEngine.calculate_volume_discount(total_packs, total_kg, active_rules)
        
        # Calculate loyalty discount
        loyalty_discount = DiscountEngine.calculate_loyalty_discount(user)
        
        # Initial stacked discount
        stacked_discount = volume_discount + loyalty_discount
        
        # Check promo code override
        promo_discount = 0
        use_promo_instead = False
        
        if promo_code and promo_code.is_valid():
            promo_discount = promo_code.discount_percent
            if promo_discount > stacked_discount:
                use_promo_instead = True
        
        # Determine final discount structure
        if use_promo_instead:
            final_volume = 0
            final_loyalty = 0
            final_promo = promo_discount
            total_discount = promo_discount
        else:
            final_volume = volume_discount
            final_loyalty = loyalty_discount
            final_promo = 0
            total_discount = stacked_discount
        
        # Calculate discount amounts
        volume_amount = int(subtotal * final_volume / 100)
        loyalty_amount = int(subtotal * final_loyalty / 100)
        promo_amount = int(subtotal * final_promo / 100)
        total_discount_amount = volume_amount + loyalty_amount + promo_amount
        
        # Final total
        final_total = subtotal - total_discount_amount
        
        # Progress tracking
        next_pack_tier = DiscountEngine._get_next_pack_discount_tier(total_packs)
        kg_discount_active = total_kg >= KG_DISCOUNT_THRESHOLD
        
        return DiscountBreakdown(
            volume_discount_percent=final_volume,
            loyalty_discount_percent=final_loyalty,
            promo_discount_percent=final_promo,
            total_discount_percent=total_discount,
            subtotal=subtotal,
            volume_discount_amount=volume_amount,
            loyalty_discount_amount=loyalty_amount,
            promo_discount_amount=promo_amount,
            total_discount_amount=total_discount_amount,
            final_total=final_total,
            total_packs_300g=total_packs,
            total_weight_kg=total_kg,
            next_pack_discount_tier=next_pack_tier,
            next_kg_discount_active=kg_discount_active,
        )


    @staticmethod
    def _get_next_pack_discount_tier(current_packs: int) -> Optional[int]:
        """Get next pack discount tier threshold."""
        thresholds = sorted(VOLUME_DISCOUNTS_PACKS.keys())
        for t in thresholds:
            if current_packs < t:
                return t
        return None

    @staticmethod
    def format_discount_progress(
        breakdown: DiscountBreakdown,
        current_format: str = "both"
    ) -> str:
        """Friendly progress message for beginners (no tables)."""
        from config import settings
        
        lines = ["🐒 <b>ПРОГРЕС ДО ЗНИЖОК:</b>\n"]
        
        packs = breakdown.total_packs_300g
        weight = breakdown.total_weight_kg
        
        # 1. Volume Discount Progress
        if breakdown.volume_discount_percent >= 25:
            lines.append("🔥 <b>ВІТАЄМО!</b> У тебе активована максимальна оптова знижка <b>-25%</b>! Це найкраща ціна, на яку ти міг розраховувати.")
        else:
            # Tell how many packs to next tier
            next_tier = breakdown.next_pack_discount_tier
            if next_tier:
                needed_packs = next_tier - packs
                next_discount = VOLUME_DISCOUNTS_PACKS.get(next_tier, 25)
                lines.append(f"📦 Ще {needed_packs} пачки (по 300г) — і отримаєш знижку <b>-{next_discount}%</b> на все замовлення!")
            
            # Tell about kg threshold
            if weight < KG_DISCOUNT_THRESHOLD:
                needed_kg = KG_DISCOUNT_THRESHOLD - weight
                lines.append(f"⚖️ Або додай ще <b>{needed_kg:.1f} кг</b>, щоб миттєво отримати <b>-25%</b>!")
        
        # 2. Free Delivery Progress
        threshold = settings.free_delivery_threshold
        if breakdown.final_total < threshold:
            remaining = threshold - breakdown.final_total
            lines.append(f"\n🚚 <b>Доставка:</b> Ще {remaining} грн до <b>безкоштовної доставки</b>.")
            lines.append("<i>Порада: Додай ще одну пачку і ми привеземо все за наш рахунок!</i>")
        else:
            lines.append("\n✅ <b>БЕЗКОШТОВНА ДОСТАВКА АКТИВНА!</b>")

        return "\n".join(lines)
