import yt_dlp
import os
import imageio_ffmpeg              # pip install imageio-ffmpeg
from typing import Optional
# путь к встроенному ffmpeg
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

from typing import Optional

import logging
# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def download_video(url: str, output_dir: str = "./downloads") -> Optional[str]:
    os.makedirs(output_dir, exist_ok=True)

    # 720p обычно влезает в 50 МБ для роликов до 5–7 мин
    ydl_opts = {
        'format': 'best[height<=720]',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'ffmpeg_location': FFMPEG_PATH,
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            logger.info(f"✅ Видео сохранено: {path}")
            return path
    except Exception as e:
        logger.error(f"❌ Ошибка при скачивании: {e}")
        return None
    
    
if __name__ == "__main__":
    url = 'https://www.youtube.com/shorts/8tFHstWpQNc?si=aZWIMheN5X5xMQGf'    
    download_video(url)