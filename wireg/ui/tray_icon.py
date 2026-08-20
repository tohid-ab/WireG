from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu

from ..utils.paths import get_asset_path


def create_tray_icon_pixmap(is_connected: bool) -> QPixmap:
    """Draws a crisp tray icon using the official WireG logo with status indicator dot."""
    icon_path = get_asset_path("icons/icon_64x64.png")
    
    pix = QPixmap(32, 32)
    pix.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

    if icon_path.exists():
        base_icon = QPixmap(str(icon_path))
        painter.drawPixmap(0, 0, 32, 32, base_icon)
    else:
        # Fallback vector shield
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#6366f1"))
        painter.drawRoundedRect(2, 2, 28, 28, 6, 6)
        painter.setPen(QColor("#ffffff"))
        font = painter.font()
        font.setBold(True)
        font.setPixelSize(14)
        painter.setFont(font)
        painter.drawText(0, 0, 32, 32, Qt.AlignmentFlag.AlignCenter, "W")

    # Status dot (Bottom Right)
    dot_color = QColor("#10b981") if is_connected else QColor("#71717a")
    painter.setBrush(dot_color)
    painter.setPen(QColor("#090d16"))
    painter.drawEllipse(20, 20, 10, 10)

    painter.end()
    return pix


class WireGTrayIcon(QSystemTrayIcon):
    """
    System Tray integration providing quick status, background minimize, and quick actions.
    """
    show_window_requested = pyqtSignal()
    toggle_connect_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_connected = False
        self.active_tunnel_name = ""
        self._init_ui()
        self.update_status(False, "")

    def _init_ui(self):
        self.activated.connect(self._on_tray_activated)

        self.menu = QMenu()
        
        self.status_item = self.menu.addAction("WireG - Disconnected")
        self.status_item.setEnabled(False)

        self.menu.addSeparator()

        self.toggle_action = self.menu.addAction("Connect")
        self.toggle_action.triggered.connect(self.toggle_connect_requested.emit)

        self.show_action = self.menu.addAction("Show WireG Window")
        self.show_action.triggered.connect(self.show_window_requested.emit)

        self.menu.addSeparator()

        self.quit_action = self.menu.addAction("Quit WireG")
        self.quit_action.triggered.connect(self.quit_requested.emit)

        self.setContextMenu(self.menu)

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.show_window_requested.emit()

    def update_status(self, is_connected: bool, tunnel_name: str = ""):
        self.is_connected = is_connected
        self.active_tunnel_name = tunnel_name

        pix = create_tray_icon_pixmap(is_connected)
        self.setIcon(QIcon(pix))

        if is_connected:
            tip = f"WireG: Connected to {tunnel_name}"
            self.status_item.setText(f"● Connected: {tunnel_name}")
            self.toggle_action.setText("Disconnect Tunnel")
        else:
            tip = "WireG: Disconnected"
            self.status_item.setText("○ Disconnected")
            self.toggle_action.setText("Connect")

        self.setToolTip(tip)

    def notify(self, title: str, message: str, is_error: bool = False):
        icon = QSystemTrayIcon.MessageIcon.Critical if is_error else QSystemTrayIcon.MessageIcon.Information
        self.showMessage(title, message, icon, 3000)
