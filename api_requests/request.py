import requests
from settings import api_config


# функция принимает название города, подставляет в параметры запроса и делает get запрос на api
def get_city_coord(city):
    payload = {'geocode': city, 'apikey': api_config.geo_key, 'format': 'json'} # словарь с параметрами запроса
    r = requests.get('https://geocode-maps.yandex.ru/1.x', params=payload)
    # передаем в get url нашего api, а в params - ранее созданную переменную с параметрами запроса
    # возвращаем координаты
    return r.json()['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']

def get_weather(city):
    coords = get_city_coord(city).split()
    payload = {'lat': coords[1], 'lon': coords[0], 'lang': 'ru_RU'} #словарь с широтой, долготовй и языком
    r = requests.get('https://api.weather.yandex.ru/v2/forecast',  # передаем стандартный url (из доки)
                     params=payload,  # параметры, заданные ранее
                     headers=api_config.weather_key)  # погодный ключ
    return r.json()['fact'] # преобразуем в json и обращаемся к ключу fact (инфо о погоде за текущий день хранится в этом ключе)
