from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
)
from PyQt6.QtCore import Qt, pyqtProperty, pyqtSignal, QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup
from PyQt6.QtGui import QPainter, QCursor
from ui.icons import get_svg_pixmap, get_svg_icon

class FloatingIconWidget(QWidget):
    """Floating download icon with subtle ambient bobbing."""
    def __init__(self, icon_name: str, color: str = "#c084fc", size: int = 48, parent=None):
        super().__init__(parent)
        self.pixmap = get_svg_pixmap(icon_name, color=color, size=size)
        self.setFixedSize(size + 36, size + 36)
        self._y_offset = 0.0

        # Gentle floating animation
        self.anim_group = QSequentialAnimationGroup(self)
        
        up_anim = QPropertyAnimation(self, b"y_offset")
        up_anim.setDuration(1600)
        up_anim.setStartValue(0.0)
        up_anim.setEndValue(-6.0)
        up_anim.setEasingCurve(QEasingCurve.Type.InOutSine)

        down_anim = QPropertyAnimation(self, b"y_offset")
        down_anim.setDuration(1600)
        down_anim.setStartValue(-6.0)
        down_anim.setEndValue(0.0)
        down_anim.setEasingCurve(QEasingCurve.Type.InOutSine)

        self.anim_group.addAnimation(up_anim)
        self.anim_group.addAnimation(down_anim)
        self.anim_group.setLoopCount(-1)
        self.anim_group.start()

    @pyqtProperty(float)
    def y_offset(self):
        return self._y_offset

    @y_offset.setter
    def y_offset(self, val: float):
        self._y_offset = val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Draw glowing ambient halo circle behind icon
        cx = self.width() // 2
        cy = int(self.height() // 2 + self._y_offset)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(Qt.GlobalColor.transparent)
        
        # Center the pixmap
        x = (self.width() - self.pixmap.width()) // 2
        y = int((self.height() - self.pixmap.height()) // 2 + self._y_offset)
        painter.drawPixmap(x, y, self.pixmap)
        painter.end()

class EmptyStateWidget(QWidget):
    paste_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # Center card container - Obsidian aesthetic
        card = QFrame()
        card.setObjectName("EmptyStateCard")
        card.setStyleSheet("""
            QFrame#EmptyStateCard {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0f0f18, stop:1 #09090f);
                border: 1px solid #1f1f2e;
                border-radius: 20px;
                padding: 44px 50px;
                max-width: 620px;
            }
            QFrame#EmptyStateCard:hover {
                border-color: #382a52;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(18)

        # Ambient Aura Container holding the floating icon
        icon_wrapper = QFrame()
        icon_wrapper.setFixedSize(84, 84)
        icon_wrapper.setStyleSheet("""
            background-color: #160e28;
            border: 1px solid #4c1d95;
            border-radius: 42px;
        """)
        iw_layout = QVBoxLayout(icon_wrapper)
        iw_layout.setContentsMargins(0, 0, 0, 0)
        iw_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.floating_icon = FloatingIconWidget("download", color="#c084fc", size=40, parent=self)
        iw_layout.addWidget(self.floating_icon, alignment=Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(icon_wrapper, alignment=Qt.AlignmentFlag.AlignCenter)

        # Heading (Render.com typography)
        title_box = QVBoxLayout()
        title_box.setSpacing(6)
        
        heading = QLabel("Paste link to start downloading")
        heading.setStyleSheet("background: transparent; border: none; font-size: 20px; font-weight: 800; color: #f4f4f6; letter-spacing: -0.3px;")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_box.addWidget(heading)

        sub = QLabel("Fast, obsidian YouTube & media extractor with built-in 4K, 1080p, playlists & MP3 support.")
        sub.setStyleSheet("background: transparent; border: none; font-size: 13px; color: #a1a1aa; line-height: 1.5;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_box.addWidget(sub)
        card_layout.addLayout(title_box)

        # Interactive Center Action Button
        btn_paste_hero = QPushButton("  Paste from Clipboard")
        btn_paste_hero.setIcon(get_svg_icon("paste", color="#ffffff", size=16))
        btn_paste_hero.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_paste_hero.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #9333ea);
                color: #ffffff;
                font-size: 13px;
                font-weight: 700;
                padding: 10px 24px;
                border: 1px solid #a855f7;
                border-radius: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #a855f7);
                border-color: #c084fc;
            }
            QPushButton:pressed {
                background-color: #6b21a8;
            }
        """)
        btn_paste_hero.clicked.connect(lambda: self.paste_clicked.emit())
        card_layout.addWidget(btn_paste_hero, alignment=Qt.AlignmentFlag.AlignCenter)

        # Keyboard hotkey hint badge
        hotkey_lbl = QLabel("or simply press  Ctrl + V")
        hotkey_lbl.setStyleSheet("background: transparent; border: none; font-size: 11px; color: #71717a; font-weight: 500;")
        hotkey_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(hotkey_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        # Feature pills
        chips_layout = QHBoxLayout()
        chips_layout.setSpacing(8)
        chips_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        features = ["✦ 4K Ultra HD", "✦ Lossless MP3", "✦ Batch Playlists", "✦ Offline FFmpeg"]
        for feat in features:
            f_lbl = QLabel(feat)
            f_lbl.setStyleSheet("""
                background-color: #11111a;
                color: #c084fc;
                border: 1px solid #281a42;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                padding: 4px 10px;
            """)
            chips_layout.addWidget(f_lbl)

        card_layout.addLayout(chips_layout)
        main_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
