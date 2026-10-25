from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QComboBox, QLineEdit, QFileDialog, QFrame, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from ui.icons import get_svg_icon

class SmartModeDialog(QDialog):
    smart_mode_saved = pyqtSignal(dict)

    def __init__(self, current_settings: dict, parent=None):
        super().__init__(parent)
        self.settings = current_settings.copy()
        self.setWindowTitle("Smart Mode Settings")
        self.setFixedSize(480, 440)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Info card
        info_card = QFrame()
        info_card.setStyleSheet("""
            QFrame {
                background-color: #0d0d15;
                border: 1px solid #1e1e2c;
                border-radius: 12px;
                padding: 14px;
            }
        """)
        ic_layout = QVBoxLayout(info_card)
        ic_layout.setSpacing(6)

        title = QLabel("⚡ Smart Mode")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #c084fc;")
        ic_layout.addWidget(title)

        desc = QLabel("Download videos or audio in 1-click using your favorite preset without showing format prompts.")
        desc.setStyleSheet("font-size: 12px; color: #a1a1aa; line-height: 1.4;")
        desc.setWordWrap(True)
        ic_layout.addWidget(desc)

        layout.addWidget(info_card)

        # Enable checkbox
        self.chk_enable = QCheckBox("Enable Smart Mode")
        self.chk_enable.setStyleSheet("font-weight: 700; font-size: 13px; color: #f4f4f6;")
        self.chk_enable.setChecked(self.settings.get("enabled", False))
        layout.addWidget(self.chk_enable)

        # Format & Quality Group
        settings_frame = QFrame()
        settings_frame.setStyleSheet("""
            QFrame {
                background-color: #0c0c14;
                border: 1px solid #1e1e2c;
                border-radius: 12px;
                padding: 14px;
            }
        """)
        sf_layout = QVBoxLayout(settings_frame)
        sf_layout.setSpacing(12)

        # Type: Video vs Audio
        type_row = QHBoxLayout()
        type_lbl = QLabel("Type:")
        type_lbl.setFixedWidth(80)
        type_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.rb_video = QRadioButton("Video")
        self.rb_audio = QRadioButton("Audio")
        if self.settings.get("mode") == "audio":
            self.rb_audio.setChecked(True)
        else:
            self.rb_video.setChecked(True)
        
        self.type_group = QButtonGroup(self)
        self.type_group.addButton(self.rb_video)
        self.type_group.addButton(self.rb_audio)
        self.rb_video.toggled.connect(self._on_type_changed)

        type_row.addWidget(type_lbl)
        type_row.addWidget(self.rb_video)
        type_row.addWidget(self.rb_audio)
        type_row.addStretch()
        sf_layout.addLayout(type_row)

        # Format combo
        fmt_row = QHBoxLayout()
        fmt_lbl = QLabel("Format:")
        fmt_lbl.setFixedWidth(80)
        fmt_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.combo_fmt = QComboBox()
        fmt_row.addWidget(fmt_lbl)
        fmt_row.addWidget(self.combo_fmt)
        sf_layout.addLayout(fmt_row)

        # Quality combo
        qual_row = QHBoxLayout()
        qual_lbl = QLabel("Quality:")
        qual_lbl.setFixedWidth(80)
        qual_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.combo_qual = QComboBox()
        qual_row.addWidget(qual_lbl)
        qual_row.addWidget(self.combo_qual)
        sf_layout.addLayout(qual_row)

        # Output Folder
        dir_row = QHBoxLayout()
        dir_lbl = QLabel("Directory:")
        dir_lbl.setFixedWidth(80)
        dir_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.dir_input = QLineEdit(self.settings.get("download_path", ""))
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._browse)

        dir_row.addWidget(dir_lbl)
        dir_row.addWidget(self.dir_input)
        dir_row.addWidget(btn_browse)
        sf_layout.addLayout(dir_row)

        layout.addWidget(settings_frame)

        # Bottom buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_save = QPushButton("Save Settings")
        btn_save.setProperty("class", "PrimaryBtn")
        btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_save.clicked.connect(self._save)
        btn_box.addWidget(btn_save)

        layout.addLayout(btn_box)

        self._on_type_changed()

    def _on_type_changed(self):
        is_video = self.rb_video.isChecked()
        self.combo_fmt.clear()
        self.combo_qual.clear()

        if is_video:
            self.combo_fmt.addItems(["MP4", "MKV", "WebM"])
            self.combo_qual.addItems(["Best Available (4K/1080p)", "1080p Full HD", "720p HD", "480p SD"])
        else:
            self.combo_fmt.addItems(["MP3", "M4A", "FLAC", "WAV", "OPUS"])
            self.combo_qual.addItems(["320 kbps (Original/Best)", "256 kbps (High)", "192 kbps (Standard)", "128 kbps (Normal)"])

    def _browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder", self.dir_input.text())
        if folder:
            self.dir_input.setText(folder)

    def _save(self):
        is_video = self.rb_video.isChecked()
        mode = "video" if is_video else "audio"
        fmt = self.combo_fmt.currentText().lower()
        
        if is_video:
            qual_idx = self.combo_qual.currentIndex()
            if qual_idx == 0:
                qual = "best"
            elif qual_idx == 1:
                qual = "1080"
            elif qual_idx == 2:
                qual = "720"
            else:
                qual = "480"
        else:
            abr_idx = self.combo_qual.currentIndex()
            qual = [320, 256, 192, 128][abr_idx]

        res = {
            "enabled": self.chk_enable.isChecked(),
            "mode": mode,
            "format": fmt,
            "quality": qual,
            "download_path": self.dir_input.text().strip()
        }
        self.smart_mode_saved.emit(res)
        self.accept()
