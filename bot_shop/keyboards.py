from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

keyboard_lang = InlineKeyboardMarkup().add(
                InlineKeyboardButton("Українська мова 🇺🇦", callback_data='lang_ua'),
                InlineKeyboardButton("Русский язык 🇷🇺", callback_data='lang_ru')
            )
keyboard_main = InlineKeyboardMarkup().add(
    InlineKeyboardButton("🛒 Корзина", callback_data='show_basket'),
    InlineKeyboardButton("🔍 Перейти к фильтрам", callback_data='go_to_filters'),
    InlineKeyboardButton("🔗 Техническая поддержка", callback_data='support'),
	InlineKeyboardButton("⬅️ Назад", callback_data='back_to_lang')
)
keyboard_main_ua = InlineKeyboardMarkup().add(
    InlineKeyboardButton("🛒 Корзина", callback_data='show_basket_ua'),
    InlineKeyboardButton("🔍 Перейти до фильтрів", callback_data='go_to_filters_ua'),
    InlineKeyboardButton("🔗 Технічна підтримка", callback_data='support_ua'),
	InlineKeyboardButton("⬅️ Назад", callback_data='back_to_lang')
)
keyboard_support_back = InlineKeyboardMarkup().add(
	InlineKeyboardButton("⬅️ Назад", callback_data='support_back')
)
keyboard_country = InlineKeyboardMarkup().add(
    InlineKeyboardButton("🇪🇬 Товары из Египта", callback_data='country_egypt'),
    InlineKeyboardButton("🇹🇷 Товары из Турции", callback_data='country_turkey'),
    InlineKeyboardButton("🇦🇪 Товары из ОАЭ", callback_data='country_emirates'),
	InlineKeyboardButton("⬅️ Назад", callback_data='back_to_lang')
)
keyboard_country_ua = InlineKeyboardMarkup().add(
    InlineKeyboardButton("🇪🇬 Товари з Египту", callback_data='ua_egypt'),
    InlineKeyboardButton("🇹🇷 Товари з Турції", callback_data='ua_turkey'),
    InlineKeyboardButton("🇦🇪 Товари з ОАЄ", callback_data='ua_emirates'),
	InlineKeyboardButton("⬅️ Назад", callback_data='back_to_lang')
)
keyboard_category = InlineKeyboardMarkup().add(
    InlineKeyboardButton("🚿 Шампуни и косметические товары для волос", callback_data='category_shampoos'),
    InlineKeyboardButton("💄 Декоративная косметика", callback_data='category_cosmetic'),
    InlineKeyboardButton("🌸 Парфумерия", callback_data='category_perfume'),
    InlineKeyboardButton("💆🏻 Массажные пренадлежности", callback_data='category_massage'),
    InlineKeyboardButton("🍵 Чаи", callback_data='category_tea'),
    InlineKeyboardButton("☕ Кофе", callback_data='category_coffe'),
    InlineKeyboardButton("🍶 Крема", callback_data='category_cream'),
    InlineKeyboardButton("💊 Лекарства", callback_data='category_drugs'),
    InlineKeyboardButton("🔠 Витамины", callback_data='category_vitamin'),
    InlineKeyboardButton("🧴 Масла", callback_data='category_oil'),
    InlineKeyboardButton("⚕️ Мази", callback_data='category_ointment'),
    InlineKeyboardButton("🗞️ Зубные пасты", callback_data='category_toothpaste'),
    InlineKeyboardButton("🥗 Еда", callback_data='category_food'),
    InlineKeyboardButton("🧪 Дезодоранты", callback_data='category_deodorant'),
    InlineKeyboardButton("🧽 Гели", callback_data='category_gel'),
    InlineKeyboardButton("🕯️ Свечи", callback_data='category_candle'),
    InlineKeyboardButton("🪒 Товары для депиляции и бритья", callback_data='category_depilation'),
    InlineKeyboardButton("👛 Кошелек", callback_data='category_wallet'),
    InlineKeyboardButton("🏊 Товары для плавания", callback_data='category_swimming'),
    InlineKeyboardButton("🎭 Маски для лица", callback_data='category_mask'),
    InlineKeyboardButton("🧼 Скрабы", callback_data='category_scrub'),
	InlineKeyboardButton("⬅️ Назад", callback_data='back')
)
keyboard_category_ua = InlineKeyboardMarkup().add(
    InlineKeyboardButton("🚿 Шампуні та косметичні товари для волосся", callback_data='catu_shampoos'),
    InlineKeyboardButton("💄 Декоративна косметика", callback_data='catu_cosmetic'),
    InlineKeyboardButton("🌸 Парфумерія", callback_data='catu_perfume'),
    InlineKeyboardButton("💆🏻 Масажне приладдя", callback_data='catu_massage'),
    InlineKeyboardButton("🍵 Чаї", callback_data='catu_tea'),
    InlineKeyboardButton("☕ Кава", callback_data='catu_coffe'),
    InlineKeyboardButton("🍶 Креми", callback_data='catu_cream'),
    InlineKeyboardButton("💊 Ліки", callback_data='catu_drugs'),
    InlineKeyboardButton("🔠 Вітаміни", callback_data='catu_vitamin'),
    InlineKeyboardButton("🧴 Олії", callback_data='catu_oil'),
    InlineKeyboardButton("⚕️ Мазі", callback_data='catu_ointment'),
    InlineKeyboardButton("🗞️ Зубні пасти", callback_data='catu_toothpaste'),
    InlineKeyboardButton("🥗 Їжа", callback_data='catu_food'),
    InlineKeyboardButton("🧪 Дезодоранти", callback_data='catu_deodorant'),
    InlineKeyboardButton("🧽 Гелі", callback_data='catu_gel'),
    InlineKeyboardButton("🕯️ Свічки", callback_data='catu_candle'),
    InlineKeyboardButton("🪒 Товари для депіляції та гоління", callback_data='catu_depilation'),
    InlineKeyboardButton("👛 Гаманці", callback_data='catu_wallet'),
    InlineKeyboardButton("🏊 Товари для плавання", callback_data='catu_swimming'),
    InlineKeyboardButton("🎭 Маски для обличчя", callback_data='catu_mask'),
    InlineKeyboardButton("🧼 Скраби", callback_data='catu_scrub'),
    InlineKeyboardButton("⬅️ Назад", callback_data='back_ua')
)

keyboard_buy = InlineKeyboardMarkup().add(
    InlineKeyboardButton("🛒 Добавить в корзину", callback_data='add_to_basket'),
	InlineKeyboardButton("⬅️ Назад", callback_data='back')
)
keyboard_buy_ua = InlineKeyboardMarkup().add(
    InlineKeyboardButton("🛒 Додати в корзину", callback_data='add_to_basket_ua'),
	InlineKeyboardButton("⬅️ Назад", callback_data='back_ua')
)
keyboard_back = InlineKeyboardMarkup().add(
	InlineKeyboardButton("⬅️ Назад", callback_data='back')
)
keyboard_back_ua = InlineKeyboardMarkup().add(
	InlineKeyboardButton("⬅️ Назад", callback_data='back_ua')
)
keyboard_back_prescr = InlineKeyboardMarkup().add(
	InlineKeyboardButton("⬅️ Назад", callback_data='back_prescr')
)
keyboard_delete = InlineKeyboardMarkup().add(
    InlineKeyboardButton("🗑️ Удалить", callback_data='delete_from_basket'),
	InlineKeyboardButton("⬅️ Назад", callback_data='back')
)
keyboard_delete_ua = InlineKeyboardMarkup().add(
    InlineKeyboardButton("🗑️ Удалить", callback_data='delete_from_basket_ua'),
	InlineKeyboardButton("⬅️ Назад", callback_data='back_ua')
)
keyboard_back_form = InlineKeyboardMarkup().add(
	InlineKeyboardButton("⬅️ Назад", callback_data='back_form')
)