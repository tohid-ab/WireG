import time
from pathlib import Path
from typing import Tuple, Optional
from PyQt6.QtCore import QObject, QTimer, pyqtSignal


def format_bytes(num_bytes: float) -> str:
    """Formats bytes to human-readable string (B, KB, MB, GB)."""
    if num_bytes < 1024:
        return f"{num_bytes:.0f} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    elif num_bytes < 1024 * 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{num_bytes / (1024 * 1024 * 1024):.2f} GB"


def format_speed(bps: float) -> str:
    """Formats speed in bytes per second to human readable string (KB/s, MB/s)."""
    if bps < 1024:
        return f"{bps:.0f} B/s"
    elif bps < 1024 * 1024:
        return f"{bps / 1024:.1f} KB/s"
    else:
        return f"{bps / (1024 * 1024):.2f} MB/s"


class TrafficMonitor(QObject):
    """
    Monitors real-time network traffic and transfer speeds for a Linux network interface
    without requiring root permissions.
    """
    stats_updated = pyqtSignal(float, float, int, int)  # rx_speed_bps, tx_speed_bps, total_rx, total_tx

    def __init__(self, interface_name: str = "wireg0", interval_ms: int = 1000):
        super().__init__()
        self.interface_name = interface_name
        self.interval_ms = interval_ms

        self._timer = QTimer(self)
        self._timer.setInterval(self.interval_ms)
        self._timer.timeout.connect(self._poll_stats)

        self._last_rx: Optional[int] = None
        self._last_tx: Optional[int] = None
        self._last_time: Optional[float] = None

        self.initial_rx: int = 0
        self.initial_tx: int = 0

    def start(self):
        self._last_rx = None
        self._last_tx = None
        self._last_time = None
        self._poll_stats()
        self._timer.start()

    def stop(self):
        self._timer.stop()
        self.stats_updated.emit(0.0, 0.0, 0, 0)

    def _read_interface_bytes(self) -> Tuple[Optional[int], Optional[int]]:
        rx_path = Path(f"/sys/class/net/{self.interface_name}/statistics/rx_bytes")
        tx_path = Path(f"/sys/class/net/{self.interface_name}/statistics/tx_bytes")

        if not rx_path.exists() or not tx_path.exists():
            return None, None

        try:
            rx = int(rx_path.read_text().strip())
            tx = int(tx_path.read_text().strip())
            return rx, tx
        except Exception:
            return None, None

    def _poll_stats(self):
        rx, tx = self._read_interface_bytes()
        now = time.time()

        if rx is None or tx is None:
            # Interface inactive
            self._last_rx = None
            self._last_tx = None
            self._last_time = None
            self.stats_updated.emit(0.0, 0.0, 0, 0)
            return

        if self._last_rx is None or self._last_time is None:
            self._last_rx = rx
            self._last_tx = tx
            self._last_time = now
            self.initial_rx = rx
            self.initial_tx = tx
            self.stats_updated.emit(0.0, 0.0, 0, 0)
            return

        dt = now - self._last_time
        if dt <= 0:
            return

        rx_diff = max(0, rx - self._last_rx)
        tx_diff = max(0, tx - self._last_tx)

        rx_speed = rx_diff / dt
        tx_speed = tx_diff / dt

        self._last_rx = rx
        self._last_tx = tx
        self._last_time = now

        total_rx_session = max(0, rx - self.initial_rx)
        total_tx_session = max(0, tx - self.initial_tx)

        self.stats_updated.emit(rx_speed, tx_speed, total_rx_session, total_tx_session)
