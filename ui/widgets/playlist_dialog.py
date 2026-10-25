import os
import re
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QLineEdit, QFileDialog, QCheckBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from ui.icons import get_svg_icon

def sanitize_folder_name(name: str) -> str:
    cleaned = re.sub(r'[\\/*?:"<>|]', '', name).strip()
    return cleaned if cleaned else "Channel_Media"

class PlaylistDialog(QDialog):
    batch_download_requested = pyqtSignal(list)

    def __init__(self, playlist_info: dict, default_download_dir: str, parent=None):
        super().__init__(parent)
        self.playlist_info = playlist_info
        self.base_download_dir = default_download_dir
        self.is_channel = playlist_info.get("is_channel", False)
        self.channel_name = playlist_info.get("channel_name") or playlist_info.get("playlist_title", "Media")
        self.safe_folder = sanitize_folder_name(self.channel_name)

        title_type = "Channel" if self.is_channel else "Playlist"
        self.setWindowTitle(f"Download {title_type}: {self.channel_name}")
        self.setFixedSize(720, 620)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 1. Header Info Card
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #0d0d15;
                border: 1px solid #1e1e2c;
                border-radius: 12px;
                padding: 14px;
            }
        """)
        h_layout = QVBoxLayout(header)
        h_layout.setSpacing(4)
        
        icon_str = "📺 Channel:" if self.is_channel else "📋 Playlist:"
        title_lbl = QLabel(f"{icon_str}  {self.playlist_info.get('playlist_title', 'Channel')}")
        title_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        h_layout.addWidget(title_lbl)

        count = self.playlist_info.get("playlist_count", 0)
        sub_type = "uploaded videos available" if self.is_channel else "items available"
        count_lbl = QLabel(f"{count} {sub_type}  •  Select items below to download")
        count_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")
        h_layout.addWidget(count_lbl)

        layout.addWidget(header)

        # 2. Search & Quick Filters Bar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Filter videos by title...")
        self.search_input.textChanged.connect(self._filter_table)
        filter_bar.addWidget(self.search_input, 1)

        self.btn_select_all = QPushButton("All")
        self.btn_select_all.setToolTip("Select all videos")
        self.btn_select_all.clicked.connect(self._select_all)
        filter_bar.addWidget(self.btn_select_all)

        self.btn_deselect_all = QPushButton("None")
        self.btn_deselect_all.setToolTip("Deselect all videos")
        self.btn_deselect_all.clicked.connect(self._deselect_all)
        filter_bar.addWidget(self.btn_deselect_all)

        self.btn_latest_10 = QPushButton("Latest 10")
        self.btn_latest_10.setToolTip("Select the first 10 latest videos")
        self.btn_latest_10.clicked.connect(lambda: self._select_range(10))
        filter_bar.addWidget(self.btn_latest_10)

        self.btn_latest_50 = QPushButton("Latest 50")
        self.btn_latest_50.setToolTip("Select the first 50 latest videos")
        self.btn_latest_50.clicked.connect(lambda: self._select_range(50))
        filter_bar.addWidget(self.btn_latest_50)

        layout.addLayout(filter_bar)

        # 3. Items Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["", "Video Title", "Duration"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setStyleSheet("QTableWidget { border: 1px solid #232535; background-color: #11121a; }")

        items = self.playlist_info.get("playlist_items", [])
        self.table.setRowCount(len(items))
        self.checkboxes = []

        for row, it in enumerate(items):
            chk = QCheckBox()
            chk.setChecked(True)
            chk.stateChanged.connect(self._update_count)
            self.checkboxes.append(chk)
            self.table.setCellWidget(row, 0, chk)

            title_item = QTableWidgetItem(f"{it['index']}. {it['title']}")
            title_item.setFlags(title_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, title_item)

            dur_item = QTableWidgetItem(it['duration'])
            dur_item.setFlags(dur_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            dur_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, dur_item)

        layout.addWidget(self.table)

        # 4. Count and Format Selection Bar
        opt_box = QHBoxLayout()
        opt_box.setSpacing(12)

        fmt_lbl = QLabel("Format & Quality:")
        fmt_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.combo_preset = QComboBox()
        self.combo_preset.addItems([
            "Video: Best 1080p / 4K MP4",
            "Video: 720p HD MP4",
            "Video: Best MKV",
            "Audio: Best 320 kbps MP3",
            "Audio: 192 kbps MP3",
            "Audio: M4A Audio",
        ])
        opt_box.addWidget(fmt_lbl)
        opt_box.addWidget(self.combo_preset)
        opt_box.addStretch()

        self.selected_count_lbl = QLabel(f"Selected: {count} / {count}")
        self.selected_count_lbl.setStyleSheet("color: #c084fc; font-weight: 700; font-size: 13px;")
        opt_box.addWidget(self.selected_count_lbl)

        layout.addLayout(opt_box)

        # 5. Organization Options: Subfolder & Ordering
        org_box = QHBoxLayout()
        org_box.setSpacing(16)

        self.chk_subfolder = QCheckBox(f"Save in subfolder: gjats\\{self.safe_folder}")
        self.chk_subfolder.setChecked(True)
        self.chk_subfolder.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.chk_subfolder.toggled.connect(self._update_folder_path)
        org_box.addWidget(self.chk_subfolder)

        self.chk_numbering = QCheckBox("Number videos sequentially (01, 02...)")
        self.chk_numbering.setChecked(True)
        self.chk_numbering.setStyleSheet("color: #94a3b8;")
        org_box.addWidget(self.chk_numbering)

        self.chk_save_thumb = QCheckBox("Save Thumbnails (.jpg)")
        self.chk_save_thumb.setStyleSheet("color: #cbd5e1;")
        org_box.addWidget(self.chk_save_thumb)
        org_box.addStretch()

        layout.addLayout(org_box)

        # 6. Destination Directory
        path_box = QHBoxLayout()
        path_lbl = QLabel("Save to:")
        path_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        
        default_target = os.path.join(self.base_download_dir, self.safe_folder)
        self.path_input = QLineEdit(default_target)
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._browse_dir)

        path_box.addWidget(path_lbl)
        path_box.addWidget(self.path_input)
        path_box.addWidget(btn_browse)
        layout.addLayout(path_box)

        # 7. Action Buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        self.btn_download = QPushButton("Download Selected")
        self.btn_download.setProperty("class", "PrimaryBtn")
        self.btn_download.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_download.clicked.connect(self._on_confirm)
        btn_box.addWidget(self.btn_download)

        layout.addLayout(btn_box)

    def _filter_table(self, query: str):
        query = query.lower().strip()
        items = self.playlist_info.get("playlist_items", [])
        for row, it in enumerate(items):
            title = it.get("title", "").lower()
            if not query or query in title:
                self.table.setRowHidden(row, False)
            else:
                self.table.setRowHidden(row, True)

    def _select_all(self):
        for chk in self.checkboxes:
            chk.setChecked(True)

    def _deselect_all(self):
        for chk in self.checkboxes:
            chk.setChecked(False)

    def _select_range(self, count: int):
        for idx, chk in enumerate(self.checkboxes):
            chk.setChecked(idx < count)

    def _update_count(self):
        cnt = sum(1 for chk in self.checkboxes if chk.isChecked())
        total = len(self.checkboxes)
        self.selected_count_lbl.setText(f"Selected: {cnt} / {total}")
        self.btn_download.setEnabled(cnt > 0)

    def _update_folder_path(self, enabled: bool):
        if enabled:
            self.path_input.setText(os.path.join(self.base_download_dir, self.safe_folder))
        else:
            self.path_input.setText(self.base_download_dir)

    def _browse_dir(self):
        f = QFileDialog.getExistingDirectory(self, "Select Download Folder", self.path_input.text())
        if f:
            self.path_input.setText(f)

    def _on_confirm(self):
        preset_idx = self.combo_preset.currentIndex()
        target_dir = self.path_input.text().strip() or self.base_download_dir
        numbering = self.chk_numbering.isChecked()
        
        items = self.playlist_info.get("playlist_items", [])
        tasks = []

        is_audio = "Audio" in self.combo_preset.currentText()
        if preset_idx == 0:
            mode, fmt, q_id, abr, desc = "video", "mp4", "bestvideo", 0, "1080p/4K MP4"
        elif preset_idx == 1:
            mode, fmt, q_id, abr, desc = "video", "mp4", "bestvideo[height<=720]", 0, "720p MP4"
        elif preset_idx == 2:
            mode, fmt, q_id, abr, desc = "video", "mkv", "bestvideo", 0, "Best MKV"
        elif preset_idx == 3:
            mode, fmt, q_id, abr, desc = "audio", "mp3", "", 320, "320k MP3"
        elif preset_idx == 4:
            mode, fmt, q_id, abr, desc = "audio", "mp3", "", 192, "192k MP3"
        else:
            mode, fmt, q_id, abr, desc = "audio", "m4a", "", 256, "Best M4A"

        for row, chk in enumerate(self.checkboxes):
            if chk.isChecked():
                it = items[row]
                item_title = it["title"]
                if numbering:
                    item_title = f"{it['index']:02d} - {item_title}"

                tasks.append({
                    "url": it["url"],
                    "title": item_title,
                    "uploader": it["uploader"],
                    "thumbnail": it["thumbnail"],
                    "duration": it["duration"],
                    "mode": mode,
                    "format": fmt,
                    "quality_format_id": q_id,
                    "audio_abr": abr,
                    "format_desc": desc,
                    "download_path": target_dir,
                    "save_thumbnail_file": self.chk_save_thumb.isChecked(),
                })

        self.batch_download_requested.emit(tasks)
        self.accept()
