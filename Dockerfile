# Используем базовый образ Python
FROM python:3.11-slim

# Установка Tesseract и русского языка
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-rus

# Копируем скрипт зависимостей внутрь контейнера
COPY req.txt .

# Установка зависимостей Python
RUN pip install --no-cache-dir -r req.txt

# Копируем весь код бота в контейнер
COPY . .

# Запускаем скрипт
CMD ["python3", "run.py"]
