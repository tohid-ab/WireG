from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
)
from ..core.traffic_monitor import format_speed, format_bytes


class TrafficWidget(QFrame):
    """
    shadcn Glassmorphism Hero Traffic Dashboard displaying real-time metrics,
    connection state, and cumulative transfer rates.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("trafficCard")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        # 1. Top row: Status Badge + Active Config Name
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        # shadcn Status Badge Container
        self.status_badge = QFrame()
        badge_layout = QHBoxLayout(self.status_badge)
        badge_layout.setContentsMargins(10, 4, 12, 4)
        badge_layout.setSpacing(6)

        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("font-size: 11px;")
        
        self.status_label = QLabel("Disconnected")
        self.status_label.setStyleSheet("font-size: 12px; font-weight: 700;")

        badge_layout.addWidget(self.status_dot)
        badge_layout.addWidget(self.status_label)
        top_row.addWidget(self.status_badge)

        top_row.addStretch()

        self.tunnel_name_label = QLabel("No active tunnel")
        self.tunnel_name_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #a1a1aa;")
        top_row.addWidget(self.tunnel_name_label)

        layout.addLayout(top_row)

        # 2. Sleek Glass Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: rgba(255, 255, 255, 0.08); max-height: 1px;")
        layout.addWidget(divider)

        # 3. Metrics Stats Grid (3 Columns)
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(14)

        # Column 1: Download Card
        self.dl_card = self._create_metric_card("↓ Download", "0 B/s", "#38bdf8", "rgba(56, 189, 248, 0.12)")
        self.dl_val = self.dl_card.findChild(QLabel, "metricValue")
        stats_layout.addWidget(self.dl_card)

        # Column 2: Upload Card
        self.ul_card = self._create_metric_card("↑ Upload", "0 B/s", "#c084fc", "rgba(192, 132, 252, 0.12)")
        self.ul_val = self.ul_card.findChild(QLabel, "metricValue")
        stats_layout.addWidget(self.ul_card)

        # Column 3: Session Total Card
        self.tot_card = self._create_metric_card("⇄ Total Transfer", "0 B", "#f4f4f5", "rgba(255, 255, 255, 0.06)")
        self.tot_val = self.tot_card.findChild(QLabel, "metricValue")
        stats_layout.addWidget(self.tot_card)

        layout.addLayout(stats_layout)
        self.set_status(False)

    def _create_metric_card(self, title_text: str, default_val: str, accent_color: str, bg_tint: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_tint};
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 10px;
                padding: 4px;
            }}
        """)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(12, 10, 12, 10)
        c_layout.setSpacing(3)

        title = QLabel(title_text)
        title.setStyleSheet(f"color: {accent_color}; font-size: 11px; font-weight: 700; text-transform: uppercase;")

        val = QLabel(default_val)
        val.setObjectName("metricValue")
        val.setStyleSheet("font-size: 17px; font-weight: 800; color: #ffffff;")

        c_layout.addWidget(title)
        c_layout.addWidget(val)
        return card

    def set_status(self, is_connected: bool, tunnel_name: str = "", is_connecting: bool = False):
        if is_connecting:
            self.status_badge.setStyleSheet("""
                QFrame {
                    background-color: rgba(245, 158, 11, 0.15);
                    border: 1px solid rgba(245, 158, 11, 0.35);
                    border-radius: 12px;
                }
            """)
            self.status_dot.setStyleSheet("color: #f59e0b;")
            self.status_label.setText("Connecting...")
            self.status_label.setStyleSheet("color: #fbbf24; font-weight: 700; font-size: 12px;")
            self.tunnel_name_label.setText(tunnel_name)
        elif is_connected:
            self.status_badge.setStyleSheet("""
                QFrame {
                    background-color: rgba(16, 185, 129, 0.15);
                    border: 1px solid rgba(16, 185, 129, 0.4);
                    border-radius: 12px;
                }
            """)
            self.status_dot.setStyleSheet("color: #34d399;")
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet("color: #34d399; font-weight: 700; font-size: 12px;")
            self.tunnel_name_label.setText(f"Active: {tunnel_name}")
            self.tunnel_name_label.setStyleSheet("font-size: 13px; font-weight: 700; color: #34d399;")
        else:
            self.status_badge.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 12px;
                }
            """)
            self.status_dot.setStyleSheet("color: #71717a;")
            self.status_label.setText("Disconnected")
            self.status_label.setStyleSheet("color: #a1a1aa; font-weight: 700; font-size: 12px;")
            self.tunnel_name_label.setText("No active tunnel")
            self.tunnel_name_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #71717a;")
            self.update_traffic(0.0, 0.0, 0, 0)

    def update_traffic(self, rx_speed: float, tx_speed: float, total_rx: int, total_tx: int):
        self.dl_val.setText(format_speed(rx_speed))
        self.ul_val.setText(format_speed(tx_speed))
        self.tot_val.setText(format_bytes(total_rx + total_tx))
