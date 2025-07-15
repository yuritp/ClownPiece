import yt_dlp
import os
from config import Config


def search_youtube(query: str) -> dict | None:
    """
    Busca un vídeo en YouTube y devuelve su información (título, URL, etc.) sin descargarlo.
    """
    YDL_OPTIONS = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'default_search': 'ytsearch',
        'quiet': True,
    }
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(query, download=False)
            # Si es una búsqueda, toma el primer resultado
            if 'entries' in info:
                video = info['entries'][0]
            else:
                video = info

            return {
                'title': video.get('title', 'Título desconocido'),
                'stream_url': video.get('url'),
                'uploader': video.get('uploader', 'Artista desconocido'),
                'duration': video.get('duration', 0)
            }
    except Exception as e:
        print(f"Error buscando en YouTube: {e}")
        return None


def download_video(url: str) -> str | None:
    """
    Descarga un vídeo desde una URL y lo guarda localmente.
    """
    # ... (esta función se mantiene igual que antes)
    os.makedirs(Config.DOWNLOADS_PATH, exist_ok=True)
    ydl_opts = {
        'outtmpl': os.path.join(Config.DOWNLOADS_PATH, '%(id)s.%(ext)s'),
        'format': 'best[ext=mp4][height<=1080]/best[ext=mp4]/best',
        'noplaylist': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except yt_dlp.utils.DownloadError:
        print(f"yt-dlp no pudo encontrar un vídeo en la URL: {url}")
        return None