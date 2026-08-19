import os
from pathlib import Path
from typing import List, Optional
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QIcon
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QScrollArea,
    QFileDialog,
    QMessageBox,
    QProgressBar,
    QFrame,
    QApplication,
    QSystemTrayIcon,
)

from ..core.config_manager import ConfigManager, WireGuardConfig
from ..core.wireguard_service import WireGuardService
from ..core.ping_tester import PingTester
from ..core.traffic_monitor import TrafficMonitor
from .config_card import ConfigCard
from .config_editor_dialog import ConfigEditorDialog
from .qr_dialog import QRDialog
from .traffic_widget import TrafficWidget
from .tray_icon import WireGTrayIcon, create_tray_icon_pixmap


class MainWindow(QMainWindow):
    """
    shadcn Glassmorphism Main Application Window for WireG.
    """

    def __init__(self, config_manager: ConfigManager, wg_service: WireGuardService):
        super().__init__()
        self.config_manager = config_manager
        self.wg_service = wg_service
        self.ping_tester = PingTester()
        self.traffic_monitor = TrafficMonitor()

        self.cards_map = {}
        self.current_sort = "name_asc"
        self.favorites_only = False
        self.search_query = ""

        self.setWindowTitle("WireG - WireGuard Client")
        # Locked / Fixed Window Size as requested
        self.setFixedSize(720, 800)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowMaximizeButtonHint)
        self.setAcceptDrops(True)

        self._init_ui()
        self._init_tray()
        self._connect_signals()
        self.refresh_configs_list()

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 18, 20, 18)
        main_layout.setSpacing(14)

        # 1. Top Header Bar (shadcn glass header)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        # Branding
        brand_layout = QVBoxLayout()
        brand_layout.setSpacing(1)

        logo_label = QLabel("🛡 WireG")
        logo_label.setStyleSheet("font-size: 22px; font-weight: 900; color: #818cf8; letter-spacing: -0.5px;")

        sub_label = QLabel("Next-Gen WireGuard Manager")
        sub_label.setStyleSheet("font-size: 11px; color: #71717a; font-weight: 500;")

        brand_layout.addWidget(logo_label)
        brand_layout.addWidget(sub_label)
        header_layout.addLayout(brand_layout)

        header_layout.addStretch()

        # Header Action Buttons
        self.ping_all_btn = QPushButton("⚡ Ping All")
        self.ping_all_btn.setToolTip("Test latency for all configurations")
        self.ping_all_btn.setFixedHeight(36)
        self.ping_all_btn.clicked.connect(self._on_ping_all_clicked)

        self.import_btn = QPushButton("📁 Import .conf")
        self.import_btn.setToolTip("Import WireGuard configuration file (.conf)")
        self.import_btn.setFixedHeight(36)
        self.import_btn.clicked.connect(self._on_import_clicked)

        self.add_btn = QPushButton("＋ Add Config")
        self.add_btn.setObjectName("primaryButton")
        self.add_btn.setToolTip("Create new configuration manually")
        self.add_btn.setFixedHeight(36)
        self.add_btn.clicked.connect(self._on_add_clicked)

        header_layout.addWidget(self.ping_all_btn)
        header_layout.addWidget(self.import_btn)
        header_layout.addWidget(self.add_btn)

        main_layout.addLayout(header_layout)

        # 2. Hero Traffic & Status Card
        self.traffic_widget = TrafficWidget()
        main_layout.addWidget(self.traffic_widget)

        # 3. Search & Sort Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(10)

        # Search Bar with clear icon
        self.search_edit = QLineEdit()
        self.search_edit.setFixedHeight(38)
        self.search_edit.setPlaceholderText("🔍 Search configs by name, endpoint, IP...")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._on_search_changed)
        toolbar_layout.addWidget(self.search_edit, stretch=2)

        # Sort Dropdown
        self.sort_combo = QComboBox()
        self.sort_combo.setFixedHeight(38)
        self.sort_combo.addItem("🔤 Name (A → Z)", "name_asc")
        self.sort_combo.addItem("🔤 Name (Z → A)", "name_desc")
        self.sort_combo.addItem("⚡ Lowest Ping", "ping_asc")
        self.sort_combo.addItem("⚡ Highest Ping", "ping_desc")
        self.sort_combo.addItem("⏱ Recently Used", "last_connected")
        self.sort_combo.addItem("📅 Date Added", "created_at")
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        toolbar_layout.addWidget(self.sort_combo, stretch=1)

        # Favorites Filter Toggle
        self.fav_filter_btn = QPushButton("★ Favorites")
        self.fav_filter_btn.setFixedHeight(38)
        self.fav_filter_btn.setCheckable(True)
        self.fav_filter_btn.setToolTip("Show only starred/favorite configurations")
        self.fav_filter_btn.clicked.connect(self._on_fav_filter_toggled)
        toolbar_layout.addWidget(self.fav_filter_btn)

        main_layout.addLayout(toolbar_layout)

        # Batch Ping Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.04);
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #38bdf8);
                border-radius: 2px;
            }
        """)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        # 4. Scrollable Configs List
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)
        self.cards_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area, stretch=1)

        # 5. Bottom Hint Banner
        self.drop_hint = QLabel("✨ Tip: Drag & drop .conf files anywhere into this window to import instantly.")
        self.drop_hint.setStyleSheet("font-size: 11px; color: #52525b; padding: 2px;")
        self.drop_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.drop_hint)

    def _init_tray(self):
        self.tray_icon = WireGTrayIcon(self)
        self.tray_icon.show_window_requested.connect(self._show_and_activate)
        self.tray_icon.toggle_connect_requested.connect(self._on_tray_toggle_connect)
        self.tray_icon.quit_requested.connect(self._on_app_quit)
        self.tray_icon.show()
        self.setWindowIcon(QIcon(create_tray_icon_pixmap(False)))

    def _connect_signals(self):
        self.wg_service.connected.connect(self._on_wg_connected)
        self.wg_service.disconnected.connect(self._on_wg_disconnected)
        self.wg_service.error_occurred.connect(self._on_wg_error)
        self.wg_service.busy_changed.connect(self._on_wg_busy)

        self.ping_tester.ping_result.connect(self._on_ping_result)
        self.ping_tester.batch_progress.connect(self._on_batch_progress)
        self.ping_tester.batch_finished.connect(self._on_batch_finished)

        self.traffic_monitor.stats_updated.connect(self.traffic_widget.update_traffic)

    def refresh_configs_list(self):
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.cards_map.clear()
        configs = self.config_manager.search_and_sort(
            query=self.search_query,
            sort_by=self.current_sort,
            favorites_first=True
        )

        if self.favorites_only:
            configs = [c for c in configs if c.is_favorite]

        if not configs:
            empty_frame = QFrame()
            empty_frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 255, 255, 0.02);
                    border: 1px dashed rgba(255, 255, 255, 0.1);
                    border-radius: 16px;
                }
            """)
            empty_layout = QVBoxLayout(empty_frame)
            empty_layout.setContentsMargins(24, 48, 24, 48)
            empty_layout.setSpacing(14)
            empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            icon_lbl = QLabel("🛡")
            icon_lbl.setStyleSheet("font-size: 42px; color: #6366f1;")
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(icon_lbl)

            msg_lbl = QLabel("No WireGuard configurations found." if not self.search_query else "No matching configurations found.")
            msg_lbl.setStyleSheet("font-size: 15px; color: #a1a1aa; font-weight: 700;")
            msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(msg_lbl)

            if not self.search_query:
                btn_import_empty = QPushButton("📁 Import .conf File")
                btn_import_empty.setObjectName("primaryButton")
                btn_import_empty.setFixedHeight(36)
                btn_import_empty.clicked.connect(self._on_import_clicked)
                empty_layout.addWidget(btn_import_empty, alignment=Qt.AlignmentFlag.AlignCenter)

            self.cards_layout.insertWidget(0, empty_frame)
            return

        for i, cfg in enumerate(configs):
            is_active = (self.wg_service.active_config_id == cfg.id)
            card = ConfigCard(cfg, is_active=is_active)

            card.connect_requested.connect(self._on_connect_card)
            card.disconnect_requested.connect(self._on_disconnect_card)
            card.edit_requested.connect(self._on_edit_card)
            card.delete_requested.connect(self._on_delete_card)
            card.duplicate_requested.connect(self._on_duplicate_card)
            card.export_requested.connect(self._on_export_card)
            card.qr_requested.connect(self._on_qr_card)
            card.ping_requested.connect(self._on_ping_single_card)
            card.favorite_toggled.connect(self._on_favorite_toggled)

            self.cards_map[cfg.id] = card
            self.cards_layout.insertWidget(i, card)

    def _on_search_changed(self, text: str):
        self.search_query = text
        self.refresh_configs_list()

    def _on_sort_changed(self, index: int):
        self.current_sort = self.sort_combo.currentData()
        self.refresh_configs_list()

    def _on_fav_filter_toggled(self, checked: bool):
        self.favorites_only = checked
        if checked:
            self.fav_filter_btn.setStyleSheet("""
                background-color: rgba(251, 191, 36, 0.2);
                border: 1px solid rgba(251, 191, 36, 0.5);
                color: #fbbf24;
                font-weight: 700;
            """)
        else:
            self.fav_filter_btn.setStyleSheet("")
        self.refresh_configs_list()

    def _on_add_clicked(self):
        dlg = ConfigEditorDialog(parent=self)
        if dlg.exec():
            cfg = dlg.get_result_config()
            self.config_manager.add(cfg)
            self.refresh_configs_list()

    def _on_import_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import WireGuard Configuration",
            str(Path.home()),
            "WireGuard Configs (*.conf);;All Files (*)"
        )
        if file_path:
            self._import_file(file_path)

    def _import_file(self, file_path: str):
        try:
            cfg = self.config_manager.import_from_file(file_path)
            self.refresh_configs_list()
            QMessageBox.information(self, "Success", f"Successfully imported '{cfg.name}'.")
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import configuration:\n{e}")

    def _on_connect_card(self, config_id: str):
        cfg = self.config_manager.get_by_id(config_id)
        if cfg:
            self.wg_service.connect(cfg)

    def _on_disconnect_card(self, config_id: str):
        self.wg_service.disconnect()

    def _on_edit_card(self, config_id: str):
        cfg = self.config_manager.get_by_id(config_id)
        if not cfg:
            return
        dlg = ConfigEditorDialog(config=cfg, parent=self)
        if dlg.exec():
            updated_cfg = dlg.get_result_config()
            self.config_manager.update(updated_cfg)
            self.refresh_configs_list()

    def _on_delete_card(self, config_id: str):
        cfg = self.config_manager.get_by_id(config_id)
        if not cfg:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{cfg.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.wg_service.active_config_id == config_id:
                self.wg_service.disconnect()
            self.config_manager.delete(config_id)
            self.refresh_configs_list()

    def _on_duplicate_card(self, config_id: str):
        new_cfg = self.config_manager.duplicate(config_id)
        if new_cfg:
            self.refresh_configs_list()

    def _on_export_card(self, config_id: str):
        cfg = self.config_manager.get_by_id(config_id)
        if not cfg:
            return
        clean_name = "".join(c for c in cfg.name if c.isalnum() or c in (" ", "_", "-")).rstrip()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Configuration",
            f"{clean_name}.conf",
            "WireGuard Configs (*.conf)"
        )
        if file_path:
            if self.config_manager.export_to_file(config_id, file_path):
                QMessageBox.information(self, "Exported", f"Exported successfully to:\n{file_path}")
            else:
                QMessageBox.critical(self, "Error", "Failed to export configuration.")

    def _on_qr_card(self, config_id: str):
        cfg = self.config_manager.get_by_id(config_id)
        if cfg:
            dlg = QRDialog(cfg, parent=self)
            dlg.exec()

    def _on_ping_single_card(self, config_id: str):
        cfg = self.config_manager.get_by_id(config_id)
        if cfg and config_id in self.cards_map:
            self.cards_map[config_id].set_ping_testing()
            self.ping_tester.test_single(cfg)

    def _on_favorite_toggled(self, config_id: str):
        self.config_manager.toggle_favorite(config_id)
        self.refresh_configs_list()

    def _on_ping_all_clicked(self):
        configs = self.config_manager.get_all()
        if not configs:
            return
        self.ping_all_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.show()

        for c_id, card in self.cards_map.items():
            card.set_ping_testing()

        self.ping_tester.test_all(configs)

    def _on_batch_progress(self, current: int, total: int):
        if total > 0:
            self.progress_bar.setValue(int((current / total) * 100))

    def _on_batch_finished(self):
        self.ping_all_btn.setEnabled(True)
        self.progress_bar.hide()
        if "ping" in self.current_sort:
            self.refresh_configs_list()

    def _on_ping_result(self, config_id: str, latency, status: str):
        self.config_manager.update_ping_result(config_id, latency, status)
        if config_id in self.cards_map:
            self.cards_map[config_id].update_ping_badge(latency, status)

    def _on_wg_connected(self, config_id: str):
        self.config_manager.update_last_connected(config_id)
        cfg = self.config_manager.get_by_id(config_id)
        name = cfg.name if cfg else "Tunnel"

        self.traffic_widget.set_status(True, name)
        self.tray_icon.update_status(True, name)
        self.tray_icon.notify("WireG Connected", f"Successfully connected to {name}")
        self.setWindowIcon(QIcon(create_tray_icon_pixmap(True)))
        self.traffic_monitor.start()
        self.refresh_configs_list()

    def _on_wg_disconnected(self):
        self.traffic_monitor.stop()
        self.traffic_widget.set_status(False)
        self.tray_icon.update_status(False)
        self.tray_icon.notify("WireG Disconnected", "WireGuard tunnel closed")
        self.setWindowIcon(QIcon(create_tray_icon_pixmap(False)))
        self.refresh_configs_list()

    def _on_wg_error(self, message: str):
        self.tray_icon.notify("Connection Error", message, is_error=True)
        QMessageBox.critical(self, "WireGuard Error", message)

    def _on_wg_busy(self, is_busy: bool, status_text: str):
        if is_busy:
            self.traffic_widget.set_status(False, status_text, is_connecting=True)
        else:
            is_active = self.wg_service.is_interface_active()
            cfg_name = self.wg_service.active_config_name or ""
            self.traffic_widget.set_status(is_active, cfg_name)

    def _show_and_activate(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _on_tray_toggle_connect(self):
        if self.wg_service.is_interface_active():
            self.wg_service.disconnect()
        else:
            configs = self.config_manager.get_all()
            if configs:
                favs = [c for c in configs if c.is_favorite]
                target = favs[0] if favs else configs[0]
                self.wg_service.connect(target)
            else:
                self._show_and_activate()

    def _on_app_quit(self):
        if self.wg_service.is_interface_active():
            self.wg_service.disconnect()
        QApplication.quit()

    def closeEvent(self, event):
        if self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage(
                "WireG Minimized",
                "WireG is running in the background. Click the tray icon to reopen.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            event.ignore()
        else:
            event.accept()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().endswith(".conf"):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        imported_count = 0
        for url in urls:
            local_path = url.toLocalFile()
            if local_path.endswith(".conf") and os.path.isfile(local_path):
                try:
                    self.config_manager.import_from_file(local_path)
                    imported_count += 1
                except Exception as e:
                    QMessageBox.warning(self, "Import Error", f"Error importing {local_path}:\n{e}")
        if imported_count > 0:
            self.refresh_configs_list()
            QMessageBox.information(self, "Success", f"Successfully imported {imported_count} configuration(s).")
