import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import StepViewer

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dark_stylesheet = """
        QWidget { background-color: #212121; color: #FAFAFA; font-size: 11pt; }
        QMainWindow, QDialog { border: 1px solid #424242; }
        #TopBar, #NavBar { background-color: #303030; border-bottom: 1px solid #424242; }
        #NavBar { border-top: 1px solid #424242; border-bottom: none; }
        QPushButton { background-color: #424242; border: 1px solid #616161; padding: 8px; min-width: 80px; border-radius: 4px; }
        QPushButton:hover { background-color: #616161; }
        QPushButton:pressed { background-color: #757575; }
        QPushButton:disabled { background-color: #292929; color: #757575; }
        #ActionButton { background-color: #0277BD; }
        #ActionButton:hover { background-color: #039BE5; }
        QComboBox, QDateEdit, QLineEdit { background-color: #424242; border: 1px solid #616161; padding: 5px; border-radius: 4px; }
        QComboBox::drop-down { border: none; }
        QCalendarWidget QWidget { alternate-background-color: #424242; }
        QTextEdit { background-color: #2a2a2a; border: 1px solid #424242; color: #BDBDBD; font-family: "Courier New", monospace; }
        QLabel { padding: 5px; }
        #TotalStepsLabel { font-size: 16pt; font-weight: bold; color: #4FC3F7; }
        QFrame#SubFrame { border: 1px solid #424242; border-radius: 4px; margin-top: 5px; padding: 5px; }
    """
    app.setStyleSheet(dark_stylesheet)

    # The application will look for 'Steps.db' in the same directory by default
    # or use the one provided as a command-line argument.
    db_file = sys.argv[1] if len(sys.argv) > 1 else "Steps.db"

    viewer = StepViewer(db_file)
    viewer.show()
    sys.exit(app.exec())
