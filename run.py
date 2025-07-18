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
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
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
    logger.debug(f"Starting OCR for file_id={file_id}")
    try:
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        image = Image.open(BytesIO(downloaded_file))
        text = pytesseract.image_to_string(image, lang='rus+eng').strip()
        logger.debug(f"OCR result for file_id={file_id}: '{text}'")
        return text
    except Exception as e:
        logger.error(f"Text recognition error for file_id={file_id}: {e}")
        return ""

def process_media_group(media_group_id):
    logger.debug(f"Processing media group: {media_group_id}")
    try:
        messages = media_groups.pop(media_group_id, [])
        if not messages:
            return
        messages.sort(key=lambda x: x.message_id)

        media_group = []
        media_with_text = []
        for msg in messages:
            if msg.photo:
                file_id = msg.photo[-1].file_id
                media_group.append(telebot.types.InputMediaPhoto(file_id))
                text = recognize_text_from_photo(file_id)
                caption = text if text else None
                media_with_text.append(telebot.types.InputMediaPhoto(file_id, caption=caption) if caption else telebot.types.InputMediaPhoto(file_id))
            elif msg.video:
                media_group.append(telebot.types.InputMediaVideo(msg.video.file_id))

        bot.send_media_group(SOURCE_CHAT_ID, media_group)
        bot.send_media_group(TARGET_CHANNEL_ID, media_with_text)

        for msg in messages:
            try:
                bot.delete_message(msg.chat.id, msg.message_id)
            except Exception as e:
                logger.error(f"Error deleting message id={msg.message_id}: {e}")
    except Exception as e:
        logger.error(f"Error in process_media_group: {e}")


def delayed_process_media_group(media_group_id):
    time.sleep(1)
    process_media_group(media_group_id)

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, (
        "🎯 Функциональность бота \"МЕМОЛОГ\"\n\n"
        "1️⃣ Распознавание текста на мемах  \n"
        "🔍 распознаёт текст на изображении и пересылает в канал  \n"
        "2️⃣ Очистка YouTube Shorts  \n"
        "🤖 отправьте ссылку на Shorts — бот вернёт чистое видео"
    ))

# YouTube Shorts handler
YOUTUBE_SHORTS_RE = re.compile(r"(https?://)?(www\.)?youtube\.com/shorts/[\w-]+", re.IGNORECASE)
from yt_download import download_video

@bot.message_handler(func=lambda m: m.chat.id == SOURCE_CHAT_ID and m.entities, content_types=['text'])
def handle_video_links(message):
    for ent in message.entities:
        if ent.type in ['url', 'text_link']:
            url = message.text[ent.offset:ent.offset+ent.length] if ent.type=='url' else ent.url
            if YOUTUBE_SHORTS_RE.search(url):
                try:
                    path = download_video(url)
                    with open(path, 'rb') as v:
                        bot.send_video(SOURCE_CHAT_ID, v, supports_streaming=True)
                    bot.delete_message(message.chat.id, message.message_id)
                    os.remove(path)
                except Exception as e:
                    logger.error(f"Error downloading shorts: {e}")
                break

# Forwarded media (group/single)
@bot.message_handler(func=lambda m: m.chat.id == SOURCE_CHAT_ID and m.forward_date, content_types=['photo', 'video'])
def handle_forwarded(m):
    if m.media_group_id:
        gid = m.media_group_id
        media_groups[gid].append(m)
        if gid in media_group_timers:
            media_group_timers[gid].cancel()
        import threading
        t = threading.Timer(1, delayed_process_media_group, args=(gid,))
        media_group_timers[gid] = t
        t.start()
    else:
        if m.photo:
            fid = m.photo[-1].file_id
            bot.send_photo(SOURCE_CHAT_ID, fid)
            text = recognize_text_from_photo(fid)
            bot.send_photo(TARGET_CHANNEL_ID, fid, caption=text if text else None)
        elif m.video:
            bot.send_video(SOURCE_CHAT_ID, m.video.file_id, supports_streaming=True)
        bot.delete_message(m.chat.id, m.message_id)

# Direct photo (no forward)
@bot.message_handler(func=lambda m: m.chat.id == SOURCE_CHAT_ID, content_types=['photo'])
def handle_photo(m):
    fid = m.photo[-1].file_id
    text = recognize_text_from_photo(fid)
    bot.send_photo(TARGET_CHANNEL_ID, fid, caption=text if text else None)

bot.polling(none_stop=True)
