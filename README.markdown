# Приложение для распознавания текста в мемах

Это телеграм бот, который делает подписи для мемов и публикует результаты в отдельный канал, упрощая поиск мемов в случае необходимости. 

Пока что реализован только поиск по тексту на пикче

## Использование

После выполнения шагов установки приложение будет запущено

1. Добавьте бота в чат в качесве обычного участника
2. Добавьте бота в канал в качестве администратора, 
   (В этот канал будут публиковаться пикчи и распознанный текст)
3. Просто пользуйтесь чатом как обычно, бот сделает все сам


# Установка

1. **Клонирование репозитория:**

   ```bash
   git clone https://github.com/dhsxvrozq/memes_search_system.git
   cd memes_search_system
   ```

2. **Создай файл .env рядом с docker-compose.yml**
   ```
   TGBOT_TOKEN=ваш_токен_бота
   SOURCE_CHAT_ID=ID_чата_или_канала
   TARGET_CHANNEL_ID=@target_channel_или_ID
   ```
2. **Сборка и запуск приложения с помощью Docker Compose:**

   ```bash
   docker compose build
   docker compose up
   ```



## Содержание
- [Предварительные требования](#предварительные-требования)
- [Установка](#установка)
- [Структура проекта](#структура-проекта)
- [Использование](#использование)
- [Вклад в проект](#вклад-в-проект)
- [Лицензия](#лицензия)

## Предварительные требования
- Ubuntu (или совместимый дистрибутив Linux)
```
apt install git
```

## Установка

1. **Добавление официального GPG-ключа Docker:**

   ```bash
   sudo apt-get update
   sudo apt-get install ca-certificates curl
   sudo install -m 0755 -d /etc/apt/keyrings
   sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
   sudo chmod a+r /etc/apt/keyrings/docker.asc
   ```

2. **Добавление репозитория Docker в источники Apt:**

   ```bash
   echo \
     "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
     $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
     sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   sudo apt-get update
   ```

3. **Установка Docker и связанных компонентов:**

   ```bash
   sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   ```

4. **Клонирование репозитория:**

   ```bash
   git clone https://github.com/dhsxvrozq/memes_search_system.git
   cd memes
   ```

5. **Сборка и запуск приложения с помощью Docker Compose:**

   ```bash
   docker compose build
   docker compose up
   ```

## Структура проекта

```plaintext
.
├── docker-compose.yml         # Конфигурация Docker Compose для оркестрации сервисов
├── ocr                        # Папка сервиса OCR
│   ├── Dockerfile.ocr         # Dockerfile для сборки контейнера OCR
│   └── ocr_api.py             # Основной скрипт API для OCR
├── README.md                  # Документация проекта
└── tg_bot                     # Папка Telegram-бота
    ├── Dockerfile.tg_bot      # Dockerfile для сборки контейнера бота
    ├── req.txt                # Файл с зависимостями для бота
    └── run.py                 # Основной скрипт для запуска бота
```


Для остановки приложения используйте:

```bash
docker compose down
```

## Вклад в проект

Мы приветствуем любые улучшения и предложения! Чтобы внести свой вклад:

1. Сделайте форк репозитория.
2. Создайте новую ветку (`git checkout -b feature/ваша-фича`).
3. Внесите изменения и закоммитьте их (`git commit -m 'Добавлена новая фича'`).
4. Отправьте изменения в ваш форк (`git push origin feature/ваша-фича`).
5. Создайте Pull Request в основной репозиторий.

## Лицензия

Этот проект распространяется под лицензией [MIT](LICENSE). Подробности см. в файле LICENSE.