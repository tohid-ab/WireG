import os
import sys
import tempfile
from pathlib import Path
import unittest

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PyQt6.QtWidgets import QApplication

from wireg.core.config_manager import ConfigManager, WireGuardConfig
from wireg.core.wireguard_service import WireGuardService
from wireg.ui.main_window import MainWindow
from wireg.ui.config_editor_dialog import ConfigEditorDialog
from wireg.ui.qr_dialog import QRDialog
from wireg.ui.styles import DARK_THEME_QSS


class TestGUIHeadless(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)
        cls.app.setStyleSheet(DARK_THEME_QSS)

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.json_path = Path(self.tmp_dir.name) / "configs.json"
        self.mgr = ConfigManager(json_path=self.json_path)
        self.service = WireGuardService()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_main_window_lifecycle(self):
        # Add sample config
        cfg = WireGuardConfig(
            name="Test Tunnel",
            interface={"PrivateKey": "aAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=", "Address": "10.0.0.2/32"},
            peer={"PublicKey": "bBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=", "Endpoint": "198.51.100.1:51820"}
        )
        self.mgr.add(cfg)

        win = MainWindow(self.mgr, self.service)
        win.show()

        # Check card exists in map
        self.assertIn(cfg.id, win.cards_map)
        card = win.cards_map[cfg.id]
        self.assertEqual(card.name_label.text(), "Test Tunnel")

        # Test search filter
        win.search_edit.setText("Nonexistent")
        self.assertEqual(len(win.cards_map), 0)

        win.search_edit.setText("Test")
        self.assertEqual(len(win.cards_map), 1)

        win.close()

    def test_editor_dialog(self):
        cfg = WireGuardConfig(
            name="Editor Test",
            interface={"PrivateKey": "aAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=", "Address": "10.0.0.2/32"},
            peer={"PublicKey": "bBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=", "Endpoint": "198.51.100.1:51820"}
        )
        dlg = ConfigEditorDialog(config=cfg)
        self.assertEqual(dlg.name_edit.text(), "Editor Test")
        self.assertEqual(dlg.address_edit.text(), "10.0.0.2/32")
        dlg.close()

    def test_qr_dialog(self):
        cfg = WireGuardConfig(
            name="QR Test",
            interface={"PrivateKey": "aAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=", "Address": "10.0.0.2/32"},
            peer={"PublicKey": "bBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=", "Endpoint": "198.51.100.1:51820"}
        )
        dlg = QRDialog(config=cfg)
        self.assertFalse(dlg.qr_pixmap.isNull())
        dlg.close()


if __name__ == "__main__":
    unittest.main()
