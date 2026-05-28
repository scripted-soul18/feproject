import os

# Application Window Settings
APP_TITLE = "Apex Face Recognition Dashboard"
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 700

# Base Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
REGISTERED_DIR = os.path.join(DATA_DIR, "registered")
SNAPSHOTS_DIR = os.path.join(DATA_DIR, "snapshots")
DB_PATH = os.path.join(DATA_DIR, "faces.db")

# Create directories if they do not exist
os.makedirs(REGISTERED_DIR, exist_ok=True)
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

# Default Face Recognition Settings
DEFAULT_TOLERANCE = 0.6  # Default distance threshold (lower is stricter)
DEFAULT_CAMERA_INDEX = 0
DEFAULT_FRAME_SKIP = 2   # Process every Nth frame for performance

# Styled Colors (Palette)
COLOR_BG_DARK = "#121212"
COLOR_BG_PANEL = "#1E1E24"
COLOR_BORDER = "#2E2E38"
COLOR_CYAN = "#00F0FF"
COLOR_GREEN = "#39FF14"
COLOR_RED = "#FF007F"
COLOR_TEXT_MAIN = "#ECEFF1"
COLOR_TEXT_MUTED = "#90A4AE"

# Premium Dark Glassmorphism QSS Stylesheet
STYLESHEET = """
QMainWindow {
    background-color: #121212;
}

QWidget {
    font-family: 'Segoe UI', 'Outfit', 'Inter', sans-serif;
    color: #ECEFF1;
    font-size: 13px;
}

/* Sidebar Navigation */
QFrame#Sidebar {
    background-color: #1A1A20;
    border-right: 1px solid #2E2E38;
}

QPushButton#SidebarBtn {
    background-color: transparent;
    border: none;
    border-left: 3px solid transparent;
    padding: 12px 20px;
    text-align: left;
    font-weight: bold;
    font-size: 14px;
    color: #90A4AE;
    border-radius: 0px;
}

QPushButton#SidebarBtn:hover {
    background-color: #252530;
    color: #00F0FF;
}

QPushButton#SidebarBtn:checked {
    background-color: #2A2A38;
    color: #00F0FF;
    border-left: 3px solid #00F0FF;
}

/* Base Panel Screens */
QFrame#PanelScreen {
    background-color: #121212;
}

/* Styled Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #181820;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #3E3E4F;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #00F0FF;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}

/* Buttons */
QPushButton {
    background-color: #1E1E24;
    border: 1px solid #2E2E38;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
    color: #ECEFF1;
}

QPushButton:hover {
    background-color: #2D2D38;
    border-color: #00F0FF;
}

QPushButton:pressed {
    background-color: #00F0FF;
    color: #121212;
}

QPushButton#AccentButton {
    background-color: #00F0FF;
    color: #121212;
    border: none;
}

QPushButton#AccentButton:hover {
    background-color: #33F3FF;
    border: 1px solid #ECEFF1;
}

QPushButton#AccentButton:pressed {
    background-color: #00BCC6;
}

QPushButton#DangerButton {
    background-color: #5C1A2E;
    border: 1px solid #FF007F;
    color: #FFB3D1;
}

QPushButton#DangerButton:hover {
    background-color: #7E1C38;
    border-color: #FF3399;
}

/* Line Edits & ComboBoxes */
QLineEdit {
    background-color: #1A1A20;
    border: 1px solid #2E2E38;
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: #00F0FF;
    selection-color: #121212;
}

QLineEdit:focus {
    border: 1px solid #00F0FF;
}

QComboBox {
    background-color: #1A1A20;
    border: 1px solid #2E2E38;
    border-radius: 6px;
    padding: 8px 12px;
}

QComboBox:focus {
    border: 1px solid #00F0FF;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

/* Slider */
QSlider::groove:horizontal {
    border: 1px solid #2E2E38;
    height: 6px;
    background: #1A1A20;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #00F0FF;
    border: none;
    width: 14px;
    margin: -4px 0;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background: #33F3FF;
    box-shadow: 0 0 8px #00F0FF;
}

/* Tables */
QTableWidget {
    background-color: #1E1E24;
    border: 1px solid #2E2E38;
    gridline-color: #2E2E38;
    border-radius: 8px;
}

QTableWidget::item {
    padding: 10px;
    border-bottom: 1px solid #2E2E38;
}

QTableWidget::item:selected {
    background-color: #2D2D38;
    color: #00F0FF;
}

QHeaderView::section {
    background-color: #181820;
    color: #90A4AE;
    padding: 10px;
    font-weight: bold;
    border: none;
    border-bottom: 1px solid #2E2E38;
}

/* Headings and Cards */
QLabel#PanelHeading {
    font-size: 24px;
    font-weight: bold;
    color: #ECEFF1;
    margin-bottom: 10px;
}

QLabel#PanelSubheading {
    font-size: 13px;
    color: #90A4AE;
}

QFrame#Card {
    background-color: #1E1E24;
    border: 1px solid #2E2E38;
    border-radius: 10px;
    padding: 15px;
}

QFrame#CameraFrame {
    border: 2px solid #2E2E38;
    border-radius: 12px;
    background-color: #08080C;
    overflow: hidden;
}

/* User Profile Cards in Grid */
QFrame#UserCard {
    background-color: #1A1A20;
    border: 1px solid #2E2E38;
    border-radius: 8px;
}

QFrame#UserCard:hover {
    border-color: #00F0FF;
}
"""
