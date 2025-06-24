import telebot
import os
from dotenv import load_dotenv
from datetime import datetime
import logging
import requests
# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

load_dotenv()

TGBOT_TOKEN = os.getenv('TGBOT_TOKEN')
MEMASY_CHAT_ID = int(os.getenv('SOURCE_CHAT_ID'))
TARGET_CHANNEL_ID = int(os.getenv('TARGET_CHANNEL_ID'))

bot = telebot.TeleBot(TGBOT_TOKEN)

OCR_API_URL = "http://ocr_api:8000/ocr"

def test_connection():
    """Проверка соединения с Telegram API"""
    try:
        bot_info = bot.get_me()
        logger.info(f"Соединение установлено. Бот: @{bot_info.username} ({bot_info.first_name})")
        return True
    except Exception as e:
        logger.error(f"Ошибка соединения с Telegram API: {e}")
        return False

def test_chat_access():
    """Проверка доступа к чатам"""
    try:
        # Проверяем доступ к исходному чату
        source_chat = bot.get_chat(MEMASY_CHAT_ID)
        logger.info(f"Доступ к исходному чату: {source_chat.title or source_chat.type}")
        
        # Проверяем доступ к целевому каналу
        target_chat = bot.get_chat(TARGET_CHANNEL_ID)
        logger.info(f"Доступ к целевому каналу: {target_chat.title or target_chat.type}")
        
        return True
    except Exception as e:
        logger.error(f"Ошибка доступа к чатам: {e}")
        return False

@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker'])
def handle_messages(message):
    if message.chat.id == MEMASY_CHAT_ID:
        logger.info(f"Получено сообщение от пользователя {message.from_user.id}")
        
        try:
            if message.text:
                bot.send_message(TARGET_CHANNEL_ID, message.text)
                logger.info(f"Отправлен текст: {message.text[:100]}{'...' if len(message.text) > 100 else ''}")
                
            elif message.photo:
                # Получаем самый качественный вариант фото
                file_id = message.photo[-1].file_id
                file_info = bot.get_file(file_id)
                downloaded_file = bot.download_file(file_info.file_path)

                # Сохраняем временно файл
                temp_file_path = f"/tmp/{file_id}.jpg"
                with open(temp_file_path, 'wb') as new_file:
                    new_file.write(downloaded_file)

                # Отправляем файл на /ocr
                with open(temp_file_path, 'rb') as f:
                    files = {"file": (f"{file_id}.jpg", f, "image/jpeg")}
                    response = requests.post(OCR_API_URL, files=files)
                
                # Логируем ответ
                logger.info(f"OCR-ответ: {response.text}")
                
                # Можно отправить фото тоже, если нужно:
                bot.send_photo(TARGET_CHANNEL_ID, file_id, caption=response.text)

                # Удаляем временный файл
                os.remove(temp_file_path)

                caption_info = f" с подписью: {message.caption}" if message.caption else ""
                logger.info(f"Отправлено фото{caption_info}")

                
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
    else:
        logger.debug(f"Игнорирую сообщение из чата {message.chat.id}")

def main():
    logger.info("Запуск бота...")
    
    # Проверка соединения
    if not test_connection():
        logger.critical("Не удалось установить соединение с Telegram API")
        return
    
    # Проверка доступа к чатам
    if not test_chat_access():
        logger.critical("Не удалось получить доступ к чатам")
        return
    
    logger.info(f"Конфигурация:")
    logger.info(f"  Исходный чат ID: {MEMASY_CHAT_ID}")
    logger.info(f"  Целевой канал ID: {TARGET_CHANNEL_ID}")
    logger.info("Бот готов к работе. Ожидание сообщений...")
    
    try:
        bot.polling(none_stop=True)
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    main()