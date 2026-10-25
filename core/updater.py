import os
import re
import sys
import json
import time
import urllib.request
import subprocess
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication

from core.config import APP_VERSION, APP_NAME, DEFAULT_UPDATE_URL

def parse_version_tuple(version_str: str) -> tuple:
    """Extract numeric parts from a version string (e.g. 'v1.2.0' -> (1, 2, 0))."""
    if not version_str:
        return (0, 0, 0)
    cleaned = version_str.strip().lstrip("vV")
    numbers = re.findall(r'\d+', cleaned)
    return tuple(int(n) for n in numbers) if numbers else (0, 0, 0)

def is_newer_version(remote_ver: str, local_ver: str) -> bool:
    """Returns True if remote_ver is strictly newer than local_ver."""
    return parse_version_tuple(remote_ver) > parse_version_tuple(local_ver)

def normalize_update_endpoint(url: str) -> str:
    """Converts a GitHub repository shorthand or URL into a GitHub Releases API endpoint."""
    if not url:
        return DEFAULT_UPDATE_URL
    url = url.strip()

    # Matches 'username/repo'
    if re.match(r'^[a-zA-Z0-9_\-\.]+/[a-zA-Z0-9_\-\.]+$', url):
        return f"https://api.github.com/repos/{url}/releases/latest"

    # Matches 'https://github.com/username/repo' or 'https://github.com/username/repo/releases'
    gh_match = re.match(r'https?://github\.com/([a-zA-Z0-9_\-\.]+)/([a-zA-Z0-9_\-\.]+)', url)
    if gh_match:
        owner = gh_match.group(1)
        repo = gh_match.group(2).rstrip('/')
        if repo.endswith(".git"):
            repo = repo[:-4]
        return f"https://api.github.com/repos/{owner}/{repo}/releases/latest"

    return url

class VersionCheckerWorker(QThread):
    """Checks remote server or GitHub Releases API for application updates."""
    update_found = pyqtSignal(dict)
    up_to_date = pyqtSignal(str)
    check_error = pyqtSignal(str)

    def __init__(self, check_url: str = None, parent=None):
        super().__init__(parent)
        self.check_url = check_url or DEFAULT_UPDATE_URL

    def run(self):
        try:
            endpoint = normalize_update_endpoint(self.check_url)

            # Allow local file path testing if specified
            if os.path.exists(endpoint):
                with open(endpoint, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
            else:
                req = urllib.request.Request(
                    endpoint,
                    headers={
                        "User-Agent": f"GjatDownloader/{APP_VERSION}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                )
                with urllib.request.urlopen(req, timeout=12) as response:
                    raw_data = json.loads(response.read().decode("utf-8"))

            # Handle native GitHub Releases API payload
            if "tag_name" in raw_data and "assets" in raw_data:
                remote_tag = raw_data.get("tag_name", "0.0.0")
                remote_ver = remote_tag.lstrip("vV")
                title = raw_data.get("name") or f"Gjat Downloader v{remote_ver}"
                body_notes = raw_data.get("body", "").strip()

                if body_notes:
                    notes = [
                        line.strip().lstrip("*-#• ")
                        for line in body_notes.splitlines()
                        if line.strip() and not line.strip().startswith("#")
                    ]
                else:
                    notes = ["New version published on GitHub!"]

                download_url = None
                exe_download_url = None
                for asset in raw_data.get("assets", []):
                    aname = asset.get("name", "").lower()
                    burl = asset.get("browser_download_url", "")
                    if aname.endswith(".msi") and not download_url:
                        download_url = burl
                    elif aname.endswith(".exe") and not exe_download_url:
                        exe_download_url = burl

                data = {
                    "version": remote_ver,
                    "title": title,
                    "download_url": download_url or exe_download_url or raw_data.get("html_url", ""),
                    "exe_download_url": exe_download_url,
                    "notes": notes[:8],  # Keep top notes concise
                    "release_date": (raw_data.get("published_at") or "")[:10]
                }
            else:
                data = raw_data
                remote_ver = data.get("version", "0.0.0")

            if is_newer_version(remote_ver, APP_VERSION):
                self.update_found.emit(data)
            else:
                self.up_to_date.emit(APP_VERSION)
        except Exception as e:
            self.check_error.emit(str(e))

class UpdateDownloaderWorker(QThread):
    """Downloads installer package (.msi or .exe) with live progress tracking."""
    progress = pyqtSignal(int, str, str)  # percent, speed_str, size_str
    finished = pyqtSignal(str)           # local saved path
    error = pyqtSignal(str)

    def __init__(self, download_url: str, filename: str = None, parent=None):
        super().__init__(parent)
        self.download_url = download_url
        self.filename = filename or download_url.split("/")[-1].split("?")[0]
        if not self.filename.endswith((".msi", ".exe")):
            self.filename = "GjatDownloader-Setup.msi"
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            temp_dir = Path(os.environ.get("TEMP", ".")) / "GjatDownloader_Update"
            temp_dir.mkdir(parents=True, exist_ok=True)
            save_path = temp_dir / self.filename

            req = urllib.request.Request(
                self.download_url,
                headers={"User-Agent": f"GjatDownloader/{APP_VERSION}"}
            )

            start_time = time.time()
            downloaded = 0

            with urllib.request.urlopen(req, timeout=30) as resp:
                total_size = int(resp.headers.get("Content-Length", 0))
                with open(save_path, "wb") as f:
                    chunk_size = 64 * 1024  # 64 KB
                    while True:
                        if self._cancelled:
                            return
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)

                        elapsed = max(time.time() - start_time, 0.001)
                        speed = downloaded / elapsed  # B/s
                        speed_str = f"{speed / (1024 * 1024):.1f} MB/s" if speed > 1024 * 1024 else f"{speed / 1024:.0f} KB/s"

                        if total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            size_str = f"{downloaded / (1024 * 1024):.1f} / {total_size / (1024 * 1024):.1f} MB"
                        else:
                            percent = 0
                            size_str = f"{downloaded / (1024 * 1024):.1f} MB"

                        self.progress.emit(percent, speed_str, size_str)

            self.finished.emit(str(save_path))
        except Exception as e:
            self.error.emit(f"Failed to download update: {e}")

def launch_installer_and_exit(installer_path: str):
    """Executes the downloaded update installer and gracefully exits the running application."""
    installer_path = str(Path(installer_path).resolve())
    if not os.path.exists(installer_path):
        return

    try:
        if installer_path.lower().endswith(".msi"):
            # Launch standard Windows Installer
            subprocess.Popen(["msiexec.exe", "/i", installer_path], shell=False)
        else:
            # Launch standalone executable installer
            subprocess.Popen([installer_path], shell=False)
    except Exception as e:
        print(f"Error launching installer: {e}")

    # Gracefully quit current application
    app = QApplication.instance()
    if app:
        app.quit()
    sys.exit(0)

class YtDlpEngineUpdaterWorker(QThread):
    """Checks and updates the underlying yt-dlp core engine."""
    status_update = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def run(self):
        try:
            self.status_update.emit("Checking for yt-dlp updates...")
            # Run pip upgrade on yt-dlp or yt-dlp --update
            cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"]
            startupinfo = None
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
                timeout=60
            )

            if proc.returncode == 0:
                out = proc.stdout.strip()
                if "Requirement already satisfied" in out:
                    self.finished.emit("yt-dlp is already at the latest version!")
                else:
                    self.finished.emit("yt-dlp engine updated successfully! Please restart app.")
            else:
                self.error.emit(f"Update failed: {proc.stderr[:200]}")
        except Exception as e:
            self.error.emit(f"yt-dlp update error: {e}")
