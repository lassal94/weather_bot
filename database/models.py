from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base #для одновременного определения таблиц и моделей
from sqlalchemy.orm import relationship # для связывания объектов
from datetime import datetime as dt

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    tg_id = Column(String, nullable=False) # строка, т.к. может быть очень большим числом
    city = Column(String(30))
    connection_date = Column(DateTime, default=dt.now, nullable=False)
    reports = relationship('WeatherReport', backref='user', lazy=True, cascade='all, delete-orphan')
    # cascade='all, delete-orphan' - чтобы при удалении юзера удалялись все его отчеты о погоде

    def __repr__(self):
        return f'Пользователь {self.id}'

class WeatherReport(Base):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=dt.now, nullable=False)
    temp = Column(Integer, nullable=False)
    feels_like = Column(Integer, nullable=False)
    wind_speed = Column(Integer, nullable=False)
    pressure_mm = Column(Integer, nullable=False)
    city = Column(String(30), nullable=False)
    owner = Column(Integer, ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f'Отчет {self.city}'



