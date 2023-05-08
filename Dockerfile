FROM python:3.10
# Создаём папку bot
RUN mkdir -p /usr/src/bot
# Делаем созданную папку нашей рабочей областью
WORKDIR /usr/src/bot
# Копируем файлы с нашей машины . , в контейнер /usr/src/bot
COPY . /usr/src/bot
# Устанавливаем все необходимые библиотеки Python читая requirements.txt (не забудьте его заполнить)
RUN pip install --no-cache-dir -r requirments.txt
# Говорим что надо сделать после запуска контейнера, в нашем случае выполнить команду python bot.py
CMD ["python", "bot.py"]

