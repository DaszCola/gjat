import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QPushButton, QLineEdit,
    QLabel, QSizePolicy, QWidget
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QCursor, QPixmap, QPainter, QPainterPath
from ui.icons import get_svg_icon, get_svg_pixmap
from core.config import APP_VERSION

def get_brand_logo_pixmap(size: int = 30) -> QPixmap:
    """Finds and prepares the new custom program logo with smooth rounded corners."""
    if getattr(sys, 'frozen', False):
        base = Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
    else:
        base = Path(__file__).resolve().parent.parent.parent

    candidates = [
        base / "app_icon.png",
        base / "_internal" / "app_icon.png",
        Path(sys.executable).parent / "app_icon.png",
        Path.home() / "Desktop" / "the program.png"
    ]
    for p in candidates:
        if p.exists():
            pix = QPixmap(str(p))
            if not pix.isNull():
                scaled = pix.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                rounded = QPixmap(size, size)
                rounded.fill(Qt.GlobalColor.transparent)
                painter = QPainter(rounded)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                path = QPainterPath()
                path.addRoundedRect(0, 0, size, size, 7, 7)
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, scaled)
                painter.end()
                return rounded

    return get_svg_pixmap("logo", size=size)

class HeaderBar(QFrame):
    paste_clicked = pyqtSignal()
    url_submitted = pyqtSignal(str)
    smart_mode_toggled = pyqtSignal(bool)
    smart_mode_settings_requested = pyqtSignal()
    open_folder_clicked = pyqtSignal()
    update_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    clear_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HeaderBar")
        self.setFixedHeight(64)
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(10)

        # 1. Left Brand Branding (Render.com Obsidian style with custom user logo)
        brand_widget = QWidget()
        brand_layout = QHBoxLayout(brand_widget)
        brand_layout.setContentsMargins(0, 0, 8, 0)
        brand_layout.setSpacing(8)

        self.logo_lbl = QLabel()
        self.logo_lbl.setPixmap(get_brand_logo_pixmap(size=30))
        self.logo_lbl.setFixedSize(30, 30)
        brand_layout.addWidget(self.logo_lbl)

        title_box = QHBoxLayout()
        title_box.setSpacing(3)
        lbl_brand_1 = QLabel("Gjat")
        lbl_brand_1.setObjectName("BrandLogoTitle")
        lbl_brand_2 = QLabel("Downloader")
        lbl_brand_2.setObjectName("BrandLogoAccent")
        title_box.addWidget(lbl_brand_1)
        title_box.addWidget(lbl_brand_2)

        lbl_ver = QLabel(f"v{APP_VERSION}")
        lbl_ver.setObjectName("BrandBadge")
        title_box.addWidget(lbl_ver)
        brand_layout.addLayout(title_box)

        layout.addWidget(brand_widget)

        # 2. Omnibar Search / Paste Area
        omnibar_container = QFrame()
        omnibar_container.setStyleSheet("""
            QFrame {
                background-color: #0b0b12;
                border: 1px solid #20202e;
                border-radius: 9px;
            }
            QFrame:hover {
                border-color: #382c52;
            }
        """)
        omnibar_layout = QHBoxLayout(omnibar_container)
        omnibar_layout.setContentsMargins(10, 2, 4, 2)
        omnibar_layout.setSpacing(8)

        link_icon = QLabel()
        link_icon.setPixmap(get_svg_pixmap("link", color="#8b5cf6", size=16))
        link_icon.setStyleSheet("background: transparent; border: none;")
        omnibar_layout.addWidget(link_icon)

        self.url_input = QLineEdit()
        self.url_input.setObjectName("OmnibarInput")
        self.url_input.setPlaceholderText("Paste YouTube or media link... (Ctrl+V)")
        self.url_input.setStyleSheet("border: none; background: transparent; padding: 6px 0; font-size: 13px; color: #f4f4f6;")
        self.url_input.returnPressed.connect(self._on_url_enter)
        self.url_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        omnibar_layout.addWidget(self.url_input)

        # "+ Paste Link" Button inside the omnibar
        self.btn_paste = QPushButton("  Paste")
        self.btn_paste.setObjectName("PasteButton")
        self.btn_paste.setIcon(get_svg_icon("paste", color="#ffffff", size=15))
        self.btn_paste.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_paste.setToolTip("Parse URL from clipboard (Ctrl+V)")
        self.btn_paste.setFixedHeight(32)
        self.btn_paste.clicked.connect(self._on_paste_button_click)
        omnibar_layout.addWidget(self.btn_paste)

        layout.addWidget(omnibar_container, 1)

        # 3. Action Buttons Section
        # Smart Mode Toggle
        self.btn_smart = QPushButton(" Smart")
        self.btn_smart.setProperty("class", "ActionBtn")
        self.btn_smart.setCheckable(True)
        self.btn_smart.setFixedHeight(36)
        self.btn_smart.setIcon(get_svg_icon("smart_mode", color="#a1a1aa", size=15))
        self.btn_smart.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_smart.setToolTip("Smart Mode: 1-Click instant downloads using saved presets.\nRight-click to configure.")
        self.btn_smart.clicked.connect(self._on_smart_mode_click)
        self.btn_smart.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.btn_smart.customContextMenuRequested.connect(lambda: self.smart_mode_settings_requested.emit())
        layout.addWidget(self.btn_smart)

        # Open Downloads Folder
        self.btn_folder = QPushButton()
        self.btn_folder.setProperty("class", "ActionBtn")
        self.btn_folder.setFixedHeight(36)
        self.btn_folder.setFixedWidth(38)
        self.btn_folder.setIcon(get_svg_icon("folder", color="#cbd5e1", size=16))
        self.btn_folder.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_folder.setToolTip("Open Downloads Folder")
        self.btn_folder.clicked.connect(self.open_folder_clicked.emit)
        layout.addWidget(self.btn_folder)

        # Clear Completed
        self.btn_clear = QPushButton()
        self.btn_clear.setProperty("class", "ActionBtn")
        self.btn_clear.setFixedHeight(36)
        self.btn_clear.setFixedWidth(38)
        self.btn_clear.setIcon(get_svg_icon("trash", color="#94a3b8", size=16))
        self.btn_clear.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_clear.setToolTip("Clear completed downloads from list")
        self.btn_clear.clicked.connect(self.clear_clicked.emit)
        layout.addWidget(self.btn_clear)

        # Settings
        self.btn_settings = QPushButton()
        self.btn_settings.setProperty("class", "ActionBtn")
        self.btn_settings.setFixedHeight(36)
        self.btn_settings.setFixedWidth(38)
        self.btn_settings.setIcon(get_svg_icon("settings", color="#cbd5e1", size=16))
        self.btn_settings.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_settings.setToolTip("Preferences and Settings")
        self.btn_settings.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(self.btn_settings)

        # Update Button: Normal gray by default like other buttons
        self.btn_update = QPushButton(" Update")
        self.btn_update.setProperty("class", "ActionBtn")
        self.btn_update.setObjectName("UpdateBtn")
        self.btn_update.setFixedHeight(36)
        self.btn_update.setIcon(get_svg_icon("sparkle", color="#a1a1aa", size=15))
        self.btn_update.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_update.setToolTip("Check for Updates")
        self.btn_update.clicked.connect(self.update_clicked.emit)
        layout.addWidget(self.btn_update)

    def set_update_available(self, new_ver: str):
        """Highlights the update button in glowing violet when an update is available."""
        self.btn_update.setText(f" Update ({new_ver})")
        self.btn_update.setIcon(get_svg_icon("sparkle", color="#ffffff", size=15))
        self.btn_update.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #9333ea);
                border: 1px solid #c084fc;
                border-radius: 8px;
                color: #ffffff;
                font-size: 12px;
                font-weight: 700;
                padding: 0 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #a855f7);
                border-color: #e9d5ff;
            }
        """)

    def set_update_normal(self):
        """Resets the update button back to regular gray style."""
        self.btn_update.setText(" Update")
        self.btn_update.setIcon(get_svg_icon("sparkle", color="#a1a1aa", size=15))
        self.btn_update.setStyleSheet("")

    def _on_url_enter(self):
        text = self.url_input.text().strip()
        if text:
            self.url_submitted.emit(text)
            self.url_input.clear()

    def _on_paste_button_click(self):
        self.paste_clicked.emit()

    def _on_smart_mode_click(self):
        checked = self.btn_smart.isChecked()
        color = "#c084fc" if checked else "#a1a1aa"
        self.btn_smart.setIcon(get_svg_icon("smart_mode", color=color, size=15))
        self.smart_mode_toggled.emit(checked)

    def set_smart_mode_state(self, enabled: bool):
        self.btn_smart.setChecked(enabled)
        color = "#c084fc" if enabled else "#a1a1aa"
        self.btn_smart.setIcon(get_svg_icon("smart_mode", color=color, size=15))
