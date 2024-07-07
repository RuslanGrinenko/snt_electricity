import asyncio
import aiohttp
from nicegui import ui

import datetime
import requests
import json
import os
import csv

DELAY = 86400
# API_KEY="Нужно посмотреть на портале waviot и сохранить в файл api.key"
# Получаем значение API_KEY из файла
api_key_file = os.path.join(os.path.dirname(__file__), 'api.key')
with open(api_key_file, 'r') as file:
    API_KEY = file.read().strip()

WAVIOT_T1_URL = "https://lk.waviot.ru/api.data/get_modem_channel_values/?channel=electro_ac_p_lsum_t1&key=" + API_KEY + "&modem_id="
WAVIOT_T2_URL = "https://lk.waviot.ru/api.data/get_modem_channel_values/?channel=electro_ac_p_lsum_t2&key=" + API_KEY + "&modem_id="

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.json()

async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

async def async_task():
    global T1_registrators_data, T2_registrators_data, rows
    ui.notify('Asynchronous task started')
    T1_registrators_data = await fetch_all(T1_urls)
    T2_registrators_data = await fetch_all(T2_urls)
    
    starttimestamp = '1717189200'
    finishtimestamp = '1719781200'
    for row in rows:
        raw_data = T1_registrators_data[int (row['num'])]
        row['T1_start'] = raw_data["values"].get(starttimestamp) if "values" in raw_data else None
        row['T1_finish'] = raw_data["values"].get(finishtimestamp) if "values" in raw_data else None
    
    table.update()
    ui.notify('Asynchronous task finished')

# Получаем путь к файлу registrators.csv 
registrators_file = os.path.join(os.path.dirname(__file__), 'registrators.csv')
with open(registrators_file, 'r') as file:
    reader = csv.reader(file)
    header = next(reader) # считываем первую строку как заголовок
    data = list(reader) # считываем оставшиеся строки в список

# Преобразуем данные в нужный формат
registrators = []
T1_urls = []
T2_urls = []
rows = []
i=0
for row in data:
    address, registrator = row
    registrators.append((address, registrator))
    T1_urls.append(WAVIOT_T1_URL + registrator)
    T2_urls.append(WAVIOT_T2_URL + registrator)
    rows.append({'num':str(i), 'address':address, 'registrator':registrator})
    i+=1

T1_registrators_data = []
T2_registrators_data = []

# Рисуем таблицу
columns = [
    {'name': 'address', 'label': 'Номер участка', 'field': 'address', 'required': True, 'align': 'left', 'sortable': True},
    {'name': 'registrator', 'label': 'Номер счётчика', 'field': 'registrator', 'sortable': False},
    {'name': 'T1_start', 'label': 'T1 начало', 'field': 'T1_start', 'sortable': False},
    {'name': 'T1_finish', 'label': 'T1 конец', 'field': 'T1_finish', 'sortable': False},
]

ui.button('Получить данные WAVIoT', on_click=async_task)

table = ui.table(columns=columns, rows=rows, row_key='name')

ui.run()
