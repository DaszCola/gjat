import os
import re
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QFrame, QMessageBox, QApplication, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QKeySequence, QShortcut, QDragEnterEvent, QDropEvent

from core.config import ConfigManager
from core.queue_manager import QueueManager
from core.extractor import LinkExtractorWorker
from ui.icons import get_svg_icon, get_svg_pixmap
from ui.widgets.header_bar import HeaderBar
from ui.widgets.empty_state import EmptyStateWidget
from ui.widgets.download_card import DownloadCard
from ui.widgets.format_dialog import FormatDialog
from ui.widgets.playlist_dialog import PlaylistDialog
from ui.widgets.smart_mode_dialog import SmartModeDialog
from ui.widgets.settings_dialog import SettingsDialog

URL_REGEX = re.compile(r'https?://[^\s]+')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gjat Downloader!")
        self.setWindowIcon(get_svg_icon("logo", size=32))
        self.resize(920, 680)
        self.setMinimumSize(720, 520)

        # Core Services
        self.config_mgr = ConfigManager()
        self.queue_mgr = QueueManager(max_concurrent=self.config_mgr.get("max_concurrent_downloads", 3))

        # State & tracking
        self.cards = {}  # task_id -> DownloadCard
        self.current_extractor = None
        self._last_clipboard_text = ""
        self.startup_checker = None

        self._init_ui()
        self._setup_connections()
        self._setup_shortcuts()
        self._setup_clipboard_monitor()
        self.setAcceptDrops(True)

        if self.config_mgr.get("auto_check_updates", True):
            QTimer.singleShot(2500, self._check_updates_silently)
        QTimer.singleShot(1500, self._check_ffmpeg_silently)

    def _init_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("MainContainer")
        self.setCentralWidget(central_widget)

        self.root_layout = QVBoxLayout(central_widget)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        # 1. Header Bar
        self.header = HeaderBar()
        smart_mode = self.config_mgr.get_smart_mode()
        self.header.set_smart_mode_state(smart_mode.get("enabled", False))
        self.root_layout.addWidget(self.header)

        # 2. Main Center Area: Stack container with Empty State & Download List
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(18, 14, 18, 14)
        self.content_layout.setSpacing(10)

        # Scroll area for cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.cards_container)
        self.content_layout.addWidget(self.scroll_area)

        # Empty State
        self.empty_state = EmptyStateWidget()
        self.content_layout.addWidget(self.empty_state)

        self.root_layout.addWidget(self.content_container, 1)

        # 4. Bottom Footer / Status Bar
        self.footer = QFrame()
        self.footer.setStyleSheet("background-color: #0a0a0f; border-top: 1px solid #1a1a26; padding: 2px 18px;")
        self.footer.setFixedHeight(30)
        f_layout = QHBoxLayout(self.footer)
        f_layout.setContentsMargins(16, 0, 16, 0)

        self.footer_left_lbl = QLabel("● Ready")
        self.footer_left_lbl.setStyleSheet("font-size: 11px; color: #10b981; font-weight: 600;")
        f_layout.addWidget(self.footer_left_lbl)

        f_layout.addStretch()

        self.footer_right_lbl = QLabel(f"Download Folder: {self.config_mgr.get('download_path')}")
        self.footer_right_lbl.setStyleSheet("font-size: 11px; color: #71717a;")
        f_layout.addWidget(self.footer_right_lbl)

        self.root_layout.addWidget(self.footer)

        self._refresh_view()

    def _setup_connections(self):
        # Header actions
        self.header.paste_clicked.connect(self.on_paste_link)
        self.header.url_submitted.connect(self.process_url)
        self.header.smart_mode_toggled.connect(self._on_smart_mode_toggled)
        self.header.smart_mode_settings_requested.connect(self._open_smart_mode_settings)
        self.header.open_folder_clicked.connect(self._open_downloads_folder)
        self.header.update_clicked.connect(self._open_update_dialog)
        self.header.settings_clicked.connect(self._open_settings)
        self.header.clear_clicked.connect(self._on_clear_completed)
        self.empty_state.paste_clicked.connect(self.on_paste_link)

        # Queue Manager events
        self.queue_mgr.task_added.connect(self._on_task_added)
        self.queue_mgr.task_updated.connect(self._on_task_updated)
        self.queue_mgr.task_completed.connect(self._on_task_completed)
        self.queue_mgr.task_failed.connect(self._on_task_failed)
        self.queue_mgr.queue_changed.connect(self._update_footer)

    def _setup_shortcuts(self):
        # Ctrl+V to paste link anywhere
        shortcut_paste = QShortcut(QKeySequence("Ctrl+V"), self)
        shortcut_paste.activated.connect(self.on_paste_link)

    def _setup_clipboard_monitor(self):
        clipboard = QApplication.clipboard()
        clipboard.dataChanged.connect(self._on_clipboard_changed)

    def _on_clipboard_changed(self):
        if not self.config_mgr.get("clipboard_watch", True):
            return
        text = QApplication.clipboard().text().strip()
        if text and text != self._last_clipboard_text and URL_REGEX.match(text):
            self._last_clipboard_text = text
            # Highlight paste button briefly with purple
            self.header.btn_paste.setStyleSheet("""
                background-color: #a855f7; color: #ffffff; font-weight: 700;
            """)
            QTimer.singleShot(1500, lambda: self.header.btn_paste.setStyleSheet(""))

    def show_banner(self, text: str, show_spinner: bool = True, timeout_ms: int = 0):
        if show_spinner:
            self.footer_left_lbl.setText(f"⚡ {text}")
            self.footer_left_lbl.setStyleSheet("font-size: 11px; color: #c084fc; font-weight: 600;")
        else:
            self.footer_left_lbl.setText(f"● {text}")
            self.footer_left_lbl.setStyleSheet("font-size: 11px; color: #a1a1aa; font-weight: 500;")

        if timeout_ms > 0:
            QTimer.singleShot(timeout_ms, self._update_footer)

    def hide_banner(self):
        self._update_footer()

    def _on_banner_anim_finished(self):
        pass

    def on_paste_link(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        if not text:
            self.show_banner("Clipboard is empty! Copy a video link first.", show_spinner=False, timeout_ms=3000)
            return
        
        match = URL_REGEX.search(text)
        if match:
            url = match.group(0)
            self.process_url(url)
        else:
            self.show_banner("No valid media URL found in clipboard.", show_spinner=False, timeout_ms=3000)

    def process_url(self, url: str):
        url = url.strip()
        if not url:
            return

        self.show_banner(f"Analyzing link: {url[:50]}...", show_spinner=True)
        self.header.btn_paste.setEnabled(False)

        cookies = self.config_mgr.get("cookies_browser", "none")
        self.current_extractor = LinkExtractorWorker(url, cookies_browser=cookies)
        self.current_extractor.finished_success.connect(self._on_extractor_success)
        self.current_extractor.finished_error.connect(self._on_extractor_error)
        self.current_extractor.status_update.connect(lambda s: self.show_banner(f"{s}", show_spinner=True))
        self.current_extractor.start()

    def _on_extractor_success(self, info: dict):
        self.header.btn_paste.setEnabled(True)
        self.hide_banner()

        smart_mode = self.config_mgr.get_smart_mode()
        if smart_mode.get("enabled", False) and not info.get("is_playlist"):
            # Execute 1-click download with smart mode preset!
            self._handle_smart_mode_download(info, smart_mode)
            return

        if info.get("is_playlist"):
            dialog = PlaylistDialog(info, self.config_mgr.get("download_path", ""), self)
            dialog.batch_download_requested.connect(self._on_batch_download_confirmed)
            dialog.exec()
        else:
            dialog = FormatDialog(info, self.config_mgr.get("download_path", ""), self)
            dialog.download_requested.connect(self._on_download_confirmed)
            dialog.exec()

    def _handle_smart_mode_download(self, info: dict, smart_mode: dict):
        mode = smart_mode.get("mode", "video")
        fmt = smart_mode.get("format", "mp4").lower()
        target_dir = smart_mode.get("download_path") or self.config_mgr.get("download_path")
        quality = smart_mode.get("quality", "best")

        if mode == "video":
            q_id = "best"
            desc = f"Smart Best {fmt.upper()}"
            if quality != "best":
                q_id = f"bestvideo[height<={quality}]"
                desc = f"Smart {quality}p {fmt.upper()}"

            opts = {
                "url": info["url"],
                "title": info["title"],
                "uploader": info["uploader"],
                "thumbnail": info.get("thumbnail", ""),
                "duration": info.get("duration_str", ""),
                "mode": "video",
                "format": fmt,
                "quality_format_id": q_id,
                "format_desc": desc,
                "download_path": target_dir,
                "download_subtitles": False,
                "include_video_id": self.config_mgr.get("include_video_id", False),
                "save_thumbnail_file": self.config_mgr.get("save_thumbnail_file", False),
            }
        else:
            abr = int(quality) if str(quality).isdigit() else 320
            opts = {
                "url": info["url"],
                "title": info["title"],
                "uploader": info["uploader"],
                "thumbnail": info.get("thumbnail", ""),
                "duration": info.get("duration_str", ""),
                "mode": "audio",
                "format": fmt,
                "audio_abr": abr,
                "format_desc": f"Smart {abr}k {fmt.upper()}",
                "download_path": target_dir,
                "include_video_id": self.config_mgr.get("include_video_id", False),
                "save_thumbnail_file": self.config_mgr.get("save_thumbnail_file", False),
            }

        self.queue_mgr.add_download(opts)
        self.show_banner(f"Added to download: {info['title'][:45]}", show_spinner=False, timeout_ms=3000)

    def _on_extractor_error(self, err: str):
        self.header.btn_paste.setEnabled(True)
        self.hide_banner()
        QMessageBox.warning(self, "Download Error", f"Unable to parse video URL:\n\n{err}")

    def _on_download_confirmed(self, opts: dict):
        opts["speed_limit_kb"] = self.config_mgr.get("speed_limit_kb", 0)
        opts["cookies_browser"] = self.config_mgr.get("cookies_browser", "none")
        opts["embed_metadata"] = self.config_mgr.get("embed_metadata", True)
        opts["embed_thumbnail"] = self.config_mgr.get("embed_thumbnail", True)
        opts["include_video_id"] = self.config_mgr.get("include_video_id", False)
        if "save_thumbnail_file" not in opts:
            opts["save_thumbnail_file"] = self.config_mgr.get("save_thumbnail_file", False)
        self.queue_mgr.add_download(opts)

    def _on_batch_download_confirmed(self, task_list: list):
        for opts in task_list:
            opts["speed_limit_kb"] = self.config_mgr.get("speed_limit_kb", 0)
            opts["cookies_browser"] = self.config_mgr.get("cookies_browser", "none")
            opts["embed_metadata"] = self.config_mgr.get("embed_metadata", True)
            opts["embed_thumbnail"] = self.config_mgr.get("embed_thumbnail", True)
            opts["include_video_id"] = self.config_mgr.get("include_video_id", False)
            if "save_thumbnail_file" not in opts:
                opts["save_thumbnail_file"] = self.config_mgr.get("save_thumbnail_file", False)
            self.queue_mgr.add_download(opts)

    def _on_task_added(self, task_info: dict):
        card = DownloadCard(task_info, self)
        card.cancel_clicked.connect(self.queue_mgr.cancel_task)
        card.remove_clicked.connect(self._remove_card)
        self.cards[task_info["id"]] = card

        # Insert at the top of the cards layout
        self.cards_layout.insertWidget(0, card)
        self._refresh_view()

    def _on_task_updated(self, task_id: str, p: dict):
        if task_id in self.cards:
            self.cards[task_id].update_progress(p)

    def _on_task_completed(self, task_id: str, filepath: str):
        if task_id in self.cards:
            self.cards[task_id].set_completed(filepath)

    def _on_task_failed(self, task_id: str, err: str):
        if task_id in self.cards:
            self.cards[task_id].set_failed(err)

    def _remove_card(self, task_id: str):
        if task_id in self.cards:
            card = self.cards.pop(task_id)
            self.cards_layout.removeWidget(card)
            card.deleteLater()
            self.queue_mgr.remove_task(task_id)
            self._refresh_view()

    def _on_clear_completed(self):
        self.queue_mgr.clear_completed()
        for task_id in list(self.cards.keys()):
            card = self.cards[task_id]
            status = card.task_info.get("status", "")
            if status in ("completed", "cancelled", "error"):
                self.cards_layout.removeWidget(card)
                card.deleteLater()
                del self.cards[task_id]
        self._refresh_view()

    def _refresh_view(self):
        has_items = len(self.cards) > 0
        if has_items:
            self.empty_state.hide()
            self.scroll_area.show()
        else:
            self.scroll_area.hide()
            self.empty_state.show()
        self._update_footer()

    def _update_footer(self):
        total = len(self.cards)
        active = len(self.queue_mgr.workers)
        waiting = len(self.queue_mgr.waiting_queue)
        
        if total == 0:
            self.footer_left_lbl.setText("● Ready")
            self.footer_left_lbl.setStyleSheet("font-size: 11px; color: #10b981; font-weight: 600;")
        else:
            self.footer_left_lbl.setText(f"● {active} Active  ·  {waiting} Queued  ·  {total} Total")
            self.footer_left_lbl.setStyleSheet("font-size: 11px; color: #c084fc; font-weight: 600;")

        path = self.config_mgr.get("download_path", "")
        self.footer_right_lbl.setText(f"Folder: {path}")

    def _on_smart_mode_toggled(self, enabled: bool):
        sm = self.config_mgr.get_smart_mode()
        sm["enabled"] = enabled
        self.config_mgr.set_smart_mode(sm)
        msg = "Smart Mode: ON (1-click download active)" if enabled else "Smart Mode: OFF"
        self.show_banner(msg, show_spinner=False, timeout_ms=2500)

    def _open_smart_mode_settings(self):
        sm = self.config_mgr.get_smart_mode()
        dialog = SmartModeDialog(sm, self)
        dialog.smart_mode_saved.connect(self._on_smart_mode_saved)
        dialog.exec()

    def _on_smart_mode_saved(self, new_sm: dict):
        self.config_mgr.set_smart_mode(new_sm)
        self.header.set_smart_mode_state(new_sm.get("enabled", False))
        msg = "Smart Mode settings updated."
        self.show_banner(msg, show_spinner=False, timeout_ms=2500)

    def _open_downloads_folder(self):
        path = self.config_mgr.get("download_path")
        if path and os.path.exists(path):
            os.startfile(path)
        else:
            fallback = str(Path.home() / "Downloads")
            os.startfile(fallback)

    def _open_settings(self):
        dialog = SettingsDialog(self.config_mgr, self)
        dialog.settings_saved.connect(self._on_settings_saved)
        dialog.exec()

    def _open_update_dialog(self):
        from ui.widgets.update_dialog import UpdateDialog
        url = self.config_mgr.get("custom_update_url", "").strip() or None
        dialog = UpdateDialog(check_url=url, parent=self)
        dialog.exec()

    def _check_ffmpeg_silently(self):
        from core.ffmpeg_checker import is_ffmpeg_available, FFmpegDownloaderWorker
        if not is_ffmpeg_available():
            self.show_banner("⚡ FFmpeg is missing. Downloading automatically for 1080p/4K support...", show_spinner=True)
            self._auto_ffmpeg_worker = FFmpegDownloaderWorker()
            self._auto_ffmpeg_worker.finished_signal.connect(lambda d: self.show_banner("✅ FFmpeg configured successfully!", show_spinner=False, timeout_ms=4000))
            self._auto_ffmpeg_worker.error_signal.connect(lambda err: self.show_banner(f"⚠️ FFmpeg auto-install: {err}", show_spinner=False, timeout_ms=6000))
            self._auto_ffmpeg_worker.start()

    def _check_updates_silently(self):
        from core.updater import VersionCheckerWorker
        url = self.config_mgr.get("custom_update_url", "").strip() or None
        self.startup_checker = VersionCheckerWorker(check_url=url)
        self.startup_checker.update_found.connect(self._on_silent_update_found)
        self.startup_checker.start()

    def _on_silent_update_found(self, data: dict):
        new_ver = data.get("version", "")
        self.header.set_update_available(new_ver)
        self.show_banner(f"Update available: v{new_ver} is out! Click 'Update' above to install.", show_spinner=False, timeout_ms=8000)

    def _on_settings_saved(self, new_settings: dict):
        self.queue_mgr.set_max_concurrent(new_settings.get("max_concurrent_downloads", 3))
        self._update_footer()
        self.show_banner("Settings applied successfully.", show_spinner=False, timeout_ms=2500)

    # Drag and Drop support
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasText() or event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        text = ""
        if event.mimeData().hasUrls():
            for u in event.mimeData().urls():
                text = u.toString()
                break
        elif event.mimeData().hasText():
            text = event.mimeData().text().strip()

        if text:
            m = URL_REGEX.search(text)
            if m:
                self.process_url(m.group(0))
