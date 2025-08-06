import subprocess
import os
from PyQt6.QtCore import QObject, pyqtSignal
from logger import log

class AdbWorker(QObject):
    log_message = pyqtSignal(str)
    devices_listed = pyqtSignal(list)
    wifi_connected = pyqtSignal(str)
    pull_complete = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, command, *args):
        super().__init__()
        self.command = command
        self.args = args

    def run(self):
        try:
            command_method = getattr(self, f"_{self.command}")
            command_method(*self.args)
        except Exception as e:
            log.error(f"ADB Worker failed for command '{self.command}': {e}")
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()

    def _run_adb(self, args, timeout=20):
        """
        Helper to run an ADB command and capture text output.
        NOTE: This implementation assumes 'adb' is in the system's PATH,
        which is common on Linux/macOS.
        """
        command_str = f"adb {' '.join(args)}"
        self.log_message.emit(f"Running: {command_str}")
        log.info(f"Running: {command_str}")
        try:
            process = subprocess.run(
                ["adb"] + args,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True,
                encoding="utf-8",
            )
            output = process.stdout.strip()
            if output:
                log.info(f"Output:\n{output}")
                self.log_message.emit(f"Output:\n{output}")
            return output
        except FileNotFoundError:
            raise Exception("ADB executable not found. Make sure it's in your system's PATH.")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip()
            log.error(f"ADB command failed:\n{error_msg}")
            raise Exception(f"ADB command failed:\n{error_msg}")
        except subprocess.TimeoutExpired:
            raise Exception("ADB command timed out. Is the device responsive?")

    def _list_devices(self):
        output = self._run_adb(["devices"])
        lines = output.strip().split("\n")[1:]
        devices = [line.split("\t")[0] for line in lines if "\t" in line and "device" in line]
        self.devices_listed.emit(devices)

    def _connect_wifi(self, ip_address):
        self.log_message.emit(f"Attempting to connect to {ip_address}...")
        output = self._run_adb(["connect", ip_address])
        if f"connected to {ip_address}" in output or f"already connected to {ip_address}" in output:
            self.wifi_connected.emit(ip_address)
        else:
            raise Exception(f"Failed to connect. ADB response: {output}")

    def _pull_db_root(self, device_id):
        self.log_message.emit("Attempting DB pull using root method...")
        db_path = "/data/data/com.miui.rom/databases/Steps.db"
        tmp_path = "/sdcard/Steps_tmp.db"
        self._run_adb(["-s", device_id, "shell", "su", "-c", f"cp {db_path} {tmp_path} && chmod 644 {tmp_path}"])
        self._pull_and_cleanup(device_id, tmp_path)

    def _pull_and_cleanup(self, device_id, tmp_path_on_sdcard):
        local_path = "Steps.db"
        if os.path.exists(local_path):
            os.remove(local_path)
        self.log_message.emit("Pulling database from temporary location...")
        self._run_adb(["-s", device_id, "pull", tmp_path_on_sdcard, local_path])
        self.log_message.emit("Cleaning up temporary file on device...")
        self._run_adb(["-s", device_id, "shell", "rm", tmp_path_on_sdcard])
        self.log_message.emit("Database pull successful!")
        self.pull_complete.emit(local_path)
