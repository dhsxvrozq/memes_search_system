import os
import telebot
from dotenv import load_dotenv
import pytesseract
from PIL import Image
from io import BytesIO
import logging
from telebot.apihelper import ApiTelegramException

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

TGBOT_TOKEN = os.getenv('TGBOT_TOKEN')
SOURCE_CHAT_ID = int(os.getenv('SOURCE_CHAT_ID'))
TARGET_CHANNEL_ID = int(os.getenv('TARGET_CHANNEL_ID'))

bot = telebot.TeleBot(TGBOT_TOKEN)

@bot.message_handler(commands=['start'])
def handle_start(message):
    logger.info(f"Команда /start от пользователя {message.from_user.id}")
    text = (
    "🎯 Функциональность бота \"МЕМОЛОГ\"\n\n"
    "1️⃣ Распознавание текста на мемах  \n"
    "Бот автоматически обрабатывает картинки, отправленные в чат:  \n"
    "🔍 находит и распознаёт текст на изображении  \n"
    "📤 пересылает мем в закрытый канал с подписью  \n"
    "🔎 благодаря этому можно быстро найти нужные мемы по тексту  \n"
    "📌 Мемасы.Поиск — https://t.me/+Q56JVqUrZThjMjJi\n\n"
    "2️⃣ Очистка YouTube Shorts  \n"
    "📎 Просто отправь ссылку на YouTube Shorts в чат  \n"
    "🤖 Бот удалит ссылку и вернёт в чат чистое видео — без лишнего мусора"
)

    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda message: message.chat.id == SOURCE_CHAT_ID, content_types=['photo'])
def handle_photo(message):
    try:
        user_id = message.from_user.id
        file_id = message.photo[-1].file_id
        logger.info(f"Получено фото от пользователя {user_id}, file_id: {file_id}")

        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        logger.info(f"Фото {file_id} скачано успешно")

        image = Image.open(BytesIO(downloaded_file))
        text = pytesseract.image_to_string(image, lang='rus+eng')
        logger.info(f"Распознанный текст: {text[:100]}...")

        bot.send_photo(TARGET_CHANNEL_ID, file_id, caption=text)
        logger.info(f"Фото {file_id} отправлено в канал {TARGET_CHANNEL_ID}")

    except Exception as e:
        logger.error(f"Ошибка при обработке фото: {e}")


import re

YOUTUBE_RE = re.compile(
    r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/(watch\?v=)?[\w-]+',
    re.IGNORECASE
)


from yt_download import download_video
@bot.message_handler(func=lambda m: m.chat.id == SOURCE_CHAT_ID,
                     content_types=['text'])
def handle_video_links(message):
    """
    Обрабатывает только сообщения, содержащие ссылки на YouTube.
    Остальные текстовые сообщения остаются без изменений.
    """
    if not message.entities:
        return

    sender_name = message.from_user.full_name
    sender_username = message.from_user.username
    url = None  # сюда запишем первую найденную YouTube-ссылку

    for ent in message.entities:
        if ent.type == 'url':
            candidate = message.text[ent.offset:ent.offset + ent.length]
        elif ent.type == 'text_link':
            candidate = ent.url
        else:
            continue

        if YOUTUBE_RE.search(candidate):
            url = candidate
            break

    if not url:
        return  # YouTube-ссылок нет

    # далее можно использовать переменную url
    try:
        video_path = download_video(url)
        if video_path and os.path.isfile(video_path):
            file_size = os.path.getsize(video_path)
            if file_size > 50 * 1024 * 1024:
                logger.warning("Файл > 50 МБ, отправляем как документ")
                bot.send_document(TARGET_CHANNEL_ID, open(video_path, 'rb'))
            else:
                with open(video_path, 'rb') as v:
                    bot.send_video(
                        SOURCE_CHAT_ID,
                        video=v,
                        caption=f'{message.from_user.full_name} \n@{message.from_user.username}',
                        supports_streaming=True   # ключевой флаг
                    )

                    try:
                        bot.delete_message(message.chat.id, message.message_id)
                        logger.info("Исходное сообщение удалено")
                    except ApiTelegramException as e:
                        logger.warning(f"Не удалось удалить сообщение: {e}")

            os.remove(video_path)  # удалить после отправки, если нужно
    except Exception as e:
        logger.error(f"Ошибка при пересылке ссылки: {e}")

# Логируем запуск
logger.info("Бот запущен и ожидает сообщения...")

bot.polling(none_stop=True)
