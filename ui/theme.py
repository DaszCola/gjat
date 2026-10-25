"""
Render.com Obsidian & Aesthetic Purple Theme for Gjat Downloader!
Palette: Deep Obsidian Black, Rich Slate Charcoal, Electric Violet & Royal Purple accents.
"""

OBSIDIAN_PURPLE_THEME = """
/* ==========================================================================
   Obsidian & Aesthetic Purple Global Style (Render.com inspired)
   ========================================================================== */

QWidget {
    background-color: #08080c;
    color: #f4f4f6;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Inter", "Helvetica Neue", sans-serif;
    font-size: 13px;
    outline: none;
}

/* Main Window & Root Containers */
QMainWindow {
    background-color: #08080c;
}

QFrame#MainContainer {
    background-color: #08080c;
}

/* ==========================================================================
   Header Bar (Render.com top navigation)
   ========================================================================== */
QFrame#HeaderBar {
    background-color: #0d0d14;
    border-bottom: 1px solid #1a1a26;
}

/* Brand Logo Text */
QLabel#BrandLogoTitle {
    font-size: 17px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.5px;
}

QLabel#BrandLogoAccent {
    font-size: 17px;
    font-weight: 800;
    color: #c084fc;
    letter-spacing: -0.5px;
}

QLabel#BrandBadge {
    background-color: #1a102e;
    color: #c084fc;
    border: 1px solid #581c87;
    border-radius: 6px;
    font-size: 10px;
    font-weight: 700;
    padding: 2px 6px;
    margin-left: 4px;
}

/* ==========================================================================
   Action & Primary Buttons
   ========================================================================== */

/* Hero / Primary Action Button */
QPushButton#PasteButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #9333ea);
    color: #ffffff;
    font-size: 13px;
    font-weight: 700;
    border-radius: 8px;
    padding: 8px 18px;
    border: 1px solid #a855f7;
}
QPushButton#PasteButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #a855f7);
    border-color: #c084fc;
}
QPushButton#PasteButton:pressed {
    background-color: #6b21a8;
    border-color: #7e22ce;
}
QPushButton#PasteButton:disabled {
    background: #191224;
    color: #6b5a82;
    border: 1px solid #281a3d;
}

/* Secondary Action Buttons (Render style icon & text buttons) */
QPushButton.ActionBtn, QPushButton#ActionBtn {
    background-color: #11111a;
    color: #e4e4e7;
    border: 1px solid #222232;
    border-radius: 8px;
    padding: 7px 13px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton.ActionBtn:hover, QPushButton#ActionBtn:hover {
    background-color: #171724;
    border-color: #3f3f58;
    color: #ffffff;
}
QPushButton.ActionBtn:pressed, QPushButton#ActionBtn:pressed {
    background-color: #0c0c14;
    border-color: #1a1a28;
}
QPushButton.ActionBtn:checked, QPushButton#ActionBtn:checked {
    background-color: #1e1136;
    border-color: #9333ea;
    color: #e9d5ff;
}

/* Standard Buttons */
QPushButton {
    background-color: #11111a;
    color: #f4f4f6;
    border: 1px solid #232334;
    border-radius: 8px;
    padding: 7px 16px;
    font-weight: 600;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #181826;
    border-color: #3b3b52;
}
QPushButton:pressed {
    background-color: #0d0d14;
    border-color: #1e1e2c;
}
QPushButton:disabled {
    background-color: #0e0e15;
    color: #52525b;
    border-color: #181822;
}

/* Primary Modal / Dialog Button */
QPushButton.PrimaryBtn, QPushButton#PrimaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #9333ea);
    color: #ffffff;
    font-weight: 700;
    border: 1px solid #a855f7;
    border-radius: 8px;
    padding: 9px 22px;
    font-size: 13px;
}
QPushButton.PrimaryBtn:hover, QPushButton#PrimaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #a855f7);
    border-color: #c084fc;
}
QPushButton.PrimaryBtn:pressed, QPushButton#PrimaryBtn:pressed {
    background: #6b21a8;
    border-color: #7e22ce;
}

/* Update Header Button glowing state (when an update is available) */
QPushButton#UpdateAvailableBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #9333ea);
    border: 1px solid #c084fc;
    border-radius: 8px;
    color: #ffffff;
    font-size: 12px;
    font-weight: 700;
    padding: 0 14px;
}
QPushButton#UpdateAvailableBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #a855f7);
    border-color: #e9d5ff;
}

/* ==========================================================================
   Line Edits & Omnibar Inputs
   ========================================================================== */
QLineEdit {
    background-color: #0c0c14;
    border: 1px solid #222232;
    border-radius: 8px;
    padding: 8px 14px;
    color: #f4f4f6;
    font-size: 13px;
    selection-background-color: #7c3aed;
    selection-color: #ffffff;
}
QLineEdit:hover {
    border-color: #333348;
}
QLineEdit:focus {
    border: 1px solid #9333ea;
    background-color: #10101b;
}

/* Omnibar in Header */
QLineEdit#OmnibarInput {
    background-color: #0a0a10;
    border: 1px solid #222234;
    border-radius: 9px;
    padding: 8px 14px;
    color: #f4f4f6;
    font-size: 13px;
}
QLineEdit#OmnibarInput:focus {
    border: 1px solid #9333ea;
    background-color: #0e0e18;
}

/* ==========================================================================
   Download Cards (Render.com Dashboard Style)
   ========================================================================== */
QFrame.DownloadCard, QFrame#DownloadCard {
    background-color: #0d0d15;
    border: 1px solid #1c1c28;
    border-radius: 12px;
}
QFrame.DownloadCard:hover, QFrame#DownloadCard:hover {
    border-color: #382c52;
    background-color: #11111c;
}

/* Slim Modern Progress Bar */
QProgressBar {
    background-color: #171724;
    border-radius: 3px;
    height: 5px;
    text-align: center;
    border: none;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #c084fc);
    border-radius: 3px;
}

/* ==========================================================================
   Scroll Bars (Ultra-thin aesthetic scrollbars)
   ========================================================================== */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #232332;
    min-height: 28px;
    border-radius: 3px;
}
QScrollBar::handle:vertical:hover {
    background: #3e3e56;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}

QScrollBar:horizontal {
    background: transparent;
    height: 6px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background: #232332;
    min-width: 28px;
    border-radius: 3px;
}
QScrollBar::handle:horizontal:hover {
    background: #3e3e56;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
}

/* ==========================================================================
   Combo Boxes & Menus
   ========================================================================== */
QComboBox {
    background-color: #0e0e16;
    border: 1px solid #232334;
    border-radius: 8px;
    padding: 7px 12px;
    color: #f4f4f6;
    font-size: 12px;
    font-weight: 500;
}
QComboBox:hover {
    border-color: #35354a;
}
QComboBox:focus {
    border-color: #9333ea;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: none;
}
QComboBox QAbstractItemView {
    background-color: #0f0f18;
    border: 1px solid #27273a;
    border-radius: 8px;
    selection-background-color: #271442;
    selection-color: #d8b4fe;
    padding: 6px;
    outline: none;
}

QMenu {
    background-color: #0e0e16;
    border: 1px solid #242436;
    border-radius: 8px;
    padding: 6px;
    color: #f4f4f6;
}
QMenu::item {
    padding: 6px 20px;
    border-radius: 6px;
}
QMenu::item:selected {
    background-color: #1e1136;
    color: #d8b4fe;
}
QMenu::separator {
    height: 1px;
    background-color: #20202e;
    margin: 4px 8px;
}

/* ==========================================================================
   Tabs
   ========================================================================== */
QTabWidget::pane {
    border: 1px solid #1e1e2c;
    background-color: #0b0b12;
    border-radius: 10px;
}
QTabBar::tab {
    background-color: #0e0e16;
    color: #a1a1aa;
    padding: 9px 24px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 600;
    font-size: 12px;
}
QTabBar::tab:selected {
    background-color: #0b0b12;
    color: #c084fc;
    border-bottom: 2px solid #a855f7;
}
QTabBar::tab:hover:!selected {
    background-color: #14141f;
    color: #f4f4f6;
}

/* ==========================================================================
   Radio Buttons & Checkboxes
   ========================================================================== */
QRadioButton {
    spacing: 9px;
    color: #e4e4e7;
    font-size: 13px;
}
QRadioButton::indicator {
    width: 17px;
    height: 17px;
    border-radius: 8.5px;
    border: 1.5px solid #353548;
    background-color: #0e0e15;
}
QRadioButton::indicator:hover {
    border-color: #a855f7;
}
QRadioButton::indicator:checked {
    border: 5px solid #9333ea;
    background-color: #ffffff;
}

QCheckBox {
    spacing: 9px;
    color: #e4e4e7;
    font-size: 13px;
}
QCheckBox::indicator {
    width: 17px;
    height: 17px;
    border-radius: 5px;
    border: 1.5px solid #353548;
    background-color: #0e0e15;
}
QCheckBox::indicator:hover {
    border-color: #a855f7;
}
QCheckBox::indicator:checked {
    background-color: #9333ea;
    border-color: #a855f7;
}

/* Spin Box */
QSpinBox {
    background-color: #0e0e16;
    border: 1px solid #232334;
    border-radius: 8px;
    padding: 6px 10px;
    color: #f4f4f6;
    font-size: 13px;
}
QSpinBox:focus {
    border-color: #9333ea;
}

/* Table / Tree / List View */
QTableWidget, QTreeWidget, QListWidget {
    background-color: #0c0c14;
    border: 1px solid #1e1e2c;
    border-radius: 8px;
    gridline-color: #171722;
    selection-background-color: #24123c;
    selection-color: #ffffff;
}
QHeaderView::section {
    background-color: #0f0f18;
    color: #a1a1aa;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #1e1e2c;
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Tooltips */
QToolTip {
    background-color: #12121c;
    color: #f4f4f6;
    border: 1px solid #2b2b3e;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}
"""

def apply_theme(app):
    app.setStyleSheet(OBSIDIAN_PURPLE_THEME)
