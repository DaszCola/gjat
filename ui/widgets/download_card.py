import os
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QProgressBar, QSizePolicy, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QPixmap, QCursor, QPainter, QPainterPath
import urllib.request
from ui.icons import get_svg_icon

class ThumbnailWorker(QThread):
    loaded = pyqtSignal(bytes)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        if not self.url:
            return
        try:
            req = urllib.request.Request(self.url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = resp.read()
                self.loaded.emit(data)
        except Exception:
            pass

class DownloadCard(QFrame):
    cancel_clicked = pyqtSignal(str)
    remove_clicked = pyqtSignal(str)

    def __init__(self, task_info: dict, parent=None):
        super().__init__(parent)
        self.task_id = task_info.get("id", "")
        self.task_info = task_info
        self.filepath = task_info.get("filepath", "")
        self.setObjectName("DownloadCard")
        self.setProperty("class", "DownloadCard")
        self.setFixedHeight(96)
        self._init_ui()
        self._load_thumbnail(task_info.get("thumbnail", ""))

        # Smooth progress bar animator
        self.progress_anim = QPropertyAnimation(self.progress_bar, b"value")
        self.progress_anim.setEasingCurve(QEasingCurve.Type.OutQuad)

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 16, 12)
        main_layout.setSpacing(14)

        # 1. Thumbnail Container (16:9 ratio with smooth 8px corners)
        self.thumb_lbl = QLabel()
        self.thumb_lbl.setFixedSize(118, 68)
        self.thumb_lbl.setStyleSheet("""
            background-color: #0c0c14;
            border-radius: 8px;
            border: 1px solid #1e1e2c;
            color: #71717a;
            font-size: 11px;
            font-weight: 600;
        """)
        self.thumb_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_lbl.setText("Media")
        main_layout.addWidget(self.thumb_lbl)

        # 2. Middle Info & Progress Column
        center_layout = QVBoxLayout()
        center_layout.setSpacing(5)
        center_layout.setContentsMargins(0, 0, 0, 0)

        # Top Row: Title + Format Pill Badge
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self.title_lbl = QLabel(self.task_info.get("title", "Untitled Media"))
        self.title_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #f4f4f6; letter-spacing: -0.2px;")
        self.title_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top_row.addWidget(self.title_lbl)

        fmt_text = self.task_info.get("format_desc") or self.task_info.get("options", {}).get("format", "MP4").upper()
        self.fmt_badge = QLabel(fmt_text)
        self.fmt_badge.setStyleSheet("""
            background-color: #171026;
            color: #c084fc;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 5px;
            border: 1px solid #4c1d95;
        """)
        top_row.addWidget(self.fmt_badge)

        center_layout.addLayout(top_row)

        # Meta Row: Uploader and Speed / ETA stats
        meta_row = QHBoxLayout()
        meta_row.setSpacing(10)
        
        uploader = self.task_info.get("uploader", "")
        self.uploader_lbl = QLabel(uploader if uploader else "YouTube")
        self.uploader_lbl.setStyleSheet("font-size: 11px; color: #a1a1aa; font-weight: 500;")
        meta_row.addWidget(self.uploader_lbl)

        meta_row.addStretch()

        self.stats_lbl = QLabel("Queued")
        self.stats_lbl.setStyleSheet("font-size: 11px; color: #a1a1aa; font-weight: 600; font-family: monospace, sans-serif;")
        meta_row.addWidget(self.stats_lbl)

        center_layout.addLayout(meta_row)

        # Slim Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(0)
        center_layout.addWidget(self.progress_bar)

        # Status text (bottom detail)
        self.status_detail_lbl = QLabel("Preparing stream...")
        self.status_detail_lbl.setStyleSheet("font-size: 11px; color: #71717a;")
        center_layout.addWidget(self.status_detail_lbl)

        main_layout.addLayout(center_layout)

        # 3. Actions Column (Render.com icon button style)
        self.action_layout = QHBoxLayout()
        self.action_layout.setSpacing(6)

        # Play Button (Shown when finished)
        self.btn_play = QPushButton()
        self.btn_play.setProperty("class", "ActionBtn")
        self.btn_play.setFixedSize(32, 32)
        self.btn_play.setIcon(get_svg_icon("play", color="#c084fc", size=14))
        self.btn_play.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_play.setToolTip("Play file")
        self.btn_play.clicked.connect(self._open_file)
        self.btn_play.hide()
        self.action_layout.addWidget(self.btn_play)

        # Show in Folder Button (Shown when finished)
        self.btn_folder = QPushButton()
        self.btn_folder.setProperty("class", "ActionBtn")
        self.btn_folder.setFixedSize(32, 32)
        self.btn_folder.setIcon(get_svg_icon("open_folder", color="#d8b4fe", size=14))
        self.btn_folder.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_folder.setToolTip("Show in file explorer")
        self.btn_folder.clicked.connect(self._open_folder)
        self.btn_folder.hide()
        self.action_layout.addWidget(self.btn_folder)

        # Cancel / Delete Button
        self.btn_cancel = QPushButton()
        self.btn_cancel.setProperty("class", "ActionBtn")
        self.btn_cancel.setFixedSize(32, 32)
        self.btn_cancel.setIcon(get_svg_icon("cancel", color="#a1a1aa", size=14))
        self.btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cancel.setToolTip("Cancel download")
        self.btn_cancel.clicked.connect(self._on_cancel_or_delete)
        self.action_layout.addWidget(self.btn_cancel)

        main_layout.addLayout(self.action_layout)

    def _load_thumbnail(self, thumb_url: str):
        if not thumb_url:
            return
        self.worker = ThumbnailWorker(thumb_url)
        self.worker.loaded.connect(self._set_thumbnail_image)
        self.worker.start()

    def _set_thumbnail_image(self, data: bytes):
        pix = QPixmap()
        if pix.loadFromData(data):
            scaled = pix.scaled(118, 68, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            cropped = scaled.copy(0, 0, 118, 68)
            
            rounded = QPixmap(118, 68)
            rounded.fill(Qt.GlobalColor.transparent)
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(0, 0, 118, 68, 8, 8)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, cropped)
            painter.end()

            self.thumb_lbl.setPixmap(rounded)
            self.thumb_lbl.setText("")

    def update_progress(self, p: dict):
        target_pct = int(p.get("percent", 0.0))
        cur_pct = self.progress_bar.value()

        if abs(target_pct - cur_pct) >= 1:
            self.progress_anim.stop()
            self.progress_anim.setDuration(220)
            self.progress_anim.setStartValue(cur_pct)
            self.progress_anim.setEndValue(target_pct)
            self.progress_anim.start()

        speed = p.get("speed", "")
        eta = p.get("eta", "")
        status_text = p.get("status_text", "")

        if speed and eta:
            self.stats_lbl.setText(f"{speed} · ETA {eta}")
        elif speed:
            self.stats_lbl.setText(speed)
        
        if status_text:
            self.status_detail_lbl.setText(status_text)

    def set_completed(self, filepath: str):
        self.filepath = filepath
        self.progress_anim.stop()
        self.progress_bar.setValue(100)
        self.progress_bar.setStyleSheet("""
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #34d399); }
        """)
        self.stats_lbl.setText("✓ 100% Completed")
        self.stats_lbl.setStyleSheet("font-size: 11px; color: #34d399; font-weight: 700;")
        self.status_detail_lbl.setText("Download complete")
        
        # Subtle celebratory highlight
        self.setStyleSheet("QFrame#DownloadCard { border: 1px solid #10b981; }")
        QTimer.singleShot(1200, lambda: self.setStyleSheet(""))

        self.btn_play.show()
        self.btn_folder.show()
        self.btn_cancel.setToolTip("Remove from list")
        self.btn_cancel.setIcon(get_svg_icon("trash", color="#71717a", size=14))

    def set_failed(self, error: str):
        self.progress_bar.setValue(100)
        self.progress_bar.setStyleSheet("""
            QProgressBar::chunk { background-color: #f43f5e; }
        """)
        self.stats_lbl.setText("Failed")
        self.stats_lbl.setStyleSheet("font-size: 11px; color: #f43f5e; font-weight: 700;")
        self.status_detail_lbl.setText(f"Error: {error}")
        self.btn_cancel.setToolTip("Remove")
        self.btn_cancel.setIcon(get_svg_icon("trash", color="#71717a", size=14))

    def _open_file(self):
        if self.filepath and os.path.exists(self.filepath):
            try:
                os.startfile(self.filepath)
            except Exception as e:
                print(f"Error opening file: {e}")

    def _open_folder(self):
        if self.filepath and os.path.exists(self.filepath):
            try:
                subprocess.Popen(f'explorer /select,"{os.path.abspath(self.filepath)}"')
            except Exception:
                folder = os.path.dirname(self.filepath)
                os.startfile(folder)
        else:
            default_dir = self.task_info.get("options", {}).get("download_path", "")
            if default_dir and os.path.exists(default_dir):
                os.startfile(default_dir)

    def _on_cancel_or_delete(self):
        status = self.task_info.get("status", "")
        if status in ("completed", "error", "cancelled"):
            self.remove_clicked.emit(self.task_id)
        else:
            self.cancel_clicked.emit(self.task_id)
