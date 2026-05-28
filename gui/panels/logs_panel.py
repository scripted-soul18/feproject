import os
import csv
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, QFrame, 
                             QFileDialog, QMessageBox, QHeaderView, QDialog)
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtCore import Qt, Slot
from config import COLOR_CYAN, COLOR_RED, COLOR_GREEN, COLOR_TEXT_MUTED

class ImagePreviewDialog(QDialog):
    """Sleek image viewer to preview full logs snapshots."""
    def __init__(self, image_path, title_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Detection Snapshot - {title_text}")
        self.setStyleSheet("background-color: #08080C; color: #ECEFF1;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        img_label = QLabel()
        img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            # Scale to fit standard screen nicely
            img_label.setPixmap(pixmap.scaled(720, 540, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            img_label.setText("SNAPSHOT FILE NOT FOUND")
            img_label.setStyleSheet("color: #FF007F; font-size: 16px; font-weight: bold;")
            
        layout.addWidget(img_label)
        
        btn_close = QPushButton("Close Viewer")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)


class LogsPanel(QWidget):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.init_ui()

    def init_ui(self):
        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)

        # ----------------- Top Header Section -----------------
        header_layout = QHBoxLayout()
        
        title_layout = QVBoxLayout()
        heading = QLabel("System Activity Logs")
        heading.setObjectName("PanelHeading")
        title_layout.addWidget(heading)

        subheading = QLabel("Review past identification records and sensor archives")
        subheading.setObjectName("PanelSubheading")
        title_layout.addWidget(subheading)
        header_layout.addLayout(title_layout)

        # Export & Clear Buttons
        btn_layout = QHBoxLayout()
        self.btn_export = QPushButton("Export to CSV")
        self.btn_export.clicked.connect(self.export_to_csv)
        
        self.btn_clear = QPushButton("Clear Logs")
        self.btn_clear.setObjectName("DangerButton")
        self.btn_clear.clicked.connect(self.clear_logs)
        
        btn_layout.addWidget(self.btn_export)
        btn_layout.addWidget(self.btn_clear)
        header_layout.addLayout(btn_layout)
        
        main_layout.addLayout(header_layout)

        # ----------------- Filter & Search Bar -----------------
        search_card = QFrame()
        search_card.setObjectName("Card")
        search_card_layout = QHBoxLayout(search_card)
        search_card_layout.setContentsMargins(10, 10, 10, 10)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search logs by name (e.g. Unknown, Jane Doe)...")
        self.search_bar.textChanged.connect(self.filter_logs)
        search_card_layout.addWidget(self.search_bar)
        
        main_layout.addWidget(search_card)

        # ----------------- Logs Table -----------------
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Snapshot", "Name Identity", "Timestamp", "Match Accuracy"])
        
        # Table configuration
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Stretch columns
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Snapshot
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)          # Name
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)          # Timestamp
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # Accuracy

        # Connect double click to preview image
        self.table.doubleClicked.connect(self.show_snapshot_preview)

        main_layout.addWidget(self.table, 1)

        # Initial Load
        self.refresh_logs()

    @Slot()
    def refresh_logs(self, query=None):
        """Fetches logs from SQLite database and populates the table."""
        logs = self.db.get_logs(query)
        
        self.table.setRowCount(0)
        self.table.verticalHeader().setVisible(False)
        self.table.setRowHeight(38, 48)  # Generous row height for thumbnails

        for row_idx, log in enumerate(logs):
            self.table.insertRow(row_idx)
            self.table.setRowHeight(row_idx, 46)

            # 1. ID
            id_item = QTableWidgetItem(str(log['id']))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 0, id_item)

            # 2. Snapshot Thumbnail (Custom widget inside cell)
            snap_widget = QWidget()
            snap_layout = QHBoxLayout(snap_widget)
            snap_layout.setContentsMargins(4, 4, 4, 4)
            snap_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            snap_lbl = QLabel()
            snap_lbl.setFixedSize(50, 36)
            snap_lbl.setStyleSheet("border: 1px solid #3E3E4F; border-radius: 4px; background-color: #08080C;")
            snap_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            snap_path = log['snapshot_path']
            if snap_path and os.path.exists(snap_path):
                pixmap = QPixmap(snap_path)
                snap_lbl.setPixmap(pixmap.scaled(50, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                # Store full path inside tool tip for debug reference
                snap_lbl.setToolTip("Double click row to preview full frame")
            else:
                snap_lbl.setText("N/A")
                snap_lbl.setStyleSheet("font-size: 9px; color: #90A4AE; border: 1px dashed #2E2E38;")
                
            snap_layout.addWidget(snap_lbl)
            self.table.setCellWidget(row_idx, 1, snap_widget)

            # 3. Name Identity
            name = log['name']
            name_item = QTableWidgetItem(name)
            name_item.setFont(Qt.AlignmentFlag.AlignVCenter)
            
            # Text coloring based on classification
            if name == "Unknown":
                name_item.setForeground(QColor(COLOR_RED))
            else:
                name_item.setForeground(QColor(COLOR_GREEN))
                
            self.table.setItem(row_idx, 2, name_item)

            # 4. Timestamp
            time_item = QTableWidgetItem(log['timestamp'])
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 3, time_item)

            # 5. Accuracy / Confidence
            conf = log['confidence']
            conf_text = f"{conf:.1f}%" if name != "Unknown" else "—"
            conf_item = QTableWidgetItem(conf_text)
            conf_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 4, conf_item)

    @Slot(str)
    def filter_logs(self):
        """Invoked live when user types in search bar."""
        query = self.search_bar.text().strip()
        self.refresh_logs(query if query else None)

    def show_snapshot_preview(self, model_index):
        """Pops up a high-quality dialog to preview full frame when double clicked."""
        row = model_index.row()
        
        # Get ID and Name
        log_id = self.table.item(row, 0).text()
        name = self.table.item(row, 2).text()
        time_str = self.table.item(row, 3).text()
        
        # Fetch log details directly from database to get correct snapshot_path
        logs = self.db.get_logs()
        target_log = next((l for l in logs if str(l['id']) == log_id), None)
        
        if target_log and target_log['snapshot_path']:
            snap_path = target_log['snapshot_path']
            if os.path.exists(snap_path):
                dialog = ImagePreviewDialog(snap_path, f"{name} ({time_str})", self)
                dialog.exec()
            else:
                QMessageBox.warning(self, "Missing Snapshot File", "The high-resolution snapshot file associated with this log has been deleted or moved.")
        else:
            QMessageBox.warning(self, "No Snapshot Available", "No snapshot file is recorded for this identification log.")

    def clear_logs(self):
        """Clears logs after double confirmation."""
        reply = QMessageBox.question(
            self, "Confirm Clear", 
            "Are you sure you want to delete ALL activity logs and their associated face snapshots?\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success = self.db.clear_all_logs()
            if success:
                self.refresh_logs()
                QMessageBox.information(self, "Logs Cleared", "All activity database records and snapshot files have been successfully purged.")
            else:
                QMessageBox.critical(self, "Error", "Failed to clear activity logs.")

    def export_to_csv(self):
        """Exports log history to CSV using QFileDialog."""
        logs = self.db.get_logs()
        if not logs:
            QMessageBox.warning(self, "No Data", "There are no activity log records available to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Export File", "", "CSV Files (*.csv)"
        )
        if not file_path:
            return

        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow(["ID", "Name Identity", "Timestamp", "Confidence Match (%)", "Snapshot Path"])
                # Write rows
                for log in logs:
                    writer.writerow([
                        log['id'],
                        log['name'],
                        log['timestamp'],
                        f"{log['confidence']:.2f}" if log['name'] != "Unknown" else "0.0",
                        log['snapshot_path'] if log['snapshot_path'] else "N/A"
                    ])
            QMessageBox.information(self, "Export Success", f"Successfully exported {len(logs)} log entries to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"An error occurred while saving the CSV file:\n{str(e)}")
