from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from math import ceil

from settings import bot_config
from api_requests import request
from database import orm

bot = Bot(token=bot_config.token) # создаем объект бота
storage = MemoryStorage() # состояния будем записывать в оперативную память
disp = Dispatcher(bot, storage=storage) # осуществляет опрос сервера телеграмм с последующим выбором хэндлера для обработки принятого ответа

# класс, который будет хранить наше состояние
class ChoiceCityWeather(StatesGroup):
    waiting_city = State() # в этой переменной и будет храниться состояние диалога

class SetUserCity(StatesGroup):
    waiting_user_city = State()

# функция для вызова меню
async def main_menu():
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)  # создаем объект клавиатуры
    btn1 = types.KeyboardButton('Погода в моём городе')  # и кнопки к ней
    btn2 = types.KeyboardButton('Погода в другом месте')
    btn3 = types.KeyboardButton('История')
    btn4 = types.KeyboardButton('Установить свой город')
    markup.add(btn1, btn2, btn3, btn4)  # добавляем созданные кнопки в клавиатуру
    return markup

# такой декоратор нужен, чтобы зарегистрировать функцию, как обработчик сообщений
# (т.е.функция начнет работать, когда бот получит сообщение с текстом установленной команды)
@disp.message_handler(commands=['start'])
@disp.message_handler(regexp='Меню')
async def start_message(message):
    orm.add_user(message.from_user.id) # вызываем функцию добавления пользователя в бд из orm
    markup = await main_menu() # вызываем меню
    # выводим приветственный текст. Имя пользователя можно получить из message (как и многое другое)
    text = f'Привет, {message.from_user.first_name}, я бот, который расскажет тебе о погоде на сегодня'
    # отправляем пользователю приветственный текст и клавиатуру (reply_markup)
    await message.answer(text, reply_markup=markup)

@disp.message_handler(regexp='Погода в моём городе')
async def get_user_city_weather(message):
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
    btn1 = types.KeyboardButton('Меню')
    markup.add(btn1)
    user = orm.get_user_city(message.from_user.id)
    if user.city:
        data = request.get_weather(user.city)
        orm.create_report(message.from_user.id, data["temp"], data["feels_like"], data["wind_speed"],
                          data["pressure_mm"], user.city)
        text = f'Погода в {user.city}\nТемпература: {data["temp"]} ' \
               f'C\nОщущается как: {data["feels_like"]} ' \
               f'C \nСкорость ветра: {data["wind_speed"]}м/с\nДавление: {data["pressure_mm"]}мм'
    else:
        text = 'Город пользователя не установлен'
    await message.answer(text, reply_markup=markup)

@disp.message_handler(regexp='Погода в другом месте')
async def city_start(message: types.Message):
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
    btn1 = types.KeyboardButton('Меню')
    markup.add(btn1)
    text = 'Введите название города'
    await message.answer(text, reply_markup=markup)
    await ChoiceCityWeather.waiting_city.set() # переход бота в состояние ожидания ввода города

@disp.message_handler(state=ChoiceCityWeather.waiting_city) # укажем, на какое конкретно состояние должен реагировать хэндлер
async def city_chosen(message: types.Message, state: FSMContext): # FSMContext - чтобы записывать данные пользователя в память
    message.text = message.text.capitalize() # вдруг пользователь город с маленькой напишет
    await state.update_data(waiting_city=message.text) # записываем введенный текст
    markup = await main_menu()
    city = await state.get_data() # записываем в переменную введенные пользователем данные
    data = request.get_weather(city.get('waiting_city')) # передаём в наш модуль отвечающий за запросы к API введённые пользователем данные
    orm.create_report(message.from_user.id, data["temp"], data["feels_like"], data["wind_speed"], data["pressure_mm"],
                      city.get('waiting_city')) # создание отчета
    text = f'Погода в {city.get("waiting_city")}\nТемпература: {data["temp"]} C\nОщущается как: {data["feels_like"]} ' \
           f'C \nСкорость ветра: {data["wind_speed"]}м/с\nДавление: {data["pressure_mm"]}мм'
    await message.answer(text, reply_markup=markup)
    await state.finish() # выводим диалог из состояния, т.е. он перестаёт записывать чего там пользователь пишет

@disp.message_handler(regexp='Установить свой город')
async def set_user_city_start(message: types.Message):
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)
    btn1 = types.KeyboardButton('Меню')
    markup.add(btn1)
    text = 'Укажите свой город'
    await message.answer(text, reply_markup=markup)
    await SetUserCity.waiting_user_city.set()

# для установки города пользователя
@disp.message_handler(state=SetUserCity.waiting_user_city)
async def city_choose(message: types.Message, state: FSMContext):
    message.text = message.text.capitalize()
    await state.update_data(waiting_user_city=message.text)
    user_data = await state.get_data()
    orm.set_user_city(message.from_user.id, user_data.get('waiting_user_city')) # вызываем функцию установки города
    markup = await main_menu()
    text = f'Запомнил, {user_data.get("waiting_user_city")} ваш город'
    await message.answer(text, reply_markup=markup)
    await state.finish()

# для вывода истории запросов конкретного пользователя
@disp.message_handler(regexp= 'История')
async def reports_history(message: types.Message):
    current_page = 1 # номер текущей страницы
    reports = orm.get_reports(message.from_user.id) # вызываем функцию из orm
    total_pages = ceil(len(reports) / 3)
    # получаем общее число страниц для вывода - общее число отчетов делим на 3 и округляем в большую сторону
    # (будем выводить по 3 отчета на страницу)
    text = 'История запросов:'
    inline_markup = types.InlineKeyboardMarkup() # клавиатура для вывода
    for report in reports[:current_page*3]:
        inline_markup.add(types.InlineKeyboardButton(
            text=f'{report.city} {report.date.day}.{report.date.month}.{report.date.year}', # указываем данные, которые будут на кнопке отчета
            callback_data=f'report_{report.id}' # перекидываем на отчет при нажатии
        ))
    inline_markup.row(
        types.InlineKeyboardButton(text=f'{current_page-1}/{total_pages}', callback_data='None'),
        types.InlineKeyboardButton(text='Вперёд', callback_data=f'next_{current_page}')
    ) # для пагинации
    await message.answer(text, reply_markup=inline_markup)

@disp.callback_query_handler(lambda call: True) # реагирует только на callback_data
async def callback_query(call, state: FSMContext):
    query_type = call.data.split('_')[0] # записываем в переменную query_type callback_data

    async with state.proxy() as data:

        if data.get('current_page', None) is None:
            data['current_page'] = 0

        if query_type == 'None':
            return

        if query_type == 'next' or query_type == 'prev' or query_type == 'reports':
            data['current_page'] = data['current_page'] + {
                'next': 1,
                'prev': -1,
                'reports': 0
            }[query_type]
            await state.update_data(current_page=data['current_page'])
            reports = orm.get_reports(call.from_user.id)
            total_pages = ceil(len(reports) / 3)
            inline_markup = types.InlineKeyboardMarkup()
            for report in reports[data['current_page'] * 3:(data['current_page'] + 1) * 3]:
                inline_markup.add(types.InlineKeyboardButton(
                    text=f'{report.city} {report.date.day}.{report.date.month}.{report.date.year}',
                    callback_data=f'report_{report.id}'
                ))
            btns = [
                types.InlineKeyboardButton(text=f'{data["current_page"] + 1}/{total_pages}', callback_data='None')
            ]
            if data['current_page'] != 0:
                btns.append(types.InlineKeyboardButton(text='Назад', callback_data=f'prev_{data["current_page"] - 1}'))
            if (data['current_page'] + 1) * 3 < len(reports):
                btns.append(types.InlineKeyboardButton(text='Вперёд', callback_data=f'next_{data["current_page"] + 1}'))
            inline_markup.row(*btns)
            await call.message.edit_text(text="История запросов:", reply_markup=inline_markup)

        if query_type == 'report':
            reports = orm.get_reports(call.from_user.id)
            report_id = call.data.split('_')[1]
            inline_markup = types.InlineKeyboardMarkup()
            for report in reports:
                if report.id == int(report_id):
                    inline_markup.add(
                        types.InlineKeyboardButton(text='Назад', callback_data=f'reports_{data["current_page"]}'),
                        types.InlineKeyboardButton(text='Удалить запрос', callback_data=f'delete_report_{report_id}')
                    )
                    await call.message.edit_text(
                        text=f'Данные по запросу\n'
                             f'Город: {report.city}\n'
                             f'Температура: {report.temp} C\n'
                             f'Ощущается как: {report.feels_like} C\n'
                             f'Скорость ветра: {report.wind_speed} м/c\n'
                             f'Давление: {report.pressure_mm} mm',
                        reply_markup=inline_markup
                    )
                    break

        # ну и для удаления
        if query_type == 'delete' and call.data.split('_')[1] == 'report':
            report_id = call.data.split('_')[2]
            orm.delete_user_report(report_id)
            current_page = 0
            reports = orm.get_reports(call.from_user.id)
            total_pages = ceil(len(reports) / 3)
            text = 'История запросов:'
            inline_markup = types.InlineKeyboardMarkup()
            for report in reports[current_page * 3:(current_page + 1) * 3]:
                inline_markup.add(types.InlineKeyboardButton(
                    text=f'{report.city} {report.date.day}.{report.date.month}.{report.date.year}',
                    callback_data=f'report_{report.id}'
                ))
            btns = [types.InlineKeyboardButton(text=f'{current_page + 1}/{total_pages}', callback_data='None')]
            if len(reports) > 3:
                btns.append(types.InlineKeyboardButton(text='Вперёд', callback_data=f'next_{current_page}'))
            inline_markup.row(*btns)
            await state.update_data(current_page=current_page)
            await call.message.edit_text(text, reply_markup=inline_markup)

# чтобы бот постоянно опрашивал сервер телеграм на предмет новых сообщений
if __name__ == '__main__':
    executor.start_polling(disp, skip_updates=True)
