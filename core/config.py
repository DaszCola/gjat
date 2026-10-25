import os
import json
from pathlib import Path

# Default download folder: C:\Users\<username>\Videos\gjats
DEFAULT_DOWNLOAD_DIR = str(Path.home() / "Videos" / "gjats")

# Ensure the default folder exists automatically
try:
    Path(DEFAULT_DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"Notice: Could not auto-create default directory {DEFAULT_DOWNLOAD_DIR}: {e}")

APP_NAME = "Gjat Downloader!"
APP_VERSION = "1.4.2"
DEFAULT_UPDATE_URL = "https://github.com/DaszCola/gjat"

DEFAULT_CONFIG = {
    "download_path": DEFAULT_DOWNLOAD_DIR,
    "max_concurrent_downloads": 3,
    "speed_limit_kb": 0,  # 0 means unlimited
    "clipboard_watch": True,
    "auto_check_updates": True,
    "custom_update_url": "",
    "cookies_browser": "none",  # none, chrome, firefox, edge, brave
    "embed_metadata": True,
    "embed_thumbnail": True,
    "embed_subtitles": False,
    "subtitles_lang": "en",
    "include_video_id": False,
    "save_thumbnail_file": False,
    "theme": "purple_dark",
    "smart_mode": {
        "enabled": False,
        "mode": "video",       # "video" or "audio"
        "format": "mp4",       # "mp4", "mkv", "mp3", "m4a"
        "quality": "best",     # "2160", "1440", "1080", "720", "best", "320"
        "download_path": DEFAULT_DOWNLOAD_DIR,
    }
}

class ConfigManager:
    def __init__(self, config_file: str = None):
        if config_file is None:
            app_dir = Path.home() / ".gjat_downloader"
            app_dir.mkdir(parents=True, exist_ok=True)
            self.config_path = app_dir / "settings.json"
        else:
            self.config_path = Path(config_file)
        
        self.data = self._load()

    def _load(self) -> dict:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    config = DEFAULT_CONFIG.copy()
                    config.update(loaded)
                    if "smart_mode" in loaded:
                        sm = DEFAULT_CONFIG["smart_mode"].copy()
                        sm.update(loaded["smart_mode"])
                        config["smart_mode"] = sm
                    
                    # Ensure download_path is valid, fallback to DEFAULT_DOWNLOAD_DIR
                    if not config.get("download_path"):
                        config["download_path"] = DEFAULT_DOWNLOAD_DIR
                    return config
            except Exception as e:
                print(f"Error loading config, using defaults: {e}")
                return DEFAULT_CONFIG.copy()
        else:
            return DEFAULT_CONFIG.copy()

    def save(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def get_smart_mode(self) -> dict:
        return self.data.get("smart_mode", DEFAULT_CONFIG["smart_mode"])

    def set_smart_mode(self, sm_dict: dict):
        self.data["smart_mode"] = sm_dict
        self.save()
