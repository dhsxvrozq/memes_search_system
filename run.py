import os
import telebot
from dotenv import load_dotenv
import pytesseract
from PIL import Image
from io import BytesIO
import logging
import re
import time
from collections import defaultdict

# Basic logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

TGBOT_TOKEN = os.getenv('TGBOT_TOKEN')
SOURCE_CHAT_ID = int(os.getenv('SOURCE_CHAT_ID'))
TARGET_CHANNEL_ID = int(os.getenv('TARGET_CHANNEL_ID'))

bot = telebot.TeleBot(TGBOT_TOKEN)

# Storage for media groups
media_groups = defaultdict(list)
media_group_timers = {}

# Function to recognize text from a photo by file_id
def recognize_text_from_photo(file_id):
    try:
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        image = Image.open(BytesIO(downloaded_file))
        text = pytesseract.image_to_string(image, lang='rus+eng')
        return text.strip()
    except Exception as e:
        logger.error(f"Text recognition error: {e}")
        return ""

def process_media_group(media_group_id):
    """Process collected media group"""
    try:
        if media_group_id not in media_groups:
            return
            
        messages = media_groups[media_group_id]
        # Sort messages by message_id to maintain order
        messages.sort(key=lambda x: x.message_id)
        
        media_to_send = []
        media_with_text = []
        
        for message in messages:
            if message.photo:
                file_id = message.photo[-1].file_id
                media_to_send.append(telebot.types.InputMediaPhoto(file_id))
                
                # Recognize text for TARGET_CHANNEL_ID
                text = recognize_text_from_photo(file_id)
                if text:
                    media_with_text.append(telebot.types.InputMediaPhoto(file_id, caption=text))
                    
            elif message.video:
                file_id = message.video.file_id
                media_to_send.append(telebot.types.InputMediaVideo(file_id))
        
        # Send media group to SOURCE_CHAT_ID
        if media_to_send:
            bot.send_media_group(SOURCE_CHAT_ID, media_to_send)
            
            # Send photos with recognized text to TARGET_CHANNEL_ID
            if media_with_text:
                bot.send_media_group(TARGET_CHANNEL_ID, media_with_text)
        
        # Delete original messages
        for message in messages:
            try:
                bot.delete_message(message.chat.id, message.message_id)
            except Exception as e:
                logger.error(f"Error deleting message: {e}")
        
        # Clean up
        del media_groups[media_group_id]
        if media_group_id in media_group_timers:
            del media_group_timers[media_group_id]
            
    except Exception as e:
        logger.error(f"Error processing media group: {e}")

def delayed_process_media_group(media_group_id):
    """Process media group after a delay to collect all messages"""
    time.sleep(1)  # Wait 1 second to collect all messages in the group
    process_media_group(media_group_id)

@bot.message_handler(commands=['start'])
def handle_start(message):
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

@bot.message_handler(func=lambda message: message.chat.id == SOURCE_CHAT_ID and message.forward_date is not None, content_types=['photo', 'video'])
def handle_forwarded_media(message):
    try:
        # Check if this is part of a media group
        if message.media_group_id:
            media_group_id = message.media_group_id
            media_groups[media_group_id].append(message)
            
            # Start timer for processing media group (or reset if already exists)
            if media_group_id in media_group_timers:
                media_group_timers[media_group_id].cancel()
            
            import threading
            timer = threading.Timer(1.0, delayed_process_media_group, args=(media_group_id,))
            media_group_timers[media_group_id] = timer
            timer.start()
            
        else:
            # Single media message - process immediately
            if message.photo:
                file_id = message.photo[-1].file_id
                bot.send_photo(SOURCE_CHAT_ID, file_id)
                text = recognize_text_from_photo(file_id)
                if text:
                    bot.send_photo(TARGET_CHANNEL_ID, file_id, caption=text)

            elif message.video:
                file_id = message.video.file_id
                bot.send_video(SOURCE_CHAT_ID, file_id, supports_streaming=True)

            # Delete the original forwarded message
            bot.delete_message(message.chat.id, message.message_id)

    except Exception as e:
        logger.error(f"Error processing forwarded media: {e}")

@bot.message_handler(func=lambda message: message.chat.id == SOURCE_CHAT_ID, content_types=['photo'])
def handle_photo(message):
    try:
        file_id = message.photo[-1].file_id
        text = recognize_text_from_photo(file_id)
        if text:
            bot.send_photo(TARGET_CHANNEL_ID, file_id, caption=text)
    except Exception as e:
        logger.error(f"Error processing photo: {e}")

# YouTube Shorts handler
YOUTUBE_RE = re.compile(r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/(watch\?v=)?[\w-]+', re.IGNORECASE)

from yt_download import download_video

@bot.message_handler(func=lambda m: m.chat.id == SOURCE_CHAT_ID, content_types=['text'])
def handle_video_links(message):
    if not message.entities:
        return

    url = None
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
        return

    try:
        video_path = download_video(url)
        if video_path and os.path.isfile(video_path):
            with open(video_path, 'rb') as v:
                bot.send_video(
                    SOURCE_CHAT_ID,
                    video=v,
                    supports_streaming=True
                )
                bot.delete_message(message.chat.id, message.message_id)
            os.remove(video_path)
    except Exception as e:
        logger.error(f"Error processing YouTube link: {e}")

logger.info("Bot started and waiting for messages...")
bot.polling(none_stop=True)
