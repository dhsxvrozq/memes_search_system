import os
import telebot
from dotenv import load_dotenv
import pytesseract
from PIL import Image
from io import BytesIO
import logging

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
    bot.send_message(message.chat.id, "Привет! Я распознаю текст на фото и пересылаю его в канал.")

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

# Логируем запуск
logger.info("Бот запущен и ожидает сообщения...")

bot.polling(none_stop=True)
