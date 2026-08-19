from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QApplication,
    QMessageBox,
    QFrame,
)
from PyQt6.QtGui import QPixmap

from ..core.config_manager import WireGuardConfig
from ..core.qr_generator import generate_qr_pixmap


class QRDialog(QDialog):
    """
    shadcn Glassmorphic Dialog displaying a QR Code for mobile WireGuard configuration.
    """

    def __init__(self, config: WireGuardConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle(f"Mobile QR Code - {config.name}")
        self.setFixedSize(380, 480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowMaximizeButtonHint)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        title = QLabel(self.config.name)
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Scan with WireGuard app on iOS or Android")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # QR Code Container Frame with crisp glass effect
        qr_frame = QFrame()
        qr_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 16px;
                padding: 12px;
            }
        """)
        qr_layout = QVBoxLayout(qr_frame)
        qr_layout.setContentsMargins(10, 10, 10, 10)

        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_pixmap = generate_qr_pixmap(self.config.to_conf_str(), pixel_size=260)
        self.qr_label.setPixmap(self.qr_pixmap)
        qr_layout.addWidget(self.qr_label)

        layout.addWidget(qr_frame, alignment=Qt.AlignmentFlag.AlignCenter)

        # Actions Row
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        self.copy_btn = QPushButton("📋 Copy Text")
        self.copy_btn.setFixedHeight(36)
        self.copy_btn.clicked.connect(self._on_copy_clicked)

        self.save_btn = QPushButton("💾 Save QR")
        self.save_btn.setFixedHeight(36)
        self.save_btn.clicked.connect(self._on_save_clicked)

        actions_layout.addWidget(self.copy_btn)
        actions_layout.addWidget(self.save_btn)
        layout.addLayout(actions_layout)

        # Close Button
        close_btn = QPushButton("Close")
        close_btn.setObjectName("primaryButton")
        close_btn.setFixedHeight(36)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _on_copy_clicked(self):
        cb = QApplication.clipboard()
        cb.setText(self.config.to_conf_str())
        QMessageBox.information(self, "Copied", "Configuration copied to clipboard.")

    def _on_save_clicked(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save QR Code Image",
            f"{self.config.name}_qr.png",
            "PNG Images (*.png)"
        )
        if file_path:
            self.qr_pixmap.save(file_path, "PNG")
            QMessageBox.information(self, "Saved", f"QR Code saved to:\n{file_path}")
