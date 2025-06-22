import os
import discord
from collections import deque
from config import FFMPEG_PATH
from .downloader import download_and_queue_track
from .utils import delete_file, get_track_ids
import re
from discord import VoiceClient
from typing import Optional

vc: Optional[VoiceClient] = None
queue = deque()
is_playing = False


def setup(bot):
    @bot.command(name='play')
    async def play(ctx, *, url: str = None):
        global vc
        if url is None:
            await ctx.send("Пример: !play <ссылка>")
            return

        # Подключение к голосовому каналу
        voice_channel = ctx.author.voice.channel
        if vc is None or not vc.is_connected():
            vc = await voice_channel.connect()
        elif vc.channel != voice_channel:
            await vc.move_to(voice_channel)

        try:
            # Пытаемся получить список треков из плейлиста/альбома
            track_ids = get_track_ids(url)
            for tid in track_ids:
                await download_and_queue_track(tid, queue)
            await ctx.send(f"Добавлено {len(track_ids)} треков.")

        except ValueError:
            # Если не плейлист/альбом, проверим, трек ли это
            match = re.search(r'track/(\d+)', url)
            if match:
                tid = match.group(1)
                path = await download_and_queue_track(tid, queue)
                await ctx.send(f"Добавлен: {os.path.basename(path)}")
            else:
                await ctx.send("Неверная ссылка. Ожидалась ссылка на трек, альбом или плейлист.")
        except Exception as e:
            await ctx.send(f"Ошибка при добавлении треков: {e}")

        if not vc.is_playing() and queue:
            await play_next_track(ctx)

    async def play_next_track(ctx):
        global vc, is_playing

        if is_playing:
            return  # Уже играет — повторный вызов не нужен

        if not queue:
            is_playing = False
            return

        if vc is None or not vc.is_connected():
            await ctx.send("Ошибка: Бот не подключён к голосовому каналу.")
            is_playing = False
            return

        current = queue.popleft()

        if not os.path.exists(current):
            await ctx.send(f"Файл не найден: {os.path.basename(current)}. Пропускаю.")
            await play_next_track(ctx)
            return

        try:
            is_playing = True
            vc.play(
                discord.FFmpegPCMAudio(current, executable=FFMPEG_PATH),
                after=lambda err: ctx.bot.loop.create_task(track_finished(ctx, current))
            )
            await ctx.send(f"Сейчас играет: {os.path.basename(current)}")
        except Exception as e:
            await ctx.send(f"Ошибка воспроизведения: {e}")
            await delete_file(current)
            is_playing = False
            await play_next_track(ctx)

    async def track_finished(ctx, path):
        global is_playing
        await delete_file(path)
        is_playing = False
        await play_next_track(ctx)

    @bot.command(name='pause')
    async def pause(ctx):
        global vc
        if vc is not None and vc.is_connected():
            if vc.is_playing():
                vc.pause()
                await ctx.send("⏸️ Воспроизведение на паузе.")
            else:
                await ctx.send("🎵 Сейчас ничего не воспроизводится.")
        else:
            await ctx.send("⚠️ Бот не подключён к голосовому каналу.")

    @bot.command(name='resume')
    async def resume(ctx):
        global vc
        if vc is not None and vc.is_connected():
            if vc.is_paused():
                vc.resume()
                await ctx.send("▶️ Продолжено воспроизведение.")
            else:
                await ctx.send("⚠️ Ничего не стоит на паузе.")
        else:
            await ctx.send("⚠️ Бот не подключён к голосовому каналу.")

    @bot.command(name='stop')
    async def stop(ctx):
        global vc, queue, is_playing

        if vc is not None and vc.is_connected():
            if vc.is_playing():
                vc.stop()
            await vc.disconnect()
            vc = None

        # Очистка очереди
        queue.clear()
        is_playing = False

        # Удаление всех mp3-файлов в папке tracks
        deleted = 0
        if os.path.exists("tracks"):
            for filename in os.listdir("tracks"):
                if filename.endswith(".mp3"):
                    filepath = os.path.join("tracks", filename)
                    try:
                        os.remove(filepath)
                        deleted += 1
                    except Exception as e:
                        print(f"[ERROR] Не удалось удалить {filepath}: {e}")

        await ctx.send(f"Остановлено. Удалено {deleted} треков.")

    @bot.command(name='skip')
    async def skip(ctx):
        global vc
        if vc is not None and vc.is_connected():
            if vc.is_playing() or vc.is_paused():
                vc.stop()
                await ctx.send("⏭️ Пропущено. Воспроизводим следующий трек...")
            else:
                await ctx.send("⚠️ Сейчас ничего не воспроизводится.")
        else:
            await ctx.send("⚠️ Бот не подключён к голосовому каналу.")

    @bot.command(name='queue')
    async def show_queue(ctx):
        if queue:
            q_list = list(queue)
            display_count = min(len(q_list), 10)
            display = "\n".join([f"{i + 1}. {os.path.basename(p)}" for i, p in enumerate(q_list[:display_count])])
            more = f"\n...и ещё {len(q_list) - display_count} треков." if len(q_list) > display_count else ""
            await ctx.send(f"📃 Очередь треков:\n{display}{more}")
        else:
            await ctx.send("📭 Очередь пуста.")
