#imports

import base64
from bson import ObjectId
from pymongo import MongoClient
from aiogram import Dispatcher, Bot, types, executor
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import MessageCantBeDeleted
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import API_TOKEN, CLUSTER_URL
from keyboards import (
    keyboard_category,
    keyboard_category_ua,
    keyboard_country,
    keyboard_country_ua,
    keyboard_main,
    keyboard_main_ua,
    keyboard_back,
    keyboard_back_ua,
    keyboard_lang,
    keyboard_delete,
    keyboard_back_form,

)
from functions import translate_text

#api_token

token = API_TOKEN
bot = Bot(token)
dp = Dispatcher(bot, storage=MemoryStorage())

#database MongoDB

cluster = MongoClient(CLUSTER_URL)

db = cluster['VIC_BOT_SUPPORT']
collection_users = db['collection_users']
collection_goods = db['collection_goods']
collection_basket = db['collection_basket']
collection_buys = db['collection_buys']

#states

class ClientStates(StatesGroup):
    name = State()
    surname = State()
    tel_number = State()
    area = State()
    town = State()
    postal_adres = State()

#start_message

@dp.message_handler(commands=['start'])
async def start_buttons(message: types.Message, state:FSMContext):
    async with state.proxy() as data:
        data['start_id'] =  message.message_id
        user_id = message.from_user.username
        if user_id is not None:
            user = {
                'tg_name': user_id,
                'status': 'customer'
            }
            existing_user = collection_users.find_one({'tg_name': user_id})
            if existing_user:
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
                collection_users.insert_one(user)
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
            await message.answer(
                'Для работы со службой тех.поддержки вы *обязаны* установить ID в настройках мессенджера Telegram',
                parse_mode='Markdown'
            )

#handlers GUI(ru)

@dp.callback_query_handler(lambda c: c.data == 'lang_ru')
async def country_filter_ru(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=callback_query.message.message_id,
        text=f'Здравствуйте, *{callback_query.from_user.first_name}*!\n\nДоступный функционал:',
        reply_markup=keyboard_main,
        parse_mode='Markdown',
    )

@dp.callback_query_handler(lambda c: c.data == 'support')
async def support_ru(callback_query: types.CallbackQuery, state:FSMContext):
    async with state.proxy() as data:
        chat_id = callback_query.message.chat.id
        msg_support  = await bot.edit_message_text(
            chat_id=chat_id,
            message_id=callback_query.message.message_id,
            text=f'Ссылка - https://t.me/tovaru_victoria_help_bot',
            reply_markup=keyboard_back,
        )
        data['msg_support'] = msg_support.message_id

@dp.callback_query_handler(lambda c: c.data == 'show_basket')
async def country_filter_ru(callback_query: types.CallbackQuery, state:FSMContext):
    async with state.proxy() as data:
        user_id = callback_query.from_user.username
        search_results = collection_basket.find({'user_id': user_id})
        if collection_basket.count_documents({'user_id':user_id}) > 0:
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(InlineKeyboardButton('⬅️ Назад', callback_data='back'))
            keyboard.add(InlineKeyboardButton('💵 Подтвердить заказ', callback_data='make_form'))

            for result in search_results:
                name = result.get('name')
                number = result.get('number')
                data['article_goods'] = collection_goods.find_one({'articul': result.get('article')})
                data['article_basket'] = result.get('article')
                result_goods = data['article_goods'].get('_id')
                callback_data = f"item_basket_{result_goods}"
                keyboard.add(InlineKeyboardButton(f"{number} - {name}", callback_data=callback_data))
            chat_id = callback_query.message.chat.id
            msg = await bot.edit_message_text(
                chat_id=chat_id,
                message_id=callback_query.message.message_id,
                text=f'Товары в корзине: ',
                reply_markup=keyboard,
                parse_mode='Markdown',
            )
            data['basket_id'] = msg.message_id
        else:
            chat_id = callback_query.message.chat.id
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=callback_query.message.message_id,
                text='Корзина пуста!',
                reply_markup=keyboard_back,
                parse_mode='Markdown',
            )

@dp.callback_query_handler(lambda c: c.data == 'make_form')
async def make_form(callback_query: types.CallbackQuery, state:FSMContext):
    async with state.proxy() as data:
        await ClientStates.name.set()
        msg = await callback_query.message.edit_text(
            text='Сейчас вы должны будете заполнить форму заказа!\n\nПожалуйста укажите ваше *имя* 1 словом без ошибок:',
            reply_markup=keyboard_back,
            parse_mode='Markdown',
        )
        data['id_to_edit'] = msg.message_id

@dp.message_handler(state=ClientStates.name)
async def name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
        user_id = message.from_user.username
        user_ticket = {
            'user_id': user_id,
            'name': data['name'],
            'surname': 'tbd',
            'tel_number': 'tbd',
            'area': 'tbd',
            'town': 'tbd',
            'postal_adres': 'tbd'
        }
        insert_result = collection_buys.insert_one(user_ticket)
        data['object_id'] = str(insert_result.inserted_id)
        chat_id = message.chat.id
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=data.get('id_to_edit'),
            text=f"Успешно!\nВы добавили имя - {data['name']}\n\nТеперь отправьте вашу *фамилию* 1 словом без ошибок:",
            reply_markup=keyboard_back_form,
            parse_mode='Markdown',
        )
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await state.reset_state()
        await ClientStates.surname.set()

@dp.message_handler(state=ClientStates.surname)
async def surname(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['surname'] = message.text
        collection_buys.update_one({'_id': ObjectId(str(data.get('object_id')))}, {'$set': {'surname': data['surname']}})
        chat_id = message.chat.id
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=data.get('id_to_edit'),
            text=f"Успешно!\nВы добавили фамилию - {data['surname']}\n\nТеперь отправьте ваш *номер телефона* без ошибок:",
            reply_markup=keyboard_back_form,
            parse_mode='Markdown',
        )
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
        await state.reset_state()
        await ClientStates.tel_number.set()

@dp.message_handler(state=ClientStates.tel_number)
async def tel_number(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['tel_number'] = message.text
        collection_buys.update_one({'_id': ObjectId(str(data.get('object_id')))}, {'$set': {'tel_number': data['tel_number']}})
        chat_id = message.chat.id
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=data.get('id_to_edit'),
            text=f"Успешно!\nВы добавили номер телефона - {data['tel_number']}\n\nТеперь отправьте вашу *область* без ошибок:",
            reply_markup=keyboard_back_form,
            parse_mode='Markdown',
        )
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
        await state.reset_state()
        await ClientStates.area.set()

@dp.message_handler(state=ClientStates.area)
async def area(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['area'] = message.text
        collection_buys.update_one({'_id': ObjectId(str(data.get('object_id')))}, {'$set': {'area': data['area']}})
        chat_id = message.chat.id
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=data.get('id_to_edit'),
            text=f"Успешно!\nВы добавили вашу область - {data['area']}\n\nТеперь отправьте ваш *город* без ошибок:",
            reply_markup=keyboard_back_form,
            parse_mode='Markdown',
        )
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
        await state.reset_state()
        await ClientStates.town.set()

@dp.message_handler(state=ClientStates.town)
async def town(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['town'] = message.text
        collection_buys.update_one({'_id': ObjectId(str(data.get('object_id')))}, {'$set': {'town': data['town']}})
        chat_id = message.chat.id
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=data.get('id_to_edit'),
            text=f"Успешно!\nВы добавили ваш город - {data['town']}\n\nТеперь отправьте ваше *почтовое отделение* без ошибок:",
            reply_markup=keyboard_back_form,
            parse_mode='Markdown',
        )
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
        await state.reset_state()
        await ClientStates.postal_adres.set()

@dp.message_handler(state=ClientStates.postal_adres)
async def postal_adres(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['postal_adres'] = message.text
        record = collection_buys.find_one({'_id': ObjectId(str(data.get('object_id')))})
        collection_buys.update_one({'_id': record['_id']}, {'$set': {'postal_adres': data['postal_adres']}})
        chat_id = message.chat.id
        user_basket = collection_basket.find({'user_id': record.get('user_id')})
        basket_info = ""
        total_price = 0
        for index, item in enumerate(user_basket, start=1):
            name = item.get('name')
            price = collection_goods.find_one({'name': name})
            price = price.get('price')
            basket_info += f"{index}. {name} - {price}\n"
            total_price += price
            
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=data.get('id_to_edit'),
            text=f"Успешно!\nВы добавили ваше почтовое отделение - {data['postal_adres']}\n\nОжидайте, в течении 48 часов вам напишет владелец магазина для подтверждения заказа!",
            reply_markup=keyboard_back,
            parse_mode='Markdown',
        )
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
        ticket_text = f"Заказчик: @{record.get('user_id')}\nИмя: {data['name']}\nФамилия: {data['surname']}\nНомер телефона: {data['tel_number']}\nОбласть: {data['area']}\nГород: {data['postal_adres']}\n\n\n{basket_info}\n\nОбщая сумма заказа: {total_price}"
        msg_1 = await bot.send_message(7418316844, ticket_text)
        msg_2 = await bot.send_message(1310689865, ticket_text)
        collection_basket.delete_many({'user_id': record.get('user_id')})
        data['msg_1_id'] = msg_1.message_id
        data['msg_2_id'] = msg_2.message_id
        keyboard_answered = InlineKeyboardMarkup().add(
            InlineKeyboardButton("✅ Заказ подтвержден", callback_data=f"approved_{str(data.get('object_id'))}_{data['msg_1_id']}_{data['msg_2_id']}")
        )
        await bot.edit_message_text(
            chat_id=7418316844,
            message_id=data['msg_1_id'],
            text=ticket_text,
            reply_markup=keyboard_answered,
        )
        await bot.edit_message_text(
            chat_id=1310689865,
            message_id=data['msg_2_id'],
            text=ticket_text,
            reply_markup=keyboard_answered,
        )
        await state.reset_state()

@dp.callback_query_handler(lambda query: query.data.startswith("approved_"))
async def show_record_callback(callback_query: types.CallbackQuery, state:FSMContext):
    async with state.proxy() as data:
        record_id = str(callback_query.data.split("_")[1])
        msg_1_id = str(callback_query.data.split("_")[2])
        msg_2_id = str(callback_query.data.split("_")[3])
        if callback_query.from_user.username == 'matttvii_dev':
            try:
                await bot.delete_message(chat_id=callback_query.from_user.id, message_id=msg_1_id)
            except:
                pass
        else:
            try:
                await bot.delete_message(chat_id=callback_query.from_user.id, message_id=msg_2_id)
            except:
                pass
        collection_buys.delete_one({'_id': ObjectId(record_id)})
        await state.finish()

@dp.callback_query_handler(lambda query: query.data.startswith("item_basket_"))
async def show_record_callback(callback_query: types.CallbackQuery, state:FSMContext):
    async with state.proxy() as data:
        record_id = str(callback_query.data.split("_")[2])
        record = collection_goods.find_one({"_id": ObjectId(record_id)})

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

            caption = f'#️*{articul}*\n📛*{name}* - *{price}*₴\nСтатус - {"❌" if is_available == "0" else "✔️"}\nСтрана производитель - {"🇪🇬" if country == "egypt" else "🇹🇷"}\nКатегория - {translate_text(str(category))}\n\n\n📜Описание товара: \n\n{prescription}'
            basket = data.get('basket_id')
            start = data.get('start_id')
            chat_id = callback_query.from_user.id
            try:
                await bot.delete_message(chat_id=chat_id, message_id=start)
                await bot.delete_message(chat_id=chat_id, message_id=basket)
            except:
                await bot.delete_message(chat_id=chat_id, message_id=basket)
            if len(caption) < 255:
                photo = await bot.send_photo(callback_query.from_user.id, photo_binary, caption=caption, reply_markup=keyboard_delete, parse_mode='Markdown')
                data['photo_basket'] = photo.message_id
            else:
                keyboard_delete = InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🗑️ Удалить", callback_data='delete_from_basket'),
                    InlineKeyboardButton("⬅️ Назад", callback_data='back_prescr')
                )
                caption_without_prescr = f'#️*{articul}*\n📛*{name}* - *{price}*₴\nСтатус - {"❌" if is_available == "0" else "✔️"}\nСтрана производитель - {"🇪🇬" if country == "egypt" else "🇹🇷"}\nКатегория - {translate_text(str(category))}'
                photo = await bot.send_photo(callback_query.from_user.id, photo_binary, caption=caption_without_prescr, parse_mode='Markdown')
                msg = await bot.send_message(callback_query.from_user.id, prescription, reply_markup=keyboard_delete)
                data['msg_id_prescr'] = msg.message_id
                data['photo_basket'] = photo.message_id
        else:
            chat_id = callback_query.from_user.id
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=callback_query.message.message_id,
                text='Запись не найдена',
                reply_markup=keyboard_back,
                parse_mode='Markdown',
            )


@dp.callback_query_handler(lambda c: c.data == 'delete_from_basket')
async def country_filter_ru(callback_query: types.CallbackQuery, state:FSMContext):
    async with state.proxy() as data:
        article = data.get('article_basket')
        collection_basket.delete_one({'article': article})
        chat_id = callback_query.from_user.id
        await bot.delete_message(chat_id=chat_id, message_id=data['photo_basket'])
        try:
            await bot.delete_message(chat_id=chat_id, message_id=data['msg_id_prescr'])
        except:
            pass
        await bot.send_message(
            callback_query.from_user.id,
            'Товар удален с корзины!',
            reply_markup=keyboard_back,
            parse_mode='Markdown',
        )

@dp.callback_query_handler(lambda c: c.data == 'go_to_filters')
async def country_filter_ru(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=callback_query.message.message_id,
        text=f'Здравствуйте!\n\nУважаемый покупатель, выберите фильтр по стране:',
        reply_markup=keyboard_country,
        parse_mode='Markdown',
    )

@dp.callback_query_handler(lambda query: query.data.startswith("country_"))
async def show_record_callback(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        country_name = str(callback_query.data.split("_")[1])
        data['country'] = country_name
        chat_id = callback_query.message.chat.id
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=callback_query.message.message_id,
            text=f'Доступные фильтры для этой страны: ',
            reply_markup=keyboard_category,
            parse_mode='Markdown',
        )

@dp.callback_query_handler(lambda query: query.data.startswith("category_"))
async def show_record_callback(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        category_name = str(callback_query.data.split("_")[1])
        data['category'] = category_name
        country_name = data.get('country')
        search_results = collection_goods.find({
            'category': str(data['category']),
            'country': str(country_name)
        })
        if collection_goods.count_documents({
            'category': str(data['category']),
            'country': str(country_name)
        }) > 0:
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton('⬅️ Назад', callback_data='back'))

            for result in search_results:
                name = result.get('name')
                article = result.get('articul')
                callback_data = f"item_{result['_id']}"
                keyboard.add(InlineKeyboardButton(f"#{article} {name}", callback_data=callback_data))
            chat_id = callback_query.message.chat.id
            msg =  await bot.edit_message_text(
                chat_id=chat_id,
                message_id=callback_query.message.message_id,
                text=f'Доступные товары: ',
                reply_markup=keyboard,
                parse_mode='Markdown',
            )
            data['available_id'] = msg.message_id
        else:
            chat_id = callback_query.message.chat.id
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=callback_query.message.message_id,
                text='Товаров по данным фильтрам нет!',
                reply_markup=keyboard_back,
                parse_mode='Markdown',
            )

@dp.callback_query_handler(lambda query: query.data.startswith("item_"))
async def show_record_callback(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        record_id = str(callback_query.data.split("_")[1])
        record = collection_goods.find_one({"_id": ObjectId(record_id)})

        if record:
            photo = record.get('base64_data')
            photo_binary = base64.b64decode(photo)
            name = record.get('name')
            price = record.get('price')
            prescription = record.get('prescription')
            is_available = record.get('is_available')
            articul = record.get('articul')
            data['article'] = articul
            country = record.get('country')
            category = record.get('category')

            caption = f'#️*{articul}*\n📛*{name}* - *{price}*₴\nСтатус - {"❌" if is_available == "0" else "✔️"}\nСтрана производитель - {"🇪🇬" if country == "egypt" else ("🇹🇷" if country == "turkey" else "🇦🇪")}\nКатегория - {translate_text(str(category))}\n\n\n📜Описание товара: \n\n{prescription}'
            start = data.get('start_id')
            available_id = data.get('available_id')
            chat_id = callback_query.from_user.id
            
            try:
                if start:
                    await bot.delete_message(chat_id=chat_id, message_id=start)
                if available_id:
                    await bot.delete_message(chat_id=chat_id, message_id=available_id)
            except MessageCantBeDeleted:
                if available_id:
                    await bot.delete_message(chat_id=chat_id, message_id=available_id)
            except Exception as e:
                print(f"Произошла ошибка: {e}")
                
            if len(caption) < 255:
                photo = await bot.send_photo(chat_id=chat_id, photo=photo_binary, caption=caption, reply_markup=keyboard_delete, parse_mode='Markdown')
                data['photo_basket'] = photo.message_id
            else:
                keyboard_buy = InlineKeyboardMarkup().add(
                InlineKeyboardButton("🛒 Добавить в корзину", callback_data='add_to_basket'),
                InlineKeyboardButton("⬅️ Назад", callback_data='back_prescr')
            )
                caption_without_prescr = f'#️*{articul}*\n📛*{name}* - *{price}*₴\nСтатус - {"❌" if is_available == "0" else "✔️"}\nСтрана производитель - {"🇪🇬" if country == "egypt" else "🇹🇷"}\nКатегория - {translate_text(str(category))}'
                photo = await bot.send_photo(chat_id=chat_id, photo=photo_binary, caption=caption_without_prescr, parse_mode='Markdown')
                msg = await bot.send_message(chat_id=chat_id, text=prescription, reply_markup=keyboard_buy)
                data['msg_id_prescr'] = msg.message_id
                data['photo_basket'] = photo.message_id
        else:
            chat_id = callback_query.from_user.id
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=callback_query.message.message_id,
                text='Запись не найдена',
                reply_markup=keyboard_back,
                parse_mode='Markdown',
            )

@dp.callback_query_handler(lambda c: c.data == 'add_to_basket')
async def country_filter_ru(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        article = data.get('article')
        record = collection_goods.find_one({"articul": int(article)})
        name = record.get('name')
        last_basket = collection_basket.find().sort([('number', -1)]).limit(1)
        try:
            last_busket_number = next(last_basket)['number']
        except:
            last_busket_number = 0
        item = {
            'article': article,
            'name': name,
            'number': last_busket_number+1,
            'user_id': callback_query.from_user.username
        }
        collection_basket.insert_one(item)
        chat_id = callback_query.message.chat.id
        await bot.delete_message(chat_id=chat_id, message_id=data['photo_basket'])
        try:
            await bot.delete_message(chat_id=chat_id, message_id=data['msg_id_prescr'])
        except:
            pass
        await bot.send_message(
            callback_query.from_user.id,
            f'Товар с артикулом *#{article}* успешно добавлен в корзину!',
            reply_markup=keyboard_category,
            parse_mode='Markdown'
        )


@dp.callback_query_handler(lambda query: query.data == 'back', state='*')
async def back_button_callback(callback_query: types.CallbackQuery, state: FSMContext):
    chat_id = callback_query.message.chat.id
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=callback_query.message.message_id,
        text='Выберите действие',
        reply_markup=keyboard_main,
        parse_mode='Markdown',
    )
    await state.reset_state()

@dp.callback_query_handler(lambda query: query.data == 'back_prescr', state='*')
async def back_button_callback(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        chat_id = callback_query.message.chat.id
        try:
            await bot.delete_message(chat_id=chat_id, message_id=data['photo_basket'])
        except:
            pass

        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=data['msg_id_prescr'],
            text='Оберіть дії',
            reply_markup=keyboard_main_ua,
            parse_mode='Markdown',
        )
        await state.reset_state()

@dp.callback_query_handler(lambda query: query.data == 'back_form', state='*')
async def back_button_callback(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        chat_id = callback_query.message.chat.id
        collection_buys.delete_one({'_id': ObjectId(str(data.get('object_id')))})
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=callback_query.message.message_id,
            text='Выберите действие',
            reply_markup=keyboard_main,
            parse_mode='Markdown',
        )
        await state.reset_state()

@dp.callback_query_handler(lambda query: query.data == 'back_to_lang', state='*')
async def back_button_lang_callback(callback_query: types.CallbackQuery, state: FSMContext):
    chat_id = callback_query.message.chat.id
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=callback_query.message.message_id,
        text='Выберите язык:',
        reply_markup=keyboard_lang,
        parse_mode='Markdown',
    )
    await state.reset_state()

#handlers UA(GUI)

@dp.callback_query_handler(lambda c: c.data == 'lang_ua')
async def country_filter_ru(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=callback_query.message.message_id,
        text=f'Добрий день, *{callback_query.from_user.first_name}*!\n\nДоступний функціонал:',
        reply_markup=keyboard_main_ua,
        parse_mode='Markdown',
    )

@dp.callback_query_handler(lambda c: c.data == 'support_ua')
async def support_ru(callback_query: types.CallbackQuery, state:FSMContext):
    async with state.proxy() as data:
        chat_id = callback_query.message.chat.id
        msg_support = await bot.edit_message_text(
            chat_id=chat_id,
            message_id=callback_query.message.message_id,
            text=f'Посилання - https://t.me/victoria_shop_support_bot',
            reply_markup=keyboard_back_ua,
        )
        data['msg_support_ua'] =  msg_support.message_id


@dp.callback_query_handler(lambda c: c.data == 'show_basket_ua')
async def country_filter_ru(callback_query: types.CallbackQuery, state:FSMContext):
    async with state.proxy() as data:
        user_id = callback_query.from_user.username
        search_results = collection_basket.find({'user_id': user_id})
        if collection_basket.count_documents({'user_id':user_id}) > 0:
            keyboard = InlineKeyboardMarkup(row_width=2)
            keyboard.add(InlineKeyboardButton('⬅️ Назад', callback_data='back_ua'))
            keyboard.add(InlineKeyboardButton('💵 Підтвердити замовлення', callback_data='make_form_ua'))

            for result in search_results:
                name = result.get('name')
                number = result.get('number')
                data['article_goods'] = collection_goods.find_one({'articul': result.get('article')})
                data['article_basket'] = result.get('article')
                result_goods = data['article_goods'].get('_id')
                callback_data = f"qua_{result_goods}"
                keyboard.add(InlineKeyboardButton(f"{number} - {name}", callback_data=callback_data))
            chat_id = callback_query.message.chat.id
            msg = await bot.edit_message_text(
                chat_id=chat_id,
                message_id=callback_query.message.message_id,
                text=f'Товари у кошику: ',
                reply_markup=keyboard,
                parse_mode='Markdown',
            )
            data['basket_id'] = msg.message_id
        else:
            chat_id = callback_query.message.chat.id
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=callback_query.message.message_id,
                text='Корзина пуста!',
                reply_markup=keyboard_back,
                parse_mode='Markdown',
            )

@dp.callback_query_handler(lambda c: c.data == 'make_form_ua')
async def make_form(callback_query: types.CallbackQuery, state:FSMContext):
    async with state.proxy() as data:
        await ClientStates.name.set()
        msg = await callback_query.message.edit_text(
            text="Тепер ви повинні заповнити форму замовлення!\n\nБудь ласка, вкажіть ваше *ім`я* 1 словом без ошибок:",
            reply_markup=keyboard_back,
            parse_mode='Markdown',
        )
        data['id_to_edit'] = msg.message_id

@dp.message_handler(state=ClientStates.name)
async def name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
        user_id = message.from_user.username
        user_ticket = {
            'user_id': user_id,
            'name': data['name'],
            'surname': 'tbd',
            'tel_number': 'tbd',
            'area': 'tbd',
            'town': 'tbd',
            'postal_adres': 'tbd'
        }
        insert_result = collection_buys.insert_one(user_ticket)
        data['object_id'] = str(insert_result.inserted_id)
        chat_id = message.chat.id
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=data.get('id_to_edit'),
            text=f"Добре!\nВи додали ім'я - {data['name']}\n\nТепер відправте ваше *прізвище* без помилок:",
            reply_markup=keyboard_back_form,
            parse_mode='Markdown',
        )
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await state.finish()
        await ClientStates.surname.set()

@dp.message_handler(state=ClientStates.surname)
async def surname(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['surname'] = message.text
        collection_buys.update_one({'_id': ObjectId(str(data.get('object_id')))}, {'$set': {'surname': data['surname']}})
        chat_id = message.chat.id
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=data.get('id_to_edit'),
            text=f"Добре!\nВи додали прізвище - {data['surname']}\n\nТепер відправте ваш *номер телефона* без помилок:",
            reply_markup=keyboard_back_form,
            parse_mode='Markdown',
        )
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
        await state.finish()
        await ClientStates.tel_number.set()

@dp.message_handler(state=ClientStates.tel_number)
async def surname(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['tel_number'] = message.text
        collection_buys.update_one({'_id': ObjectId(str(data.get('object_id')))}, {'$set': {'tel_number': data['tel_number']}})
        chat_id = message.chat.id
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=data.get('id_to_edit'),
            text=f"Добре!\nВи додали ваш номер телефона - {data['tel_number']}\n\nТепер відправте вашу *область* без помилок:",
            reply_markup=keyboard_back_form,
            parse_mode='Markdown',
        )
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
        await state.finish()
        await ClientStates.area.set()

@dp.message_handler(state=ClientStates.area)
async def surname(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['area'] = message.text
        collection_buys.update_one({'_id': ObjectId(str(data.get('object_id')))}, {'$set': {'area': data['area']}})
        chat_id = message.chat.id
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=data.get('id_to_edit'),
            text=f"Добре!\nВи додали вашу область - {data['area']}\n\nТепер відправте ваше *місто* без помилок:",
            reply_markup=keyboard_back_form,
            parse_mode='Markdown',
        )
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
        await state.finish()
        await ClientStates.town.set()

@dp.message_handler(state=ClientStates.town)
async def surname(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['town'] = message.text
        collection_buys.update_one({'_id': ObjectId(str(data.get('object_id')))}, {'$set': {'town': data['town']}})
        chat_id = message.chat.id
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=data.get('id_to_edit'),
            text=f"Добре!\nВи додали ваше місто - {data['town']}\n\nТепер відправте ваше *поштове відділення* без помилок:",
            reply_markup=keyboard_back_form,
            parse_mode='Markdown',
        )
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
        await state.finish()
        await ClientStates.postal_adres.set()

@dp.message_handler(state=ClientStates.postal_adres)
async def surname(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['postal_adres'] = message.text
        record = collection_buys.find_one({'_id': ObjectId(str(data.get('object_id')))})
        collection_buys.update_one({'_id': record['_id']}, {'$set': {'postal_adres': data['postal_adres']}})
        chat_id = message.chat.id
        user_basket = collection_basket.find({'user_id': record.get('user_id')})
        basket_info = ""
        total_price = 0
        for index, item in enumerate(user_basket, start=1):
            name = item.get('name')
            price = collection_goods.find_one({'name': name})
            price = price.get('price')
            basket_info += f"{index}. {name} - {price}\n"
            total_price += price
            
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=data.get('id_to_edit'),
            text=f"Добре!\nВы додали ваше поштове відділення - {data['postal_adres']}\n\nОчiкуйте, протягом 48 годин вам напише власник магазину для підтвердження замовлення!",
            reply_markup=keyboard_back,
            parse_mode='Markdown',
        )
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
        ticket_text = f"Заказчик: @{record.get('user_id')}\nИмя: {data['name']}\nФамилия: {data['surname']}\nНомер телефона: {data['tel_number']}\nОбласть: {data['area']}\nГород: {data['postal_adres']}\n\n\n{basket_info}\n\nОбщая сумма заказа: {total_price}"
        msg_1 = await bot.send_message(7418316844, ticket_text)
        msg_2 = await bot.send_message(1310689865, ticket_text)
        collection_basket.delete_many({'user_id': record.get('user_id')})
        data['msg_1_id'] = msg_1.message_id
        data['msg_2_id'] = msg_2.message_id
        keyboard_answered = InlineKeyboardMarkup().add(
            InlineKeyboardButton("✅ Заказ подтвержден", callback_data=f"approved_{str(data.get('object_id'))}_{data['msg_1_id']}_{data['msg_2_id']}")
        )
        await bot.edit_message_text(
            chat_id=7418316844,
            message_id=data['msg_1_id'],
            text=ticket_text,
            reply_markup=keyboard_answered,
        )
        await bot.edit_message_text(
            chat_id=1310689865,
            message_id=data['msg_2_id'],
            text=ticket_text,
            reply_markup=keyboard_answered,
        )

@dp.callback_query_handler(lambda query: query.data.startswith("qua_"))
async def show_record_callback(callback_query: types.CallbackQuery, state:FSMContext):
    async with state.proxy() as data:
        record_id = str(callback_query.data.split("_")[1])
        record = collection_goods.find_one({"_id": ObjectId(record_id)})

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

            caption = f'#️*{articul}*\n📛*{name}* - *{price}*₴\nСтатус - {"❌" if is_available == "0" else "✔️"}\nКраїна виробник - {"🇪🇬" if country == "egypt" else "🇹🇷"}\nКатегорія - {translate_text(str(category))}\n\n\n📜Опис товару: \n\n{prescription}'
            basket = data.get('basket_id')
            start = data.get('start_id')
            chat_id = callback_query.from_user.id
            try:
                await bot.delete_message(chat_id=chat_id, message_id=start)
                await bot.delete_message(chat_id=chat_id, message_id=basket)
            except:
                await bot.delete_message(chat_id=chat_id, message_id=basket)
            if len(caption) <255:
                photo = await bot.send_photo(callback_query.from_user.id, photo_binary, caption=caption, reply_markup=keyboard_delete_ua, parse_mode='Markdown')
                data['photo_basket'] = photo.message_id
            else:
                keyboard_delete_ua = InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🗑️ Видалити", callback_data='delete_from_basket_ua'),
                    InlineKeyboardButton("⬅️ Назад", callback_data='back_prescr_ua')
                )
                caption_without_desc = f'#️*{articul}*\n📛*{name}* - *{price}*₴\nСтатус - {"❌" if is_available == "0" else "✔️"}\nКраїна виробник - {"🇪🇬" if country == "egypt" else "🇹🇷"}\nКатегорiя - {translate_text(str(category))}'
                photo = await bot.send_photo(callback_query.from_user.id, photo_binary, caption=caption_without_desc, parse_mode='Markdown')
                msg = await bot.send_message(callback_query.from_user.id, prescription, reply_markup=keyboard_delete_ua)
                data['photo_basket'] = photo.message_id
                data['msg_id_prescr'] = msg.message_id

        else:
            chat_id = callback_query.from_user.id
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=callback_query.message.message_id,
                text='Запис не знайдено!',
                reply_markup=keyboard_back_ua,
                parse_mode='Markdown',
            )

@dp.callback_query_handler(lambda c: c.data == 'delete_from_basket_ua')
async def country_filter_ru(callback_query: types.CallbackQuery, state:FSMContext):
    async with state.proxy() as data:
        article = data.get('article_basket')
        collection_basket.delete_one({'article': article})
        chat_id = callback_query.from_user.id
        await bot.delete_message(chat_id=chat_id, message_id=data['photo_basket'])
        try:
            await bot.delete_message(chat_id=chat_id, message_id=data['msg_id_prescr'])
        except:
            pass
        await bot.send_message(
            callback_query.from_user.id,
            'Товар видалено з кошику!',
            reply_markup=keyboard_back_ua,
            parse_mode='Markdown',
        )

@dp.callback_query_handler(lambda c: c.data == 'go_to_filters_ua')
async def country_filter_ru(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=callback_query.message.message_id,
        text=f'Добрий день!\n\nОберiть будь ласка фільтри для країни:',
        reply_markup=keyboard_country_ua,
        parse_mode='Markdown',
    )

@dp.callback_query_handler(lambda query: query.data.startswith("ua_"))
async def show_record_callback(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        country_name = str(callback_query.data.split("_")[1])
        data['country'] = country_name
        chat_id = callback_query.message.chat.id
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=callback_query.message.message_id,
            text=f'Фільтри для цієї країни: ',
            reply_markup=keyboard_category_ua,
            parse_mode='Markdown',
        )

@dp.callback_query_handler(lambda query: query.data.startswith("catu_"))
async def show_record_callback_ua(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        category_name = str(callback_query.data.split("_")[1])
        data['category'] = category_name
        data['available_id'] =  callback_query.message.message_id
        country_name = data.get('country')
        search_results = collection_goods.find({
            'category': str(data['category']),
            'country': str(country_name)
        })
        if collection_goods.count_documents({
            'category': str(data['category']),
            'country': str(country_name)
        }) > 0:
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton('⬅️ Назад', callback_data='back_ua'))

            for result in search_results:
                name = result.get('name')
                article = result.get('articul')
                callback_data = f"temu_{result['_id']}"
                keyboard.add(InlineKeyboardButton(f"#{article} {name}", callback_data=callback_data))
            chat_id = callback_query.message.chat.id
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=callback_query.message.message_id,
                text=f'Ви можете замовити: ',
                reply_markup=keyboard,
                parse_mode='Markdown',
            )
        else:
            chat_id = callback_query.message.chat.id
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=callback_query.message.message_id,
                text='Товарів за даними фільтрами немає!',
                reply_markup=keyboard_back_ua,
                parse_mode='Markdown',
            )

@dp.callback_query_handler(lambda query: query.data.startswith("temu_"))
async def show_record_callback(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        record_id = str(callback_query.data.split("_")[1])
        record = collection_goods.find_one({"_id": ObjectId(record_id)})

        if record:
            photo = record.get('base64_data')
            photo_binary = base64.b64decode(photo)
            name = record.get('name')
            price = record.get('price')
            prescription = record.get('prescription')
            is_available = record.get('is_available')
            articul = record.get('articul')
            data['article'] = articul
            country = record.get('country')
            category = record.get('category')

            caption = f'#️*{articul}*\n📛*{name}* - *{price}*₴\nСтатус - {"❌" if is_available == "0" else "✔️"}\nКраїна виробник - {"🇪🇬" if country == "egypt" else ("🇹🇷" if country == "turkey" else "🇦🇪")}\nКатегорія - {translate_text(str(category))}\n\n\n📜Опис товара: \n\n{prescription}'
            start = data.get('start_id')
            available_id = data.get('available_id')
            chat_id = callback_query.from_user.id
            try:
                await bot.delete_message(chat_id=chat_id, message_id=start)
                await bot.delete_message(chat_id=chat_id, message_id=available_id)
            except:
                await bot.delete_message(chat_id=chat_id, message_id=available_id)
            if len(caption) < 255:
                photo = await bot.send_photo(callback_query.from_user.id, photo_binary, caption=caption, reply_markup=keyboard_buy_ua, parse_mode='Markdown')
                data['photo_id'] = photo.message_id
            else:
                keyboard_buy_ua = InlineKeyboardMarkup().add(
                    InlineKeyboardButton("🛒 Додати в корзину", callback_data='add_to_basket_ua'),
                    InlineKeyboardButton("⬅️ Назад", callback_data='back_prescr_ua')
                )
                caption_without_desc = f'#️*{articul}*\n📛*{name}* - *{price}*₴\nСтатус - {"❌" if is_available == "0" else "✔️"}\nКраїна виробник - {"🇪🇬" if country == "egypt" else "🇹🇷"}\nКатегорiя - {translate_text(str(category))}'
                photo = await bot.send_photo(callback_query.from_user.id, photo_binary, caption=caption_without_desc, parse_mode='Markdown')
                msg = await bot.send_message(callback_query.from_user.id, prescription, reply_markup=keyboard_buy_ua)
                data['photo_basket'] = photo.message_id
                data['msg_id_prescr'] = msg.message_id
        else:
            chat_id = callback_query.from_user.id
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=callback_query.message.message_id,
                text='Запис не знайдено!',
                reply_markup=keyboard_back_ua,
                parse_mode='Markdown',
            )


@dp.callback_query_handler(lambda c: c.data == 'add_to_basket_ua')
async def country_filter_ru(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        article = data.get('article')
        record = collection_goods.find_one({"articul": int(article)})
        name = record.get('name')
        last_basket = collection_basket.find().sort([('number', -1)]).limit(1)
        try:
            last_busket_number = next(last_basket)['number']
        except:
            last_busket_number = 0
        item = {
            'article': article,
            'name': name,
            'number': last_busket_number+1,
            'user_id': callback_query.from_user.username
        }
        collection_basket.insert_one(item)
        chat_id = callback_query.message.chat.id
        try:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=data['msg_id_prescr'])
            except:
                pass
            await bot.delete_message(chat_id=chat_id, message_id=data['photo_basket'])
            await bot.send_message(
                callback_query.from_user.id,
                f'Товар з артикулом *#{article}* був доданий до кошику!',
                reply_markup=keyboard_category_ua,
                parse_mode='Markdown'
            )
        except:
            await bot.delete_message(chat_id=chat_id, message_id=data['photo_id'])
            await bot.send_message(
                callback_query.from_user.id,
                f'Товар з артикулом *#{article}* був доданий до кошику!',
                reply_markup=keyboard_category_ua,
                parse_mode='Markdown'
            )


@dp.callback_query_handler(lambda query: query.data == 'back_ua', state='*')
async def back_button_callback(callback_query: types.CallbackQuery, state: FSMContext):
    chat_id = callback_query.message.chat.id
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=callback_query.message.message_id,
        text='Оберіть дії',
        reply_markup=keyboard_main_ua,
        parse_mode='Markdown',
    )
    await state.reset_state()

@dp.callback_query_handler(lambda query: query.data == 'back_prescr_ua', state='*')
async def back_button_callback(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        chat_id = callback_query.message.chat.id
        try:
            await bot.delete_message(chat_id=chat_id, message_id=data['photo_basket'])
        except:
            pass
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=data['msg_id_prescr'],
            text='Оберіть дії',
            reply_markup=keyboard_main_ua,
            parse_mode='Markdown',
        )
        await state.reset_state()

@dp.callback_query_handler(lambda query: query.data == 'back_form_ua', state='*')
async def back_button_callback(callback_query: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        chat_id = callback_query.message.chat.id
        collection_buys.delete_one({'_id': ObjectId(str(data.get('object_id')))})
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=callback_query.message.message_id,
            text='Оберіть дії',
            reply_markup=keyboard_main_ua,
            parse_mode='Markdown',
        )
        await state.reset_state()

#bot pooling

if __name__ == '__main__':
    executor.start_polling(dp)