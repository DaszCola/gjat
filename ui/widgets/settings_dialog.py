import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QComboBox, QLineEdit, QFileDialog, QFrame, QSpinBox,
    QTabWidget, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QIcon
import yt_dlp.version

class SettingsDialog(QDialog):
    settings_saved = pyqtSignal(dict)

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_mgr = config_manager
        self.settings = self.config_mgr.data.copy()
        self.setWindowTitle("Preferences & Settings")
        self.setFixedSize(620, 540)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        # Set Window Icon
        icon_path = Path(__file__).resolve().parent.parent.parent / "app_icon.ico"
        if not icon_path.exists():
            icon_path = Path(__file__).resolve().parent.parent.parent / "app_icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(16)

        # Tab Widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # =====================================================================
        # Tab 1: General
        # =====================================================================
        gen_tab = QWidget()
        g_layout = QVBoxLayout(gen_tab)
        g_layout.setContentsMargins(16, 16, 16, 16)
        g_layout.setSpacing(14)

        # Download directory card
        dir_card = QFrame()
        dir_card.setObjectName("SettingsCard")
        dir_card.setStyleSheet("""
            QFrame#SettingsCard {
                background-color: #0d0d15;
                border: 1px solid #1e1e2c;
                border-radius: 10px;
                padding: 12px;
            }
            QFrame#SettingsCard QLabel {
                border: none;
                background: transparent;
                padding: 0px;
            }
        """)
        dc_layout = QVBoxLayout(dir_card)
        dc_layout.setSpacing(8)

        dir_lbl = QLabel("Default Download Directory:")
        dir_lbl.setStyleSheet("font-weight: 700; font-size: 12px; color: #f4f4f6;")
        dc_layout.addWidget(dir_lbl)

        dir_box = QHBoxLayout()
        dir_box.setSpacing(8)
        self.dir_input = QLineEdit(self.settings.get("download_path", ""))
        btn_browse = QPushButton("Browse...")
        btn_browse.setProperty("class", "ActionBtn")
        btn_browse.setFixedHeight(34)
        btn_browse.clicked.connect(self._browse)
        dir_box.addWidget(self.dir_input, 1)
        dir_box.addWidget(btn_browse)
        dc_layout.addLayout(dir_box)

        g_layout.addWidget(dir_card)

        # Concurrent & Speed Options Card
        opts_card = QFrame()
        opts_card.setObjectName("SettingsCard")
        opts_card.setStyleSheet("""
            QFrame#SettingsCard {
                background-color: #0d0d15;
                border: 1px solid #1e1e2c;
                border-radius: 10px;
                padding: 14px;
            }
            QFrame#SettingsCard QLabel {
                border: none;
                background: transparent;
                padding: 0px;
            }
        """)
        oc_layout = QVBoxLayout(opts_card)
        oc_layout.setSpacing(12)

        # Max Concurrent Downloads
        concur_row = QHBoxLayout()
        concur_lbl = QLabel("Concurrent Downloads:")
        concur_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1; font-size: 12px;")
        self.spin_concur = QSpinBox()
        self.spin_concur.setRange(1, 6)
        self.spin_concur.setValue(self.settings.get("max_concurrent_downloads", 3))
        self.spin_concur.setFixedWidth(70)
        self.spin_concur.setFixedHeight(32)
        concur_row.addWidget(concur_lbl)
        concur_row.addWidget(self.spin_concur)
        concur_row.addStretch()
        oc_layout.addLayout(concur_row)

        # Speed limit
        spd_row = QHBoxLayout()
        spd_lbl = QLabel("Download Speed Limit:")
        spd_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1; font-size: 12px;")
        self.combo_speed = QComboBox()
        self.combo_speed.setFixedHeight(32)
        self.combo_speed.addItems([
            "Unlimited (Maximum speed)",
            "5 MB/s (5120 KB/s)",
            "10 MB/s (10240 KB/s)",
            "20 MB/s (20480 KB/s)",
            "50 MB/s (51200 KB/s)"
        ])
        current_limit = self.settings.get("speed_limit_kb", 0)
        if current_limit == 5120:
            self.combo_speed.setCurrentIndex(1)
        elif current_limit == 10240:
            self.combo_speed.setCurrentIndex(2)
        elif current_limit == 20480:
            self.combo_speed.setCurrentIndex(3)
        elif current_limit == 51200:
            self.combo_speed.setCurrentIndex(4)
        else:
            self.combo_speed.setCurrentIndex(0)

        spd_row.addWidget(spd_lbl)
        spd_row.addWidget(self.combo_speed)
        spd_row.addStretch()
        oc_layout.addLayout(spd_row)

        g_layout.addWidget(opts_card)

        # Behavior Toggles
        beh_card = QFrame()
        beh_card.setObjectName("SettingsCard")
        beh_card.setStyleSheet("""
            QFrame#SettingsCard {
                background-color: #0d0d15;
                border: 1px solid #1e1e2c;
                border-radius: 10px;
                padding: 12px;
            }
            QFrame#SettingsCard QLabel {
                border: none;
                background: transparent;
                padding: 0px;
            }
        """)
        bc_layout = QVBoxLayout(beh_card)
        bc_layout.setSpacing(10)

        self.chk_clipboard = QCheckBox("Automatically detect video URLs in clipboard (Instant download prompt)")
        self.chk_clipboard.setChecked(self.settings.get("clipboard_watch", True))
        bc_layout.addWidget(self.chk_clipboard)

        self.chk_include_id = QCheckBox("Include video ID in filename (e.g. Video [ID].mp4)")
        self.chk_include_id.setChecked(self.settings.get("include_video_id", False))
        bc_layout.addWidget(self.chk_include_id)

        g_layout.addWidget(beh_card)
        g_layout.addStretch()
        self.tabs.addTab(gen_tab, "General")

        # =====================================================================
        # Tab 2: Processing & Metadata
        # =====================================================================
        proc_tab = QWidget()
        p_layout = QVBoxLayout(proc_tab)
        p_layout.setContentsMargins(16, 16, 16, 16)
        p_layout.setSpacing(14)

        meta_card = QFrame()
        meta_card.setObjectName("SettingsCard")
        meta_card.setStyleSheet("""
            QFrame#SettingsCard {
                background-color: #0d0d15;
                border: 1px solid #1e1e2c;
                border-radius: 10px;
                padding: 14px;
            }
            QFrame#SettingsCard QLabel {
                border: none;
                background: transparent;
                padding: 0px;
            }
        """)
        mc_layout = QVBoxLayout(meta_card)
        mc_layout.setSpacing(12)

        meta_title = QLabel("Media Tagging & Art")
        meta_title.setStyleSheet("font-weight: 700; font-size: 12px; color: #c084fc;")
        mc_layout.addWidget(meta_title)

        self.chk_meta = QCheckBox("Embed tags and chapters (Title, Artist, Chapters, Description)")
        self.chk_meta.setChecked(self.settings.get("embed_metadata", True))
        mc_layout.addWidget(self.chk_meta)

        self.chk_thumb = QCheckBox("Embed thumbnail cover art into media file (ID3 / MP4 tag)")
        self.chk_thumb.setChecked(self.settings.get("embed_thumbnail", True))
        mc_layout.addWidget(self.chk_thumb)

        self.chk_save_thumb_file = QCheckBox("Save standalone thumbnail image (.jpg) alongside media")
        self.chk_save_thumb_file.setChecked(self.settings.get("save_thumbnail_file", False))
        mc_layout.addWidget(self.chk_save_thumb_file)

        p_layout.addWidget(meta_card)

        sub_card = QFrame()
        sub_card.setObjectName("SettingsCard")
        sub_card.setStyleSheet("""
            QFrame#SettingsCard {
                background-color: #0d0d15;
                border: 1px solid #1e1e2c;
                border-radius: 10px;
                padding: 14px;
            }
            QFrame#SettingsCard QLabel {
                border: none;
                background: transparent;
                padding: 0px;
            }
        """)
        sc_layout = QVBoxLayout(sub_card)
        sc_layout.setSpacing(10)

        sub_title = QLabel("Subtitles")
        sub_title.setStyleSheet("font-weight: 700; font-size: 12px; color: #c084fc;")
        sc_layout.addWidget(sub_title)

        sub_lang_row = QHBoxLayout()
        sub_lang_lbl = QLabel("Preferred Subtitle Language:")
        sub_lang_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1; font-size: 12px;")
        self.combo_sub_lang = QComboBox()
        self.combo_sub_lang.setFixedHeight(32)
        self.combo_sub_lang.addItems(["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "pl"])
        self.combo_sub_lang.setCurrentText(self.settings.get("subtitles_lang", "en"))
        sub_lang_row.addWidget(sub_lang_lbl)
        sub_lang_row.addWidget(self.combo_sub_lang)
        sub_lang_row.addStretch()
        sc_layout.addLayout(sub_lang_row)

        p_layout.addWidget(sub_card)
        p_layout.addStretch()
        self.tabs.addTab(proc_tab, "Metadata")

        # =====================================================================
        # Tab 3: Authentication (Browser Cookies)
        # =====================================================================
        auth_tab = QWidget()
        a_layout = QVBoxLayout(auth_tab)
        a_layout.setContentsMargins(16, 16, 16, 16)
        a_layout.setSpacing(14)

        auth_card = QFrame()
        auth_card.setObjectName("SettingsCard")
        auth_card.setStyleSheet("""
            QFrame#SettingsCard {
                background-color: #0d0d15;
                border: 1px solid #1e1e2c;
                border-radius: 10px;
                padding: 14px;
            }
            QFrame#SettingsCard QLabel {
                border: none;
                background: transparent;
                padding: 0px;
            }
        """)
        ac_layout = QVBoxLayout(auth_card)
        ac_layout.setSpacing(12)

        ac_title = QLabel("Import Browser Cookies")
        ac_title.setStyleSheet("font-weight: 700; font-size: 12px; color: #c084fc;")
        ac_layout.addWidget(ac_title)

        cookie_info = QLabel("Allows downloading age-restricted videos, private playlists, and member-only media securely using your existing browser session.")
        cookie_info.setStyleSheet("color: #a1a1aa; font-size: 12px; line-height: 1.5;")
        cookie_info.setWordWrap(True)
        ac_layout.addWidget(cookie_info)

        cookie_row = QHBoxLayout()
        cookie_lbl = QLabel("Source Browser:")
        cookie_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1; font-size: 12px;")
        self.combo_browser = QComboBox()
        self.combo_browser.setFixedHeight(32)
        self.combo_browser.addItems(["none", "chrome", "firefox", "edge", "brave", "opera", "vivaldi"])
        self.combo_browser.setCurrentText(self.settings.get("cookies_browser", "none"))
        cookie_row.addWidget(cookie_lbl)
        cookie_row.addWidget(self.combo_browser)
        cookie_row.addStretch()
        ac_layout.addLayout(cookie_row)

        a_layout.addWidget(auth_card)
        a_layout.addStretch()
        self.tabs.addTab(auth_tab, "Authentication")

        # =====================================================================
        # Tab 4: Updates & Engine
        # =====================================================================
        upd_tab = QWidget()
        u_layout = QVBoxLayout(upd_tab)
        u_layout.setContentsMargins(16, 16, 16, 16)
        u_layout.setSpacing(14)

        from core.config import APP_VERSION
        from core.updater import YtDlpEngineUpdaterWorker
        from core.ffmpeg_checker import is_ffmpeg_available, get_ffmpeg_dir, FFmpegDownloaderWorker
        from core.js_checker import get_deno_dir

        # Card 1: App Updates
        app_upd_card = QFrame()
        app_upd_card.setObjectName("SettingsCard")
        app_upd_card.setStyleSheet("""
            QFrame#SettingsCard {
                background-color: #0d0d15;
                border: 1px solid #1e1e2c;
                border-radius: 10px;
                padding: 14px;
            }
            QFrame#SettingsCard QLabel {
                border: none;
                background: transparent;
                padding: 0px;
            }
        """)
        auc_l = QVBoxLayout(app_upd_card)
        auc_l.setSpacing(10)

        auc_top = QHBoxLayout()
        auc_title = QLabel(f"Gjat Downloader! v{APP_VERSION}")
        auc_title.setStyleSheet("font-weight: 800; font-size: 13px; color: #f4f4f6;")
        self.btn_check_app_update = QPushButton("🔄 Check for Updates")
        self.btn_check_app_update.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #9333ea);
                color: #ffffff;
                font-weight: 700;
                font-size: 12px;
                padding: 6px 14px;
                border: 1px solid #a855f7;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #a855f7);
            }
        """)
        self.btn_check_app_update.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_check_app_update.clicked.connect(self._open_update_dialog)
        auc_top.addWidget(auc_title)
        auc_top.addStretch()
        auc_top.addWidget(self.btn_check_app_update)
        auc_l.addLayout(auc_top)

        self.chk_auto_update = QCheckBox("Check for updates automatically when application starts")
        self.chk_auto_update.setChecked(self.settings.get("auto_check_updates", True))
        auc_l.addWidget(self.chk_auto_update)

        # Custom Update URL row
        url_box = QHBoxLayout()
        url_box.setSpacing(8)
        url_lbl = QLabel("Repository:")
        url_lbl.setStyleSheet("font-weight: 600; color: #a1a1aa; font-size: 12px;")
        self.input_custom_url = QLineEdit(self.settings.get("custom_update_url", ""))
        self.input_custom_url.setPlaceholderText("Default: DaszCola/gjat")
        self.input_custom_url.setFixedHeight(30)
        url_box.addWidget(url_lbl)
        url_box.addWidget(self.input_custom_url, 1)
        auc_l.addLayout(url_box)

        u_layout.addWidget(app_upd_card)

        # Card 2: Core Engine Status
        eng_card = QFrame()
        eng_card.setObjectName("SettingsCard")
        eng_card.setStyleSheet("""
            QFrame#SettingsCard {
                background-color: #0d0d15;
                border: 1px solid #1e1e2c;
                border-radius: 10px;
                padding: 14px;
            }
            QFrame#SettingsCard QLabel {
                border: none;
                background: transparent;
                padding: 0px;
            }
        """)
        eng_layout = QVBoxLayout(eng_card)
        eng_layout.setSpacing(10)

        # Row 1: yt-dlp
        ytdlp_top = QHBoxLayout()
        self.ytdlp_lbl = QLabel(f"yt-dlp Core Engine: v{yt_dlp.version.__version__}")
        self.ytdlp_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1; font-size: 12px;")
        self.btn_update_ytdlp = QPushButton("⚡ Update Engine")
        self.btn_update_ytdlp.setProperty("class", "ActionBtn")
        self.btn_update_ytdlp.setFixedHeight(30)
        self.btn_update_ytdlp.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_update_ytdlp.clicked.connect(self._start_ytdlp_update)
        ytdlp_top.addWidget(self.ytdlp_lbl)
        ytdlp_top.addStretch()
        ytdlp_top.addWidget(self.btn_update_ytdlp)
        eng_layout.addLayout(ytdlp_top)

        # Row 2: FFmpeg Status
        ff_row = QHBoxLayout()
        self.ffmpeg_status_lbl = QLabel()
        ff_row.addWidget(self.ffmpeg_status_lbl)
        ff_row.addStretch()

        self.btn_install_ffmpeg = QPushButton("Install FFmpeg")
        self.btn_install_ffmpeg.setProperty("class", "ActionBtn")
        self.btn_install_ffmpeg.setFixedHeight(30)
        self.btn_install_ffmpeg.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_install_ffmpeg.clicked.connect(self._start_ffmpeg_install)
        ff_row.addWidget(self.btn_install_ffmpeg)
        eng_layout.addLayout(ff_row)

        # Row 3: Deno JS Runtime Status
        deno_row = QHBoxLayout()
        deno_dir = get_deno_dir()
        if deno_dir:
            deno_lbl = QLabel("● Deno JS Runtime: Active (Challenge Solver)")
            deno_lbl.setStyleSheet("color: #10b981; font-size: 12px; font-weight: 600;")
        else:
            deno_lbl = QLabel("● Deno JS Runtime: Standby")
            deno_lbl.setStyleSheet("color: #a1a1aa; font-size: 12px; font-weight: 500;")
        deno_row.addWidget(deno_lbl)
        deno_row.addStretch()
        eng_layout.addLayout(deno_row)

        self._refresh_ffmpeg_status()

        u_layout.addWidget(eng_card)
        u_layout.addStretch()
        self.tabs.addTab(upd_tab, "Engine")

        # =====================================================================
        # Dialog Footer Buttons
        # =====================================================================
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)
        btn_box.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "ActionBtn")
        btn_cancel.setFixedHeight(36)
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_save = QPushButton("Save Settings")
        btn_save.setProperty("class", "PrimaryBtn")
        btn_save.setFixedHeight(36)
        btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_save.clicked.connect(self._save)
        btn_box.addWidget(btn_save)

        layout.addLayout(btn_box)

    def _open_update_dialog(self):
        from ui.widgets.update_dialog import UpdateDialog
        url = self.input_custom_url.text().strip() or None
        dialog = UpdateDialog(check_url=url, parent=self)
        dialog.exec()

    def _start_ytdlp_update(self):
        from core.updater import YtDlpEngineUpdaterWorker
        self.btn_update_ytdlp.setEnabled(False)
        self.btn_update_ytdlp.setText("Updating...")
        self.ytdlp_worker = YtDlpEngineUpdaterWorker()
        self.ytdlp_worker.status_update.connect(lambda s: self.ytdlp_lbl.setText(s))
        self.ytdlp_worker.finished.connect(lambda msg: (self.ytdlp_lbl.setText(msg), self.btn_update_ytdlp.setEnabled(True), self.btn_update_ytdlp.setText("⚡ Update Engine")))
        self.ytdlp_worker.error.connect(lambda err: (self.ytdlp_lbl.setText(err), self.btn_update_ytdlp.setEnabled(True), self.btn_update_ytdlp.setText("Retry Update")))
        self.ytdlp_worker.start()

    def _browse(self):
        f = QFileDialog.getExistingDirectory(self, "Select Download Folder", self.dir_input.text())
        if f:
            self.dir_input.setText(f)

    def _save(self):
        spd_idx = self.combo_speed.currentIndex()
        spd_map = [0, 5120, 10240, 20480, 51200]
        speed_limit = spd_map[spd_idx] if spd_idx < len(spd_map) else 0

        self.settings["download_path"] = self.dir_input.text().strip()
        self.settings["max_concurrent_downloads"] = self.spin_concur.value()
        self.settings["speed_limit_kb"] = speed_limit
        self.settings["clipboard_watch"] = self.chk_clipboard.isChecked()
        self.settings["auto_check_updates"] = self.chk_auto_update.isChecked()
        self.settings["custom_update_url"] = self.input_custom_url.text().strip()
        self.settings["embed_metadata"] = self.chk_meta.isChecked()
        self.settings["embed_thumbnail"] = self.chk_thumb.isChecked()
        self.settings["subtitles_lang"] = self.combo_sub_lang.currentText()
        self.settings["cookies_browser"] = self.combo_browser.currentText()
        self.settings["include_video_id"] = self.chk_include_id.isChecked()
        self.settings["save_thumbnail_file"] = self.chk_save_thumb_file.isChecked()

        self.config_mgr.data.update(self.settings)
        self.config_mgr.save()
        self.settings_saved.emit(self.settings)
        self.accept()

    def _refresh_ffmpeg_status(self):
        from core.ffmpeg_checker import is_ffmpeg_available
        if is_ffmpeg_available():
            self.ffmpeg_status_lbl.setText("● FFmpeg Multiplexer: Active & Enabled (Built-in)")
            self.ffmpeg_status_lbl.setStyleSheet("color: #10b981; font-size: 12px; font-weight: 600;")
            self.btn_install_ffmpeg.hide()
        else:
            self.ffmpeg_status_lbl.setText("● FFmpeg: Not Found (Required for 4K video merging & MP3s)")
            self.ffmpeg_status_lbl.setStyleSheet("color: #f43f5e; font-size: 12px; font-weight: 500;")
            self.btn_install_ffmpeg.show()

    def _start_ffmpeg_install(self):
        from core.ffmpeg_checker import FFmpegDownloaderWorker
        self.btn_install_ffmpeg.setEnabled(False)
        self.btn_install_ffmpeg.setText("Installing...")
        self.ffmpeg_worker = FFmpegDownloaderWorker()
        self.ffmpeg_worker.progress_signal.connect(lambda p, msg: self.ffmpeg_status_lbl.setText(f"{msg} ({p}%)"))
        self.ffmpeg_worker.finished_signal.connect(lambda p: self._refresh_ffmpeg_status())
        self.ffmpeg_worker.error_signal.connect(lambda err: (self.ffmpeg_status_lbl.setText(err), self.btn_install_ffmpeg.setEnabled(True), self.btn_install_ffmpeg.setText("Retry Auto-Install")))
        self.ffmpeg_worker.start()
