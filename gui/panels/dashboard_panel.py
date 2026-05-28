from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QListWidget, QListWidgetItem
from PySide6.QtGui import QPixmap, QImage, QColor
from PySide6.QtCore import Qt, Slot
from config import COLOR_CYAN, COLOR_GREEN, COLOR_RED, COLOR_TEXT_MUTED

class DashboardPanel(QWidget):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.init_ui()

    def init_ui(self):
        # Main Layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)

        # ----------------- Left: Video Feed Screen -----------------
        left_layout = QVBoxLayout()
        
        # Heading
        heading = QLabel("Live Feed Operations")
        heading.setObjectName("PanelHeading")
        left_layout.addWidget(heading)

        subheading = QLabel("Real-time facial scanning, classification, and matching")
        subheading.setObjectName("PanelSubheading")
        subheading.setStyleSheet("margin-bottom: 10px;")
        left_layout.addWidget(subheading)

        # Camera Frame container
        self.camera_frame = QFrame()
        self.camera_frame.setObjectName("CameraFrame")
        self.camera_frame.setMinimumSize(640, 480)
        
        frame_layout = QVBoxLayout(self.camera_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)

        # Screen label (Webcam output renders here)
        self.screen_label = QLabel("CAMERA FEED INACTIVE\nConfigure camera port or start system")
        self.screen_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screen_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLOR_TEXT_MUTED};")
        frame_layout.addWidget(self.screen_label)
        
        left_layout.addWidget(self.camera_frame, 1) # Expanding factor 1
        main_layout.addLayout(left_layout, 3) # Stretching factor 3

        # ----------------- Right: Scene Statistics -----------------
        right_layout = QVBoxLayout()
        
        # Sidebar Card
        stats_card = QFrame()
        stats_card.setObjectName("Card")
        stats_card.setFixedWidth(280)
        
        card_layout = QVBoxLayout(stats_card)
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(15)

        # Heading
        stats_title = QLabel("SCENE METRICS")
        stats_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #00F0FF; letter-spacing: 1px;")
        card_layout.addWidget(stats_title)

        # Stat: Total Faces
        self.faces_count_lbl = QLabel("Active Detections: 0")
        self.faces_count_lbl.setStyleSheet("font-size: 15px; font-weight: 600;")
        card_layout.addWidget(self.faces_count_lbl)

        # Stat: Match List
        card_layout.addWidget(QLabel("Current Targets:"))
        self.targets_list = QListWidget()
        self.targets_list.setStyleSheet("""
            QListWidget {
                background-color: #1A1A20;
                border: 1px solid #2E2E38;
                border-radius: 6px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 6px;
                color: #ECEFF1;
                border-bottom: 1px solid #252530;
            }
        """)
        self.targets_list.setFixedHeight(120)
        card_layout.addWidget(self.targets_list)

        card_layout.addWidget(QFrame()) # Visual separator

        # Live Feed Alerts/Logs (Rolling widget showing last 5 snapshots)
        alert_title = QLabel("SYSTEM RADAR ALERTS")
        alert_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #90A4AE; letter-spacing: 0.5px;")
        card_layout.addWidget(alert_title)

        self.radar_alerts = QListWidget()
        self.radar_alerts.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                background-color: #1A1A20;
                border: 1px solid #2E2E38;
                border-radius: 6px;
                margin-bottom: 8px;
                padding: 10px;
            }
        """)
        card_layout.addWidget(self.radar_alerts, 1)

        right_layout.addWidget(stats_card, 1)
        main_layout.addLayout(right_layout, 1) # Stretching factor 1
        
        # Populate radar alerts initially from DB
        self.refresh_radar_alerts()

    @Slot(QImage, list)
    def update_frame(self, q_image, detections):
        """Receives live frame from thread and displays it."""
        pixmap = QPixmap.fromImage(q_image)
        # Scale pixmap smoothly to fit label while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.screen_label.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.screen_label.setPixmap(scaled_pixmap)

        # Update metrics
        self.faces_count_lbl.setText(f"Active Detections: {len(detections)}")
        
        # Update current targets
        self.targets_list.clear()
        for d in detections:
            name = d['name']
            conf = d['confidence']
            item_text = f"● {name} ({conf:.0f}%)" if name != "Unknown" else f"○ {name}"
            item = QListWidgetItem(item_text)
            
            # Text coloring based on classification
            if name == "Unknown":
                item.setForeground(QColor(COLOR_RED))
            else:
                item.setForeground(QColor(COLOR_GREEN))
                
            self.targets_list.addItem(item)

    @Slot(str, float, str)
    def add_detection_alert(self, name, confidence, snapshot_path):
        """Invoked when thread logs a new detection event."""
        # Add alert at the top of the rolling list
        self.refresh_radar_alerts()

    def refresh_radar_alerts(self):
        """Loads latest 5 detection events from logs."""
        self.radar_alerts.clear()
        logs = self.db.get_logs()[:5]  # Get top 5 logs
        
        for log in logs:
            name = log['name']
            time_str = log['timestamp'].split(" ")[1] # Get time only
            conf = log['confidence']
            
            item = QListWidgetItem()
            
            # Custom styled widgets inside the list widget
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(2)
            
            lbl_name = QLabel(f"{name}")
            lbl_name.setStyleSheet("font-weight: bold; font-size: 13px;")
            if name == "Unknown":
                lbl_name.setStyleSheet(f"font-weight: bold; font-size: 13px; color: {COLOR_RED};")
            else:
                lbl_name.setStyleSheet(f"font-weight: bold; font-size: 13px; color: {COLOR_GREEN};")
                
            lbl_info = QLabel(f"Score: {conf:.0f}%  |  Logged at: {time_str}") if name != "Unknown" else QLabel(f"Logged at: {time_str}")
            lbl_info.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_MUTED};")
            
            layout.addWidget(lbl_name)
            layout.addWidget(lbl_info)
            
            item.setSizeHint(widget.sizeHint())
            self.radar_alerts.addItem(item)
            self.radar_alerts.setItemWidget(item, widget)

    def set_offline(self):
        """Resets panel UI when camera is turned off."""
        self.screen_label.clear()
        self.screen_label.setText("CAMERA FEED INACTIVE\nConfigure camera port or start system")
        self.faces_count_lbl.setText("Active Detections: 0")
        self.targets_list.clear()
