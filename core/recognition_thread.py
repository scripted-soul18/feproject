import cv2
import time
import os
import numpy as np
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage
import face_recognition
from database.db_manager import DatabaseManager
from config import SNAPSHOTS_DIR, DEFAULT_TOLERANCE, DEFAULT_FRAME_SKIP

class FaceRecognitionThread(QThread):
    # Signals
    frame_processed = Signal(QImage, list)
    face_logged = Signal(str, float, str)  # name, distance, snapshot_path
    status_message = Signal(str)

    def __init__(self, camera_index=0, parent=None):
        super().__init__(parent)
        self.camera_index = camera_index
        self.tolerance = DEFAULT_TOLERANCE
        self.frame_skip = DEFAULT_FRAME_SKIP
        
        self.running = False
        self.db = DatabaseManager()
        
        # In-memory cache for registered faces
        self.known_encodings = []
        self.known_names = []
        self.load_known_faces()
        
        # Debouncing: map of name -> last logged timestamp
        self.last_logged = {}
        self.cooldown_period = 10.0  # seconds

    def load_known_faces(self):
        """Reloads registered users and encodings from the database."""
        users = self.db.get_all_users()
        self.known_encodings = [u['encoding'] for u in users]
        self.known_names = [u['name'] for u in users]
        self.status_message.emit(f"Loaded {len(self.known_names)} registered faces.")

    def update_settings(self, tolerance, camera_index, frame_skip):
        """Update settings dynamically."""
        self.tolerance = tolerance
        self.frame_skip = frame_skip
        if self.camera_index != camera_index:
            self.camera_index = camera_index
            # Force restart camera if thread is active
            if self.running:
                self.status_message.emit("Restarting camera thread due to camera index change...")
                self.stop()
                # Brief wait before restarting
                time.sleep(0.5)
                self.start()

    def run(self):
        self.running = True
        video = cv2.VideoCapture(self.camera_index)
        
        if not video.isOpened():
            self.status_message.emit(f"Error: Camera index {self.camera_index} could not be opened.")
            self.running = False
            return
            
        self.status_message.emit("Camera feed initialized successfully.")
        frame_count = 0
        
        # Local variables to cache previous detections (for smoothness during skipped frames)
        face_locations = []
        face_names = []
        face_distances = []
        
        while self.running:
            ret, frame = video.read()
            if not ret:
                self.status_message.emit("Error: Failed to grab frame from webcam.")
                break
                
            # Horizontal mirror for a natural webcam presentation
            frame = cv2.flip(frame, 1)
            
            # Process recognition only on selected frame intervals to optimize CPU
            if frame_count % self.frame_skip == 0:
                # 1/4 size scaling for super-fast face detection/recognition
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = small_frame[:, :, ::-1]
                
                # Face Detection
                face_locations = face_recognition.face_locations(rgb_small_frame)
                
                # Face Encoding
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                
                face_names = []
                face_distances = []
                
                for face_encoding in face_encodings:
                    name = "Unknown"
                    distance = 1.0
                    
                    if self.known_encodings:
                        # Compare face with registered encodings
                        distances = face_recognition.face_distance(self.known_encodings, face_encoding)
                        best_match_idx = np.argmin(distances)
                        
                        if distances[best_match_idx] <= self.tolerance:
                            name = self.known_names[best_match_idx]
                            distance = float(distances[best_match_idx])
                            
                    face_names.append(name)
                    face_distances.append(distance)
                    
                    # Handle logging and snapshots
                    self.handle_face_logging(frame, face_encoding, name, distance)
                    
            # Scale coordinates back up to full frame size
            detections = []
            for (top, right, bottom, left), name, dist in zip(face_locations, face_names, face_distances):
                t, r, b, l = top * 4, right * 4, bottom * 4, left * 4
                
                # Calculate confidence percentage (1.0 - distance)
                confidence = (1.0 - dist) * 100 if name != "Unknown" else 0.0
                
                # Neon BGR Colors
                # Matched: Glowing Mint Green (20, 255, 57)
                # Unknown: Glowing Electric Magenta (255, 0, 127)
                color = (57, 255, 20) if name != "Unknown" else (127, 0, 255)
                
                detections.append({
                    "box": (t, r, b, l),
                    "name": name,
                    "confidence": confidence,
                    "color": color
                })
                
                # Draw the futuristic HUD box onto the frame
                self.draw_hud_face_box(frame, l, t, r, b, name, confidence, color)
                
            # Convert raw frame to QImage for GUI
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_BGR888)
            
            # Emit processed frame and detections
            self.frame_processed.emit(q_img, detections)
            
            frame_count += 1
            # Control frame rate roughly (e.g., 30ms sleep)
            time.sleep(0.03)
            
        video.release()
        self.status_message.emit("Camera feed stopped.")

    def stop(self):
        self.running = False
        self.wait()

    def handle_face_logging(self, frame, face_encoding, name, distance):
        """Handles face detection logs and saves face snapshots with debouncing."""
        now = time.time()
        
        # Debounce: check if we registered this face recently
        if name in self.last_logged:
            if now - self.last_logged[name] < self.cooldown_period:
                return  # Skip logging due to cooldown
                
        # Update cooldown timer
        self.last_logged[name] = now
        
        # Save snapshot
        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        safe_name = name.replace(" ", "_")
        snapshot_filename = f"snap_{timestamp_str}_{safe_name}.jpg"
        snapshot_path = os.path.join(SNAPSHOTS_DIR, snapshot_filename)
        
        # Convert distance to confidence %
        confidence = (1.0 - distance) * 100 if name != "Unknown" else 0.0
        
        # Save frame to file
        try:
            cv2.imwrite(snapshot_path, frame)
            
            # Log to DB
            self.db.log_detection(name, confidence, snapshot_path)
            
            # Emit log signal so GUI panels update live
            self.face_logged.emit(name, confidence, snapshot_path)
        except Exception as e:
            print("Error writing snapshot:", e)

    def draw_hud_face_box(self, frame, left, top, right, bottom, name, confidence, color):
        """Draws a premium, high-tech HUD-style face border with neon corners and text banner."""
        h, w, _ = frame.shape
        
        # Ensure coordinates are within image boundaries
        left, top = max(0, left), max(0, top)
        right, bottom = min(w - 1, right), min(h - 1, bottom)
        
        # 1. Draw thin outer box for reference
        cv2.rectangle(frame, (left, top), (right, bottom), color, 1)
        
        # 2. Draw thick tech-bracket corners
        width = right - left
        height = bottom - top
        bracket_len = min(width, height) // 6  # Length of brackets is 1/6 of box size
        thickness = 3
        
        # Top Left
        cv2.line(frame, (left, top), (left + bracket_len, top), color, thickness)
        cv2.line(frame, (left, top), (left, top + bracket_len), color, thickness)
        
        # Top Right
        cv2.line(frame, (right, top), (right - bracket_len, top), color, thickness)
        cv2.line(frame, (right, top), (right, top + bracket_len), color, thickness)
        
        # Bottom Left
        cv2.line(frame, (left, bottom), (left + bracket_len, bottom), color, thickness)
        cv2.line(frame, (left, bottom), (left, bottom - bracket_len), color, thickness)
        
        # Bottom Right
        cv2.line(frame, (right, bottom), (right - bracket_len, bottom), color, thickness)
        cv2.line(frame, (right, bottom), (right, bottom - bracket_len), color, thickness)
        
        # 3. Text Overlay Banner (Futuristic floating tag)
        label = f"{name} ({confidence:.0f}%)" if name != "Unknown" else name
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        font_thickness = 1
        
        # Calculate text size
        text_size, _ = cv2.getTextSize(label, font, font_scale, font_thickness)
        text_w, text_h = text_size
        
        # Background text banner coordinates
        banner_h = text_h + 10
        banner_top = top - banner_h if top - banner_h > 0 else bottom
        banner_bottom = top if top - banner_h > 0 else bottom + banner_h
        
        # Draw translucent dark banner background
        overlay = frame.copy()
        cv2.rectangle(overlay, (left, banner_top), (left + text_w + 12, banner_bottom), (18, 18, 24), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Draw neon line on left side of text banner
        cv2.line(frame, (left, banner_top), (left, banner_bottom), color, 2)
        
        # Put text inside banner
        cv2.putText(
            frame,
            label,
            (left + 6, banner_bottom - 5),
            font,
            font_scale,
            color,
            font_thickness,
            cv2.LINE_AA
        )
