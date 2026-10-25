import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QRadioButton, QButtonGroup, QComboBox,
    QCheckBox, QLineEdit, QFileDialog, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap, QCursor, QPainter, QPainterPath
import urllib.request
from ui.icons import get_svg_icon, get_svg_pixmap

class ThumbnailLoader(QThread):
    loaded = pyqtSignal(bytes)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        if not self.url:
            return
        try:
            req = urllib.request.Request(self.url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = resp.read()
                self.loaded.emit(data)
        except Exception:
            pass

class FormatDialog(QDialog):
    download_requested = pyqtSignal(dict)

    def __init__(self, info: dict, default_download_dir: str, parent=None):
        super().__init__(parent)
        self.info = info
        self.download_dir = default_download_dir
        self.setWindowTitle("Download Clip")
        self.setFixedSize(580, 580)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self._init_ui()
        self._load_thumb()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 1. Header with Thumbnail + Title + Info
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background-color: #0d0d15;
                border: 1px solid #1c1c28;
                border-radius: 12px;
                padding: 10px;
            }
        """)
        h_layout = QHBoxLayout(header_card)
        h_layout.setContentsMargins(10, 10, 10, 10)
        h_layout.setSpacing(14)

        self.thumb_lbl = QLabel()
        self.thumb_lbl.setFixedSize(120, 68)
        self.thumb_lbl.setStyleSheet("background-color: #08080c; border-radius: 8px; border: 1px solid #1e1e2c; color: #71717a;")
        self.thumb_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_lbl.setText("Preview")
        h_layout.addWidget(self.thumb_lbl)

        info_col = QVBoxLayout()
        info_col.setSpacing(4)
        
        self.title_lbl = QLabel(self.info.get("title", "Unknown Title"))
        self.title_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #f8fafc;")
        self.title_lbl.setWordWrap(True)
        info_col.addWidget(self.title_lbl)

        meta_lbl = QLabel(f"{self.info.get('uploader', 'Unknown')}  •  Duration: {self.info.get('duration_str', 'Unknown')}")
        meta_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")
        info_col.addWidget(meta_lbl)

        h_layout.addLayout(info_col)
        layout.addWidget(header_card)

        # 2. Tabs: [ Download Video ]  |  [ Extract Audio ]
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Tab 1: Video
        video_tab = QWidget()
        v_layout = QVBoxLayout(video_tab)
        v_layout.setContentsMargins(14, 14, 14, 14)
        v_layout.setSpacing(12)

        # Format Dropdown (MP4, MKV)
        fmt_row = QHBoxLayout()
        fmt_lbl = QLabel("Format:")
        fmt_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.combo_video_fmt = QComboBox()
        self.combo_video_fmt.addItems(["MP4", "MKV", "WebM"])
        self.combo_video_fmt.setFixedWidth(110)
        fmt_row.addWidget(fmt_lbl)
        fmt_row.addWidget(self.combo_video_fmt)
        fmt_row.addStretch()
        v_layout.addLayout(fmt_row)

        # Video Qualities List inside a scroll area
        qual_lbl = QLabel("Select Resolution:")
        qual_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        v_layout.addWidget(qual_lbl)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #1c1c28; border-radius: 8px; background-color: #0b0b12; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(10, 8, 10, 8)
        scroll_layout.setSpacing(8)

        self.video_group = QButtonGroup(self)
        self.video_options = self.info.get("video_options", [])

        if not self.video_options:
            # Fallback if no specific parsed options
            rb = QRadioButton("Best Available Quality")
            rb.setChecked(True)
            self.video_group.addButton(rb, 0)
            scroll_layout.addWidget(rb)
        else:
            for idx, opt in enumerate(self.video_options):
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)

                rb = QRadioButton(opt["label"])
                if idx == 0:
                    rb.setChecked(True)
                self.video_group.addButton(rb, idx)
                row_layout.addWidget(rb)

                row_layout.addStretch()

                size_lbl = QLabel(opt["size_str"])
                size_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 500;")
                row_layout.addWidget(size_lbl)

                scroll_layout.addWidget(row_widget)

        scroll.setWidget(scroll_content)
        v_layout.addWidget(scroll)

        # Subtitles row
        sub_row = QHBoxLayout()
        self.chk_subtitles = QCheckBox("Download Subtitles")
        self.combo_subtitles = QComboBox()
        self.combo_subtitles.setEnabled(False)
        self.combo_subtitles.addItems(self.info.get("subtitles", ["None"]))
        self.chk_subtitles.toggled.connect(self.combo_subtitles.setEnabled)

        self.chk_embed_sub = QCheckBox("Embed into video")
        self.chk_embed_sub.setChecked(True)
        self.chk_embed_sub.setEnabled(False)
        self.chk_subtitles.toggled.connect(self.chk_embed_sub.setEnabled)

        sub_row.addWidget(self.chk_subtitles)
        sub_row.addWidget(self.combo_subtitles)
        sub_row.addWidget(self.chk_embed_sub)
        v_layout.addLayout(sub_row)

        self.tabs.addTab(video_tab, "Download Video")

        # Tab 2: Audio
        audio_tab = QWidget()
        a_layout = QVBoxLayout(audio_tab)
        a_layout.setContentsMargins(14, 14, 14, 14)
        a_layout.setSpacing(14)

        a_fmt_row = QHBoxLayout()
        a_fmt_lbl = QLabel("Audio Format:")
        a_fmt_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.combo_audio_fmt = QComboBox()
        self.combo_audio_fmt.addItems(["MP3", "M4A", "FLAC", "WAV", "OPUS"])
        self.combo_audio_fmt.setFixedWidth(110)
        a_fmt_row.addWidget(a_fmt_lbl)
        a_fmt_row.addWidget(self.combo_audio_fmt)
        a_fmt_row.addStretch()
        a_layout.addLayout(a_fmt_row)

        a_qual_lbl = QLabel("Audio Bitrate:")
        a_qual_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        a_layout.addWidget(a_qual_lbl)

        self.audio_group = QButtonGroup(self)
        self.audio_options = self.info.get("audio_options", [])
        for idx, opt in enumerate(self.audio_options):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)

            rb = QRadioButton(opt["label"])
            if idx == 0:
                rb.setChecked(True)
            self.audio_group.addButton(rb, idx)
            row_layout.addWidget(rb)

            row_layout.addStretch()

            size_lbl = QLabel(opt["size_str"])
            size_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 500;")
            row_layout.addWidget(size_lbl)

            a_layout.addWidget(row_widget)

        a_layout.addStretch()
        self.tabs.addTab(audio_tab, "Extract Audio")

        # Thumbnail & Extra Options
        extra_row = QHBoxLayout()
        self.chk_save_thumb = QCheckBox("Save Thumbnail image (.jpg)")
        self.chk_save_thumb.setStyleSheet("font-weight: 500; color: #cbd5e1;")
        extra_row.addWidget(self.chk_save_thumb)
        extra_row.addStretch()
        layout.addLayout(extra_row)

        # 3. Output Path
        path_box = QHBoxLayout()
        path_lbl = QLabel("Save to:")
        path_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.path_input = QLineEdit(self.download_dir)
        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.clicked.connect(self._browse_dir)

        path_box.addWidget(path_lbl)
        path_box.addWidget(self.path_input)
        path_box.addWidget(self.btn_browse)
        layout.addLayout(path_box)

        # 4. Dialog Buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)
        btn_box.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancel)

        self.btn_download = QPushButton("Download")
        self.btn_download.setProperty("class", "PrimaryBtn")
        self.btn_download.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_download.clicked.connect(self._on_download_confirm)
        btn_box.addWidget(self.btn_download)

        layout.addLayout(btn_box)

    def _load_thumb(self):
        thumb_url = self.info.get("thumbnail")
        if thumb_url:
            self.worker = ThumbnailLoader(thumb_url)
            self.worker.loaded.connect(self._set_thumb)
            self.worker.start()

    def _set_thumb(self, data: bytes):
        pix = QPixmap()
        if pix.loadFromData(data):
            scaled = pix.scaled(120, 68, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            cropped = scaled.copy(0, 0, 120, 68)
            rounded = QPixmap(120, 68)
            rounded.fill(Qt.GlobalColor.transparent)
            p = QPainter(rounded)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(0, 0, 120, 68, 8, 8)
            p.setClipPath(path)
            p.drawPixmap(0, 0, cropped)
            p.end()
            self.thumb_lbl.setPixmap(rounded)
            self.thumb_lbl.setText("")

    def _browse_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder", self.path_input.text())
        if folder:
            self.path_input.setText(folder)

    def _on_download_confirm(self):
        is_video = (self.tabs.currentIndex() == 0)
        target_dir = self.path_input.text().strip() or self.download_dir

        if is_video:
            selected_idx = self.video_group.checkedId()
            opt = self.video_options[selected_idx] if (0 <= selected_idx < len(self.video_options)) else None
            fmt_id = opt["format_id"] if opt else "best"
            fmt_desc = f"{opt['height']}p{opt['fps']} {self.combo_video_fmt.currentText()}" if opt else f"Best {self.combo_video_fmt.currentText()}"

            opts = {
                "url": self.info["url"],
                "title": self.info["title"],
                "uploader": self.info["uploader"],
                "thumbnail": self.info.get("thumbnail", ""),
                "duration": self.info.get("duration_str", ""),
                "mode": "video",
                "format": self.combo_video_fmt.currentText().lower(),
                "quality_format_id": fmt_id,
                "format_desc": fmt_desc,
                "download_path": target_dir,
                "download_subtitles": self.chk_subtitles.isChecked(),
                "subtitles_lang": self.combo_subtitles.currentText() if self.chk_subtitles.isChecked() else "",
                "embed_subtitles": self.chk_embed_sub.isChecked() if self.chk_subtitles.isChecked() else False,
                "save_thumbnail_file": self.chk_save_thumb.isChecked(),
            }
        else:
            selected_idx = self.audio_group.checkedId()
            opt = self.audio_options[selected_idx] if (0 <= selected_idx < len(self.audio_options)) else None
            abr = opt["abr"] if opt else 320
            fmt_desc = f"{abr}kbps {self.combo_audio_fmt.currentText()}"

            opts = {
                "url": self.info["url"],
                "title": self.info["title"],
                "uploader": self.info["uploader"],
                "thumbnail": self.info.get("thumbnail", ""),
                "duration": self.info.get("duration_str", ""),
                "mode": "audio",
                "format": self.combo_audio_fmt.currentText().lower(),
                "audio_abr": abr,
                "format_desc": fmt_desc,
                "download_path": target_dir,
                "save_thumbnail_file": self.chk_save_thumb.isChecked(),
            }

        self.download_requested.emit(opts)
        self.accept()
