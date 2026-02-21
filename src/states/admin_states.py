"""Admin panel FSM states."""
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext


class AdminNavigationHistory:
    """Глибока навігація для адмін-панелі.
    
    Зберігає історію переходів користувача в адмін-панелі
    для можливості повернення на будь-який попередній рівень.
    
    Використовує FSM context data для збереження історії.
    """
    
    # Максимальна глибина історії
    MAX_HISTORY = 10
    
    # Ключ для збереження історії в state data
    HISTORY_KEY = "admin_nav_history"
    
    @classmethod
    async def push(cls, state: FSMContext, page: str, title: str = "", data: dict = None):
        """Додати сторінку до історії навігації."""
        # Отримуємо поточну історію
        state_data = await state.get_data()
        current_state = await state.get_state()
        
        history = state_data.get(cls.HISTORY_KEY, [])
        
        # Додаємо нову сторінку
        history.append({
            'page': page,
            'title': title,
            'data': data or {},
            'state': current_state
        })
        
        # Обрізаємо історію до максимальної глибини
        if len(history) > cls.MAX_HISTORY:
            history = history[-cls.MAX_HISTORY:]
        
        # Зберігаємо
        await state.update_data({cls.HISTORY_KEY: history})
    
    @classmethod
    async def pop(cls, state: FSMContext) -> dict:
        """Отримати та видалити останню сторінку з історії."""
        state_data = await state.get_data()
        history = state_data.get(cls.HISTORY_KEY, [])
        
        if not history:
            return None
        
        # Видаляємо останній елемент
        last_page = history.pop()
        
        # Зберігаємо оновлену історію
        await state.update_data({cls.HISTORY_KEY: history})
        
        return last_page
    
    @classmethod
    async def peek(cls, state: FSMContext) -> dict:
        """Подивитися останню сторінку без видалення."""
        state_data = await state.get_data()
        history = state_data.get(cls.HISTORY_KEY, [])
        
        if not history:
            return None
        
        return history[-1]
    
    @classmethod
    async def clear(cls, state: FSMContext):
        """Очистити історію навігації."""
        state_data = await state.get_data()
        if cls.HISTORY_KEY in state_data:
            await state.update_data({cls.HISTORY_KEY: []})
    
    @classmethod
    async def can_go_back(cls, state: FSMContext) -> bool:
        """Перевірити чи можна повернутися назад."""
        state_data = await state.get_data()
        history = state_data.get(cls.HISTORY_KEY, [])
        return len(history) > 1
    
    @classmethod
    async def get_all(cls, state: FSMContext) -> list:
        """Отримати всю історію навігації."""
        state_data = await state.get_data()
        return state_data.get(cls.HISTORY_KEY, [])


# ============================================
# Адмінські стани
# ============================================

class AdminStates(StatesGroup):
    """Admin panel states."""
    waiting_for_tracking_number = State()
    # Product type selection (Coffee or Shop)
    waiting_for_product_type = State()
    waiting_for_product_category = State()
    waiting_for_product_name = State()
    waiting_for_product_origin = State()
    waiting_for_product_tasting_notes = State()
    waiting_for_product_price_300g = State()
    waiting_for_product_price_1kg = State()
    waiting_for_product_image = State()
    waiting_for_product_confirm_generated = State()
    
    # New interactive flow states
    waiting_for_product_profile = State()
    waiting_for_product_roast_level = State()
    waiting_for_product_processing = State()
    
    # Product editing
    waiting_for_product_edit_field = State()
    waiting_for_product_edit_value = State()
    
    # Product deletion
    waiting_for_product_delete_confirm = State()
    
    # User management
    waiting_for_user_search = State()
    
    # Content & Discounts
    waiting_for_module_image = State()
    waiting_for_volume_discount_type = State()
    waiting_for_volume_discount_threshold = State()
    waiting_for_volume_discount_percent = State()
    waiting_for_volume_discount_description = State()
    
    # Text Content
    waiting_for_text_content = State()
    waiting_for_text_content_confirm = State()
    
    # Categories
    waiting_for_category_name = State()
    waiting_for_category_name_en = State()
    waiting_for_category_slug = State()
    waiting_for_category_sort_order = State()
    waiting_for_category_rename = State()
    
    # Promo Codes
    waiting_for_promo_code = State()
    waiting_for_promo_discount = State()
    waiting_for_promo_description = State()
    waiting_for_promo_usage_limit = State()
    waiting_for_promo_min_amount = State()
    waiting_for_promo_valid_until = State()


# ============================================
# Константи для адмін-навігації
# ============================================

class AdminPages:
    """Константи для сторінок адмін-панелі."""
    # Головне меню
    MAIN = "admin_main"
    
    # Замовлення
    ORDERS = "admin_orders"
    ORDERS_PENDING = "admin_orders_pending"
    ORDERS_PAID = "admin_orders_paid"
    ORDERS_SHIPPED = "admin_orders_shipped"
    ORDERS_ALL = "admin_orders_all"
    ORDER_DETAILS = "admin_order_details"
    
    # Товари
    PRODUCTS = "admin_products"
    PRODUCTS_LIST = "admin_products_list"
    PRODUCT_VIEW = "admin_product_view"
    PRODUCT_EDIT = "admin_product_edit"
    PRODUCT_ADD = "admin_product_add"
    
    # Категорії
    CATEGORIES = "admin_categories"
    CATEGORY_EDIT = "admin_category_edit"
    CATEGORY_ADD = "admin_category_add"
    
    # Аналітика
    ANALYTICS = "admin_analytics"
    STATS_GENERAL = "admin_stats_general"
    STATS_DISCOUNTS = "admin_stats_discounts"
    STATS_LOYALTY = "admin_stats_loyalty"
    STATS_SALES = "admin_stats_sales"
    
    # Користувачі
    USERS = "admin_users"
    USERS_LIST = "admin_users_list"
    USER_SEARCH = "admin_users_search"
    
    # Контент
    CONTENT = "admin_content"
    CONTENT_TEXTS = "admin_content_texts"
    CONTENT_IMAGES = "admin_content_images"
    CONTENT_DISCOUNTS = "admin_content_discounts"
    
    # Промокоди
    PROMOS = "admin_promos"
    PROMOS_LIST = "admin_promos_list"
    PROMO_ADD = "admin_promo_add"
    PROMO_EDIT = "admin_promo_edit"
