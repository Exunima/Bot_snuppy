import os
import re
from yandex_music import Client
from config import YANDEX_MUSIC_TOKEN


async def delete_file(path):
    try:
        if os.path.exists(path):
            os.remove(path)
        else:
            print(f"[INFO] Файл уже удалён или не существует: {path}")
    except Exception as e:
        print(f"[ERROR] Не удалось удалить файл {path}: {e}")


def get_track_ids(url):
    try:
        client = Client(YANDEX_MUSIC_TOKEN).init()
    except Exception as e:
        raise ValueError(f"Ошибка инициализации Yandex Music клиента: {e}")

    # Если ссылка содержит конкретный трек
    track_match = re.search(r'/track/(\d+)', url)
    if track_match:
        return [track_match.group(1)]

    # Если плейлист
    playlist_match = re.search(r'/users/([^/]+)/playlists/(\d+)', url)
    if playlist_match:
        user, playlist_id = playlist_match.groups()
        try:
            playlist = client.users_playlists(int(playlist_id), user)
            track_ids = [str(track.track.track_id) for track in playlist.tracks if track.track]
            if not track_ids:
                raise ValueError("Плейлист пуст или содержит неподдерживаемые треки.")
            return track_ids
        except Exception as e:
            raise ValueError(f"Ошибка при загрузке плейлиста: {e}")

    # Если альбом
    album_match = re.search(r'/album/(\d+)', url)
    if album_match:
        album_id = album_match.group(1)
        try:
            album = client.albums_with_tracks(album_id)
            track_ids = [str(track.id) for volume in album.volumes for track in volume if track]
            if not track_ids:
                raise ValueError("Альбом пуст или содержит ошибки.")
            return track_ids
        except Exception as e:
            raise ValueError(f"Ошибка при загрузке альбома: {e}")

    raise ValueError("Неверная ссылка: поддерживаются только треки, альбомы и плейлисты.")
