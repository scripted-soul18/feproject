import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QFrame, QFileDialog, QLineEdit, QDialog, QScrollArea, QGridLayout, QMessageBox)
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, Slot, Signal
import cv2
import numpy as np
import face_recognition
from config import REGISTERED_DIR, COLOR_CYAN, COLOR_RED, COLOR_GREEN

class RegisterDialog(QDialog):
    """Sleek modal dialog to prompt for Name when registering a face."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Register Face Profile")
        self.setModal(True)
        self.setFixedWidth(320)
        self.setStyleSheet("background-color: #1E1E24; color: #ECEFF1;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("ENTER IDENTITY NAME")
        title.setStyleSheet("font-weight: bold; font-size: 13px; color: #00F0FF;")
        layout.addWidget(title)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. John Doe")
        layout.addWidget(self.name_input)

        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_save = QPushButton("Confirm & Register")
        self.btn_save.setObjectName("AccentButton")
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self.accept)

    def get_name(self):
        return self.name_input.text().strip()


class DatabasePanel(QWidget):
    # Signals
    user_database_changed = Signal()  # Emit when users are added or deleted

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        
        # Keep track of active webcam frame to allow instant webcam registration
        self.current_live_frame = None
        
        self.init_ui()

    def init_ui(self):
        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)

        # ----------------- Top Header & Add User Buttons -----------------
        header_layout = QHBoxLayout()
        
        title_layout = QVBoxLayout()
        heading = QLabel("Identity Database Manager")
        heading.setObjectName("PanelHeading")
        title_layout.addWidget(heading)

        subheading = QLabel("Manage enrolled biometric face profiles and credentials")
        subheading.setObjectName("PanelSubheading")
        title_layout.addWidget(subheading)
        header_layout.addLayout(title_layout)

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.btn_upload = QPushButton("Upload Photo...")
        self.btn_upload.setIcon(QIcon.fromTheme("document-open"))
        self.btn_upload.clicked.connect(self.register_via_file)
        
        self.btn_capture = QPushButton("Register Live Face")
        self.btn_capture.setObjectName("AccentButton")
        self.btn_capture.clicked.connect(self.register_via_live_feed)
        
        btn_layout.addWidget(self.btn_upload)
        btn_layout.addWidget(self.btn_capture)
        header_layout.addLayout(btn_layout)
        
        main_layout.addLayout(header_layout)

        # ----------------- Bottom: Scrollable Grid of Enrolled Users -----------------
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)

        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background-color: transparent;")
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(0, 10, 0, 10)
        self.grid_layout.setSpacing(20)
        
        self.scroll_area.setWidget(self.grid_widget)
        main_layout.addWidget(self.scroll_area, 1)

        # Initial Load
        self.refresh_user_grid()

    def set_active_live_frame(self, q_image):
        """Called by the main loop to cache the current live QImage for registration."""
        self.current_live_frame = q_image

    def refresh_user_grid(self):
        """Loads and updates the cards displaying registered users."""
        # 1. Clear existing items in grid
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget is not None: 
                widget.deleteLater()

        users = self.db.get_all_users()
        
        if not users:
            empty_lbl = QLabel("NO REGISTERED FACE IDENTITIES FOUND\nUse the buttons above to enroll new faces.")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: #90A4AE; margin-top: 100px;")
            self.grid_layout.addWidget(empty_lbl, 0, 0, 1, 4)
            return

        # 2. Add grid cards
        columns = 4
        for idx, user in enumerate(users):
            row = idx // columns
            col = idx % columns

            card = QFrame()
            card.setObjectName("UserCard")
            card.setFixedSize(200, 240)
            
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(10, 15, 10, 15)
            card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Profile Picture
            profile_lbl = QLabel()
            profile_lbl.setFixedSize(120, 120)
            profile_lbl.setStyleSheet("""
                border: 2px solid #2E2E38;
                border-radius: 60px;
                background-color: #121212;
            """)
            profile_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Load cropped face if exists, or general avatar
            if user['photo_path'] and os.path.exists(user['photo_path']):
                pix = QPixmap(user['photo_path'])
                profile_lbl.setPixmap(pix.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
            else:
                profile_lbl.setText("NO PHOTO")
                profile_lbl.setStyleSheet("border: 2px solid #2E2E38; border-radius: 60px; background-color: #121212; color: #90A4AE;")

            card_layout.addWidget(profile_lbl)

            # Name Label
            name_lbl = QLabel(user['name'])
            name_lbl.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 5px;")
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(name_lbl)

            # Date Label
            date_only = user['created_at'].split(" ")[0] if user['created_at'] else "N/A"
            date_lbl = QLabel(f"Registered: {date_only}")
            date_lbl.setStyleSheet("font-size: 11px; color: #90A4AE;")
            date_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(date_lbl)

            card_layout.addWidget(QFrame()) # Padding spacer

            # Delete Button
            btn_del = QPushButton("Delete Profile")
            btn_del.setObjectName("DangerButton")
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # Use closure to pass user ID
            btn_del.clicked.connect(lambda checked=False, u_id=user['id'], u_name=user['name']: self.delete_user(u_id, u_name))
            card_layout.addWidget(btn_del)

            self.grid_layout.addWidget(card, row, col)

    def delete_user(self, user_id, user_name):
        """Triggered to remove a user."""
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to permanently delete profile '{user_name}'?\nThis will clear all association encodings.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success = self.db.delete_user(user_id)
            if success:
                self.refresh_user_grid()
                self.user_database_changed.emit() # Notify thread to reload faces
            else:
                QMessageBox.critical(self, "Error", "Failed to delete user profile from database.")

    def register_via_file(self):
        """Prompts to upload a file and extracts face for database registration."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Face Image", "", "Images (*.jpg *.jpeg *.png)"
        )
        if not file_path:
            return

        # Load image
        img = face_recognition.load_image_file(file_path)
        
        # Verify face existence
        face_locations = face_recognition.face_locations(img)
        if not face_locations:
            QMessageBox.warning(self, "No Face Detected", "Could not find any face in the uploaded image. Please choose another image.")
            return
        if len(face_locations) > 1:
            QMessageBox.warning(self, "Multiple Faces Detected", "Detected multiple faces. For database enrollment, please choose an image with exactly one visible face.")
            return

        # Extract encoding
        encoding = face_recognition.face_encodings(img, face_locations)[0]
        
        # Prompt for name
        dialog = RegisterDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.get_name()
            if not name:
                QMessageBox.warning(self, "Invalid Name", "Registration canceled. Name cannot be empty.")
                return

            # Crop face image to save as profile picture
            top, right, bottom, left = face_locations[0]
            # Convert loaded RGB image to BGR for cv2 saving
            img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            face_crop = img_bgr[top:bottom, left:right]
            
            # Save cropped face photo
            photo_filename = f"profile_{name.replace(' ', '_')}.jpg"
            photo_path = os.path.join(REGISTERED_DIR, photo_filename)
            cv2.imwrite(photo_path, face_crop)

            # Insert into database
            success, msg = self.db.add_user(name, photo_path, encoding)
            if success:
                QMessageBox.information(self, "Success", msg)
                self.refresh_user_grid()
                self.user_database_changed.emit() # Notify thread to reload faces
            else:
                QMessageBox.critical(self, "Error", msg)

    def register_via_live_feed(self):
        """Grabs current frame from live stream thread and registers user face."""
        if self.current_live_frame is None:
            QMessageBox.warning(self, "Camera Inactive", "Live camera stream is offline. Please start the camera feed on the Live Feed tab first to capture profiles.")
            return

        # Convert QImage to OpenCV BGR numpy array
        q_image = self.current_live_frame
        width = q_image.width()
        height = q_image.height()
        
        ptr = q_image.bits()
        # Create numpy array from pointer
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape((height, width, 4))
        # Drop Alpha channel if present and convert BGRA to RGB
        frame_rgb = cv2.cvtColor(arr, cv2.COLOR_BGRA2RGB)

        # Detect face
        face_locations = face_recognition.face_locations(frame_rgb)
        if not face_locations:
            QMessageBox.warning(self, "Face Scan Failed", "No face was detected in the current camera frame. Face the camera directly and try again.")
            return
        if len(face_locations) > 1:
            QMessageBox.warning(self, "Multiple Faces Detected", "Detected multiple faces. Make sure only one person is in the frame when registering.")
            return

        # Extract encoding
        encoding = face_recognition.face_encodings(frame_rgb, face_locations)[0]

        # Prompt for name
        dialog = RegisterDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.get_name()
            if not name:
                QMessageBox.warning(self, "Invalid Name", "Registration canceled. Name cannot be empty.")
                return

            # Crop face image
            top, right, bottom, left = face_locations[0]
            # Crop original BGRA frame and convert to BGR for saving
            face_crop = cv2.cvtColor(arr[top:bottom, left:right], cv2.COLOR_BGRA2BGR)
            
            # Save crop
            photo_filename = f"profile_{name.replace(' ', '_')}.jpg"
            photo_path = os.path.join(REGISTERED_DIR, photo_filename)
            cv2.imwrite(photo_path, face_crop)

            # Insert into database
            success, msg = self.db.add_user(name, photo_path, encoding)
            if success:
                QMessageBox.information(self, "Success", msg)
                self.refresh_user_grid()
                self.user_database_changed.emit() # Notify thread to reload faces
            else:
                QMessageBox.critical(self, "Error", msg)
