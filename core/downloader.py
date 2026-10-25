import os
import re
import uuid
import time
from pathlib import Path
from typing import Dict, Any, Optional
from PyQt6.QtCore import QThread, pyqtSignal
import yt_dlp
from core.ffmpeg_checker import get_ffmpeg_dir

class DownloadCancelledException(Exception):
    pass

class DownloadTask(QThread):
    progress_signal = pyqtSignal(str, dict)       # task_id, progress_dict
    finished_signal = pyqtSignal(str, str)        # task_id, final_filepath
    error_signal = pyqtSignal(str, str)           # task_id, error_message

    def __init__(self, task_id: str, options: dict):
        """
        options:
          - url: str
          - title: str
          - thumbnail: str
          - mode: 'video' or 'audio'
          - format: 'mp4', 'mkv', 'mp3', 'm4a', etc.
          - quality_format_id: str (for video, e.g. '137' or 'bestvideo')
          - audio_abr: int (for audio, e.g. 320)
          - download_path: str
          - speed_limit_kb: int (0 for unlimited)
          - cookies_browser: str ('none', 'chrome', etc.)
          - embed_thumbnail: bool
          - embed_metadata: bool
          - download_subtitles: bool
          - subtitles_lang: str
          - embed_subtitles: bool
        """
        super().__init__()
        self.task_id = task_id
        self.opts = options
        self._is_cancelled = False
        self._final_filepath = ""

    def cancel(self):
        self._is_cancelled = True

    def _progress_hook(self, d: dict):
        if self._is_cancelled:
            raise DownloadCancelledException("Download was cancelled by user.")

        status = d.get('status')
        if status == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            
            percent = 0.0
            if total and total > 0:
                percent = (downloaded / total) * 100.0
            elif d.get('_percent_str'):
                try:
                    clean_pct = re.sub(r'[^\d.]', '', d['_percent_str'])
                    percent = float(clean_pct)
                except Exception:
                    pass

            speed_str = d.get('_speed_str', '').strip() or "0 B/s"
            eta_str = d.get('_eta_str', '').strip() or "--:--"
            
            # Clean ANSI color codes from strings if present
            speed_str = re.sub(r'\x1b\[[0-9;]*m', '', speed_str)
            eta_str = re.sub(r'\x1b\[[0-9;]*m', '', eta_str)

            self.progress_signal.emit(self.task_id, {
                "status": "downloading",
                "percent": percent,
                "speed": speed_str,
                "eta": eta_str,
                "downloaded_bytes": downloaded,
                "total_bytes": total,
                "status_text": f"Downloading... {percent:.1f}% ({speed_str})"
            })

        elif status == 'finished':
            self._final_filepath = d.get('filename', '')
            self.progress_signal.emit(self.task_id, {
                "status": "processing",
                "percent": 100.0,
                "speed": "",
                "eta": "00:00",
                "status_text": "Processing & merging media streams..."
            })

    def _postprocessor_hook(self, d: dict):
        if self._is_cancelled:
            raise DownloadCancelledException("Download cancelled.")
        status = d.get('status')
        pp_name = d.get('postprocessor', '')
        if status == 'started':
            msg = "Processing with FFmpeg..."
            if 'ExtractAudio' in pp_name:
                msg = "Converting audio stream..."
            elif 'EmbedThumbnail' in pp_name:
                msg = "Embedding cover art..."
            elif 'FFmpegMetadata' in pp_name:
                msg = "Embedding tags and chapters..."
            elif 'EmbedSubtitle' in pp_name:
                msg = "Embedding subtitles..."
            self.progress_signal.emit(self.task_id, {
                "status": "processing",
                "percent": 100.0,
                "speed": "",
                "eta": "",
                "status_text": msg
            })
        elif status == 'finished':
            # Updated filename might be here
            if 'info_dict' in d and '_filename' in d['info_dict']:
                self._final_filepath = d['info_dict']['_filename']

    def run(self):
        try:
            url = self.opts.get("url")
            mode = self.opts.get("mode", "video")
            container_format = self.opts.get("format", "mp4").lower()
            download_dir = self.opts.get("download_path", str(Path.home() / "Videos" / "gjats"))
            speed_limit = self.opts.get("speed_limit_kb", 0)
            cookies_browser = self.opts.get("cookies_browser", "none")
            
            Path(download_dir).mkdir(parents=True, exist_ok=True)
            
            # Clean filename: no ugly video ID [ql-wvCkTARM] at the end
            include_id = self.opts.get("include_video_id", False)
            title_prefix = self.opts.get("title_prefix", "")
            if include_id:
                name_pattern = f"{title_prefix}%(title)s [%(id)s].%(ext)s"
            else:
                name_pattern = f"{title_prefix}%(title)s.%(ext)s"

            outtmpl = os.path.join(download_dir, name_pattern)

            from core.js_checker import setup_js_runtime
            setup_js_runtime()
            from core.ffmpeg_checker import get_ffmpeg_dir, setup_ffmpeg_runtime
            setup_ffmpeg_runtime()

            ydl_opts = {
                'outtmpl': outtmpl,
                'progress_hooks': [self._progress_hook],
                'postprocessor_hooks': [self._postprocessor_hook],
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': False,
                'windowsfilenames': True,
                'restrictfilenames': False,
                'source_address': '0.0.0.0',   # Force IPv4
                'socket_timeout': 20,
                'retries': 10,
                'fragment_retries': 10,
                'extractor_retries': 5,
                'file_access_retries': 5,
                'remote_components': ['ejs:github'],
            }

            ffmpeg_dir = get_ffmpeg_dir()
            if ffmpeg_dir:
                ydl_opts['ffmpeg_location'] = ffmpeg_dir

            if speed_limit and speed_limit > 0:
                ydl_opts['ratelimit'] = speed_limit * 1024

            if cookies_browser and cookies_browser != "none":
                ydl_opts['cookiesfrombrowser'] = (cookies_browser,)

            postprocessors = []

            if mode == "video":
                fmt_id = self.opts.get("quality_format_id")
                if fmt_id and fmt_id != "best":
                    # Video stream + best audio stream with resilient fallbacks for single-stream sites (TikTok/X/Insta)
                    ydl_opts['format'] = f"{fmt_id}+bestaudio/{fmt_id}/bestvideo+bestaudio/best"
                else:
                    ydl_opts['format'] = "bestvideo+bestaudio/best"

                ydl_opts['merge_output_format'] = container_format

                # Subtitles
                if self.opts.get("download_subtitles"):
                    lang = self.opts.get("subtitles_lang", "en")
                    ydl_opts['writesubtitles'] = True
                    ydl_opts['writeautomaticsub'] = True
                    ydl_opts['subtitleslangs'] = [lang]
                    if self.opts.get("embed_subtitles"):
                        postprocessors.append({'key': 'FFmpegEmbedSubtitle'})

            elif mode == "audio":
                ydl_opts['format'] = "bestaudio/best"
                abr = self.opts.get("audio_abr", 320)
                codec = container_format if container_format in ['mp3', 'm4a', 'flac', 'wav', 'opus', 'aac'] else 'mp3'
                postprocessors.append({
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': codec,
                    'preferredquality': str(abr),
                })

            # Embed metadata
            if self.opts.get("embed_metadata", True):
                postprocessors.append({'key': 'FFmpegMetadata', 'add_chapters': True})

            # Embed thumbnail
            if self.opts.get("embed_thumbnail", True):
                ydl_opts['writethumbnail'] = True
                postprocessors.append({'key': 'EmbedThumbnail', 'already_have_thumbnail': False})

            if postprocessors:
                ydl_opts['postprocessors'] = postprocessors

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                final_path = ydl.prepare_filename(info)
                
                # Check for container format changes after postprocessing
                if mode == "audio":
                    codec = container_format if container_format in ['mp3', 'm4a', 'flac', 'wav', 'opus', 'aac'] else 'mp3'
                    base = os.path.splitext(final_path)[0]
                    target = f"{base}.{codec}"
                    if os.path.exists(target):
                        final_path = target
                elif mode == "video" and container_format:
                    base = os.path.splitext(final_path)[0]
                    target = f"{base}.{container_format}"
                    if os.path.exists(target):
                        final_path = target

                self._final_filepath = final_path

                # Save standalone thumbnail file alongside media if requested
                if self.opts.get("save_thumbnail_file"):
                    thumb_url = self.opts.get("thumbnail")
                    if thumb_url and self._final_filepath:
                        try:
                            base = os.path.splitext(self._final_filepath)[0]
                            thumb_dest = f"{base}.jpg"
                            import urllib.request
                            from PIL import Image
                            import io
                            req = urllib.request.Request(thumb_url, headers={'User-Agent': 'Mozilla/5.0'})
                            with urllib.request.urlopen(req, timeout=10) as resp:
                                tdata = resp.read()
                                img = Image.open(io.BytesIO(tdata))
                                img.convert('RGB').save(thumb_dest, "JPEG", quality=95)
                        except Exception as e:
                            print(f"Could not save standalone thumbnail: {e}")

            if not self._is_cancelled:
                self.finished_signal.emit(self.task_id, self._final_filepath)

        except DownloadCancelledException:
            self.error_signal.emit(self.task_id, "Cancelled")
        except Exception as e:
            err = str(e)
            try:
                log_path = Path.home() / ".gjat_downloader" / "app.log"
                with open(log_path, "a", encoding="utf-8") as lf:
                    import datetime
                    lf.write(f"[{datetime.datetime.now()}] Download Error: {err}\n")
            except Exception:
                pass

            if self._is_cancelled:
                self.error_signal.emit(self.task_id, "Cancelled")
            else:
                if "getaddrinfo" in err or "Failed to resolve" in err or "TransportError" in err:
                    err = "Network error: Connection to media server lost or DNS failed."
                elif "HTTP Error 403" in err:
                    err = "Access forbidden (403). Try setting browser cookies in Settings."
                elif "ffmpeg" in err.lower() or "ffprobe" in err.lower():
                    err = "FFmpeg error: Post-processing failed. Make sure FFmpeg is installed or re-run setup."
                self.error_signal.emit(self.task_id, err)
