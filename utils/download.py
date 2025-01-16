import yt_dlp, re

from pathlib import Path

def extract_youtube_id(url):
    # 정규식 패턴
    pattern = (
        r"(?:https?://)?(?:www\.)?"
        r"(?:youtube\.com/(?:watch\?v=|embed/|v/|shorts/)|youtu\.be/)"
        r"([a-zA-Z0-9_-]{11})"
    )
    match = re.search(pattern, url)
    if match:
        return match.group(1)  # 매칭된 영상 ID 반환
    return None  # 매칭되지 않으면 None 반환

def download_audio_from_youtube(youtube_url:str, youtube_download_path:Path, save_subtitles:list=None, fmt:str="mp3"):        
    youtube_id = extract_youtube_id(youtube_url)

    predicted_file_path = youtube_download_path / f"{youtube_id}.{fmt}"
    if predicted_file_path.exists():
        print(f"youtube:{youtube_url} is aleardy downloaded.\ndownload path:{predicted_file_path}")
        return predicted_file_path

    ydl_opts = {
        "outtmpl": str(youtube_download_path / "%(id)s.%(ext)s"),
        "format": "bestaudio/best", 
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": fmt}],
        "quiet": False
        }
    if save_subtitles:
        ydl_opts["writesub"] = True
        ydl_opts["subtitleslangs"] = save_subtitles
        ydl_opts["subtitlesformat"] = "vtt"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            print(f"Attempting to download: {youtube_url}")
            ydl.download([youtube_url])
            predicted_file_path = youtube_download_path / f"{youtube_id}.{fmt}"
        except yt_dlp.utils.DownloadError as e:
            print(f"Error downloading {youtube_url}: {e}")
            predicted_file_path = None

    return predicted_file_path