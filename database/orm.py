from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, User, WeatherReport
from settings import database_config

#подключаемся к бд
engine = create_engine(database_config.url, echo=True)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# функция добавления нового пользователя в бд
def add_user(tg_id):
    session = Session()
    user = session.query(User).filter(User.tg_id == str(tg_id)).first() # пытаемся найти такого пользователя в бд
    if user is None: # если такого нет в бд - добавляем
        new_user = User(tg_id=tg_id)
        session.add(new_user)
        session.commit() # сохраняем в бд

# функция установки города пользователя
def set_user_city(tg_id, city):
    session = Session()
    user = session.query(User).filter(User.tg_id == str(tg_id)).first()
    user.city = city
    session.commit()

# запись отчета о погоде в бд
def create_report(tg_id, temp, feels_like, wind_speed, pressure_mm, city):
    session = Session()
    user = session.query(User).filter(User.tg_id == str(tg_id)).first()
    new_report = WeatherReport(temp=temp, feels_like=feels_like, wind_speed=wind_speed, pressure_mm=pressure_mm, city=city, owner=user.id)
    session.add(new_report)
    session.commit()

# получаем город пользователя по переданному айди
def get_user_city(tg_id):
    session = Session()
    user = session.query(User).filter(User.tg_id == str(tg_id)).first()
    if user:
        return user

# вывод отчетов
def get_reports(tg_id):
    session = Session()
    user = session.query(User).filter(User.tg_id == str(tg_id)).first()
    reports = user.reports
    return reports

# удаление отчетов
def delete_user_report(report_id):
    session = Session()
    report = session.get(WeatherReport, report_id)
    session.delete(report)
    session.commit()

