#imports

import random
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from pymongo import MongoClient
from aiogram import Dispatcher, Bot
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from config import API_TOKEN
from config import CLUSTER_URL
from translate import Translator

#database

cluster = MongoClient(CLUSTER_URL)

db = cluster['VIC_BOT_SUPPORT']
collection_users = db['collection_users']
collection_tickets = db['collection_tickets']
collection_accounting = db['collection_accounting']
collection_goods = db['collection_goods']

#api_token

token = API_TOKEN
bot = Bot(token)
dp = Dispatcher(bot, storage=MemoryStorage())

#time

def get_time_from_datetime(datetime_str):
    datetime_object = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    time_only = datetime_object.strftime("%H:%M:%S")
    return time_only

def get_last_ticket_time(user_id):
    user_tickets = collection_tickets.find({'tg_id': user_id}).sort([('date', -1)])

    previous_ticket_time = None
    try:
        previous_ticket_time = user_tickets[0].get('date', None)
    except IndexError:
        pass

    return previous_ticket_time

def can_make_new_ticket(user_id):
    last_ticket_time = get_last_ticket_time(user_id)

    if last_ticket_time is not None:
        last_ticket_datetime = datetime.strptime(last_ticket_time, "%H:%M:%S")
        current_datetime = datetime.now()
        if current_datetime - last_ticket_datetime < timedelta(hours=1):
            return False
    elif last_ticket_time is None:
        return True
    else:
        return False

#cache

def cache_user_status(func):
    cache = {}

    def wrapper(user_id):
        if user_id not in cache:
            status = get_user_status_from_db(user_id)
            cache[user_id] = status

        return cache[user_id]

    return wrapper

def get_user_status_from_db(user_id):
    user_record = collection_users.find_one({'tg_name': user_id})

    if user_record:
        return user_record.get('status', 'default')
    else:
        return 'default'

@cache_user_status
def get_user_status(user_id):
    return get_user_status_from_db(user_id)

#income_get

def get_income():
    current_date = datetime.now()
    start_date = current_date - timedelta(days=30)
    formatted_start_date = start_date.strftime("%Y-%m-%d")
    records = collection_accounting.find({
        'day': {'$gte': formatted_start_date}
    })
    total_income = 0

    for record in records:
        income = int(record.get('income', 0))
        total_income += income

    return f"Суммарный доход за последние 30 дней: {total_income}"

#get_uah/usd

def get_currency_usd():
    url = 'https://minfin.com.ua/currency/usd/'

    response = requests.get(url)
    html_content = response.content

    soup = BeautifulSoup(html_content, 'html.parser')
    div_elements = soup.find_all('div', class_='sc-1x32wa2-9 bKmKjX')

    if len(div_elements) >= 3:
        dollar_currency = div_elements[2].text.strip()
        return dollar_currency
    else:
        return "На странице не найдено достаточно <div> элементов."

#get_uah/egp

def get_currency_egp():
    url = 'https://minfin.com.ua/currency/egp/'

    response = requests.get(url)
    html_content = response.content

    soup = BeautifulSoup(html_content, 'html.parser')
    div_elements = soup.find_all('div', class_="sc-1x32wa2-9 bKmKjX")

    if len(div_elements) >= 3:
        egp_currency = div_elements[2].text.strip()
        return egp_currency
    else:
        return "На странице не найдено достаточно <div> элементов."

#get_usd/egp
def get_currency_egp2usd():

    url = 'https://wise.com/ru/currency-converter/usd-to-egp-rate'

    response = requests.get(url)
    html_content = response.content

    soup = BeautifulSoup(html_content, 'html.parser')
    div_elements = soup.find_all('span', class_="d-inline-block")
    pattern = re.compile(r'(\d+\.\d+) USD = <!-- --> <span class="text-success">(\d+\.\d+)</span> <!-- -->EGP')
    match = pattern.search(str(div_elements))

    if match:
        usd_to_egp_rate = match.group(2)
        return usd_to_egp_rate
    else:
        return "Данные не найдены"

def get_currency_uah2try():
    url = 'https://minfin.com.ua/currency/converter/uah-try/?converter-type=auction&val1=1&val2=0.6666666666666666'

    response = requests.get(url)
    html_content = response.content

    soup = BeautifulSoup(html_content, 'html.parser')
    span_elements = soup.find_all('span', class_="pyjcac-10 cWYHiB")

    if span_elements:
        span_texts = [span.text.strip() for span in span_elements]
        text = span_texts[1]
        match = re.search(r'\d+\.\d+', text)
        if match:
            return float(match.group())
        else:
            return None
    else:
        return "На странице не найдены теги <span> с классом 'pyjcac-10 cWYHiB'."

#convert_uah/usd

def uah_usd_convertor(amount_uah):
    usd = get_currency_usd()
    usd = usd.split('.')[0]
    usd = usd.replace(',', '.')
    if '.' in usd:
        full, slised = usd.split('.')
        formatted_usd = "{}.{}".format(full, slised[:2])
    else:
        raise TypeError
    result = int(amount_uah)/float(formatted_usd)
    return result

#convert_usd/egp

def usd_egp_convertor(amount_usd):
    egp = get_currency_egp2usd()
    result = int(amount_usd)*float(egp)
    return result

#convert_usd/uah

def usd_uah_convertor(amount_usd):
    usd = get_currency_usd()
    usd = usd.split('.')[0]
    usd = usd.replace(',', '.')
    if '.' in usd:
        full, slised = usd.split('.')
        formatted_usd = "{}.{}".format(full, slised[:2])
    else:
        raise TypeError
    result = int(amount_usd)*float(formatted_usd)
    return result

#convert_uah/egp

def uah_egp_convertor(amount_uah):
    egp = get_currency_egp()
    egp = egp.split('.')[0]
    egp = egp.replace(',', '.')
    if '.' in egp:
        full, slised = egp.split('.')
        formatted_egp = "{}.{}".format(full, slised[:2])
    else:
        raise TypeError
    result = int(amount_uah)/float(formatted_egp)
    return result

#covert_uah/try

def uah_try_convertor(amount_uah):
    try_ = get_currency_uah2try()
    result = int(amount_uah)*float(try_)
    return result

#format_response

def format_response(response):
    pattern = r'\[([^\]]+)\]\[(\d+)\]\[([^\]]+)\]'
    match = re.match(pattern, response)
    
    if match:
        name = match.group(1)
        price = int(match.group(2))
        description = match.group(3)
        return name, price, description
    else:
        return None

#articul generator

def generate_random_4_digit_number():
    return random.randint(1000, 9999)

#translator

def translate_text(text, target_language='ru'):
    translator= Translator(to_lang=target_language)
    translation = translator.translate(text)
    return translation

#pagination MongoDB

def display_records(page_number, items_per_page):

    start_index = (page_number-1) * items_per_page
    keyboard_list = InlineKeyboardMarkup().add(
        InlineKeyboardButton("⬅️ Выйти", callback_data='back'),
        InlineKeyboardButton("⏮️ Назад", callback_data=f'kback_{page_number-1}'),
        InlineKeyboardButton("⏭️ Далее", callback_data=f'kskip_{page_number+1}')
    )
    for record in collection_goods.find().skip(start_index).limit(items_per_page):
        articul = record['articul']
        text = record['name']
        callback_data = f"show_record_goods{record['_id']}"
        keyboard_list.add(InlineKeyboardButton(f"{articul} {text}", callback_data=callback_data))
    return keyboard_list