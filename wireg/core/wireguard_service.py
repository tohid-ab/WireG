import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from PyQt6.QtCore import QObject, pyqtSignal, QThread

from .config_manager import WireGuardConfig


def is_passwordless_configured() -> bool:
    """Checks if passwordless wireg-helper is configured in sudoers."""
    helper_path = "/usr/local/bin/wireg-helper"
    if not os.path.exists(helper_path):
        return False
    try:
        res = subprocess.run(
            ["sudo", "-n", helper_path, "status"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=2
        )
        # returncode 0 (UP) or 1 (DOWN) means sudo executed without password prompt!
        return res.returncode in (0, 1)
    except Exception:
        return False


class WireGuardWorker(QThread):
    """Background worker for executing wg-quick commands without blocking GUI."""
    finished_signal = pyqtSignal(bool, str, str)  # success, action, message

    def __init__(self, action: str, conf_path: Path, iface_name: str):
        super().__init__()
        self.action = action  # "up" or "down"
        self.conf_path = conf_path
        self.iface_name = iface_name

    def run(self):
        helper_installed = shutil.which("wireg-helper") or "/usr/local/bin/wireg-helper"
        local_helper = Path(__file__).resolve().parent / "wireg-helper.sh"
        
        target_helper = helper_installed if os.path.exists(helper_installed) else str(local_helper)

        # Strategy 1: Try passwordless sudo with helper
        cmd = ["sudo", "-n", target_helper, self.action]
        if self.action == "up":
            cmd.append(str(self.conf_path))

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20)
            if res.returncode == 0:
                self.finished_signal.emit(True, self.action, "")
                return
        except Exception:
            pass

        # Strategy 2: Fallback to pkexec with helper
        if shutil.which("pkexec"):
            cmd = ["pkexec", target_helper, self.action]
            if self.action == "up":
                cmd.append(str(self.conf_path))
        elif shutil.which("sudo"):
            cmd = ["sudo", target_helper, self.action]
            if self.action == "up":
                cmd.append(str(self.conf_path))
        else:
            cmd = [target_helper, self.action]
            if self.action == "up":
                cmd.append(str(self.conf_path))

        try:
            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=25
            )
            if res.returncode == 0:
                self.finished_signal.emit(True, self.action, "")
            else:
                err = res.stderr.strip() or res.stdout.strip() or f"Process exited with code {res.returncode}"
                if res.returncode in (126, 127):
                    err = "Authentication was cancelled by user."
                self.finished_signal.emit(False, self.action, err)
        except subprocess.TimeoutExpired:
            self.finished_signal.emit(False, self.action, "Operation timed out.")
        except Exception as e:
            self.finished_signal.emit(False, self.action, str(e))


class WireGuardService(QObject):
    """
    Manages WireGuard tunnel connection lifecycle on Linux using wireg-helper.
    """
    connected = pyqtSignal(str)           # config_id
    disconnected = pyqtSignal()
    status_changed = pyqtSignal(bool, str) # is_connected, active_config_id
    error_occurred = pyqtSignal(str)      # error message
    busy_changed = pyqtSignal(bool, str)  # is_busy, status_text

    INTERFACE_NAME = "wireg0"

    def __init__(self):
        super().__init__()
        # Use /tmp/wireg_runtime/ so root can read temp config without permission denied
        self.runtime_dir = Path(tempfile.gettempdir()) / "wireg_runtime"
        self.runtime_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
        self.active_config_id: Optional[str] = None
        self.active_config_name: Optional[str] = None
        self.is_busy: bool = False
        self._worker: Optional[WireGuardWorker] = None
        self._sync_current_state()

    def get_runtime_conf_path(self) -> Path:
        return self.runtime_dir / f"{self.INTERFACE_NAME}.conf"

    def is_interface_active(self) -> bool:
        """Checks if wireg0 network interface exists in kernel."""
        iface_path = Path(f"/sys/class/net/{self.INTERFACE_NAME}")
        return iface_path.exists()

    def _sync_current_state(self):
        """Syncs runtime status upon app startup."""
        if self.is_interface_active():
            state_file = self.runtime_dir / "active_id.txt"
            if state_file.exists():
                try:
                    lines = state_file.read_text().splitlines()
                    self.active_config_id = lines[0].strip() if lines else None
                    self.active_config_name = lines[1].strip() if len(lines) > 1 else None
                except Exception:
                    self.active_config_id = None
        else:
            self.active_config_id = None
            self.active_config_name = None

    def connect(self, config: WireGuardConfig) -> None:
        """Starts WireGuard tunnel with the given configuration."""
        if self.is_busy:
            self.error_occurred.emit("Another operation is already in progress.")
            return

        if self.is_interface_active():
            self.disconnect(callback=lambda: self._start_connect(config))
        else:
            self._start_connect(config)

    def _start_connect(self, config: WireGuardConfig) -> None:
        self.is_busy = True
        self.busy_changed.emit(True, f"Connecting to {config.name}...")

        conf_path = self.get_runtime_conf_path()
        try:
            # Write configuration with 0644 so helper running as root can copy it
            conf_str = config.to_conf_str()
            conf_path.write_text(conf_str, encoding="utf-8")
            os.chmod(conf_path, 0o644)
        except Exception as e:
            self.is_busy = False
            self.busy_changed.emit(False, "")
            self.error_occurred.emit(f"Failed to prepare config file: {e}")
            return

        self._pending_config = config
        self._worker = WireGuardWorker("up", conf_path, self.INTERFACE_NAME)
        self._worker.finished_signal.connect(self._on_worker_finished)
        self._worker.start()

    def disconnect(self, callback=None) -> None:
        """Stops WireGuard tunnel."""
        if self.is_busy:
            self.error_occurred.emit("Another operation is already in progress.")
            return

        self.is_busy = True
        self.busy_changed.emit(True, "Disconnecting WireGuard tunnel...")
        self._after_disconnect_callback = callback

        conf_path = self.get_runtime_conf_path()
        self._worker = WireGuardWorker("down", conf_path, self.INTERFACE_NAME)
        self._worker.finished_signal.connect(self._on_worker_finished)
        self._worker.start()

    def _on_worker_finished(self, success: bool, action: str, message: str):
        self.is_busy = False
        self.busy_changed.emit(False, "")

        if action == "up":
            if success and self.is_interface_active():
                self.active_config_id = self._pending_config.id
                self.active_config_name = self._pending_config.name
                state_file = self.runtime_dir / "active_id.txt"
                state_file.write_text(f"{self.active_config_id}\n{self.active_config_name}\n")
                self.connected.emit(self.active_config_id)
                self.status_changed.emit(True, self.active_config_id)
            else:
                self.active_config_id = None
                self.active_config_name = None
                err_msg = message or "Failed to bring up interface."
                self.error_occurred.emit(f"Connection Failed: {err_msg}")
                self.status_changed.emit(False, "")

        elif action == "down":
            state_file = self.runtime_dir / "active_id.txt"
            if state_file.exists():
                state_file.unlink(missing_ok=True)
            self.active_config_id = None
            self.active_config_name = None
            self.disconnected.emit()
            self.status_changed.emit(False, "")

            if getattr(self, "_after_disconnect_callback", None):
                cb = self._after_disconnect_callback
                self._after_disconnect_callback = None
                cb()
