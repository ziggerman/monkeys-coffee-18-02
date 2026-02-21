"""Admin panel keyboards."""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def get_admin_panel_keyboard() -> InlineKeyboardMarkup:
    """Get main admin panel keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="📋 Замовлення",
        callback_data="admin_orders"
    ))

    builder.row(InlineKeyboardButton(
        text="🫘 Товари",
        callback_data="admin_products"
    ))
    
    builder.row(InlineKeyboardButton(
        text="📂 Категорії",
        callback_data="admin_categories"
    ))
    
    builder.row(InlineKeyboardButton(
        text="📊 Аналітика",
        callback_data="admin_analytics"
    ))
    
    builder.row(InlineKeyboardButton(
        text="👥 Користувачі",
        callback_data="admin_users_main"
    ))
    
    builder.row(InlineKeyboardButton(
        text="🎛 Конструктор",
        callback_data="admin_content_main"
    ))
    
    builder.row(InlineKeyboardButton(
        text="🎟️ Промокоди",
        callback_data="admin_promos_list"
    ))
    
    return builder.as_markup()


def get_order_management_keyboard() -> InlineKeyboardMarkup:
    """Get order management keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="Очікують оплати",
        callback_data="admin_orders_pending"
    ))
    
    builder.row(InlineKeyboardButton(
        text="Оплачені",
        callback_data="admin_orders_paid"
    ))
    
    builder.row(InlineKeyboardButton(
        text="Відправлені",
        callback_data="admin_orders_shipped"
    ))
    
    builder.row(InlineKeyboardButton(
        text="Всі замовлення",
        callback_data="admin_orders_all"
    ))
    
    builder.row(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="admin_main"
    ))
    
    return builder.as_markup()


def get_order_action_keyboard(order_id: int, current_status: str) -> InlineKeyboardMarkup:
    """Get order action keyboard based on status."""
    builder = InlineKeyboardBuilder()
    
    if current_status == "pending":
        builder.row(InlineKeyboardButton(
            text="Підтвердити оплату",
            callback_data=f"admin_order_paid:{order_id}"
        ))
    
    if current_status == "paid":
        builder.row(InlineKeyboardButton(
            text="Відправити (ТТН)",
            callback_data=f"admin_order_ship:{order_id}"
        ))
    
    if current_status == "shipped":
        builder.row(InlineKeyboardButton(
            text="Позначити доставленим",
            callback_data=f"admin_order_delivered:{order_id}"
        ))
    
    builder.row(InlineKeyboardButton(
        text="Скасувати замовлення",
        callback_data=f"admin_order_cancel:{order_id}"
    ))
    
    builder.row(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="admin_orders"
    ))
    
    return builder.as_markup()


def get_admin_product_list_keyboard(products: list) -> InlineKeyboardMarkup:
    """Get keyboard for product listing in admin panel."""
    builder = InlineKeyboardBuilder()
    
    for product in products:
        status_text = "✅" if product.is_active else "🚫"
        builder.row(InlineKeyboardButton(
            text=f"{status_text} {product.name_ua}",
            callback_data=f"admin_product_view:{product.id}"
        ))
    
    builder.row(InlineKeyboardButton(
        text="➕ Додати товар",
        callback_data="admin_product_add"
    ))
    
    builder.row(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="admin_main"
    ))
    
    return builder.as_markup()


def get_product_action_keyboard(product_id: int, is_active: bool) -> InlineKeyboardMarkup:
    """Get product action keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="Редагувати",
        callback_data=f"admin_product_edit:{product_id}"
    ))
    
    builder.row(InlineKeyboardButton(
        text="Видалити",
        callback_data=f"admin_prod_del:{product_id}"
    ))
    
    if is_active:
        builder.row(InlineKeyboardButton(
            text="Деактивувати",
            callback_data=f"admin_product_deactivate:{product_id}"
        ))
    else:
        builder.row(InlineKeyboardButton(
            text="Активувати",
            callback_data=f"admin_product_activate:{product_id}"
        ))
    
    builder.row(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="admin_products_list"
    ))
    
    return builder.as_markup()


def get_analytics_keyboard() -> InlineKeyboardMarkup:
    """Get analytics keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="Загальна статистика",
        callback_data="admin_stats_general"
    ))
    
    builder.row(InlineKeyboardButton(
        text="Звіт по знижках",
        callback_data="admin_stats_discounts"
    ))
    
    builder.row(InlineKeyboardButton(
        text="Лояльність рівні",
        callback_data="admin_stats_loyalty"
    ))
    
    builder.row(InlineKeyboardButton(
        text="Продажі за період",
        callback_data="admin_stats_sales"
    ))
    
    builder.row(InlineKeyboardButton(
        text="Список користувачів",
        callback_data="admin_users_list"
    ))
    
    builder.row(InlineKeyboardButton(
        text="Список промокодів",
        callback_data="admin_promos_list"
    ))
    
    builder.row(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="admin_main"
    ))
    
    return builder.as_markup()


def get_admin_users_keyboard() -> InlineKeyboardMarkup:
    """Get user management menu keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="Список (Останні 20)",
        callback_data="admin_users_list"
    ))
    
    builder.row(InlineKeyboardButton(
        text="Пошук користувача",
        callback_data="admin_users_search"
    ))
    
    builder.row(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="admin_main"
    ))
    
    return builder.as_markup()


def get_product_edit_fields_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Get keyboard for selecting a field to edit."""
    builder = InlineKeyboardBuilder()
    
    fields = [
        ("Назва (UA)", "name_ua"),
        ("Походження", "origin"),
        ("Ціна 300г", "price_300g"),
        ("Ціна 1кг", "price_1kg"),
        ("Профіль", "profile"),
        ("Ступінь обсмаження", "roast_level"),
        ("Метод обробки", "processing_method"),
        ("Нотатки", "tasting_notes"),
        ("Опис", "description"),
        ("Зображення", "image"),
        ("Категорія", "category"),
    ]
    
    for label, field in fields:
        builder.row(InlineKeyboardButton(
            text=label,
            callback_data=f"admin_product_edit_field:{product_id}:{field}"
        ))
    
    builder.row(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data=f"admin_product_view:{product_id}"
    ))
    
    return builder.as_markup()


def get_product_delete_confirm_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Get keyboard for confirming product deletion."""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(
        text="ТАК, ВИДАЛИТИ",
        callback_data=f"admin_prod_conf_del:{product_id}"
    ))
    
    builder.row(InlineKeyboardButton(
        text="🔙 Скасувати",
        callback_data=f"admin_product_view:{product_id}"
    ))
    
    return builder.as_markup()


def get_roast_level_keyboard(category: str = "coffee") -> InlineKeyboardMarkup:
    """Get keyboard for selecting roast level."""
    builder = InlineKeyboardBuilder()
    
    levels = [
        ("🟡 Світле (Light)", "roast_light"),
        ("🟠 Середнє (Medium)", "roast_medium"),
        ("⚫ Темне (Dark)", "roast_dark"),
        ("🥤 Еспресо (Espresso)", "roast_espresso"),
        ("🫖 Фільтр (Filter)", "roast_filter"),
        ("⚗️ Омні (Omni)", "roast_omni"),
    ]
    
    for label, code in levels:
        builder.row(InlineKeyboardButton(text=label, callback_data=f"admin_roast:{code}"))
        
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_product_back:{category}"))
    return builder.as_markup()


def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for selecting profile."""
    builder = InlineKeyboardBuilder()
    
    profiles = [
        ("🥤 Еспресо (Espresso)", "profile_espresso"),
        ("🫖 Фільтр (Filter)", "profile_filter"),
        ("⚗️ Універсальна (Universal)", "profile_universal"),
    ]
    
    for label, code in profiles:
        builder.row(InlineKeyboardButton(text=label, callback_data=f"admin_profile:{code}"))
        
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_product_back:roast"))
    return builder.as_markup()


def get_processing_method_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for selecting processing method."""
    builder = InlineKeyboardBuilder()
    
    methods = [
        ("💧 Мита (Washed)", "proc_washed"),
        ("☀️ Натуральна (Natural)", "proc_natural"),
        ("🍯 Хані (Honey)", "proc_honey"),
        ("🧪 Анаеробна (Anaerobic)", "proc_anaerobic"),
        ("🧬 Експериментальна", "proc_experimental"),
    ]
    
    for label, code in methods:
        builder.row(InlineKeyboardButton(text=label, callback_data=f"admin_proc:{code}"))
        
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_product_back:roast"))
    return builder.as_markup()


def get_skip_image_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for skipping image upload."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="Пропустити крок 🖼️",
        callback_data="admin_product_skip_image"
    ))
    builder.row(InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="admin_product_back:price_1kg"
    ))
    return builder.as_markup()


def get_product_category_keyboard(categories: list) -> InlineKeyboardMarkup:
    """Get keyboard for selecting product category from DB."""
    builder = InlineKeyboardBuilder()
    
    for cat in categories:
        # Show emoji for category with image
        has_image = "🖼️ " if cat.image_file_id or cat.image_path else ""
        builder.row(InlineKeyboardButton(
            text=f"{has_image}{cat.name_ua}", 
            callback_data=f"admin_cat:{cat.slug}"
        ))
    
    builder.row(InlineKeyboardButton(text="➕ Створити нову категорію", callback_data="admin_cat_add_from_product"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main"))
    return builder.as_markup()
def get_content_management_keyboard() -> InlineKeyboardMarkup:
    """Get content & discounts management keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(InlineKeyboardButton(text="📝 Редагувати Тексти", callback_data="admin_content_texts"))
    builder.row(InlineKeyboardButton(text="🖼️ Керування зображеннями", callback_data="admin_content_images"))
    builder.row(InlineKeyboardButton(text="⚡ Оптові знижки", callback_data="admin_content_discounts"))
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main"))
    
    return builder.as_markup()


def get_image_management_keyboard(modules: dict) -> InlineKeyboardMarkup:
    """Get keyboard for selecting a module to update image."""
    builder = InlineKeyboardBuilder()
    
    for key, label in modules.items():
        builder.row(InlineKeyboardButton(text=label, callback_data=f"admin_img_mod:{key}"))
        
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_content_main"))
    return builder.as_markup()








def get_content_editor_keyboard(items: list) -> InlineKeyboardMarkup:
    """Get keyboard for selecting text content to edit."""
    builder = InlineKeyboardBuilder()
    
    # Group by category
    categories = {}
    for item in items:
        if item.category not in categories:
            categories[item.category] = []
        categories[item.category].append(item)
    
    for cat, cat_items in categories.items():
        builder.row(InlineKeyboardButton(text=f"📂 {cat.upper()}", callback_data="ignore"))
        for item in cat_items:
            builder.row(InlineKeyboardButton(
                text=f"✏️ {item.description}",
                callback_data=f"admin_edit_text:{item.key}"
            ))
            
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="admin_content_main"))
    return builder.as_markup()


def get_text_edit_action_keyboard(key: str) -> InlineKeyboardMarkup:
    """Get action keyboard for text editing — with AI generate and reset buttons."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🤖 AI Генерація", callback_data=f"admin_ai_gen_text:{key}"),
        InlineKeyboardButton(text="🔄 Скинути", callback_data=f"admin_reset_text:{key}")
    )
    builder.row(InlineKeyboardButton(text="🔙 Скасувати", callback_data="admin_content_texts"))
    return builder.as_markup()


def get_confirm_save_keyboard() -> InlineKeyboardMarkup:
    """Confirm/edit/cancel keyboard after preview."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Зберегти", callback_data="admin_text_save"),
        InlineKeyboardButton(text="✏️ Редагувати", callback_data="admin_text_edit_continue")
    )
    builder.row(InlineKeyboardButton(text="❌ Скасувати", callback_data="admin_text_cancel"))
    return builder.as_markup()


def get_back_keyboard(target: str) -> InlineKeyboardMarkup:
    """Get keyboard with just a back button."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_product_back:{target}"))
    return builder.as_markup()


def get_inline_cancel_keyboard() -> InlineKeyboardMarkup:
    """Get inline keyboard with just a cancel button."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Скасувати", callback_data="admin_main"))
    return builder.as_markup()


def get_product_edit_description_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Get keyboard for editing description with AI generate option."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✨ Згенерувати з AI", callback_data=f"admin_product_ai_gen:{product_id}"))
    builder.row(InlineKeyboardButton(text="❌ Скасувати", callback_data=f"admin_product_edit:{product_id}"))
    return builder.as_markup()


def get_apply_ai_text_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Get keyboard to apply AI generated text."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Застосувати", callback_data=f"admin_product_ai_apply:{product_id}"))
    builder.row(InlineKeyboardButton(text="🔄 Спробувати ще", callback_data=f"admin_product_ai_gen:{product_id}"))
    builder.row(InlineKeyboardButton(text="❌ Скасувати", callback_data=f"admin_product_edit:{product_id}"))
    return builder.as_markup()
