import sys
import os
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow

# Ensure execution context is aligned in correct directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    # 1. Initialize PySide6 Application
    app = QApplication(sys.argv)
    
    # 2. Spawn Main Dashboard Window
    window = MainWindow()
    window.show()
    
    # 3. Execute Qt Application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
