from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QFrame,
)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QCloseEvent

from adb_handler import AdbWorker


class AdbSyncDialog(QDialog):
    """Dialog for syncing the database from a device using ADB."""

    sync_successful = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ADB Device Sync (Root Required)")
        self.setMinimumSize(500, 450)
        self.worker_thread = None
        self.worker = None
        self.is_running = False
        self.refresh_on_finish = False  # Flag to fix thread crash
        self.init_ui()
        self.log_output.append(
            "NOTE: ADB functions are tested on Linux. For Windows, ensure 'adb.exe' is in your system's PATH."
        )
        self.list_devices()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Device Selection
        device_layout = QHBoxLayout()
        self.device_combo = QComboBox()
        self.device_combo.setPlaceholderText("Scanning...")
        self.refresh_btn = QPushButton()
        self.refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        self.refresh_btn.clicked.connect(self.list_devices)
        device_layout.addWidget(QLabel("Device:"))
        device_layout.addWidget(self.device_combo, 1)
        device_layout.addWidget(self.refresh_btn)
        layout.addLayout(device_layout)

        # Connection Options
        options_group = QFrame()
        options_group.setObjectName("SubFrame")
        options_layout = QVBoxLayout(options_group)
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Enter device IP:PORT (e.g., 192.168.1.5:5555)")
        self.connect_wifi_btn = QPushButton("Connect to IP") # Changed button
        self.connect_wifi_btn.clicked.connect(self.connect_wifi) # Changed connection
        options_layout.addWidget(self.ip_input)
        options_layout.addWidget(self.connect_wifi_btn)
        layout.addWidget(options_group)

        # Action Button
        self.pull_db_btn = QPushButton("Sync Steps from Device (Root)")
        self.pull_db_btn.setObjectName("ActionButton")
        self.pull_db_btn.clicked.connect(self.pull_db)
        layout.addWidget(self.pull_db_btn)

        # Log Output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output, 1)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

    def _start_worker(self, command, *args):
        self.set_controls_enabled(False)
        self.is_running = True
        self.worker_thread = QThread()
        self.worker = AdbWorker(command, *args)
        self.worker.moveToThread(self.worker_thread)

        self.worker.log_message.connect(self.log_output.append)
        self.worker.devices_listed.connect(self.on_devices_listed)
        self.worker.wifi_connected.connect(self.on_wifi_connected)
        self.worker.pull_complete.connect(self.on_pull_complete)
        self.worker.error_occurred.connect(self.on_error)

        self.worker.finished.connect(self.on_worker_finished)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def list_devices(self):
        self.log_output.clear()
        self.device_combo.clear()
        self.device_combo.setPlaceholderText("Scanning for devices...")
        self._start_worker("list_devices")

    def connect_wifi(self):
        """Connects to a device directly via IP address."""
        ip = self.ip_input.text().strip()
        if not ip:
            self.log_output.append("Error: Please enter the device's IP address and port.")
            return
        self.refresh_on_finish = True
        self._start_worker("connect_wifi", ip)

    def pull_db(self):
        device = self.device_combo.currentText()
        if not device:
            self.log_output.append("Error: No device selected.")
            return
        self._start_worker("pull_db_root", device)

    # --- Worker Result Slots ---

    def on_devices_listed(self, devices):
        self.device_combo.clear()
        self.device_combo.addItems(devices)
        if devices:
            self.device_combo.setCurrentIndex(0)
        else:
            self.device_combo.setPlaceholderText("No devices found")
        self.log_output.append(f"Found {len(devices)} device(s).")

    def on_wifi_connected(self, device_ip):
        """Only logs the message. The refresh is now handled by on_worker_finished."""
        self.log_output.append(
            f"Successfully connected to {device_ip}. Refreshing list..."
        )

    def on_pull_complete(self, local_path):
        self.log_output.append("Sync complete!")
        self.sync_successful.emit(local_path)
        self.accept()

    def on_error(self, error_message):
        self.log_output.append(f"Error: {error_message}")
        if not self.device_combo.count():
            self.device_combo.setPlaceholderText("Scan failed")
        self.refresh_on_finish = False

    def on_worker_finished(self):
        self.is_running = False
        self.set_controls_enabled(True)

        # If a refresh was requested (by connect_wifi), schedule it to run
        # after the current event has been processed. This prevents the crash.
        if self.refresh_on_finish:
            self.refresh_on_finish = False
            QTimer.singleShot(0, self.list_devices)

    def set_controls_enabled(self, enabled):
        self.device_combo.setEnabled(enabled)
        self.refresh_btn.setEnabled(enabled)
        self.ip_input.setEnabled(enabled)
        self.connect_wifi_btn.setEnabled(enabled)
        self.pull_db_btn.setEnabled(enabled)

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        if self.is_running:
            self.log_output.append("Cannot close: ADB operation in progress.")
            if a0:
                a0.ignore()
        else:
            if a0:
                a0.accept()
