import re
from typing import Dict, Any, List, Optional
from PyQt6.QtCore import QThread, pyqtSignal
import yt_dlp

def format_duration(seconds: Optional[int]) -> str:
    if not seconds:
        return "Unknown"
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def format_bytes(bytes_count: Optional[float]) -> str:
    if not bytes_count or bytes_count <= 0:
        return "Unknown"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} PB"

class LinkExtractorWorker(QThread):
    finished_success = pyqtSignal(dict)
    finished_error = pyqtSignal(str)
    status_update = pyqtSignal(str)

    def __init__(self, url: str, cookies_browser: str = "none"):
        super().__init__()
        self.url = url.strip()
        self.cookies_browser = cookies_browser

    def run(self):
        try:
            from core.js_checker import setup_js_runtime
            setup_js_runtime()

            self.status_update.emit("Connecting to server...")
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'extract_flat': 'in_playlist',  # fast playlist inspection
                'source_address': '0.0.0.0',     # Force IPv4 to prevent Windows getaddrinfo [Errno 11001]
                'socket_timeout': 15,
                'retries': 5,
                'extractor_retries': 3,
                'remote_components': ['ejs:github'],
            }
            if self.cookies_browser and self.cookies_browser != "none":
                ydl_opts['cookiesfrombrowser'] = (self.cookies_browser,)

            # Normalize YouTube channel URLs to /videos tab if no sub-tab is specified
            target_url = self.url
            if re.search(r'youtube\.com/(@[\w.-]+|channel/[\w.-]+|c/[\w.-]+|user/[\w.-]+)/?$', target_url):
                target_url = target_url.rstrip('/') + '/videos'

            self.status_update.emit("Fetching media details...")
            info = None
            last_err = None
            for attempt in range(1, 4):
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(target_url, download=False)
                        if info:
                            break
                except Exception as ex:
                    last_err = ex
                    err_s = str(ex).lower()
                    if ("getaddrinfo" in err_s or "connection" in err_s or "timed out" in err_s or "transporterror" in err_s) and attempt < 3:
                        self.status_update.emit(f"Connection retry {attempt}/3...")
                        import time
                        time.sleep(1.0)
                        continue
                    raise ex

            if not info:
                if last_err:
                    raise last_err
                self.finished_error.emit("Could not retrieve information for this URL.")
                return

            # Check if this is a playlist or channel
            is_playlist = info.get('_type') == 'playlist' or 'entries' in info
            if is_playlist:
                raw_entries = list(info.get('entries', []))
                playlist_items = []
                for idx, entry in enumerate(raw_entries):
                    if not entry:
                        continue
                    playlist_items.append({
                        "index": idx + 1,
                        "id": entry.get("id"),
                        "url": entry.get("url") or entry.get("webpage_url") or f"https://www.youtube.com/watch?v={entry.get('id')}",
                        "title": entry.get("title", f"Video {idx + 1}"),
                        "duration": format_duration(entry.get("duration")),
                        "duration_secs": entry.get("duration", 0),
                        "uploader": entry.get("uploader") or entry.get("channel", "Unknown"),
                        "thumbnail": entry.get("thumbnail") or (entry.get("thumbnails")[-1]["url"] if entry.get("thumbnails") else "")
                    })

                is_channel = bool(
                    '/@' in self.url or
                    '/channel/' in self.url or
                    '/c/' in self.url or
                    '/user/' in self.url or
                    'Videos' in (info.get('title') or '') or
                    'channel' in str(info.get('_type', '')).lower() or
                    info.get('channel_id')
                )

                channel_title = info.get("channel") or info.get("uploader") or info.get("title", "Channel Uploads")
                clean_title = re.sub(r'\s*-\s*Videos$', '', channel_title).strip()

                result = {
                    "is_playlist": True,
                    "is_channel": is_channel,
                    "playlist_title": clean_title,
                    "channel_name": clean_title,
                    "playlist_count": len(playlist_items),
                    "playlist_items": playlist_items,
                    "url": self.url,
                    "thumbnail": playlist_items[0]["thumbnail"] if playlist_items else ""
                }
                self.finished_success.emit(result)
                return

            # Single video extraction: parse video and audio streams
            self.status_update.emit("Analyzing available streams and formats...")
            formats = info.get('formats', [])
            duration = info.get('duration', 0)

            # Best audio stream for calculating total combined size
            audio_formats = [f for f in formats if f.get('vcodec') == 'none' and f.get('acodec') != 'none']
            best_audio = max(audio_formats, key=lambda f: f.get('abr') or 0) if audio_formats else None
            audio_size = 0
            if best_audio:
                audio_size = best_audio.get('filesize') or best_audio.get('filesize_approx') or 0
                if not audio_size and best_audio.get('abr') and duration:
                    audio_size = int((best_audio['abr'] * 1000 / 8) * duration)

            # Parse video streams
            video_streams = [f for f in formats if f.get('vcodec') != 'none']
            if not video_streams:
                video_streams = [f for f in formats if f.get('ext') in ('mp4', 'mkv', 'webm') or f.get('acodec') != 'none']

            res_map = {}
            for f in video_streams:
                h = f.get('height')
                if not h and f.get('resolution'):
                    try:
                        h = int(f['resolution'].split('x')[-1])
                    except Exception:
                        h = 720
                if not h:
                    h = 720

                fps = f.get('fps') or 30
                ext = f.get('ext') or 'mp4'
                key = h
                v_size = f.get('filesize') or f.get('filesize_approx') or 0
                if not v_size and f.get('tbr') and duration:
                    v_size = int((f['tbr'] * 1000 / 8) * duration)

                est_total = (v_size + audio_size) if v_size else 0
                tbr = f.get('tbr') or 0

                if key not in res_map or tbr > (res_map[key].get('tbr') or 0):
                    res_map[key] = {
                        "height": h,
                        "fps": int(fps) if fps else 30,
                        "format_id": f.get("format_id") or "best",
                        "ext": ext,
                        "vcodec": f.get("vcodec", "unknown"),
                        "size_bytes": est_total,
                        "size_str": format_bytes(est_total),
                        "tbr": tbr
                    }

            video_options = []
            for h in sorted(res_map.keys(), reverse=True):
                v = res_map[h]
                label = f"{h}p"
                if v['fps'] >= 50:
                    label += f"{v['fps']}"
                if h >= 2160:
                    label += " 4K Ultra HD"
                elif h >= 1440:
                    label += " 2K Quad HD"
                elif h >= 1080:
                    label += " Full HD"
                elif h >= 720:
                    label += " HD"

                v["label"] = label
                video_options.append(v)

            if not video_options:
                video_options.append({
                    "height": 720,
                    "fps": 30,
                    "format_id": "best",
                    "ext": "mp4",
                    "vcodec": "h264",
                    "size_bytes": audio_size or 0,
                    "size_str": format_bytes(audio_size) if audio_size else "Auto",
                    "tbr": 0,
                    "label": "Original Quality (Best)"
                })

            # Parse audio options
            audio_options = [
                {"label": "Original Quality (Best)", "abr": 320, "format": "bestaudio/best", "size_str": format_bytes(audio_size)},
                {"label": "High Quality (256 kbps)", "abr": 256, "format": "bestaudio/best", "size_str": format_bytes(int(audio_size * 0.8) if audio_size else 0)},
                {"label": "Standard Quality (192 kbps)", "abr": 192, "format": "bestaudio/best", "size_str": format_bytes(int(audio_size * 0.6) if audio_size else 0)},
                {"label": "Normal Quality (128 kbps)", "abr": 128, "format": "bestaudio/best", "size_str": format_bytes(int(audio_size * 0.4) if audio_size else 0)},
            ]

            # Parse subtitles
            subtitles_list = ["None"]
            subs = info.get('subtitles', {})
            auto_subs = info.get('automatic_captions', {})
            all_subs = set(list(subs.keys()) + list(auto_subs.keys()))
            for lang in sorted(all_subs):
                subtitles_list.append(lang)

            thumbnail = info.get('thumbnail')
            if not thumbnail and info.get('thumbnails'):
                thumbnail = info['thumbnails'][-1].get('url')

            result = {
                "is_playlist": False,
                "title": info.get("title", "Unknown Title"),
                "uploader": info.get("uploader") or info.get("channel", "Unknown Channel"),
                "duration_str": format_duration(duration),
                "duration_secs": duration,
                "thumbnail": thumbnail,
                "video_options": video_options,
                "audio_options": audio_options,
                "subtitles": subtitles_list,
                "url": self.url,
                "webpage_url": info.get("webpage_url", self.url)
            }

            self.finished_success.emit(result)

        except Exception as e:
            err_msg = str(e)
            # Make common error messages clean and user-friendly
            if "getaddrinfo" in err_msg or "Failed to resolve" in err_msg or "TransportError" in err_msg:
                err_msg = "Internet connection / DNS error: Unable to connect to YouTube.\nPlease check your network connection and try again."
            elif "Private video" in err_msg:
                err_msg = "This video is private."
            elif "Sign in to confirm your age" in err_msg:
                err_msg = "Age-restricted video. Configure browser cookies in Settings to access it."
            elif "Video unavailable" in err_msg:
                err_msg = "This video is unavailable or has been removed."
            elif "HTTP Error 429" in err_msg:
                err_msg = "Too many requests to YouTube. Please wait a minute and try again."
            self.finished_error.emit(err_msg)
