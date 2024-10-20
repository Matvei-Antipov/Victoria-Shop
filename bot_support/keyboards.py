from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

keyboard_main = InlineKeyboardMarkup().add(
	InlineKeyboardButton("❓ Создать вопрос в службу поддержки", callback_data='create_question')
)
keyboard_main_ua = InlineKeyboardMarkup().add(
	InlineKeyboardButton("❓ Створити питання до служби підтримки", callback_data='create_question_ua')
)
keyboard_admin = InlineKeyboardMarkup().add(
	InlineKeyboardButton("📖 Список обращений", callback_data='list_of_tickets'),
	InlineKeyboardButton("💵 Бухгалтерский отчет", callback_data='accountant_reply'),
	InlineKeyboardButton("📕 Работа с товарами", callback_data='job_with_goods'),
	InlineKeyboardButton("💸 Конвертор валют", callback_data='convertator'),
	InlineKeyboardButton("⬅️ Назад", callback_data='back')
)
keyboard_convertator = InlineKeyboardMarkup().add(
	InlineKeyboardButton("₴ UAH/USD $", callback_data='uah_usd'),
	InlineKeyboardButton("$ USD/UAH ₴", callback_data='usd_uah'),
	InlineKeyboardButton("$ USD/EGP £", callback_data='usd_egp'),
	InlineKeyboardButton("₴ UAH/EGP £", callback_data='uah_egp'),
	InlineKeyboardButton("₴ UAH/TRY ₺", callback_data='uah_try'),
	InlineKeyboardButton("⬅️ Назад", callback_data='back')
)
keyboard_back = InlineKeyboardMarkup().add(
	InlineKeyboardButton("⬅️ Назад", callback_data='back')
)
keyboard_back_ua = InlineKeyboardMarkup().add(
	InlineKeyboardButton("⬅️ Назад", callback_data='back_ua')
)
keyboard_lang = InlineKeyboardMarkup().add(
	InlineKeyboardButton("Українська мова 🇺🇦", callback_data='lang_ua'),
	InlineKeyboardButton("Русский язык 🇷🇺", callback_data='lang_ru')
)
keyboard_goods = InlineKeyboardMarkup().add(
	InlineKeyboardButton("⬆️ Загрузить товар", callback_data='upload_good'),
	InlineKeyboardButton("⚙️ Настройки товаров", callback_data='settings'),
    InlineKeyboardButton("📘 Список товаров", callback_data='list_of_goods'),
    InlineKeyboardButton("⬅️ Назад", callback_data='back')
)
keyboard_skip = InlineKeyboardMarkup().add(
    InlineKeyboardButton("⏭ Далее", callback_data='skip'),
	InlineKeyboardButton("⬅️ Назад", callback_data='back_skip')
)
keyboard_country = InlineKeyboardMarkup().add(
    InlineKeyboardButton("🇪🇬 Товары из Египта", callback_data='country_egypt'),
    InlineKeyboardButton("🇹🇷 Товары из Турции", callback_data='country_turkey'),
    InlineKeyboardButton("🇦🇪 Товары из ОАЭ", callback_data='country_emirates'),
	InlineKeyboardButton("⬅️ Назад", callback_data='back_skip')
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
	InlineKeyboardButton("⬅️ Назад", callback_data='back_skip')
)
keyboard_settings_list = InlineKeyboardMarkup().add(
    InlineKeyboardButton("📛 Название", callback_data='set_name'),
    InlineKeyboardButton("🏷️ Цена", callback_data='set_price'),
    InlineKeyboardButton("💭 Описание", callback_data='set_prescription'),
    InlineKeyboardButton("📜 Статус наличия", callback_data='set_status'),
    InlineKeyboardButton("🗑️ Удалить товар", callback_data='delete_good'),
	InlineKeyboardButton("⬅️ Назад", callback_data='back')
)
keyboard_status = InlineKeyboardMarkup().add(
    InlineKeyboardButton("👌 В наличии", callback_data='set_yes'),
    InlineKeyboardButton("⛔ Нет в наличии", callback_data='set_no'),
	InlineKeyboardButton("⬅️ Назад", callback_data='back')
)
keyboard_back_prescr = InlineKeyboardMarkup().add(
	InlineKeyboardButton("⬅️ Назад", callback_data='back_prescr')
)