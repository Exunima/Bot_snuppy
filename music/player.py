import os
import discord
from discord.ext import commands
from collections import deque
from config import FFMPEG_PATH
from .downloader import download_and_queue_track, get_track_ids_from_playlist
from .utils import delete_file, get_track_ids
import re

queue = deque()
vc = None


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
        global vc
        if queue:
            current = queue.popleft()
            try:
                vc.play(discord.FFmpegPCMAudio(current, executable=FFMPEG_PATH),
                        after=lambda e: ctx.bot.loop.create_task(track_finished(ctx, current)))
                await ctx.send(f"Сейчас играет: {os.path.basename(current)}")
            except Exception as e:
                await ctx.send(f"Ошибка воспроизведения: {e}")
                await delete_file(current)
                await play_next_track(ctx)

    async def track_finished(ctx, path):
        await delete_file(path)
        await play_next_track(ctx)

    @bot.command(name='pause')
    async def pause(ctx):
        if vc and vc.is_playing():
            vc.pause()
            await ctx.send("Пауза.")

    @bot.command(name='resume')
    async def resume(ctx):
        if vc and vc.is_paused():
            vc.resume()
            await ctx.send("Продолжение.")

    @bot.command(name='stop')
    async def stop(ctx):
        global vc
        if vc:
            vc.stop()
            await vc.disconnect()
            vc = None
            while queue:
                await delete_file(queue.popleft())
            await ctx.send("Остановлено.")

    @bot.command(name='skip')
    async def skip(ctx):
        if vc and vc.is_playing():
            vc.stop()
            await ctx.send("Следующий трек...")

    @bot.command(name='queue')
    async def show_queue(ctx):
        if queue:
            q = "\n".join([os.path.basename(p) for p in queue])
            await ctx.send(f"Очередь:\n{q}")
        else:
            await ctx.send("Очередь пуста.")
