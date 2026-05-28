import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QLabel, QPushButton, QStackedWidget, QFrame, QButtonGroup, QMessageBox)
from PySide6.QtGui import QImage, QCloseEvent
from PySide6.QtCore import Slot, Qt

from database.db_manager import DatabaseManager
from core.recognition_thread import FaceRecognitionThread
from gui.panels.dashboard_panel import DashboardPanel
from gui.panels.database_panel import DatabasePanel
from gui.panels.logs_panel import LogsPanel
from gui.panels.settings_panel import SettingsPanel
from config import APP_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, STYLESHEET

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(950, 600)
        
        # Apply premium global stylesheet
        self.setStyleSheet(STYLESHEET)
        
        # 1. Initialize DB and Threads
        self.db = DatabaseManager()
        self.thread = FaceRecognitionThread()
        
        # 2. Build GUI Layout
        self.init_ui()
        
        # 3. Wire Signals and Slots
        self.wire_signals()
        
        # 4. Start Camera Stream automatically
        self.thread.start()

    def init_ui(self):
        # Central Widget & Main Split Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ----------------- Left Sidebar Navigation -----------------
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(240)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Brand / Logo Header
        brand_container = QWidget()
        brand_container.setFixedHeight(70)
        brand_container.setStyleSheet("border-bottom: 1px solid #2E2E38; background-color: #16161C;")
        
        brand_layout = QVBoxLayout(brand_container)
        brand_layout.setContentsMargins(20, 0, 20, 0)
        brand_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        logo_lbl = QLabel("APEX VISION")
        logo_lbl.setStyleSheet("font-weight: 900; font-size: 18px; color: #00F0FF; letter-spacing: 2px;")
        sub_lbl = QLabel("AI FACIAL BIOMETRICS")
        sub_lbl.setStyleSheet("font-size: 8px; color: #90A4AE; letter-spacing: 1px; font-weight: bold;")
        
        brand_layout.addWidget(logo_lbl)
        brand_layout.addWidget(sub_lbl)
        sidebar_layout.addWidget(brand_container)

        # Navigation Buttons Group
        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        self.btn_dashboard = QPushButton("  LIVE OPERATIONS")
        self.btn_dashboard.setObjectName("SidebarBtn")
        self.btn_dashboard.setCheckable(True)
        self.btn_dashboard.setChecked(True)
        self.btn_dashboard.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_group.addButton(self.btn_dashboard, 0)
        sidebar_layout.addWidget(self.btn_dashboard)

        self.btn_database = QPushButton("  IDENTITY REGISTRY")
        self.btn_database.setObjectName("SidebarBtn")
        self.btn_database.setCheckable(True)
        self.btn_database.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_group.addButton(self.btn_database, 1)
        sidebar_layout.addWidget(self.btn_database)

        self.btn_logs = QPushButton("  ACTIVITY LOGS")
        self.btn_logs.setObjectName("SidebarBtn")
        self.btn_logs.setCheckable(True)
        self.btn_logs.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_group.addButton(self.btn_logs, 2)
        sidebar_layout.addWidget(self.btn_logs)

        self.btn_settings = QPushButton("  SYSTEM SETTINGS")
        self.btn_settings.setObjectName("SidebarBtn")
        self.btn_settings.setCheckable(True)
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_group.addButton(self.btn_settings, 3)
        sidebar_layout.addWidget(self.btn_settings)

        sidebar_layout.addStretch(1) # Visual stretch space

        # Sidebar footer showing connection status
        status_card = QWidget()
        status_card.setStyleSheet("border-top: 1px solid #2E2E38; background-color: #14141A; padding: 15px;")
        status_card_layout = QVBoxLayout(status_card)
        status_card_layout.setContentsMargins(15, 10, 15, 10)
        
        lbl_status_title = QLabel("THREAD DIAGNOSTICS")
        lbl_status_title.setStyleSheet("font-size: 9px; color: #90A4AE; font-weight: bold; letter-spacing: 0.5px;")
        status_card_layout.addWidget(lbl_status_title)
        
        self.lbl_camera_status = QLabel("● SYSTEM SHIELD INACTIVE")
        self.lbl_camera_status.setStyleSheet("font-size: 11px; font-weight: bold; color: #FF007F;")
        status_card_layout.addWidget(self.lbl_camera_status)

        sidebar_layout.addWidget(status_card)
        main_layout.addWidget(sidebar)

        # ----------------- Right Stacked Panel Screen -----------------
        self.container_frame = QFrame()
        self.container_frame.setObjectName("PanelScreen")
        self.container_layout = QVBoxLayout(self.container_frame)
        self.container_layout.setContentsMargins(30, 25, 30, 25)

        self.stacked_widget = QStackedWidget()
        self.container_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(self.container_frame, 1)

        # ----------------- Panels Initialization -----------------
        self.dashboard_panel = DashboardPanel(self.db)
        self.database_panel = DatabasePanel(self.db)
        self.logs_panel = LogsPanel(self.db)
        self.settings_panel = SettingsPanel()

        self.stacked_widget.addWidget(self.dashboard_panel)
        self.stacked_widget.addWidget(self.database_panel)
        self.stacked_widget.addWidget(self.logs_panel)
        self.stacked_widget.addWidget(self.settings_panel)

    def wire_signals(self):
        # 1. Sidebar tab switching
        self.btn_group.idClicked.connect(self.on_sidebar_changed)

        # 2. Worker Thread outputs -> Live dashboard stream
        self.thread.frame_processed.connect(self.dashboard_panel.update_frame)
        # Wire to main window frame capture so that the DB manager can snap live pictures
        self.thread.frame_processed.connect(self.on_frame_processed)

        # 3. Dynamic database reload on thread
        self.database_panel.user_database_changed.connect(self.thread.load_known_faces)

        # 4. Calibration & Settings update in thread
        self.settings_panel.settings_applied.connect(self.thread.update_settings)

        # 5. Live alerts logging routing (Thread events update Dashboard & Logs Panels live!)
        self.thread.face_logged.connect(self.dashboard_panel.add_detection_alert)
        self.thread.face_logged.connect(self.on_face_logged_refresh_tables)

        # 6. Diagnostics status logs to sidebar footer
        self.thread.status_message.connect(self.update_status_footer)

    @Slot(int)
    def on_sidebar_changed(self, tab_id):
        """Switches the visible stacked page matching clicked sidebar ID."""
        self.stacked_widget.setCurrentIndex(tab_id)
        
        # When switching away from dashboard tab, reset offline preview text or clear threads?
        # No, let it keep streaming in background, which is extremely nice.
        # But if switching to database or logs, we reload grids/activity to stay fresh
        if tab_id == 1:
            self.database_panel.refresh_user_grid()
        elif tab_id == 2:
            self.logs_panel.refresh_logs()

    @Slot(QImage, list)
    def on_frame_processed(self, q_image, detections):
        """Routes the active live frame QImage into the database panel for on-screen snapshot registering."""
        self.database_panel.set_active_live_frame(q_image)

    @Slot(str, float, str)
    def on_face_logged_refresh_tables(self, name, confidence, path):
        """Triggers updates on the Logs table when a new face is successfully registered."""
        # Refresh logs table so it appears live
        self.logs_panel.refresh_logs()

    @Slot(str)
    def update_status_footer(self, message):
        """Updates connection and camera state diagnostics indicator in bottom sidebar panel."""
        if "Error" in message:
            self.lbl_camera_status.setText("● CAMERA ERROR")
            self.lbl_camera_status.setStyleSheet("font-size: 11px; font-weight: bold; color: #FF007F;")
        elif "stopped" in message:
            self.lbl_camera_status.setText("● FEED DISCONNECTED")
            self.lbl_camera_status.setStyleSheet("font-size: 11px; font-weight: bold; color: #90A4AE;")
            self.dashboard_panel.set_offline()
        else:
            self.lbl_camera_status.setText("● LIVE FEED SECURE")
            self.lbl_camera_status.setStyleSheet("font-size: 11px; font-weight: bold; color: #39FF14;")

    def closeEvent(self, event: QCloseEvent):
        """Interrupts threads gracefully when window closes to avoid OpenCV hangs."""
        self.thread.stop()
        event.accept()
