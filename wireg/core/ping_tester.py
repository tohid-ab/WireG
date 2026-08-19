import re
import socket
import subprocess
import time
from typing import List, Optional, Tuple
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QRunnable, QThreadPool

from .config_manager import WireGuardConfig


def measure_host_latency(host: str, port: Optional[int] = None, timeout_sec: float = 2.0) -> Tuple[Optional[float], str]:
    """
    Measures latency to host.
    Tries standard system ping first, then falls back to TCP socket test if ping is blocked/unavailable.
    Returns (latency_ms, status) where status is 'ok', 'high', 'timeout', 'error'.
    """
    if not host:
        return None, "error"

    # Step 1: Try ICMP Ping
    try:
        start_t = time.perf_counter()
        res = subprocess.run(
            ["ping", "-c", "1", "-W", str(int(timeout_sec)), host],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_sec + 0.5
        )
        if res.returncode == 0:
            # Parse time=X.XX ms
            m = re.search(r"time[=<]\s*([0-9.]+)\s*ms", res.stdout)
            if m:
                ms = float(m.group(1))
                status = "ok" if ms < 180 else "high"
                return ms, status
            else:
                elapsed = (time.perf_counter() - start_t) * 1000.0
                status = "ok" if elapsed < 180 else "high"
                return elapsed, status
    except (subprocess.TimeoutExpired, Exception):
        pass

    # Step 2: Try DNS resolution & TCP Socket probe if port is provided or standard 53/80/443
    try:
        target_port = port if port and port not in (51820, 51847) else 80
        start_t = time.perf_counter()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout_sec)
        s.connect((host, target_port))
        ms = (time.perf_counter() - start_t) * 1000.0
        s.close()
        status = "ok" if ms < 180 else "high"
        return ms, status
    except socket.timeout:
        return None, "timeout"
    except socket.gaierror:
        return None, "error"
    except Exception:
        # If connection refused, host is still reachable and answered TCP RST!
        ms = (time.perf_counter() - start_t) * 1000.0
        if ms < (timeout_sec * 1000.0):
            status = "ok" if ms < 180 else "high"
            return ms, status
        return None, "timeout"


class PingTask(QRunnable):
    """Runnable task to ping a single config in a thread pool."""

    def __init__(self, config: WireGuardConfig, signal_callback):
        super().__init__()
        self.config = config
        self.signal_callback = signal_callback

    def run(self):
        host, port = self.config.get_endpoint_host_and_port()
        if not host:
            self.signal_callback(self.config.id, None, "error")
            return
        
        latency, status = measure_host_latency(host, port)
        self.signal_callback(self.config.id, latency, status)


class PingTester(QObject):
    """Coordinates single and batch ping testing across configs."""
    ping_result = pyqtSignal(str, object, str)  # config_id, latency_ms (float or None), status
    batch_finished = pyqtSignal()
    batch_progress = pyqtSignal(int, int)       # current, total

    def __init__(self, max_threads: int = 6):
        super().__init__()
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(max_threads)
        self._total_batch = 0
        self._completed_batch = 0

    def test_single(self, config: WireGuardConfig) -> None:
        """Tests ping for a single config asynchronously."""
        task = PingTask(config, self._on_single_done)
        self.thread_pool.start(task)

    def test_all(self, configs: List[WireGuardConfig]) -> None:
        """Tests ping for a list of configs in parallel."""
        if not configs:
            self.batch_finished.emit()
            return
        
        self._total_batch = len(configs)
        self._completed_batch = 0
        self.batch_progress.emit(0, self._total_batch)

        for cfg in configs:
            task = PingTask(cfg, self._on_batch_item_done)
            self.thread_pool.start(task)

    def _on_single_done(self, config_id: str, latency: Optional[float], status: str):
        self.ping_result.emit(config_id, latency, status)

    def _on_batch_item_done(self, config_id: str, latency: Optional[float], status: str):
        self.ping_result.emit(config_id, latency, status)
        self._completed_batch += 1
        self.batch_progress.emit(self._completed_batch, self._total_batch)
        if self._completed_batch >= self._total_batch:
            self.batch_finished.emit()
