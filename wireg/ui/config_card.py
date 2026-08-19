from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QMenu,
)
from ..core.config_manager import WireGuardConfig


class ConfigCard(QFrame):
    """
    shadcn Glassmorphic Card representing a WireGuard configuration.
    """
    connect_requested = pyqtSignal(str)     # config_id
    disconnect_requested = pyqtSignal(str)  # config_id
    edit_requested = pyqtSignal(str)        # config_id
    delete_requested = pyqtSignal(str)      # config_id
    duplicate_requested = pyqtSignal(str)   # config_id
    export_requested = pyqtSignal(str)      # config_id
    qr_requested = pyqtSignal(str)          # config_id
    ping_requested = pyqtSignal(str)        # config_id
    favorite_toggled = pyqtSignal(str)      # config_id

    def __init__(self, config: WireGuardConfig, is_active: bool = False, parent=None):
        super().__init__(parent)
        self.config = config
        self.is_active = is_active
        self.setObjectName("configCard")
        self._init_ui()
        self.update_state(config, is_active)

    def _init_ui(self):
        self.setFixedHeight(84)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # 1. Favorite Star Button
        self.star_btn = QPushButton("☆")
        self.star_btn.setObjectName("iconButton")
        self.star_btn.setFixedSize(32, 32)
        self.star_btn.setToolTip("Toggle favorite / Pin to top")
        self.star_btn.clicked.connect(lambda: self.favorite_toggled.emit(self.config.id))
        layout.addWidget(self.star_btn)

        # 2. Main Config Information (Title & Tags)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.name_label = QLabel(self.config.name)
        self.name_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #ffffff; letter-spacing: -0.3px;")

        details_layout = QHBoxLayout()
        details_layout.setSpacing(8)

        # Endpoint Badge
        ep_text = self.config.peer.get("Endpoint", "No Endpoint")
        self.ep_label = QLabel(f"🌐 {ep_text}")
        self.ep_label.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 6px;
            padding: 2px 8px;
            font-size: 11px;
            color: #d4d4d8;
            font-weight: 500;
        """)

        # Address Badge
        addr_text = self.config.interface.get("Address", "")
        self.addr_label = QLabel(f"📍 {addr_text}" if addr_text else "")
        self.addr_label.setStyleSheet("""
            background-color: rgba(99, 102, 241, 0.08);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 6px;
            padding: 2px 8px;
            font-size: 11px;
            color: #a5b4fc;
            font-weight: 500;
        """)

        details_layout.addWidget(self.ep_label)
        if addr_text:
            details_layout.addWidget(self.addr_label)
        details_layout.addStretch()

        info_layout.addWidget(self.name_label)
        info_layout.addLayout(details_layout)
        layout.addLayout(info_layout, stretch=1)

        # 3. Ping / Latency Pill Badge
        self.ping_btn = QPushButton("⟳ Ping")
        self.ping_btn.setFixedHeight(30)
        self.ping_btn.setToolTip("Click to measure latency")
        self.ping_btn.clicked.connect(lambda: self.ping_requested.emit(self.config.id))
        layout.addWidget(self.ping_btn)

        # 4. Connect / Disconnect Action Button
        self.action_btn = QPushButton("Connect")
        self.action_btn.setObjectName("connectButton")
        self.action_btn.setFixedHeight(36)
        self.action_btn.setMinimumWidth(105)
        self.action_btn.clicked.connect(self._on_action_clicked)
        layout.addWidget(self.action_btn)

        # 5. More Options Button
        self.more_btn = QPushButton("⋮")
        self.more_btn.setObjectName("iconButton")
        self.more_btn.setFixedSize(32, 32)
        self.more_btn.setStyleSheet("font-size: 18px; font-weight: bold; color: #a1a1aa;")
        self.more_btn.setToolTip("More actions")
        self.more_btn.clicked.connect(self._show_context_menu)
        layout.addWidget(self.more_btn)

    def _on_action_clicked(self):
        if self.is_active:
            self.disconnect_requested.emit(self.config.id)
        else:
            self.connect_requested.emit(self.config.id)

    def update_state(self, config: WireGuardConfig, is_active: bool):
        self.config = config
        self.is_active = is_active

        # Card container style
        if is_active:
            self.setStyleSheet("""
                QFrame#configCard {
                    background-color: rgba(16, 185, 129, 0.08);
                    border: 1.5px solid #10b981;
                    border-radius: 14px;
                }
                QFrame#configCard:hover {
                    background-color: rgba(16, 185, 129, 0.12);
                    border: 1.5px solid #34d399;
                }
            """)
            self.action_btn.setText("Disconnect")
            self.action_btn.setObjectName("disconnectButton")
            self.action_btn.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ef4444, stop:1 #dc2626);
                color: #ffffff;
                border: 1px solid rgba(248, 113, 113, 0.4);
                font-weight: 700;
                border-radius: 9px;
            """)
        else:
            self.setStyleSheet("""
                QFrame#configCard {
                    background-color: rgba(18, 24, 38, 0.6);
                    border: 1px solid rgba(255, 255, 255, 0.07);
                    border-radius: 14px;
                }
                QFrame#configCard:hover {
                    background-color: rgba(26, 35, 54, 0.75);
                    border: 1px solid rgba(99, 102, 241, 0.35);
                }
            """)
            self.action_btn.setText("Connect")
            self.action_btn.setObjectName("connectButton")
            self.action_btn.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #10b981, stop:1 #059669);
                color: #ffffff;
                border: 1px solid rgba(52, 211, 153, 0.4);
                font-weight: 700;
                border-radius: 9px;
            """)

        # Star styling
        if config.is_favorite:
            self.star_btn.setText("★")
            self.star_btn.setStyleSheet("font-size: 17px; color: #fbbf24; background: rgba(251, 191, 36, 0.1); border-radius: 8px;")
        else:
            self.star_btn.setText("☆")
            self.star_btn.setStyleSheet("font-size: 17px; color: #71717a;")

        self.name_label.setText(config.name)
        ep = config.peer.get("Endpoint", "No Endpoint")
        self.ep_label.setText(f"🌐 {ep}")
        addr = config.interface.get("Address", "")
        self.addr_label.setText(f"📍 {addr}" if addr else "")

        # Latency badge
        self.update_ping_badge(config.last_ping, config.last_ping_status)

    def set_ping_testing(self):
        self.ping_btn.setText("Testing...")
        self.ping_btn.setStyleSheet("""
            background-color: rgba(56, 189, 248, 0.12);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.4);
            border-radius: 8px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 700;
        """)

    def update_ping_badge(self, ping_ms, status: str):
        if status == "ok" and ping_ms is not None:
            self.ping_btn.setText(f"⚡ {ping_ms:.0f} ms")
            self.ping_btn.setStyleSheet("""
                background-color: rgba(16, 185, 129, 0.12);
                color: #34d399;
                border: 1px solid rgba(52, 211, 153, 0.35);
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 700;
            """)
        elif status == "high" and ping_ms is not None:
            self.ping_btn.setText(f"⚡ {ping_ms:.0f} ms")
            self.ping_btn.setStyleSheet("""
                background-color: rgba(245, 158, 11, 0.12);
                color: #fbbf24;
                border: 1px solid rgba(245, 158, 11, 0.35);
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 700;
            """)
        elif status == "timeout":
            self.ping_btn.setText("✕ Timeout")
            self.ping_btn.setStyleSheet("""
                background-color: rgba(239, 68, 68, 0.12);
                color: #f87171;
                border: 1px solid rgba(239, 68, 68, 0.35);
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 700;
            """)
        elif status == "error":
            self.ping_btn.setText("✕ Error")
            self.ping_btn.setStyleSheet("""
                background-color: rgba(255, 255, 255, 0.05);
                color: #a1a1aa;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 11px;
            """)
        else:
            self.ping_btn.setText("⟳ Ping")
            self.ping_btn.setStyleSheet("""
                background-color: rgba(255, 255, 255, 0.04);
                color: #a1a1aa;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
            """)

    def _show_context_menu(self):
        menu = QMenu(self)
        
        edit_act = menu.addAction("✏ Edit Config")
        edit_act.triggered.connect(lambda: self.edit_requested.emit(self.config.id))

        qr_act = menu.addAction("📱 Show QR Code (Mobile)")
        qr_act.triggered.connect(lambda: self.qr_requested.emit(self.config.id))

        dup_act = menu.addAction("📑 Duplicate Config")
        dup_act.triggered.connect(lambda: self.duplicate_requested.emit(self.config.id))

        export_act = menu.addAction("💾 Export to .conf")
        export_act.triggered.connect(lambda: self.export_requested.emit(self.config.id))

        menu.addSeparator()

        del_act = menu.addAction("🗑 Delete Config")
        del_act.triggered.connect(lambda: self.delete_requested.emit(self.config.id))

        btn_pos = self.more_btn.mapToGlobal(QPoint(0, self.more_btn.height()))
        menu.exec(btn_pos)
