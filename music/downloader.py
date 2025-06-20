import aiohttp
import os
import re
from yandex_music import Client
from config import YANDEX_MUSIC_TOKEN

client = Client(YANDEX_MUSIC_TOKEN).init()
track_folder = "tracks"
os.makedirs(track_folder, exist_ok=True)


async def download_track(url, path):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            with open(path, 'wb') as f:
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    f.write(chunk)


async def download_and_queue_track(track_id, queue):
    track = client.tracks([track_id])[0]
    download_info = track.get_download_info(get_direct_links=True)
    download_url = download_info[0].direct_link
    track_title = f"{track.title}.mp3"
    path = os.path.join(track_folder, track_title)
    await download_track(download_url, path)
    queue.append(path)
    return path


def get_track_ids_from_playlist(url):
    match = re.search(r'users/([^/]+)/playlists/(\d+)', url)
    if not match:
        raise Exception("Неверный URL плейлиста.")
    user, playlist_id = match.groups()
    playlist = client.users_playlists(user_id=user, kind=int(playlist_id))
    return [t.track.track_id for t in playlist.tracks if t.track]
