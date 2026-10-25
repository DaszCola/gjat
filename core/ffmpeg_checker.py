import os
import sys
import shutil
import zipfile
import urllib.request
from pathlib import Path
from typing import Optional
from PyQt6.QtCore import QThread, pyqtSignal

FFMPEG_WINDOWS_URL = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"

def get_ffmpeg_dir() -> Optional[str]:
    """Finds the directory containing ffmpeg.exe."""
    # 1. Next to the running executable or script
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent
    else:
        exe_dir = Path(__file__).resolve().parent.parent

    local_app_data = Path(os.environ.get("LOCALAPPDATA", ""))
    user_home = Path.home()

    search_dirs = [
        exe_dir / "bin",
        exe_dir,
        exe_dir / "_internal" / "bin",
        exe_dir / "_internal",
        user_home / ".gjat_downloader" / "bin",
        local_app_data / "Programs" / "GjatDownloader" / "bin",
        local_app_data / "Programs" / "GjatDownloader",
        local_app_data / "Programs" / "GjatDownloader" / "_internal" / "bin",
        local_app_data / "Programs" / "GjatDownloader" / "_internal",
    ]

    for d in search_dirs:
        if (d / "ffmpeg.exe").exists() or (d / "ffmpeg.EXE").exists():
            return str(d)

    # 2. Check system PATH
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return str(Path(sys_ffmpeg).parent)

    # 3. Check WinGet Packages
    winget_pkg_dir = local_app_data / "Microsoft" / "WinGet" / "Packages"
    if winget_pkg_dir.exists():
        for sub in winget_pkg_dir.iterdir():
            if "ffmpeg" in sub.name.lower():
                # Check directly or in bin/
                if (sub / "ffmpeg.exe").exists():
                    return str(sub)
                for nested in sub.rglob("ffmpeg.exe"):
                    return str(nested.parent)

    return None

def is_ffmpeg_available() -> bool:
    return get_ffmpeg_dir() is not None

def setup_ffmpeg_runtime() -> Optional[str]:
    """Ensures FFmpeg directory is present in PATH for yt-dlp and child processes."""
    ff_dir = get_ffmpeg_dir()
    if ff_dir:
        cur_path = os.environ.get("PATH", "")
        if ff_dir not in cur_path:
            os.environ["PATH"] = ff_dir + os.pathsep + cur_path
        return ff_dir
    return None

class FFmpegDownloaderWorker(QThread):
    progress_signal = pyqtSignal(int, str)  # percent, status
    finished_signal = pyqtSignal(str)       # ffmpeg_dir
    error_signal = pyqtSignal(str)

    def run(self):
        try:
            target_bin = Path.home() / ".gjat_downloader" / "bin"
            target_bin.mkdir(parents=True, exist_ok=True)
            zip_dest = target_bin / "ffmpeg_temp.zip"

            self.progress_signal.emit(5, "Connecting to FFmpeg repository...")
            
            # Download with progress
            req = urllib.request.Request(FFMPEG_WINDOWS_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as resp, open(zip_dest, 'wb') as out_f:
                total_len = resp.getheader('content-length')
                total_size = int(total_len) if total_len else 0
                downloaded = 0
                block_size = 1024 * 64

                while True:
                    buffer = resp.read(block_size)
                    if not buffer:
                        break
                    out_f.write(buffer)
                    downloaded += len(buffer)
                    if total_size > 0:
                        pct = int((downloaded / total_size) * 80) + 5
                        mb_down = downloaded / (1024 * 1024)
                        mb_tot = total_size / (1024 * 1024)
                        self.progress_signal.emit(pct, f"Downloading FFmpeg... {mb_down:.1f} MB / {mb_tot:.1f} MB")

            self.progress_signal.emit(90, "Extracting FFmpeg binaries...")
            with zipfile.ZipFile(zip_dest, 'r') as z:
                for member in z.namelist():
                    if member.endswith("ffmpeg.exe") or member.endswith("ffprobe.exe"):
                        filename = os.path.basename(member)
                        source = z.open(member)
                        target = open(target_bin / filename, "wb")
                        with source, target:
                            shutil.copyfileobj(source, target)

            if zip_dest.exists():
                os.remove(zip_dest)

            self.progress_signal.emit(100, "FFmpeg installed successfully!")
            self.finished_signal.emit(str(target_bin))

        except Exception as e:
            self.error_signal.emit(f"Failed to auto-install FFmpeg: {e}")
