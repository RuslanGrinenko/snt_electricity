import datetime
import requests
import json
import os
import csv
from colorama import init, Fore, Back, Style
init()

DELAY=86400
# API_KEY="Нужно посмотреть на портале waviot и сохранить в файл api.key"
# Получаем значение API_KEY из файла
api_key_file = os.path.join(os.path.dirname(__file__), 'api.key')
with open(api_key_file, 'r') as file:
    API_KEY = file.read()

# TG_BOT_API_KEY="код бота телеграм"
# Получаем значение TG_BOT_API_KEY из файла
tg_bot_api_key_file = os.path.join(os.path.dirname(__file__), 'tg_bot_api.key')
with open(tg_bot_api_key_file, 'r') as file:
    TG_BOT_API_KEY = file.read()


def registrator_worked(timestamp):
 current_time = datetime.datetime.now()
 passed_time = datetime.datetime.fromtimestamp(timestamp)
 difference = current_time - passed_time
 #print(difference.total_seconds())
 if difference.total_seconds() >= DELAY:
   return False
 else:
   return True

def get_latest_timestamp(modem_num):
 url = "https://lk.waviot.ru/api.data/get_modem_channel_values/?modem_id=" + modem_num + "&channel=electro_ac_p_lsum_t1&key=" + API_KEY
 response = requests.get(url)
 data = response.json()
 #print(data)
 return int (max(data["values"].keys()))

def get_T1_by_timestamp(modem_num, timestamp):
 url = "https://lk.waviot.ru/api.data/get_modem_channel_values/?modem_id=" + modem_num + "&channel=electro_ac_p_lsum_t1&key=" + API_KEY
 response = requests.get(url)
 data = response.json()
 #print(data)
 return data['values'][str(timestamp)]

def get_T2_by_timestamp(modem_num, timestamp):
 url = "https://lk.waviot.ru/api.data/get_modem_channel_values/?modem_id=" + modem_num + "&channel=electro_ac_p_lsum_t2&key=" + API_KEY
 response = requests.get(url)
 data = response.json()
 #print(data)
 return data['values'][str(timestamp)]


# Получаем путь к файлу registrators.csv 
registrators_file = os.path.join(os.path.dirname(__file__), 'registrators.csv')
with open(registrators_file, 'r') as file:
 reader = csv.reader(file)
 header = next(reader) # считываем первую строку как заголовок
 data = list(reader) # считываем оставшиеся строки в список

# Преобразуем данные в нужный формат
registrators = []
for row in data:
 address, registrator = row
 registrators.append((address, registrator))


for address, registrator in registrators:
    print(Style.RESET_ALL + "Registrator " + address + " :   ", end='')
    if not registrator_worked(get_latest_timestamp(registrator)):
      print(Fore.RED + "status BROKEN!")
      url = "https://api.telegram.org/" + TG_BOT_API_KEY + "/sendMessage?chat_id=114646733&text=Registrator " + registrator + " is broken!"
      response = requests.get(url)   
    else:
      print(Fore.GREEN + "status OK!")