from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QSlider, QComboBox, QFrame, QMessageBox)
from PySide6.QtCore import Qt, Slot, Signal
from config import DEFAULT_TOLERANCE, DEFAULT_CAMERA_INDEX, DEFAULT_FRAME_SKIP

class SettingsPanel(QWidget):
    # Signals
    settings_applied = Signal(float, int, int) # tolerance, camera_index, frame_skip

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Local settings variables
        self.tolerance = DEFAULT_TOLERANCE
        self.camera_index = DEFAULT_CAMERA_INDEX
        self.frame_skip = DEFAULT_FRAME_SKIP
        
        self.init_ui()

    def init_ui(self):
        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)

        # ----------------- Top Header Section -----------------
        title_layout = QVBoxLayout()
        heading = QLabel("Calibration & Settings")
        heading.setObjectName("PanelHeading")
        title_layout.addWidget(heading)

        subheading = QLabel("Tune computer vision intelligence and system parameters")
        subheading.setObjectName("PanelSubheading")
        title_layout.addWidget(subheading)
        main_layout.addLayout(title_layout)

        # ----------------- Settings Group Container -----------------
        settings_card = QFrame()
        settings_card.setObjectName("Card")
        settings_card_layout = QVBoxLayout(settings_card)
        settings_card_layout.setContentsMargins(20, 20, 20, 20)
        settings_card_layout.setSpacing(20)

        # 1. Match Sensitivity (Tolerance) Slider
        tolerance_layout = QVBoxLayout()
        tolerance_header = QHBoxLayout()
        
        lbl_tol_title = QLabel("Matching Sensitivity (Tolerance)")
        lbl_tol_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        tolerance_header.addWidget(lbl_tol_title)
        
        # Label that shows float value (e.g., 0.60)
        self.lbl_tolerance_val = QLabel(f"{self.tolerance:.2f}")
        self.lbl_tolerance_val.setStyleSheet("font-weight: bold; font-size: 14px; color: #00F0FF;")
        tolerance_header.addWidget(self.lbl_tolerance_val, 0, Qt.AlignmentFlag.AlignRight)
        tolerance_layout.addLayout(tolerance_header)

        # Explain slider values
        lbl_tol_desc = QLabel("Lower tolerance is more strict (prevents false matches but may miss faces).\nHigher tolerance is more lenient (easier match, but increases false classification risk).")
        lbl_tol_desc.setStyleSheet("font-size: 11px; color: #90A4AE; margin-bottom: 5px;")
        tolerance_layout.addWidget(lbl_tol_desc)

        # Slider config (Qt slider handles integers, so we multiply by 100: e.g., 30 to 80 corresponds to 0.3 to 0.8)
        self.tol_slider = QSlider(Qt.Orientation.Horizontal)
        self.tol_slider.setMinimum(20)  # 0.2
        self.tol_slider.setMaximum(80)  # 0.8
        self.tol_slider.setValue(int(self.tolerance * 100))
        self.tol_slider.valueChanged.connect(self.on_slider_value_changed)
        
        tolerance_layout.addWidget(self.tol_slider)
        settings_card_layout.addLayout(tolerance_layout)

        settings_card_layout.addWidget(QFrame()) # Visual separator

        # 2. Camera Input Index Selection
        camera_layout = QVBoxLayout()
        lbl_cam_title = QLabel("Hardware Video Input Capture")
        lbl_cam_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        camera_layout.addWidget(lbl_cam_title)

        lbl_cam_desc = QLabel("Select active physical camera port index attached to your terminal.")
        lbl_cam_desc.setStyleSheet("font-size: 11px; color: #90A4AE; margin-bottom: 5px;")
        camera_layout.addWidget(lbl_cam_desc)

        self.cam_combo = QComboBox()
        self.cam_combo.addItem("Camera Port Index: 0 (Default / Primary Integrated)", 0)
        self.cam_combo.addItem("Camera Port Index: 1 (Secondary / External USB)", 1)
        self.cam_combo.addItem("Camera Port Index: 2 (Third-party Captures)", 2)
        self.cam_combo.addItem("Camera Port Index: 3", 3)
        self.cam_combo.setCurrentIndex(self.camera_index)
        
        camera_layout.addWidget(self.cam_combo)
        settings_card_layout.addLayout(camera_layout)

        settings_card_layout.addWidget(QFrame()) # Visual separator

        # 3. CPU Optimization (Frame skipping)
        perf_layout = QVBoxLayout()
        lbl_perf_title = QLabel("CV Performance & Optimization")
        lbl_perf_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        perf_layout.addWidget(lbl_perf_title)

        lbl_perf_desc = QLabel("Control face detection compute intervals to save CPU resources.\nFor example, processing every 2nd frame drastically reduces overhead with minimal UI lag.")
        lbl_perf_desc.setStyleSheet("font-size: 11px; color: #90A4AE; margin-bottom: 5px;")
        perf_layout.addWidget(lbl_perf_desc)

        self.perf_combo = QComboBox()
        self.perf_combo.addItem("Process 100% of frames (Maximum precision - Very High CPU usage)", 1)
        self.perf_combo.addItem("Process 50% of frames - Every 2nd frame (Balanced - Recommended)", 2)
        self.perf_combo.addItem("Process 33% of frames - Every 3rd frame (High Performance - Low CPU)", 3)
        self.perf_combo.addItem("Process 25% of frames - Every 4th frame (Ultra Performance - Low CPU)", 4)
        self.perf_combo.setCurrentIndex(self.frame_skip - 1)
        
        perf_layout.addWidget(self.perf_combo)
        settings_card_layout.addLayout(perf_layout)

        main_layout.addWidget(settings_card)

        # ----------------- Save and Restore Buttons -----------------
        footer_layout = QHBoxLayout()
        
        self.btn_default = QPushButton("Restore Factory Defaults")
        self.btn_default.clicked.connect(self.restore_defaults)
        
        self.btn_apply = QPushButton("Apply Calibration Settings")
        self.btn_apply.setObjectName("AccentButton")
        self.btn_apply.clicked.connect(self.apply_settings)
        
        footer_layout.addWidget(self.btn_default)
        footer_layout.addStretch()
        footer_layout.addWidget(self.btn_apply)
        
        main_layout.addLayout(footer_layout)
        main_layout.addStretch(1)

    def on_slider_value_changed(self, value):
        """Dynamic slider text update."""
        val = value / 100.0
        self.lbl_tolerance_val.setText(f"{val:.2f}")

    def apply_settings(self):
        """Applies configured settings and emits settings_applied signal."""
        self.tolerance = self.tol_slider.value() / 100.0
        self.camera_index = self.cam_combo.currentData()
        self.frame_skip = self.perf_combo.currentData()
        
        # Emit signal to thread
        self.settings_applied.emit(self.tolerance, self.camera_index, self.frame_skip)
        
        QMessageBox.information(
            self, "Configuration Saved", 
            f"Settings successfully updated:\n"
            f"• Matching Sensitivity (Tolerance): {self.tolerance:.2f}\n"
            f"• Selected Camera Port: {self.camera_index}\n"
            f"• Processing Interval: Every {self.frame_skip} frames"
        )

    def restore_defaults(self):
        """Restores widgets back to config default states."""
        self.tol_slider.setValue(int(DEFAULT_TOLERANCE * 100))
        self.lbl_tolerance_val.setText(f"{DEFAULT_TOLERANCE:.2f}")
        
        # Camera index
        cam_idx = self.cam_combo.findData(DEFAULT_CAMERA_INDEX)
        if cam_idx != -1:
            self.cam_combo.setCurrentIndex(cam_idx)
            
        # Frame skip
        perf_idx = self.perf_combo.findData(DEFAULT_FRAME_SKIP)
        if perf_idx != -1:
            self.perf_combo.setCurrentIndex(perf_idx)

        QMessageBox.information(self, "Defaults Restored", "Calibration values restored to hardware recommended defaults. Click 'Apply Settings' to activate.")
