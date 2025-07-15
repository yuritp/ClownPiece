import yt_dlp
import os
from config import Config


def download_video(url: str) -> str | None:
    """
    Descarga un vídeo desde una URL usando yt-dlp y lo guarda localmente.
    Devuelve la ruta del archivo o None si falla.
    """
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