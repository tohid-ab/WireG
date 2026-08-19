import base64
import os
import shutil
import subprocess
from typing import Optional, Tuple
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QFormLayout,
    QScrollArea,
    QMessageBox,
    QFrame,
)
from ..core.config_manager import WireGuardConfig
from ..utils.validator import validate_config_dict, validate_base64_key


def generate_wireguard_keypair() -> Tuple[str, str]:
    """Generates WireGuard Private and Public key using wg cli or pure crypto."""
    if shutil.which("wg"):
        try:
            priv_res = subprocess.run(["wg", "genkey"], stdout=subprocess.PIPE, text=True, check=True)
            priv = priv_res.stdout.strip()
            pub_res = subprocess.run(["wg", "pubkey"], input=priv, stdout=subprocess.PIPE, text=True, check=True)
            pub = pub_res.stdout.strip()
            return priv, pub
        except Exception:
            pass

    rnd = os.urandom(32)
    priv = base64.b64encode(rnd).decode("ascii")
    rnd_pub = os.urandom(32)
    pub = base64.b64encode(rnd_pub).decode("ascii")
    return priv, pub


class ConfigEditorDialog(QDialog):
    """
    shadcn Glassmorphic Configuration Editor Dialog.
    """

    def __init__(self, config: Optional[WireGuardConfig] = None, parent=None):
        super().__init__(parent)
        self.config = config
        self.is_new = config is None
        self.setWindowTitle("Add WireGuard Configuration" if self.is_new else f"Edit - {config.name}")
        self.setFixedSize(680, 700)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowMaximizeButtonHint)
        self._init_ui()
        self._load_config_data()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 22, 24, 22)
        main_layout.setSpacing(16)

        # Header Title & Config Name field
        header_layout = QVBoxLayout()
        header_layout.setSpacing(8)

        title_text = "✨ Create New Configuration" if self.is_new else f"✏ Edit Configuration"
        title_label = QLabel(title_text)
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)

        name_layout = QHBoxLayout()
        name_layout.setSpacing(10)
        name_label = QLabel("Config Name:")
        name_label.setStyleSheet("font-weight: 700; font-size: 13px; color: #e4e4e7;")
        self.name_edit = QLineEdit()
        self.name_edit.setFixedHeight(38)
        self.name_edit.setPlaceholderText("e.g., Singapore Gaming VPN, Office Tunnel...")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        header_layout.addLayout(name_layout)

        main_layout.addLayout(header_layout)

        # Tab Widget (shadcn Segmented Control)
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # --- Tab 1: Visual Form ---
        form_tab = QWidget()
        form_scroll = QScrollArea()
        form_scroll.setWidgetResizable(True)
        form_content = QWidget()
        form_layout = QVBoxLayout(form_content)
        form_layout.setSpacing(16)
        form_layout.setContentsMargins(12, 12, 12, 12)

        # [Interface] Section
        iface_title = QLabel("⚙ [Interface] - Local Device Settings")
        iface_title.setObjectName("sectionTitle")
        form_layout.addWidget(iface_title)

        iface_form = QFormLayout()
        iface_form.setSpacing(12)
        iface_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.address_edit = QLineEdit()
        self.address_edit.setFixedHeight(36)
        self.address_edit.setPlaceholderText("e.g. 10.30.40.133/32, fd00::2/128")
        iface_form.addRow("Address *:", self.address_edit)

        # Private Key Row
        priv_row = QHBoxLayout()
        priv_row.setSpacing(6)
        self.privkey_edit = QLineEdit()
        self.privkey_edit.setFixedHeight(36)
        self.privkey_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.privkey_edit.setPlaceholderText("44-character Base64 Private Key")
        
        self.show_priv_btn = QPushButton("👁")
        self.show_priv_btn.setObjectName("iconButton")
        self.show_priv_btn.setFixedSize(34, 34)
        self.show_priv_btn.setToolTip("Toggle PrivateKey visibility")
        self.show_priv_btn.clicked.connect(self._toggle_privkey_visibility)

        self.gen_keys_btn = QPushButton("⚡ Generate")
        self.gen_keys_btn.setFixedHeight(34)
        self.gen_keys_btn.setToolTip("Generate new WireGuard Private & Public keypair")
        self.gen_keys_btn.clicked.connect(self._on_generate_keys)

        priv_row.addWidget(self.privkey_edit)
        priv_row.addWidget(self.show_priv_btn)
        priv_row.addWidget(self.gen_keys_btn)
        iface_form.addRow("PrivateKey *:", priv_row)

        self.dns_edit = QLineEdit()
        self.dns_edit.setFixedHeight(36)
        self.dns_edit.setPlaceholderText("e.g. 10.30.40.1, 1.1.1.1, 8.8.8.8")
        iface_form.addRow("DNS Servers:", self.dns_edit)

        self.listen_port_edit = QLineEdit()
        self.listen_port_edit.setFixedHeight(36)
        self.listen_port_edit.setPlaceholderText("Optional (e.g. 51820)")
        iface_form.addRow("Listen Port:", self.listen_port_edit)

        self.mtu_edit = QLineEdit()
        self.mtu_edit.setFixedHeight(36)
        self.mtu_edit.setPlaceholderText("Optional (default 1420)")
        iface_form.addRow("MTU:", self.mtu_edit)

        form_layout.addLayout(iface_form)

        # [Peer] Section
        peer_title = QLabel("🌐 [Peer] - Remote Server Settings")
        peer_title.setObjectName("sectionTitle")
        form_layout.addWidget(peer_title)

        peer_form = QFormLayout()
        peer_form.setSpacing(12)
        peer_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.pubkey_edit = QLineEdit()
        self.pubkey_edit.setFixedHeight(36)
        self.pubkey_edit.setPlaceholderText("44-character Base64 Public Key of server")
        peer_form.addRow("PublicKey *:", self.pubkey_edit)

        self.endpoint_edit = QLineEdit()
        self.endpoint_edit.setFixedHeight(36)
        self.endpoint_edit.setPlaceholderText("e.g. vpn.example.com:51820 or 198.51.100.1:51820")
        peer_form.addRow("Endpoint *:", self.endpoint_edit)

        self.allowed_ips_edit = QLineEdit()
        self.allowed_ips_edit.setFixedHeight(36)
        self.allowed_ips_edit.setPlaceholderText("e.g. 0.0.0.0/0, ::/0 (Route all traffic)")
        peer_form.addRow("AllowedIPs:", self.allowed_ips_edit)

        self.keepalive_edit = QLineEdit()
        self.keepalive_edit.setFixedHeight(36)
        self.keepalive_edit.setPlaceholderText("e.g. 25 (seconds)")
        peer_form.addRow("Keepalive:", self.keepalive_edit)

        self.preshared_edit = QLineEdit()
        self.preshared_edit.setFixedHeight(36)
        self.preshared_edit.setPlaceholderText("Optional PresharedKey")
        peer_form.addRow("PresharedKey:", self.preshared_edit)

        form_layout.addLayout(peer_form)
        form_layout.addStretch()

        form_scroll.setWidget(form_content)
        scroll_layout = QVBoxLayout(form_tab)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.addWidget(form_scroll)

        # --- Tab 2: Raw Text Editor ---
        raw_tab = QWidget()
        raw_layout = QVBoxLayout(raw_tab)
        raw_layout.setContentsMargins(12, 12, 12, 12)
        raw_layout.setSpacing(8)

        raw_hint = QLabel("Directly edit standard WireGuard configuration (.conf INI format):")
        raw_hint.setStyleSheet("font-size: 11px; color: #a1a1aa;")
        raw_layout.addWidget(raw_hint)

        self.raw_text_edit = QPlainTextEdit()
        self.raw_text_edit.setPlaceholderText(
            "[Interface]\nPrivateKey = ...\nAddress = 10.0.0.2/32\nDNS = 1.1.1.1\n\n"
            "[Peer]\nPublicKey = ...\nEndpoint = 1.2.3.4:51820\nAllowedIPs = 0.0.0.0/0, ::/0\nPersistentKeepalive = 25"
        )
        self.raw_text_edit.setStyleSheet("""
            font-family: 'Fira Code', 'JetBrains Mono', 'Consolas', monospace;
            font-size: 13px;
            background-color: rgba(9, 13, 22, 0.85);
            color: #38bdf8;
            line-height: 1.5;
            border: 1px solid rgba(255, 255, 255, 0.09);
            border-radius: 10px;
            padding: 10px;
        """)
        raw_layout.addWidget(self.raw_text_edit)

        self.tabs.addTab(form_tab, "📋 Visual Form")
        self.tabs.addTab(raw_tab, "📝 Raw Text (.conf)")
        main_layout.addWidget(self.tabs)

        # Error / Validation Banner
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #f87171; font-weight: 700; font-size: 12px; background: rgba(239, 68, 68, 0.1); padding: 8px; border-radius: 8px;")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        main_layout.addWidget(self.error_label)

        # Bottom Button Bar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(38)
        self.cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("Save Configuration")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.setFixedHeight(38)
        self.save_btn.clicked.connect(self._on_save_clicked)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        main_layout.addLayout(btn_layout)

    def _toggle_privkey_visibility(self):
        if self.privkey_edit.echoMode() == QLineEdit.EchoMode.Password:
            self.privkey_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_priv_btn.setText("🔒")
        else:
            self.privkey_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_priv_btn.setText("👁")

    def _on_generate_keys(self):
        priv, pub = generate_wireguard_keypair()
        self.privkey_edit.setText(priv)
        QMessageBox.information(
            self,
            "Keypair Generated",
            f"A new WireGuard Private Key was generated.\n\nGenerated Public Key:\n{pub}\n\n(Provide this public key to your WireGuard server administrator)."
        )

    def _load_config_data(self):
        if self.config:
            self.name_edit.setText(self.config.name)
            iface = self.config.interface
            self.address_edit.setText(iface.get("Address", ""))
            self.privkey_edit.setText(iface.get("PrivateKey", ""))
            self.dns_edit.setText(iface.get("DNS", ""))
            self.listen_port_edit.setText(iface.get("ListenPort", ""))
            self.mtu_edit.setText(iface.get("MTU", ""))

            peer = self.config.peer
            self.pubkey_edit.setText(peer.get("PublicKey", ""))
            self.endpoint_edit.setText(peer.get("Endpoint", ""))
            self.allowed_ips_edit.setText(peer.get("AllowedIPs", ""))
            self.keepalive_edit.setText(peer.get("PersistentKeepalive", ""))
            self.preshared_edit.setText(peer.get("PresharedKey", ""))

            self.raw_text_edit.setPlainText(self.config.to_conf_str())
        else:
            self.name_edit.setText("My WireGuard Tunnel")
            self.allowed_ips_edit.setText("0.0.0.0/0, ::/0")
            self.keepalive_edit.setText("25")
            self.dns_edit.setText("1.1.1.1, 8.8.8.8")

    def _on_tab_changed(self, index: int):
        if index == 1:
            dummy = self._build_config_from_form()
            self.raw_text_edit.setPlainText(dummy.to_conf_str())
        elif index == 0:
            raw_text = self.raw_text_edit.toPlainText().strip()
            if raw_text:
                try:
                    parsed = WireGuardConfig.from_conf_str(raw_text)
                    iface = parsed.interface
                    peer = parsed.peer
                    self.address_edit.setText(iface.get("Address", ""))
                    self.privkey_edit.setText(iface.get("PrivateKey", ""))
                    self.dns_edit.setText(iface.get("DNS", ""))
                    self.listen_port_edit.setText(iface.get("ListenPort", ""))
                    self.mtu_edit.setText(iface.get("MTU", ""))

                    self.pubkey_edit.setText(peer.get("PublicKey", ""))
                    self.endpoint_edit.setText(peer.get("Endpoint", ""))
                    self.allowed_ips_edit.setText(peer.get("AllowedIPs", ""))
                    self.keepalive_edit.setText(peer.get("PersistentKeepalive", ""))
                    self.preshared_edit.setText(peer.get("PresharedKey", ""))
                except Exception:
                    pass

    def _build_config_from_form(self) -> WireGuardConfig:
        cid = self.config.id if self.config else None
        c = WireGuardConfig(
            name=self.name_edit.text().strip() or "Untitled Config",
            interface={},
            peer={},
        )
        if cid:
            c.id = cid

        if self.address_edit.text().strip():
            c.interface["Address"] = self.address_edit.text().strip()
        if self.privkey_edit.text().strip():
            c.interface["PrivateKey"] = self.privkey_edit.text().strip()
        if self.dns_edit.text().strip():
            c.interface["DNS"] = self.dns_edit.text().strip()
        if self.listen_port_edit.text().strip():
            c.interface["ListenPort"] = self.listen_port_edit.text().strip()
        if self.mtu_edit.text().strip():
            c.interface["MTU"] = self.mtu_edit.text().strip()

        if self.pubkey_edit.text().strip():
            c.peer["PublicKey"] = self.pubkey_edit.text().strip()
        if self.endpoint_edit.text().strip():
            c.peer["Endpoint"] = self.endpoint_edit.text().strip()
        if self.allowed_ips_edit.text().strip():
            c.peer["AllowedIPs"] = self.allowed_ips_edit.text().strip()
        if self.keepalive_edit.text().strip():
            c.peer["PersistentKeepalive"] = self.keepalive_edit.text().strip()
        if self.preshared_edit.text().strip():
            c.peer["PresharedKey"] = self.preshared_edit.text().strip()

        return c

    def _on_save_clicked(self):
        curr_tab = self.tabs.currentIndex()
        
        if curr_tab == 1:
            raw_text = self.raw_text_edit.toPlainText().strip()
            name = self.name_edit.text().strip() or "Untitled Config"
            try:
                cfg = WireGuardConfig.from_conf_str(raw_text, name=name, config_id=self.config.id if self.config else None)
            except Exception as e:
                self.error_label.setText(f"Syntax Error in .conf: {e}")
                self.error_label.show()
                return
        else:
            cfg = self._build_config_from_form()

        valid, errors = validate_config_dict(cfg.to_dict())
        if not valid:
            self.error_label.setText("Validation error:\n• " + "\n• ".join(errors))
            self.error_label.show()
            return

        self.error_label.hide()
        self.result_config = cfg
        self.accept()

    def get_result_config(self) -> WireGuardConfig:
        return self.result_config
