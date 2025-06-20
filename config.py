import os
from dotenv import load_dotenv

load_dotenv()

YANDEX_MUSIC_TOKEN = os.getenv('YANDEX_MUSIC_TOKEN')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
FFMPEG_PATH = os.getenv('FFMPEG_PATH')
