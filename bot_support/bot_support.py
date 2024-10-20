#imports

import asyncpg
import datetime
import requests
import base64
from bson import ObjectId
from pymongo import MongoClient
from aiogram import Dispatcher, Bot, types, executor
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
	ContentType
)
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import API_TOKEN, CLUSTER_URL, DATABASE_CONFIG
from keyboards import (
    keyboard_main,
	keyboard_main_ua,
    keyboard_admin,
    keyboard_back,
	keyboard_back_ua,
	keyboard_lang,
	keyboard_goods,
	keyboard_skip,
	keyboard_settings_list,
	keyboard_status,
	keyboard_category,
	keyboard_country,
	keyboard_back_prescr
)
from functions import (
    get_time_from_datetime,
    can_make_new_ticket,
    get_last_ticket_time,
    get_user_status,
	get_income,
	uah_usd_convertor,
	usd_uah_convertor,
	usd_egp_convertor,
	uah_egp_convertor,
	uah_try_convertor,
	format_response,
	generate_random_4_digit_number,
	translate_text,
	display_records
)
from constants import template_reply, template_reply_rules_of_presc, template_reply_ua

#api_token

token = API_TOKEN
bot = Bot(token)
dp = Dispatcher(bot, storage=MemoryStorage())

#database MongoDB

cluster = MongoClient(CLUSTER_URL)

db = cluster['VIC_BOT_SUPPORT']
collection_users = db['collection_users']
collection_tickets = db['collection_tickets']
collection_accounting = db['collection_accounting']
collection_goods = db['collection_goods']

#database PostgreSQL

async def on_startup(dp):
    try:
        dp['db'] = await asyncpg.create_pool(**DATABASE_CONFIG)
        print("Connected to PostgreSQL")
    except Exception as e:
        print(f"Error of connection to PostgreSQL: {e}")

async def on_shutdown(dp):
    try:
        await dp['db'].close()
        print("Closed PostgreSQL")
    except Exception as e:
        print(f"Error of closing PostgreSQL: {e}")

#states

class ClientStates(StatesGroup):

	ticket = State()
	ticket_ua = State()
	document_income = State()
	document_expense = State()
	document_deals = State()
	uah_usd = State()
	usd_uah = State()
	usd_egp = State()
	uah_egp = State()
	uah_try = State()
	presc_good = State()
	get_articul = State()
	get_name = State()
	get_price = State()
	get_prescription = State()

class AdministratorUploadHandler(StatesGroup):
    uploading = State()

#check_in

check_in = {'❓ Создать вопрос в службу поддержки', '⬅️ Назад'}
admins = {'matvei_dev', 'victoria_rudnevvva'}

#start message

@dp.message_handler(commands=['start'])
async def start_buttons(message: types.Message):
	user_id = message.from_user.username
	if user_id is not None:
		if user_id in admins:
			status = 'administrator'
		else:
			status = 'default'
		user = {
			'tg_name': user_id,
			'status': status
		}
		existing_user = collection_users.find_one({'tg_name': user_id})
		if existing_user:
			user_status = get_user_status(user_id)
			if user_status == 'administrator':
				keyboard_lang = InlineKeyboardMarkup().add(
					InlineKeyboardButton("Русский язык 🇷🇺", callback_data='lang_ru')
				)
					
				await message.answer(
					f'Здравствуйте, *{message.from_user.first_name}*!\n\nВыберите язык:',
					reply_markup=keyboard_lang,
					parse_mode='Markdown'
				)
			else:
				keyboard_lang = InlineKeyboardMarkup().add(
					InlineKeyboardButton("Українська мова 🇺🇦", callback_data='lang_ua_def'),
					InlineKeyboardButton("Русский язык 🇷🇺", callback_data='lang_ru_def')
				)
					
				await message.answer(
					f'Здравствуйте, *{message.from_user.first_name}*!\n\nВыберите язык:',
					reply_markup=keyboard_lang,
					parse_mode='Markdown'
				)
		else:
			collection_users.insert_one(user)
			user_status = get_user_status(user_id)
			if user_status == 'administrator':
				keyboard_lang = InlineKeyboardMarkup().add(
					InlineKeyboardButton("Українська мова 🇺🇦", callback_data='lang_ua'),
					InlineKeyboardButton("Русский язык 🇷🇺", callback_data='lang_ru')
				)
					
				await message.answer(
					f'Здравствуйте, *{message.from_user.first_name}*!\n\nВыберите язык:',
					reply_markup=keyboard_lang,
					parse_mode='Markdown'
				)
			else:
				keyboard_lang = InlineKeyboardMarkup().add(
					InlineKeyboardButton("Українська мова 🇺🇦", callback_data='lang_ua_def'),
					InlineKeyboardButton("Русский язык 🇷🇺", callback_data='lang_ru_def')
				)
					
				await message.answer(
					f'Здравствуйте, *{message.from_user.first_name}*!\n\nВыберите язык:',
					reply_markup=keyboard_lang,
					parse_mode='Markdown'
				)
	else:
		await message.answer(
			'Для работы со службой тех.поддержки вы *обязаны* установить ID в настройках мессенджера Telegram',
			parse_mode='Markdown'
			)

#handlers(RU, administration GUI)

@dp.callback_query_handler(lambda c: c.data == 'lang_ru')
async def administrator_gui(callback_query: types.CallbackQuery):
	user_id = callback_query.from_user.username
	user_status = get_user_status(user_id)
	if user_status == 'administrator':
		keyboard_admin = InlineKeyboardMarkup().add(
			InlineKeyboardButton("📖 Список обращений", callback_data='list_of_tickets'),
			InlineKeyboardButton("💵 Бухгалтерский отчет", callback_data='accountant_reply'),
			InlineKeyboardButton("📕 Работа с товарами", callback_data='job_with_goods'),
			InlineKeyboardButton("💸 Конвертор валют", callback_data='convertator')
		)
		
		await bot.send_message(
			callback_query.from_user.id,
			f'Здравствуйте, *{callback_query.from_user.first_name}*!\n\nУважаемый администратор, вот список функций:',
			reply_markup=keyboard_admin,
			parse_mode='Markdown',
		)

@dp.callback_query_handler(lambda c: c.data == 'list_of_tickets')
async def administrator_list_of_tickets(callback_query: types.CallbackQuery):
	user_id = callback_query.from_user.username
	user_status = get_user_status(user_id)

	if user_status == 'administrator':
		records_amount = collection_tickets.count_documents({})
		if records_amount == 0:
			await callback_query.bot.send_message(
				callback_query.from_user.id,
				f'В коллекции {records_amount} записей.',
				reply_markup=keyboard_back
			)
		else:
			keyboard_list = InlineKeyboardMarkup().add(
				InlineKeyboardButton("⬅️ Назад", callback_data='back')
			)

			for record in collection_tickets.find():
				text = record['tg_name']
				callback_data = f"show_record_tickets{record['_id']}"
				keyboard_list.add(InlineKeyboardButton(text=text, callback_data=callback_data))
				await callback_query.bot.send_message(
					callback_query.from_user.id,
					f'В коллекции {records_amount} записей. Выберите запись для просмотра:',
					reply_markup=keyboard_list,
				)

@dp.callback_query_handler(lambda query: query.data.startswith("show_record_tickets"))
async def show_record_callback(callback_query: types.CallbackQuery):
    record_id = str(callback_query.data.split("_")[2])
    word_to_remove = "tickets"
    record_id = record_id.replace(word_to_remove, '')
    record = collection_tickets.find_one({"_id": ObjectId(record_id)})

    if record:
        prompt = record.get('prompt')
        tg_name = record.get('tg_name')
        number = record.get('number')
        date = record.get('date')
        ticket_text = f"Тикет №{number}\n\nПользователь:  @{tg_name}\n\nВремя создания:  {date}\n\nТело тикета:\n{prompt}"

        keyboard = InlineKeyboardMarkup(row_width=2)
        back_button = InlineKeyboardButton("⬅️ Назад", callback_data='back')
        answered_button = InlineKeyboardButton(text="✔️ Ответ был дан", callback_data=f"answered_{record_id}")
        alarm_button = InlineKeyboardButton(text="📣 Попросить открыть ЛС", callback_data=f"alarm_{record_id}")
        keyboard.add(back_button, answered_button, alarm_button)

        await bot.send_message(callback_query.from_user.id, ticket_text, reply_markup=keyboard)
    else:
        await bot.send_message(callback_query.from_user.id, "Запись не найдена.", reply_markup=keyboard_back)


@dp.callback_query_handler(lambda query: query.data.startswith("answered_"))
async def close_or_answer_callback(callback_query: types.CallbackQuery):
    try:
        action, record_id = callback_query.data.split("_", 1)
        record = collection_tickets.find_one({"_id": ObjectId(record_id)})

        if record:
            user_id = record.get('user_id')

            if action == "answered":
                collection_tickets.delete_one({"_id": ObjectId(record_id)})
                message_text = "Ваш вопрос был решен. Спасибо за ожидание!"

            await bot.send_message(user_id, message_text, reply_markup=keyboard_back)
            await bot.send_message(callback_query.from_user.id, f"Действие выполнено: {message_text}", reply_markup=keyboard_back)
        else:
            await bot.send_message(callback_query.from_user.id, "Запись не найдена.", reply_markup=keyboard_back)
    except Exception:
        await bot.send_message(callback_query.from_user.id, f"Произошла ошибка!", reply_markup=keyboard_back)

@dp.callback_query_handler(lambda query: query.data.startswith("alarm_"))
async def alarm(callback_query: types.CallbackQuery):
    try:
        action, record_id = callback_query.data.split("_", 1)
        record = collection_tickets.find_one({"_id": ObjectId(record_id)})

        if record:
            user_id = record.get('user_id')

            if action == "alarm":
                message_text = "Модератор хочет решить ваш вопрос, но вы закрыли личные сообщения, пожалуйста откройте их для связи с нами! С пониманием комманда поддержки."

            await bot.send_message(user_id, message_text, reply_markup=keyboard_back)
            await bot.send_message(callback_query.from_user.id, f"Действие выполнено!", reply_markup=keyboard_back)
        else:
            await bot.send_message(callback_query.from_user.id, "Запись не найдена!", reply_markup=keyboard_back)
    except Exception:
        await bot.send_message(callback_query.from_user.id, f"Произошла ошибка!", reply_markup=keyboard_back)

@dp.callback_query_handler(lambda c: c.data == 'accountant_reply')
async def administrator_accountant(callback_query: types.CallbackQuery):
	user_id = callback_query.from_user.username
	user_status = get_user_status(user_id)

	if user_status=='administrator':
		keyboard_accountant = InlineKeyboardMarkup().add(
			InlineKeyboardButton("⬆️ Загрузить данные", callback_data='upload_document'),
			InlineKeyboardButton("⬇️ Получить итоги месяца", callback_data='get_document'),
			InlineKeyboardButton("⬅️ Назад", callback_data='back')
		)

	await bot.send_message(
			callback_query.from_user.id,
			f'Здравствуйте, *{callback_query.from_user.first_name}*!\n\nУважаемый администратор, вот список функций бухгалтерии:',
			reply_markup=keyboard_accountant,
			parse_mode='Markdown',
		)

@dp.callback_query_handler(lambda c: c.data == 'upload_document')
async def administrator_accountant_upload(callback_query: types.CallbackQuery):
	user_id = callback_query.from_user.username
	user_status = get_user_status(user_id)

	if user_status=='administrator':
		await ClientStates.document_income.set()

		await bot.send_message(
		callback_query.from_user.id,
        f'Здравствуйте, *{callback_query.from_user.first_name}*!\n\nВведите доход за день без значка валюты слитно\n\nНапример доход в 12.000грн введите как - 12000',
        reply_markup=keyboard_back,
        parse_mode='Markdown',
    )

@dp.message_handler(state=ClientStates.document_income)
async def create_income(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        user_id = message.from_user.username
        user_status = get_user_status(user_id)
        day = datetime.datetime.now().date()
        converted_datetime = datetime.datetime.combine(day, datetime.datetime.min.time())
        formatted_date = converted_datetime.strftime("%Y-%m-%d")
        existing_record = collection_accounting.find_one({"day": formatted_date})

        if user_status == 'administrator':
            if not existing_record:
                data['document_income'] = message.text
                income = {
                    'income': data['document_income'],
                    'day': formatted_date
                }
                collection_accounting.insert_one(income)
                await state.finish()
                await message.answer('Запись о доходах создана!')
            else:
                await state.finish()
                await message.answer('Вы уже отправляли сегодня отчет о доходах\n\nВыберите функцию:', reply_markup=keyboard_admin)


@dp.callback_query_handler(lambda c: c.data == 'get_document')
async def administrator_accountant_get(callback_query: types.CallbackQuery):
	user_id = callback_query.from_user.username
	user_status = get_user_status(user_id)

	if user_status=='administrator':
		await bot.send_message(
			callback_query.from_user.id,
			f'{get_income()}'
		)
@dp.callback_query_handler(lambda c: c.data == 'convertator')
async def administrator_currency(callback_query: types.CallbackQuery):
	user_id = callback_query.from_user.username
	user_status = get_user_status(user_id)

	if user_status == 'administrator':
		keyboard_convertator = InlineKeyboardMarkup().add(
			InlineKeyboardButton("₴ UAH/USD $", callback_data='uah_usd'),
			InlineKeyboardButton("$ USD/UAH ₴", callback_data='usd_uah'),
			InlineKeyboardButton("$ USD/EGP £", callback_data='usd_egp'),
			InlineKeyboardButton("₴ UAH/EGP £", callback_data='uah_egp'),
			InlineKeyboardButton("₴ UAH/TRY ₺", callback_data='uah_try'),
			InlineKeyboardButton("⬅️ Назад", callback_data='back')
		)
		await bot.send_message(callback_query.from_user.id, 'Выберите конвертор:', reply_markup=keyboard_convertator)

@dp.callback_query_handler(lambda query: query.data == 'uah_usd')
async def administrator_uah_usd(callback_query: types.CallbackQuery):
	user_id = callback_query.from_user.username
	user_status = get_user_status(user_id)

	if user_status == 'administrator':
		await ClientStates.uah_usd.set()

		await bot.send_message(
			callback_query.from_user.id,
			'Введите целое кол-во единиц валюты *UAH(ГРН)*, которое вы хотите конвертировать в *USD(ДОЛ)*:',
			parse_mode='Markdown',
			reply_markup=keyboard_back
		)

@dp.message_handler(state=ClientStates.uah_usd)
async def create_income(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		user_id = message.from_user.username
		user_status = get_user_status(user_id)
		if user_status == 'administrator':
			data['uah_usd'] = message.text
			await message.answer(
				f"*{data['uah_usd']}* грн = *{uah_usd_convertor(data['uah_usd'])}* дол",
				parse_mode='Markdown',
				reply_markup=keyboard_back
			)

@dp.callback_query_handler(lambda query: query.data == 'usd_uah')
async def administrator_usd_uah(callback_query: types.CallbackQuery):
	user_id = callback_query.from_user.username
	user_status = get_user_status(user_id)

	if user_status == 'administrator':
		await ClientStates.usd_uah.set()

		await bot.send_message(
			callback_query.from_user.id,
			'Введите  целое кол-во единиц валюты *USD(ДОЛ)*, которое вы хотите конвертировать в *UAH(ГРН)*:',
			parse_mode='Markdown',
			reply_markup=keyboard_back
		)

@dp.message_handler(state=ClientStates.usd_uah)
async def create_income(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		user_id = message.from_user.username
		user_status = get_user_status(user_id)
		if user_status == 'administrator':
			data['usd_uah'] = message.text
			await message.answer(
				f"*{data['usd_uah']}* дол = *{usd_uah_convertor(data['usd_uah'])}* грн",
				parse_mode='Markdown',
				reply_markup=keyboard_back
			)

@dp.callback_query_handler(lambda query: query.data == 'usd_egp')
async def administrator_usd_egp(callback_query: types.CallbackQuery):
	user_id = callback_query.from_user.username
	user_status = get_user_status(user_id)

	if user_status == 'administrator':
		await ClientStates.usd_egp.set()

		await bot.send_message(
			callback_query.from_user.id,
			'Введите целое кол-во единиц валюты *USD(ДОЛ)*, которое вы хотите конвертировать в *EGP(ЛЕ)*:',
			parse_mode='Markdown',
			reply_markup=keyboard_back
		)

@dp.message_handler(state=ClientStates.usd_egp)
async def create_income(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		user_id = message.from_user.username
		user_status = get_user_status(user_id)
		if user_status == 'administrator':
			data['usd_egp'] = message.text
			await message.answer(
				f"*{data['usd_egp']}* дол = *{usd_egp_convertor(data['usd_egp'])}* ле",
				parse_mode='Markdown',
				reply_markup=keyboard_back
			)

@dp.callback_query_handler(lambda query: query.data == 'uah_egp')
async def administrator_usd_egp(callback_query: types.CallbackQuery):
	user_id = callback_query.from_user.username
	user_status = get_user_status(user_id)

	if user_status == 'administrator':
		await ClientStates.uah_egp.set()

		await bot.send_message(
			callback_query.from_user.id,
			'Введите целое кол-во единиц валюты *UAH(ГРН)*, которое вы хотите конвертировать в *EGP(ЛЕ)*:',
			parse_mode='Markdown',
			reply_markup=keyboard_back
		)

@dp.message_handler(state=ClientStates.uah_egp)
async def create_income(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		user_id = message.from_user.username
		user_status = get_user_status(user_id)
		if user_status == 'administrator':
			data['uah_egp'] = message.text
			await message.answer(
				f"*{data['uah_egp']}* грн = *{uah_egp_convertor(data['uah_egp'])}* ле",
				parse_mode='Markdown',
				reply_markup=keyboard_back
			)

@dp.callback_query_handler(lambda query: query.data == 'uah_try')
async def administrator_uah_try(callback_query: types.CallbackQuery):
	user_id = callback_query.from_user.username
	user_status = get_user_status(user_id)

	if user_status == 'administrator':
		await ClientStates.uah_try.set()

		await bot.send_message(
			callback_query.from_user.id,
			'Введите целое кол-во единиц валюты *UAH(ГРН)*, которое вы хотите конвертировать в *TRY(ЛИР)*:',
			parse_mode='Markdown',
			reply_markup=keyboard_back
		)

@dp.message_handler(state=ClientStates.uah_try)
async def uah_try_convert(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		user_id = message.from_user.username
		user_status = get_user_status(user_id)
		if user_status == 'administrator':
			data['uah_try'] = message.text
			await message.answer(
				f"*{data['uah_try']}* грн = *{uah_try_convertor(data['uah_try'])}* лир",
				parse_mode='Markdown',
				reply_markup=keyboard_back
			)

@dp.callback_query_handler(lambda query: query.data == 'job_with_goods')
async def administrator_add_good_photo(callback_query: types.CallbackQuery):
	user_id = callback_query.from_user.username
	user_status = get_user_status(user_id)
	if user_status == 'administrator':
		await bot.send_message(
				callback_query.from_user.id,
				'Функции: ',
				reply_markup=keyboard_goods
			)


@dp.callback_query_handler(lambda query: query.data == 'upload_good')
async def administrator_uah_try(callback_query: types.CallbackQuery):
	user_id = callback_query.from_user.username
	user_status = get_user_status(user_id)
	if user_status == 'administrator':
		await AdministratorUploadHandler.uploading.set()
		await bot.send_message(
				callback_query.from_user.id,
				'*ВНИМАНИЕ*\n\nНе отправляйте мне текстовые файлы\n\nОтправьте мне только *ОДНУ* фотографию вашего продукта: ',
				parse_mode='Markdown',
				reply_markup=keyboard_back
			)

@dp.message_handler(content_types=types.ContentTypes.PHOTO, state=AdministratorUploadHandler.uploading)
async def handle_photo(message: types.Message, state: FSMContext):
	user_id = message.from_user.id
	file_id = message.photo[-1].file_id
	file_info = await bot.get_file(file_id)
	file_path = file_info.file_path
	file_url = f'https://api.telegram.org/file/bot{API_TOKEN}/{file_path}'
	image_data = requests.get(file_url).content
	base64_encoded = base64.b64encode(image_data).decode('utf-8')
	document = {
        'user_id': user_id,
        'file_id': file_id,
        'base64_data': base64_encoded,
		'price':'0',
		'prescription':'0',
		'is_available': '0',
		'name':'0',
		'articul': '0',
		'category': '0',
		'country': '0'
    }
	result = collection_goods.insert_one(document)
	try:
		async with dp['db'].acquire() as connection:
			await connection.execute("""
            INSERT INTO goods (name, description, price, status, article, category, country, base64_data)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, 'tbd', 'tbd', 1111, False, 1111, 'tbd', 'tbd', str(base64_encoded))
	except Exception as e:
		print('ERROR', e)
	if result.inserted_id:
		await state.finish()
		await bot.send_message(
            user_id,
            "Изображение успешно сохранено!",
            reply_markup=keyboard_skip
        )
	else:
		last_document = collection_goods.find_one(sort=[('_id', -1)])

		if last_document:
			last_document_id = last_document['_id']
			collection_goods.delete_one({'_id': last_document_id})
			await state.finish()
			await bot.send_message(
				user_id,
				"Ошибка при сохранении изображения!",
				reply_markup=keyboard_back
			)
		else:
			await state.finish()
			await bot.send_message(
				user_id,
				"Ошибка при сохранении изображения!",
				reply_markup=keyboard_back
			)

@dp.callback_query_handler(lambda query: query.data == 'skip')
async def administrator_presc(callback_query: types.CallbackQuery):
	user_id = callback_query.from_user.username
	user_status = get_user_status(user_id)
	if user_status == 'administrator':
		await ClientStates.presc_good.set()
		await bot.send_message(
				callback_query.from_user.id,
				f'*ВНИМАНИЕ*\nВнимательно следуйте указаниям\n\n{template_reply_rules_of_presc}',
				parse_mode='Markdown'
			)

@dp.message_handler(state=ClientStates.presc_good)
async def presc_good_uploading(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        user_id = message.from_user.username
        user_status = get_user_status(user_id)
        
        if user_status == 'administrator':
            data['presc_good'] = message.text
            try:
                name, price, prescription = format_response(data['presc_good'])
                try:
                    prescription = prescription.replace("*", "")
                except:
                    pass
                latest_record = collection_goods.find_one(sort=[('_id', -1)])
                articul = generate_random_4_digit_number()
                while collection_goods.find_one({"articul": articul}):
                    articul = generate_random_4_digit_number()
                try:
                    async with dp['db'].acquire() as connection:
                        await connection.execute("""
                            UPDATE goods
                            SET
                                name = $1,
                                description = $2,
                                price = $3,
                                status = $4,
                                article = $5
                            WHERE
                                id = (SELECT id FROM goods ORDER BY id DESC LIMIT 1);
                        """, str(name), str(prescription), float(price), True, int(articul))
                except Exception as e:
                    print('ERROR', e)
                collection_goods.update_one({'_id': latest_record['_id']}, {'$set': {'price': price}})
                collection_goods.update_one({'_id': latest_record['_id']}, {'$set': {'prescription': prescription}})
                collection_goods.update_one({'_id': latest_record['_id']}, {'$set': {'is_available': '1'}})
                collection_goods.update_one({'_id': latest_record['_id']}, {'$set': {'name': name}})
                collection_goods.update_one({'_id': latest_record['_id']}, {'$set': {'articul': articul}})

                await state.finish()
                await message.answer('Выберите страну поставщик: ', reply_markup=keyboard_country)
            except TypeError:
                latest_record = collection_goods.find_one(sort=[('_id', -1)])
                last_document_id = latest_record['_id']
                collection_goods.delete_one({'_id': last_document_id})
                try:
                    async with dp['db'].acquire() as connection:
                        await connection.execute("DELETE FROM goods WHERE id = (SELECT id FROM goods ORDER BY id DESC LIMIT 1)")
                except Exception as e:
                    print('ERROR', e)
                await state.finish()
                await message.answer('Данные некорректной формы! Попробуйте снова!', reply_markup=keyboard_back)


@dp.callback_query_handler(lambda query: query.data.startswith("country_"))
async def show_record_callback(callback_query: types.CallbackQuery):
	country_name = str(callback_query.data.split("_")[1])
	latest_record = collection_goods.find_one(sort=[('_id', -1)])
	if latest_record:
		collection_goods.update_one({'_id': latest_record['_id']}, {'$set': {'country': country_name}})
		try:
			async with dp['db'].acquire() as connection:
				await connection.execute("""
					UPDATE goods
					SET
						country = $1
					WHERE
						id = (SELECT id FROM goods ORDER BY id DESC LIMIT 1);
				""", str(country_name))
		except Exception as e:
			print('ERROR', e)
		await bot.send_message(callback_query.from_user.id, "Укажите категорию товара: ", reply_markup=keyboard_category)
	else:
		await bot.send_message(callback_query.from_user.id, "Произошла ошибка!", reply_markup=keyboard_back)

@dp.callback_query_handler(lambda query: query.data.startswith("category_"))
async def show_record_callback(callback_query: types.CallbackQuery):
	category_name = str(callback_query.data.split("_")[1])
	latest_record = collection_goods.find_one(sort=[('_id', -1)])
	if latest_record:
		collection_goods.update_one({'_id': latest_record['_id']}, {'$set': {'category': category_name}})
		try:
			async with dp['db'].acquire() as connection:
				await connection.execute("""
					UPDATE goods
					SET
						category = $1
					WHERE
						id = (SELECT id FROM goods ORDER BY id DESC LIMIT 1);
				""", str(category_name))
		except Exception as e:
			print('ERROR', e)
		await bot.send_message(callback_query.from_user.id, "Товар добавлен и будет доступен во всей екосистеме вашего проекта!", reply_markup=keyboard_back)
	else:
		await bot.send_message(callback_query.from_user.id, "Произошла ошибка!", reply_markup=keyboard_back)

@dp.callback_query_handler(lambda query: query.data == 'list_of_goods')
async def administrator_list_of_goods(callback_query: types.CallbackQuery, state:FSMContext):
	async with state.proxy() as data:
		user_id = callback_query.from_user.username
		user_status = get_user_status(user_id)
		page = 1
		if user_status == 'administrator':
			records_amount = collection_goods.count_documents({})
			if records_amount == 0:
				await callback_query.bot.send_message(
					callback_query.from_user.id,
					f'В коллекции {records_amount} записей.',
					reply_markup=keyboard_back
				)
			else:
				keyboard_list = InlineKeyboardMarkup().add(
					InlineKeyboardButton("⬅️ Выйти", callback_data='back'),
					InlineKeyboardButton("⏮️ Назад", callback_data=f'kback_{page-1}'),
					InlineKeyboardButton("⏭️ Далее", callback_data=f'kskip_{page+1}')
				)
				keyboard_list_without_carousel = InlineKeyboardMarkup().add(
					InlineKeyboardButton("⬅️ Выйти", callback_data='back'),
				)
				buttons = []
				for record in collection_goods.find():
					articul = record['articul']
					text = record['name']
					callback_data = f"show_record_goods{record['_id']}"
					buttons.append(text)
					keyboard_list.add(InlineKeyboardButton(f"{articul} {text}", callback_data=callback_data))
				if len(buttons) < 10:
					for record in collection_goods.find():
						articul = record['articul']
						text = record['name']
						callback_data = f"show_record_goods{record['_id']}"
						keyboard_list_without_carousel.add(InlineKeyboardButton(f"{articul} {text}", callback_data=callback_data))
					await callback_query.bot.send_message(
						callback_query.from_user.id,
						f'В коллекции {records_amount} записей. Выберите запись для просмотра:',
						reply_markup=keyboard_list_without_carousel,
					)
				else:
					msg = await callback_query.bot.send_message(
						callback_query.from_user.id,
						f'В коллекции {records_amount} записей. Страница{page}:',
						reply_markup=display_records(page, 10),
					)
					data['msg_id_keyb'] = msg.message_id

@dp.callback_query_handler(lambda query: query.data.startswith('kskip_'))
async def skip_keyboard(callback_query: types.CallbackQuery, state:FSMContext):
	async with state.proxy() as data:
		user_id = callback_query.from_user.username
		user_status = get_user_status(user_id)
		if user_status == 'administrator':
			page = str(callback_query.data.split("_")[1])
			msg_id_keyb = data.get('msg_id_keyb')
			chat_id=callback_query.message.chat.id
			records_amount = collection_goods.count_documents({})
			await callback_query.bot.edit_message_text(
				text=f'В коллекции {records_amount} записей. Страница {page}:',
				chat_id=chat_id,
				message_id=msg_id_keyb,
				reply_markup=display_records(int(page), 10)
			)

@dp.callback_query_handler(lambda query: query.data.startswith('kback_'))
async def skip_keyboard(callback_query: types.CallbackQuery, state:FSMContext):
	async with state.proxy() as data:
		user_id = callback_query.from_user.username
		user_status = get_user_status(user_id)
		if user_status == 'administrator':
			msg_id_keyb = data.get('msg_id_keyb')
			page = str(callback_query.data.split("_")[1])
			chat_id=callback_query.message.chat.id
			if int(page)<1:
				await callback_query.bot.send_message(
					callback_query.from_user.id,
					f'Ошибка итендефекатора номера страницы',
					reply_markup=keyboard_back,
				)
			else:
				records_amount = collection_goods.count_documents({})
				await callback_query.bot.edit_message_text(
					text=f'В коллекции {records_amount} записей. Страница {page}:',
					chat_id=chat_id,
					message_id=msg_id_keyb,
					reply_markup=display_records(int(page), 10)
				)

@dp.callback_query_handler(lambda query: query.data.startswith("show_record_goods"))
async def show_record_callback(callback_query: types.CallbackQuery, state:FSMContext):
	async  with state.proxy() as data:
		record_id = str(callback_query.data.split("_")[2])
		word_to_remove = "goods"
		result_string = record_id.replace(word_to_remove, "")
		record = collection_goods.find_one({"_id": ObjectId(result_string)})

		if record:
			photo = record.get('base64_data')
			photo_binary = base64.b64decode(photo)
			name = record.get('name')
			price = record.get('price')
			prescription = record.get('prescription')
			is_available = record.get('is_available')
			articul = record.get('articul')
			country = record.get('country')
			category = record.get('category')
			
			keyboard = InlineKeyboardMarkup(row_width=2)
			back_button = InlineKeyboardButton("⬅️ Назад", callback_data='back')
			keyboard.add(back_button)
			
			caption = f'#️*{articul}*\n📛*{name}* - *{price}*₴\nСтатус - {"❌" if is_available == "0" else "✔️"}\nСтрана производитель - {"🇪🇬" if country == "egypt" else "🇹🇷"}\nКатегория - {translate_text(str(category))}\n\n\n📜Описание товара: \n\n{prescription}'
			caption_without_desc = f'#️*{articul}*\n📛*{name}* - *{price}*₴\nСтатус - {"❌" if is_available == "0" else "✔️"}\nСтрана производитель - {"🇪🇬" if country == "egypt" else ("🇹🇷" if country == "turkey" else "🇦🇪")}\nКатегория - {translate_text(str(category))}'
			if len(caption)<255:
				await bot.send_photo(callback_query.from_user.id, photo_binary, caption=caption, reply_markup=keyboard_back, parse_mode='Markdown')
			else:
				
				await bot.send_photo(callback_query.from_user.id, photo_binary, caption=caption_without_desc, parse_mode='Markdown')
				msg = await bot.send_message(callback_query.from_user.id, prescription, reply_markup=keyboard_back_prescr)
				data['msg_id'] = msg.message_id
		else:
			await bot.send_message(callback_query.from_user.id, "Запись не найдена.", reply_markup=keyboard_back)

@dp.callback_query_handler(lambda query: query.data == 'settings')
async def get_articul(callback_query: types.CallbackQuery):
	user_id = callback_query.from_user.username
	user_status = get_user_status(user_id)
	if user_status == 'administrator':
		existing_records = collection_goods.count_documents({})
		if existing_records>0:
			await ClientStates.get_articul.set()
			await bot.send_message(
					callback_query.from_user.id,
					f'*ВНИМАНИЕ*\nВведите артикул одной цифрой без пробелов и без знака решетки: ',
					parse_mode='Markdown'
				)
		else:
			await bot.send_message(
					callback_query.from_user.id,
					f'На данный момент товары отсутствуют!',
					reply_markup=keyboard_back
				)

@dp.message_handler(state=ClientStates.get_articul)
async def settings_of_good(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		user_id = message.from_user.username
		user_status = get_user_status(user_id)
		if user_status == 'administrator':
			data['get_articul'] = message.text
			record = collection_goods.find_one({"articul": int(data['get_articul'])})
			if record:
				photo = record.get('base64_data')
				photo_binary = base64.b64decode(photo)
				name = record.get('name')
				price = record.get('price')
				prescription = record.get('prescription')
				is_available = record.get('is_available')
				articul = record.get('articul')
				country = record.get('country')
				category = record.get('category')
				
				keyboard = InlineKeyboardMarkup(row_width=2)
				back_button = InlineKeyboardButton("⬅️ Назад", callback_data='back')
				keyboard.add(back_button)
				
				caption = f'#️*{articul}*\n📛*{name}* - *{price}*₴\nСтатус - {"❌" if is_available == "0" else "✔️"}\nСтрана производитель - {"🇪🇬" if country == "egypt" else "🇹🇷"}\nКатегория - {translate_text(str(category))}\n\n\n📜Описание товара: \n\n{prescription}'
				if len(caption) <255:
					photo = await bot.send_photo(message.from_user.id, photo_binary, caption=caption, reply_markup=keyboard_settings_list, parse_mode='Markdown')
				else:
					caption_without_desc = f'#️*{articul}*\n📛*{name}* - *{price}*₴\nСтатус - {"❌" if is_available == "0" else "✔️"}\nКраїна виробник - {"🇪🇬" if country == "egypt" else "🇹🇷"}\nКатегорiя - {translate_text(str(category))}'
					photo = await bot.send_photo(message.from_user.id, photo_binary, caption=caption_without_desc, parse_mode='Markdown')
					await bot.send_message(message.from_user.id, prescription, reply_markup=keyboard_settings_list)
			else:
				await state.finish()
				await bot.send_message(message.from_user.id, "Запись не найдена.", reply_markup=keyboard_back)

@dp.callback_query_handler(lambda query: query.data.startswith("set_name"), state=ClientStates.get_articul)
async def set_name_handler(callback_query: types.CallbackQuery, state: FSMContext):
	async with state.proxy() as data:
		articul = int(data.get('get_articul'))
		if articul:
			await ClientStates.get_name.set()
			await bot.send_message(
				callback_query.from_user.id,
				f'*ВНИМАНИЕ*\nВведите новое название товара: ',
				parse_mode='Markdown'
			)
		else:
			await bot.answer_callback_query(callback_query.id, text="Ошибка: Артикул товара не найден")

@dp.message_handler(state=ClientStates.get_name)
async def set_name_func(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        user_id = message.from_user.username
        user_status = get_user_status(user_id)
        if user_status == 'administrator':
            data['get_name'] = message.text
            new_name = data['get_name']
            articul = int(data.get('get_articul'))
            collection_goods.update_one({"articul": articul}, {"$set": {"name": new_name}})
            try:
                async with dp['db'].acquire() as connection:
                    await connection.execute("UPDATE goods SET name = $1 WHERE article = $2", new_name, articul)
            except Exception as e:
                print('ERROR', e)
            await bot.send_message(
                message.from_user.id,
                f'Вы успешно изменили имя товара с артикулом - *{articul}*',
                parse_mode='Markdown',
                reply_markup=keyboard_back
            )
            await state.finish()


@dp.callback_query_handler(lambda query: query.data.startswith("set_price"), state=ClientStates.get_articul)
async def set_price_handler(callback_query: types.CallbackQuery, state: FSMContext):
	async with state.proxy() as data:
		articul = int(data.get('get_articul'))
		if articul:
			await ClientStates.get_price.set()
			await bot.send_message(
				callback_query.from_user.id,
				f'*ВНИМАНИЕ*\nВведите новую цену товара: ',
				parse_mode='Markdown'
			)
		else:
			await bot.answer_callback_query(callback_query.id, text="Ошибка: Артикул товара не найден")
			await state.finish()

@dp.message_handler(state=ClientStates.get_price)
async def set_price_func(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        user_id = message.from_user.username
        user_status = get_user_status(user_id)
        if user_status == 'administrator':
            data['get_price'] = message.text
            articul = int(data.get('get_articul'))
            collection_goods.update_one({'articul': articul}, {'$set': {'price': int(data['get_price'])}})
            try:
                async with dp['db'].acquire() as connection:
                    await connection.execute("UPDATE goods SET price = $1 WHERE article = $2", int(data['get_price']), articul)
            except Exception as e:
                print('ERROR', e)
            await state.finish()
            await bot.send_message(
                message.from_user.id,
                f'Вы успешно изменили цену товара с артикулом - *{articul}*',
                parse_mode='Markdown',
                reply_markup=keyboard_back
            )
            await state.finish()


@dp.callback_query_handler(lambda query: query.data.startswith("set_prescription"), state=ClientStates.get_articul)
async def set_prescription_handler(callback_query: types.CallbackQuery, state: FSMContext):
	async with state.proxy() as data:
		articul = int(data.get('get_articul'))
		if articul:
			await ClientStates.get_prescription.set()
			await bot.send_message(
				callback_query.from_user.id,
				f'*ВНИМАНИЕ*\nВведите новое описание товара: ',
				parse_mode='Markdown'
			)
		else:
			await bot.answer_callback_query(callback_query.id, text="Ошибка: Артикул товара не найден")
			await state.finish()

@dp.message_handler(state=ClientStates.get_prescription)
async def set_prescription_func(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        user_id = message.from_user.username
        user_status = get_user_status(user_id)
        if user_status == 'administrator':
            data['get_prescription'] = message.text
            articul = int(data.get('get_articul'))
            collection_goods.update_one({'articul': articul}, {'$set': {'prescription': data['get_prescription']}})
            try:
                async with dp['db'].acquire() as connection:
                    await connection.execute("UPDATE goods SET description = $1 WHERE article = $2", str(data['get_prescription']), articul)
            except Exception as e:
                print('ERROR', e)
            await state.finish()
            await bot.send_message(
                message.from_user.id,
                f'Вы успешно изменили описание товара с артикулом - *{articul}*',
                parse_mode='Markdown',
                reply_markup=keyboard_back
            )
            await state.finish()


@dp.callback_query_handler(lambda query: query.data.startswith("set_status"), state=ClientStates.get_articul)
async def set_status_handler(callback_query: types.CallbackQuery, state: FSMContext):
	async with state.proxy() as data:
		articul = int(data.get('get_articul'))
		if articul:
			await bot.send_message(
				callback_query.from_user.id,
				f"Вы выбрали установку нового статуса для товара с артикулом *{articul}*",
				reply_markup=keyboard_status,
				parse_mode='Markdown'
			)
		else:
			await bot.answer_callback_query(callback_query.id, text="Ошибка: Артикул товара не найден")
			await state.finish()

@dp.callback_query_handler(lambda query: query.data.startswith("delete_good"), state=ClientStates.get_articul)
async def set_status_handler(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        articul = int(data.get('get_articul'))
        if articul:
            result_mongo = collection_goods.delete_one({"articul": articul})

            try:
                async with dp['db'].acquire() as connection:
                    await connection.execute("DELETE FROM goods WHERE article = $1 RETURNING *", articul)
            except Exception as e:
                print('ERROR', e)

            if result_mongo.deleted_count == 1:
                await state.finish()
                await bot.send_message(
                    callback_query.from_user.id,
                    f"Вы произвели удаление товара с артикулом *{articul}*",
                    reply_markup=keyboard_back,
                    parse_mode='Markdown'
                )
            else:
                await state.finish()
                await bot.send_message(
                    callback_query.from_user.id,
                    f"Ошибка удаления! Товар с артикулом *{articul}* не найден!",
                    reply_markup=keyboard_back,
                    parse_mode='Markdown'
                )


@dp.callback_query_handler(lambda query: query.data == 'set_yes', state=ClientStates.get_articul)
async def set_yes(callback_query: types.CallbackQuery, state: FSMContext):
	async with state.proxy() as data:
		user_id = callback_query.from_user.username
		user_status = get_user_status(user_id)
		if user_status == 'administrator':
			articul = int(data.get('get_articul'))
			if articul:
				collection_goods.update_one({'articul': articul}, {'$set': {'is_available': '1'}})
				try:
					async with dp['db'].acquire() as connection:
						await connection.execute("UPDATE goods SET status = $1 WHERE article = $2", True, articul)
				except Exception as e:
					print('ERROR', e)
				await bot.send_message(
				callback_query.from_user.id,
				f'Вы успешно изменили статус товара с артикулом - {articul}',
				reply_markup=keyboard_back
			)
				await state.finish()
			else:
				await bot.answer_callback_query(callback_query.id, text="Ошибка: Артикул товара не найден")
				await state.finish()

@dp.callback_query_handler(lambda query: query.data == 'set_no', state=ClientStates.get_articul)
async def set_no(callback_query: types.CallbackQuery, state: FSMContext):
	async with state.proxy() as data:
		user_id = callback_query.from_user.username
		user_status = get_user_status(user_id)
		if user_status == 'administrator':
			articul = int(data.get('get_articul'))
			if articul:
				collection_goods.update_one({'articul': articul}, {'$set': {'is_available': '0'}})
				try:
					async with dp['db'].acquire() as connection:
						await connection.execute("UPDATE goods SET status = $1 WHERE article = $2", False, articul)
				except Exception as e:
					print('ERROR', e)
				await bot.send_message(
				callback_query.from_user.id,
				f'Вы успешно изменили статус товара с артикулом - *{articul}*',
				parse_mode='Markdown',
				reply_markup=keyboard_back
			)
				await state.finish()
			else:
				await bot.answer_callback_query(callback_query.id, text="Ошибка: Артикул товара не найден")
				await state.finish()

@dp.callback_query_handler(lambda query: query.data == 'back', state='*')
async def back_button_callback(callback_query: types.CallbackQuery, state: FSMContext):
	user_id = callback_query.from_user.username
	user_status = get_user_status(user_id)
	if user_status == 'administrator':
		await bot.send_message(callback_query.from_user.id, "Выберите действие:", reply_markup=keyboard_admin)
	else:
		await bot.send_message(callback_query.from_user.id, "Выберите действие:", reply_markup=keyboard_main)
	await state.reset_state()

@dp.callback_query_handler(lambda query: query.data == 'back_prescr', state='*')
async def back_button_callback(callback_query: types.CallbackQuery, state: FSMContext):
	user_id = callback_query.from_user.username
	user_status = get_user_status(user_id)
	if user_status == 'administrator':
		await bot.send_message(callback_query.from_user.id, "Выберите действие:", reply_markup=keyboard_admin)
	else:
		await bot.send_message(callback_query.from_user.id, "Выберите действие:", reply_markup=keyboard_main)
	await state.reset_state()

@dp.callback_query_handler(lambda query: query.data == 'back_skip', state='*')
async def back_button_skip_callback(callback_query: types.CallbackQuery, state: FSMContext):
	user_id = callback_query.from_user.username
	user_status = get_user_status(user_id)
	if user_status == 'administrator':
		latest_record = collection_goods.find_one(sort=[('_id', -1)])
		if latest_record:
			collection_goods.delete_one({'_id': latest_record['_id']})
			try:
				async with dp['db'].acquire() as connection:
					await connection.execute("DELETE FROM goods WHERE id = (SELECT id FROM goods ORDER BY id DESC LIMIT 1)")
			except Exception as e:
				print('ERROR', e)
			await state.finish()
			await bot.send_message(callback_query.from_user.id, "Выберите действие:", reply_markup=keyboard_admin)
		else:
			await bot.send_message(callback_query.from_user.id, "Выберите действие:", reply_markup=keyboard_admin)
	await state.reset_state()

@dp.callback_query_handler(lambda query: query.data == 'back_prescr', state='*')
async def back_button_callback(callback_query: types.CallbackQuery, state: FSMContext):
	async with state.proxy() as data:
		user_id = callback_query.from_user.username
		user_status = get_user_status(user_id)
		try:
			await bot.delete_message(chat_id=callback_query.from_user.id, message_id=data.get('msg_id'))
		except:
			pass
		if user_status == 'administrator':
			await bot.send_message(callback_query.from_user.id, "Выберите действие:", reply_markup=keyboard_admin)
		else:
			await bot.send_message(callback_query.from_user.id, "Выберите действие:", reply_markup=keyboard_main)
		await state.reset_state()

@dp.callback_query_handler(lambda query: query.data == 'back_to_lang', state='*')
async def back_button_lang_callback(callback_query: types.CallbackQuery, state: FSMContext):
	await start_buttons(callback_query.message)
	await state.reset_state()

#handlers(RU, default GUI)

@dp.callback_query_handler(lambda c: c.data == 'lang_ru_def')
async def process_create_question(callback_query: types.CallbackQuery):
    keyboard_main = InlineKeyboardMarkup().add(
        InlineKeyboardButton("❓ Создать вопрос в службу поддержки", callback_data='create_question')
    )

    await bot.send_message(
		callback_query.from_user.id,
        f'Здравствуйте, *{callback_query.from_user.first_name}*!\n\nМы сожалеем о том, что у вас возникли трудности, вот список функций:',
        reply_markup=keyboard_main,
        parse_mode='Markdown'
    )

@dp.callback_query_handler(lambda c: c.data == 'create_question')
async def process_create_question_callback(callback_query: types.CallbackQuery):

    await ClientStates.ticket.set()
    await bot.send_message(callback_query.from_user.id, f'{template_reply}', parse_mode=types.ParseMode.MARKDOWN)
    await bot.send_message(callback_query.from_user.id, 'Введите вашу проблему в текстовом формате не используя фотографии и прочие файлы: ', reply_markup=keyboard_back)

@dp.message_handler(state=ClientStates.ticket, content_types=[ContentType.TEXT])
async def create_ticket(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		data['ticket'] = message.text
		user_id = message.from_user.username
		id_user = message.from_user.id
		user_text = message.text
		last_ticket = collection_tickets.find().sort([('number', -1)]).limit(1)
		try:
			last_ticket_number = next(last_ticket)['number']
		except:
			last_ticket_number = 0
		user_records = collection_users.find_one({'tg_name': user_id})
		date = get_time_from_datetime(str(message.date))
		if user_id in admins:
			status = 'administrator'
		else:
			status = 'default'
		if user_text in check_in:
			await state.finish()
			await message.answer('Антиспам защита !', reply_markup=keyboard_main)
		elif user_text == '/start':
			await state.finish()
			await message.answer(
				f'Здравствуйте, *{message.from_user.first_name}*!\n\nВыберите язык:',
				reply_markup=keyboard_lang,
				parse_mode='Markdown'
			)
		elif user_id == None:
			await state.finish()
			await message.answer('Установите в настройках Telegram уникальный ID.', reply_markup=keyboard_main)
		else:
			if user_records == None:
					new_ticket_number = last_ticket_number + 1
					ticket_text = f"Тикет №{new_ticket_number}\n\nПользователь:  @{user_id}\n\nВремя создания:  {date}\n\nТело тикета:\n{data['ticket']}"
					user = {
						'tg_name': user_id,
                        'status': status
                    }
					ticket = {
						'user_id': id_user,
						'tg_name': user_id,
                        'prompt': data['ticket'],
                        'date': date,
						'number': new_ticket_number
                    }
					collection_users.insert_one(user)
					collection_tickets.insert_one(ticket)
					await state.finish()
					await message.answer(f'{user_id}, ваш запрос обрабатываеться\nВ течении 24 часов администрация свяжется с вами, спасибо за понимание !\n\nВремя отправки - {date}', reply_markup=keyboard_back)
					await bot.send_message(6928296134, ticket_text)
			else:
				if can_make_new_ticket(get_last_ticket_time(user_id)):
					new_ticket_number = last_ticket_number + 1
					ticket_text = f"Тикет №{new_ticket_number}\n\nПользователь:  @{user_id}\n\nВремя создания:  {date}\n\nТело тикета:\n\n{data['ticket']}"
					user = {
						'tg_name': user_id,
                        'status': status
                    }
					ticket = {
						'user_id': id_user,
						'tg_name': user_id,
                        'prompt': data['ticket'],
                        'date': date,
						'number': new_ticket_number
                    }
					collection_tickets.insert_one(ticket)
					await state.finish()
					await message.answer(f'{user_id},ваш запрос обрабатываеться\nВ течении 24 часов администрация свяжется с вами, спасибо за понимание !\n\nВремя отправки - {date}', reply_markup=keyboard_back)
					await bot.send_message(6928296134, ticket_text)
				else:
					await state.finish()
					await message.answer(f'{user_id}, следующая возможность отправки вопроса будет доступна по истечении 1 часа со времени отправки прошлого вопроса !', reply_markup=keyboard_lang)

@dp.message_handler(state=ClientStates.ticket, content_types=[ContentType.PHOTO])
async def create_ticket_photo(message: types.Message):
    await message.answer("Извините, но я принимаю только текстовые сообщения. Пожалуйста, отправьте ваш вопрос в текстовом формате.", reply_markup=keyboard_back)

#handlers(UA, default GUI)

@dp.callback_query_handler(lambda c: c.data == 'lang_ua_def')
async def process_create_question(callback_query: types.CallbackQuery):
    keyboard_main_ua = InlineKeyboardMarkup().add(
        InlineKeyboardButton("❓ Створити питання у технічну підтримку", callback_data='create_question_ua')
    )

    await bot.send_message(
		callback_query.from_user.id,
        f'Добрий день, *{callback_query.from_user.first_name}*!\n\nНам дуже неприємно, що ви маєте якісь проблеми, ось список усіх функцій:',
        reply_markup=keyboard_main_ua,
        parse_mode='Markdown'
    )

@dp.callback_query_handler(lambda c: c.data == 'create_question_ua')
async def process_create_question_callback(callback_query: types.CallbackQuery):

    await ClientStates.ticket_ua.set()
    await bot.send_message(callback_query.from_user.id, f'{template_reply_ua}', parse_mode=types.ParseMode.MARKDOWN)
    await bot.send_message(callback_query.from_user.id, 'Введіть проблему в текстовому форматі, не використовуючи фотографії та інші файли: ', reply_markup=keyboard_back_ua)

@dp.message_handler(state=ClientStates.ticket_ua, content_types=[ContentType.TEXT])
async def create_ticket(message: types.Message, state: FSMContext):
	async with state.proxy() as data:
		data['ticket'] = message.text
		user_id = message.from_user.username
		id_user = message.from_user.id
		user_text = message.text
		last_ticket = collection_tickets.find().sort([('number', -1)]).limit(1)
		try:
			last_ticket_number = next(last_ticket)['number']
		except:
			last_ticket_number = 0
		user_records = collection_users.find_one({'tg_name': user_id})
		date = get_time_from_datetime(str(message.date))
		if user_id in admins:
			status = 'administrator'
		else:
			status = 'default'
		if user_text in check_in:
			await state.finish()
			await message.answer('Антиспам захист!', reply_markup=keyboard_main_ua)
		elif user_text == '/start':
			await state.finish()
			await message.answer(
				f'Здравствуйте, *{message.from_user.first_name}*!\n\nВыберите язык:',
				reply_markup=keyboard_lang,
				parse_mode='Markdown'
			)
		elif user_id == None:
			await state.finish()
			await message.answer('Встановіть у налаштуваннях Telegram унікальний ID.', reply_markup=keyboard_main_ua)
		else:
			if user_records == None:
					new_ticket_number = last_ticket_number + 1
					ticket_text = f"Тикет №{new_ticket_number}\n\nПользователь:  @{user_id}\n\nВремя создания:  {date}\n\nТело тикета:\n{data['ticket']}"
					user = {
						'tg_name': user_id,
                        'status': status
                    }
					ticket = {
						'user_id': id_user,
						'tg_name': user_id,
                        'prompt': data['ticket'],
                        'date': date,
						'number': new_ticket_number
                    }
					collection_users.insert_one(user)
					collection_tickets.insert_one(ticket)
					await state.finish()
					await message.answer(f'{user_id}, ваш запит обробляється\nПротягом 24 годин адміністрація зв`яжеться з вами, дякую за розуміння!\n\nЧас відправки - {date}', reply_markup=keyboard_back_ua)
					await bot.send_message(6928296134, ticket_text)
			else:
				if can_make_new_ticket(get_last_ticket_time(user_id)):
					new_ticket_number = last_ticket_number + 1
					ticket_text = f"Тикет №{new_ticket_number}\n\nПользователь:  @{user_id}\n\nВремя создания:  {date}\n\nТело тикета:\n\n{data['ticket']}"
					user = {
						'tg_name': user_id,
                        'status': status
                    }
					ticket = {
						'user_id': id_user,
						'tg_name': user_id,
                        'prompt': data['ticket'],
                        'date': date,
						'number': new_ticket_number
                    }
					collection_tickets.insert_one(ticket)
					await state.finish()
					await message.answer(f'{user_id}, ваш запит обробляється\nПротягом 24 годин адміністрація зв`яжеться з вами, дякую за розуміння!\n\nЧас відправки - {date}', reply_markup=keyboard_back_ua)
					await bot.send_message(6928296134, ticket_text)
				else:
					await state.finish()
					await message.answer(f'{user_id}, наступна можливість відправки питання буде доступна через 1 годину від часу відправлення минулого питання!', reply_markup=keyboard_lang)

@dp.message_handler(state=ClientStates.ticket_ua, content_types=[ContentType.PHOTO])
async def create_ticket_photo(message: types.Message):
    await message.answer("Вибачте, але я приймаю лише текстові повідомлення. Будь ласка, надішліть ваше запитання у текстовому форматі.", reply_markup=keyboard_back_ua)

@dp.callback_query_handler(lambda query: query.data == 'back_ua', state='*')
async def back_button_callback(callback_query: types.CallbackQuery, state: FSMContext):
	user_id = callback_query.from_user.username
	user_status = get_user_status(user_id)
	if user_status == 'administrator':
		await bot.send_message(callback_query.from_user.id, "Оберіть дію:", reply_markup=keyboard_admin)
	else:
		await bot.send_message(callback_query.from_user.id, "Оберіть дію:", reply_markup=keyboard_main_ua)
	await state.reset_state()

#bot pooling

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)