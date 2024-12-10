import discord
import asyncio
import os
import re
import aiohttp
from discord.ext import commands
from yandex_music import Client
import logging
from collections import deque
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord_bot')

# Загрузка переменных из .env
load_dotenv()

# Токены и путь к ffmpeg
YANDEX_MUSIC_TOKEN = os.getenv('YANDEX_MUSIC_TOKEN')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
ffmpeg_path = os.getenv('FFMPEG_PATH')


# Авторизация в Яндекс Музыке
client = Client(YANDEX_MUSIC_TOKEN).init()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Очередь треков и папка для треков
queue = deque()
vc = None
track_folder = "tracks"

# Создаем папку для треков, если её не существует
os.makedirs(track_folder, exist_ok=True)


async def download_track(url, path):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                with open(path, 'wb') as f:
                    while True:
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break
                        f.write(chunk)
    except aiohttp.ClientError as e:
        logger.error(f'Ошибка при скачивании трека: {e}')
        raise


async def download_and_queue_track(track_id):
    track = client.tracks([track_id])[0]
    download_info = track.get_download_info(get_direct_links=True)
    if not download_info:
        raise Exception("Не удалось получить ссылку для скачивания трека.")
    download_url = download_info[0].direct_link
    track_title = f"{track.title}.mp3"
    track_path = os.path.join(track_folder, track_title)
    await download_track(download_url, track_path)
    queue.append(track_path)
    return track_path


async def play_next_track(ctx):
    """Функция для воспроизведения следующего трека."""
    global queue, vc

    if vc is None or not vc.is_connected():
        await ctx.send("Бот не подключен к голосовому каналу.")
        return

    if queue:
        if vc.is_playing() or vc.is_paused():
            # Если трек еще играет или на паузе, ждем завершения
            return

        current_track_path = queue.popleft()
        vc.play(discord.FFmpegPCMAudio(current_track_path, executable=ffmpeg_path),
                after=lambda e: bot.loop.create_task(track_finished(ctx, current_track_path)))
        await ctx.send(f"Теперь воспроизводится: {os.path.basename(current_track_path)}")
    else:
        await ctx.send("Очередь пуста.")


async def track_finished(ctx, track_path):
    """Вызывается после завершения трека."""
    await delete_file(track_path)
    await play_next_track(ctx)


async def delete_file(path):
    """Удаление файла из файловой системы."""
    await asyncio.sleep(2)  # Увеличенная задержка, чтобы дать время ffmpeg завершить работу
    try:
        os.remove(path)
        print(f"Файл успешно удален: {path}")
    except Exception as e:
        print(f"Ошибка при удалении файла {path}: {e}")


@bot.command(name='play')
async def play(ctx, *, url: str = None):
    """Начать воспроизведение трека по URL."""
    if url is None:
        await ctx.send("Вы должны передать URL трека. Пример использования: !play <URL>")
        return
    voice_channel = ctx.author.voice.channel
    global vc
    if vc is None or not vc.is_connected():
        vc = await voice_channel.connect()
    elif vc.channel != voice_channel:
        await vc.move_to(voice_channel)

    try:
        track_id_match = re.search(r'track/(\d+)', url)
        if not track_id_match:
            await ctx.send("Неверный формат URL. Убедитесь, что URL ведет на трек Яндекс Музыки.")
            return

        track_id = track_id_match.group(1)
        track_path = await download_and_queue_track(track_id)

        # Если ничего не воспроизводится, начинаем воспроизведение
        if not vc.is_playing():
            await play_next_track(ctx)
        else:
            await ctx.send(f"Трек добавлен в очередь: {os.path.basename(track_path)}")

    except Exception as e:
        logger.error(f'Ошибка при воспроизведении музыки: {e}')
        await ctx.send(f'Произошла ошибка: {str(e)}')


@bot.command(name='pause')
async def pause(ctx):
    """Приостановить воспроизведение."""
    global vc
    if vc and vc.is_playing():
        vc.pause()
        await ctx.send("Воспроизведение приостановлено.")
    else:
        await ctx.send("В данный момент ничего не воспроизводится.")


@bot.command(name='resume')
async def resume(ctx):
    """Возобновить воспроизведение."""
    global vc
    if vc and vc.is_paused():
        vc.resume()
        await ctx.send("Воспроизведение возобновлено.")
    else:
        await ctx.send("В данный момент ничего не приостановлено.")


@bot.command(name='stop')
async def stop(ctx):
    """Остановка бота, очистка очереди и удаление треков."""
    global vc, queue
    if vc:
        vc.stop()
        await vc.disconnect()
        vc = None
        # Очистка очереди и удаление треков
        for track_path in list(queue):
            await delete_file(track_path)
        queue.clear()
        # Очистка папки "tracks"
        for track_file in os.listdir(track_folder):
            track_path = os.path.join(track_folder, track_file)
            await delete_file(track_path)
        await ctx.send("Воспроизведение остановлено, треки удалены, бот отключен от голосового канала.")
    else:
        await ctx.send("Бот не подключен к голосовому каналу.")


@bot.command(name='skip')
async def skip(ctx):
    """Пропустить текущий трек и воспроизвести следующий."""
    global queue, vc

    if vc and vc.is_playing():
        vc.stop()  # Останавливаем текущий трек

        # Переходим к следующему треку
        await asyncio.sleep(1)  # Даем время завершиться текущему треку
        await play_next_track(ctx)
    else:
        await ctx.send("В данный момент ничего не воспроизводится.")


@bot.command(name='queue')
async def show_queue(ctx):
    """Показать очередь треков."""
    if queue:
        queue_list = "\n".join([os.path.basename(track) for track in queue])
        await ctx.send(f"Очередь треков:\n{queue_list}")
    else:
        await ctx.send("Очередь треков пуста.")


@bot.event
async def on_ready():
    """Когда бот готов."""
    print(f'Logged in as {bot.user.name}')

bot.run(DISCORD_BOT_TOKEN)
