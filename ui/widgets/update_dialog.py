import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextBrowser, QFrame, QWidget, QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCursor

from core.config import APP_VERSION, APP_NAME, DEFAULT_UPDATE_URL
from core.updater import VersionCheckerWorker, UpdateDownloaderWorker, launch_installer_and_exit
from ui.icons import get_svg_icon, get_svg_pixmap

class UpdateDialog(QDialog):
    def __init__(self, check_url: str = None, parent=None):
        super().__init__(parent)
        self.check_url = check_url
        self.setWindowTitle("Software Update")
        self.setFixedSize(500, 440)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self.checker = None
        self.downloader = None
        self.update_data = None
        self.downloaded_installer_path = None

        self._init_ui()
        self._start_check()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header with Logo & Title
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_svg_pixmap("sparkle", color="#c084fc", size=32))
        header_row.addWidget(icon_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        app_title = QLabel("Gjat Downloader! Updates")
        app_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #f8fafc;")
        self.ver_lbl = QLabel(f"Current version: v{APP_VERSION}")
        self.ver_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")
        title_box.addWidget(app_title)
        title_box.addWidget(self.ver_lbl)
        header_row.addLayout(title_box)
        header_row.addStretch()

        layout.addLayout(header_row)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #272936;")
        layout.addWidget(sep)

        # Stacked Pages:
        # Page 0: Checking...
        # Page 1: Update Available
        # Page 2: Up to date
        # Page 3: Downloading...
        # Page 4: Error
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

        self._create_checking_page()
        self._create_available_page()
        self._create_uptodate_page()
        self._create_downloading_page()
        self._create_error_page()

        # Bottom Button Bar
        self.btn_box = QHBoxLayout()
        self.btn_box.addStretch()

        self.btn_secondary = QPushButton("Close")
        self.btn_secondary.clicked.connect(self._on_secondary_click)
        self.btn_box.addWidget(self.btn_secondary)

        self.btn_primary = QPushButton("Download Update")
        self.btn_primary.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #9333ea);
                color: #ffffff;
                font-weight: 700;
                padding: 9px 20px;
                border: 1px solid #a855f7;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #a855f7);
                border-color: #c084fc;
            }
        """)
        self.btn_primary.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_primary.clicked.connect(self._on_primary_click)
        self.btn_box.addWidget(self.btn_primary)

        layout.addLayout(self.btn_box)

    def _create_checking_page(self):
        p = QWidget()
        l = QVBoxLayout(p)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.setSpacing(14)

        spin_lbl = QLabel("Checking for updates...")
        spin_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #cbd5e1;")
        l.addWidget(spin_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        prog = QProgressBar()
        prog.setRange(0, 0)
        prog.setFixedWidth(200)
        prog.setFixedHeight(4)
        prog.setTextVisible(False)
        l.addWidget(prog, alignment=Qt.AlignmentFlag.AlignCenter)

        self.stack.addWidget(p)

    def _create_available_page(self):
        p = QWidget()
        l = QVBoxLayout(p)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(10)

        # Version banner
        self.new_ver_card = QFrame()
        self.new_ver_card.setStyleSheet("background-color: #1a162b; border: 1px solid #7e22ce; border-radius: 8px; padding: 10px 14px;")
        card_l = QHBoxLayout(self.new_ver_card)
        card_l.setContentsMargins(8, 6, 8, 6)

        v_box = QVBoxLayout()
        v_box.setSpacing(2)
        self.new_ver_title = QLabel("New Version Available!")
        self.new_ver_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #c084fc;")
        self.new_ver_subtitle = QLabel("A new release is ready to download.")
        self.new_ver_subtitle.setStyleSheet("font-size: 11px; color: #a1a1aa;")
        v_box.addWidget(self.new_ver_title)
        v_box.addWidget(self.new_ver_subtitle)
        card_l.addLayout(v_box)
        card_l.addStretch()

        self.badge_lbl = QLabel("v1.2.0")
        self.badge_lbl.setStyleSheet("background-color: #9333ea; color: #ffffff; font-weight: 700; font-size: 12px; padding: 4px 10px; border-radius: 6px;")
        card_l.addWidget(self.badge_lbl)

        l.addWidget(self.new_ver_card)

        # Changelog / Release notes
        notes_lbl = QLabel("What's New:")
        notes_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #cbd5e1;")
        l.addWidget(notes_lbl)

        self.notes_browser = QTextBrowser()
        self.notes_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #111218;
                border: 1px solid #20222f;
                border-radius: 8px;
                padding: 10px;
                color: #e2e8f0;
                font-size: 12px;
                line-height: 1.5;
            }
        """)
        l.addWidget(self.notes_browser, 1)

        self.stack.addWidget(p)

    def _create_uptodate_page(self):
        p = QWidget()
        l = QVBoxLayout(p)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.setSpacing(12)

        icon = QLabel()
        icon.setPixmap(get_svg_pixmap("check", color="#4ade80", size=48))
        l.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)

        msg = QLabel("You're Up to Date!")
        msg.setStyleSheet("font-size: 16px; font-weight: 700; color: #4ade80;")
        l.addWidget(msg, alignment=Qt.AlignmentFlag.AlignCenter)

        sub = QLabel(f"Gjat Downloader v{APP_VERSION} is the latest version available.")
        sub.setStyleSheet("font-size: 12px; color: #94a3b8;")
        l.addWidget(sub, alignment=Qt.AlignmentFlag.AlignCenter)

        self.stack.addWidget(p)

    def _create_downloading_page(self):
        p = QWidget()
        l = QVBoxLayout(p)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.setSpacing(14)

        self.dl_status_lbl = QLabel("Downloading update installer...")
        self.dl_status_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #cbd5e1;")
        l.addWidget(self.dl_status_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self.dl_progress_bar = QProgressBar()
        self.dl_progress_bar.setRange(0, 100)
        self.dl_progress_bar.setValue(0)
        self.dl_progress_bar.setFixedHeight(8)
        self.dl_progress_bar.setFixedWidth(360)
        l.addWidget(self.dl_progress_bar, alignment=Qt.AlignmentFlag.AlignCenter)

        self.dl_stats_lbl = QLabel("Starting download...")
        self.dl_stats_lbl.setStyleSheet("font-size: 11px; color: #94a3b8;")
        l.addWidget(self.dl_stats_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self.stack.addWidget(p)

    def _create_error_page(self):
        p = QWidget()
        l = QVBoxLayout(p)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.setSpacing(10)

        err_icon = QLabel()
        err_icon.setPixmap(get_svg_pixmap("cancel", color="#f87171", size=40))
        l.addWidget(err_icon, alignment=Qt.AlignmentFlag.AlignCenter)

        err_title = QLabel("Unable to Check for Updates")
        err_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #f87171;")
        l.addWidget(err_title, alignment=Qt.AlignmentFlag.AlignCenter)

        self.err_details_lbl = QLabel("Please verify your internet connection.")
        self.err_details_lbl.setWordWrap(True)
        self.err_details_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")
        self.err_details_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(self.err_details_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        self.stack.addWidget(p)

    def _start_check(self):
        self.stack.setCurrentIndex(0)
        self.btn_primary.hide()
        self.btn_secondary.setText("Cancel")

        self.checker = VersionCheckerWorker(self.check_url)
        self.checker.update_found.connect(self._on_update_found)
        self.checker.up_to_date.connect(self._on_up_to_date)
        self.checker.check_error.connect(self._on_check_error)
        self.checker.start()

    def _on_update_found(self, data: dict):
        self.update_data = data
        new_ver = data.get("version", "Unknown")
        title = data.get("title", f"Version {new_ver}")
        notes = data.get("notes", [])

        self.new_ver_title.setText(title)
        self.badge_lbl.setText(f"v{new_ver}")

        # Render release notes
        html = "<b>Highlights in this update:</b><br><br>"
        if isinstance(notes, list):
            html += "<ul>"
            for note in notes:
                html += f"<li>{note}</li>"
            html += "</ul>"
        else:
            html += str(notes).replace("\n", "<br>")

        self.notes_browser.setHtml(html)

        self.stack.setCurrentIndex(1)
        self.btn_primary.show()
        self.btn_primary.setText(f"🚀 Download & Install v{new_ver}")
        self.btn_secondary.setText("Remind Me Later")

    def _on_up_to_date(self, current_ver: str):
        self.stack.setCurrentIndex(2)
        self.btn_primary.hide()
        self.btn_secondary.setText("Awesome!")

    def _on_check_error(self, err: str):
        self.stack.setCurrentIndex(4)
        self.err_details_lbl.setText(f"Error checking update:\n{err}")
        self.btn_primary.show()
        self.btn_primary.setText("Retry Check")
        self.btn_secondary.setText("Close")

    def _on_primary_click(self):
        cur_idx = self.stack.currentIndex()
        if cur_idx == 1:  # Update available -> start download
            self._start_download()
        elif cur_idx == 3:  # Download complete -> install and restart
            if self.downloaded_installer_path:
                launch_installer_and_exit(self.downloaded_installer_path)
        elif cur_idx == 4:  # Error -> retry
            self._start_check()

    def _on_secondary_click(self):
        if self.downloader and self.downloader.isRunning():
            self.downloader.cancel()
        self.reject()

    def _start_download(self):
        if not self.update_data:
            return

        # Prefer MSI package URL, fallback to EXE URL
        url = self.update_data.get("download_url") or self.update_data.get("exe_download_url")
        if not url:
            self._on_check_error("No valid download URL found in release manifest.")
            return

        self.stack.setCurrentIndex(3)
        self.btn_primary.setEnabled(False)
        self.btn_primary.setText("Downloading...")
        self.btn_secondary.setText("Cancel")

        self.downloader = UpdateDownloaderWorker(url)
        self.downloader.progress.connect(self._on_download_progress)
        self.downloader.finished.connect(self._on_download_finished)
        self.downloader.error.connect(self._on_download_error)
        self.downloader.start()

    def _on_download_progress(self, percent: int, speed: str, size_str: str):
        self.dl_progress_bar.setValue(percent)
        self.dl_stats_lbl.setText(f"{size_str} ({speed}) - {percent}%")

    def _on_download_finished(self, file_path: str):
        self.downloaded_installer_path = file_path
        self.dl_status_lbl.setText("✨ Update downloaded successfully!")
        self.dl_status_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #4ade80;")
        self.dl_progress_bar.setValue(100)
        self.dl_stats_lbl.setText("Ready to install and restart.")

        self.btn_primary.setEnabled(True)
        self.btn_primary.setText("🔄 Install & Restart Now")
        self.btn_secondary.setText("Later")

    def _on_download_error(self, err: str):
        self.stack.setCurrentIndex(4)
        self.err_details_lbl.setText(err)
        self.btn_primary.setEnabled(True)
        self.btn_primary.setText("Retry Download")
        self.btn_secondary.setText("Close")
