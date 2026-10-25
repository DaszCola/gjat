import sys
import os
from pathlib import Path

# Fix Windows DLL search path for PyQt6 in PyInstaller frozen bundles
if getattr(sys, 'frozen', False):
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    candidate_dirs = [
        os.path.join(base_dir, 'PyQt6', 'Qt6', 'bin'),
        os.path.join(base_dir, '_internal', 'PyQt6', 'Qt6', 'bin'),
        os.path.join(base_dir, 'PyQt6', 'Qt', 'bin'),
        os.path.join(base_dir, '_internal'),
        base_dir,
    ]
    for d in candidate_dirs:
        if os.path.isdir(d):
            if hasattr(os, 'add_dll_directory'):
                try:
                    os.add_dll_directory(d)
                except Exception:
                    pass
            os.environ['PATH'] = d + os.pathsep + os.environ.get('PATH', '')

    candidate_plugin_dirs = [
        os.path.join(base_dir, 'PyQt6', 'Qt6', 'plugins'),
        os.path.join(base_dir, '_internal', 'PyQt6', 'Qt6', 'plugins'),
    ]
    for pd in candidate_plugin_dirs:
        if os.path.isdir(pd):
            os.environ['QT_PLUGIN_PATH'] = pd
            break

# Ensure local directories are in path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from ui.theme import apply_theme
from ui.main_window import MainWindow
from core.js_checker import setup_js_runtime
from core.ffmpeg_checker import setup_ffmpeg_runtime

def main():
    # Configure JS runtime and FFmpeg for yt-dlp
    setup_js_runtime()
    setup_ffmpeg_runtime()

    # Enable logging
    try:
        log_dir = Path.home() / ".gjat_downloader"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = open(log_dir / "app.log", "a", encoding="utf-8")
        import datetime
        log_file.write(f"\n--- App Launch {datetime.datetime.now()} ---\n")
        log_file.flush()
    except Exception:
        pass

    # Enable crisp High DPI rendering
    if hasattr(Qt.HighDpiScaleFactorRoundingPolicy, 'PassThrough'):
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

    app = QApplication(sys.argv)
    app.setApplicationName("Gjat Downloader!")
    app.setOrganizationName("Gjat")

    # Set Application Icon from custom program icon
    from PyQt6.QtGui import QIcon
    icon_p = Path(__file__).parent / "app_icon.ico"
    if not icon_p.exists():
        icon_p = Path(__file__).parent / "app_icon.png"
    if icon_p.exists():
        app.setWindowIcon(QIcon(str(icon_p)))

    # Apply modern obsidian/dark slate theme
    apply_theme(app)

    window = MainWindow()
    if icon_p.exists():
        window.setWindowIcon(QIcon(str(icon_p)))
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
