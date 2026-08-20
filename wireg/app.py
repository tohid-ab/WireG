import signal
import sys
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWidgets import QApplication

from .core.config_manager import ConfigManager
from .core.wireguard_service import WireGuardService
from .ui.main_window import MainWindow
from .ui.styles import DARK_THEME_QSS
from .ui.tray_icon import create_tray_icon_pixmap
from .utils.paths import ensure_directories, get_asset_path


def run_app():
    # Allow terminal Ctrl+C interrupts
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    ensure_directories()

    app = QApplication(sys.argv)
    app.setApplicationName("WireG")
    app.setApplicationDisplayName("WireG - WireGuard Client")
    app.setOrganizationName("WireG")
    app.setQuitOnLastWindowClosed(False)

    icon_path = get_asset_path("icon.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Global Font
    font = QFont("Segoe UI", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    # Apply Theme
    app.setStyleSheet(DARK_THEME_QSS)

    # Core Managers
    config_manager = ConfigManager()
    wg_service = WireGuardService()

    # Main Window
    window = MainWindow(config_manager, wg_service)
    window.show()

    # Heartbeat timer to process UNIX signals
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(500)

    return app.exec()
