import asyncio
import aiohttp
from nicegui import ui

import datetime
import requests
import json
import os
import csv

DELAY = 86400
T1_price = 5.68
T2_price = 3.09
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
    global T1_registrators_data, T2_registrators_data, rows, T1_lost, T2_lost
    ui.notify('Получение данных из личного кабинета WAVIoT')
    T1_registrators_data = await fetch_all(T1_urls)
    T2_registrators_data = await fetch_all(T2_urls)
    
    starttimestamp = '1719522000'
    finishtimestamp = '1719781200'
    T1_personal_registrators_sum=0
    T2_personal_registrators_sum=0
    T1_main_registrator=0
    T2_main_registrator=0
    for row in rows:
        raw_data = T1_registrators_data[int (row['num'])]
        row['T1_start'] = float(raw_data["values"].get(starttimestamp)) if "values" in raw_data else None
        row['T1_finish'] = float(raw_data["values"].get(finishtimestamp)) if "values" in raw_data else None
        row['T1_consumption'] = round(row['T1_finish'] - row['T1_start'],3)
        raw_data = T2_registrators_data[int (row['num'])]
        row['T2_start'] = float(raw_data["values"].get(starttimestamp)) if "values" in raw_data else None
        row['T2_finish'] = float(raw_data["values"].get(finishtimestamp)) if "values" in raw_data else None
        row['T2_consumption'] = round(row['T2_finish'] - row['T2_start'],3)
        if row['address']=="Общий":
            row['T1_consumption'] = row['T1_consumption'] * 50
            row['T2_consumption'] = row['T2_consumption'] * 50
            T1_main_registrator=row['T1_consumption']
            T2_main_registrator=row['T2_consumption']
        else:
            T1_personal_registrators_sum += row['T1_consumption']
            T2_personal_registrators_sum += row['T2_consumption']
    
    T1_lost = round((T1_main_registrator-T1_personal_registrators_sum)*100/T1_personal_registrators_sum, 3)
    T2_lost = round((T2_main_registrator-T2_personal_registrators_sum)*100/T2_personal_registrators_sum, 3)

    for row in rows:
        if row['address']=="Общий":
            row['sum']=round(row['T1_consumption']*T1_price+row['T2_consumption']*T2_price, 3)
        else:
            row['sum']=round((row['T1_consumption']+row['T1_consumption']*T1_lost)*T1_price+(row['T2_consumption']+row['T2_consumption']*T2_lost)*T2_price, 3)

    table.update()
    losts_text.set_content('Потери T1:  **'+str(T1_lost)+'**        |        Потери T2:  **'+str(T2_lost)+'**')
    ui.notify('Получение данных из личного кабинета WAVIoT окончено')

# Получаем путь к файлу registrators.csv 
registrators_file = os.path.join(os.path.dirname(__file__), 'registrators.csv')
with open(registrators_file, mode='r', encoding='utf-8') as file:
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
    {'name': 'T1_consumption', 'label': 'T1 расход', 'field': 'T1_consumption', 'sortable': True},
    {'name': 'T1_finish', 'label': 'T1 конец', 'field': 'T1_finish', 'sortable': False},
    {'name': 'T2_start', 'label': 'T2 начало', 'field': 'T2_start', 'sortable': False},
    {'name': 'T2_consumption', 'label': 'T2 расход', 'field': 'T2_consumption', 'sortable': True},
    {'name': 'T2_finish', 'label': 'T2 конец', 'field': 'T2_finish', 'sortable': False},
    {'name': 'Sum', 'label': 'Сумма+потери', 'field': 'sum', 'sortable': True},
]

T1_lost = 0.0
T2_lost = 0.0

ui.button('Получить данные WAVIoT', on_click=async_task)

table = ui.table(columns=columns, rows=rows, row_key='name')

losts_text = ui.markdown('Потери T1:  **'+str(T1_lost)+'**        |        Потери T2:  **'+str(T2_lost)+'**')

ui.run()
