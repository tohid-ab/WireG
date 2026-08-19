import os
import tempfile
from pathlib import Path
import unittest

from wireg.core.config_manager import WireGuardConfig, ConfigManager
from wireg.utils.validator import validate_config_dict, validate_base64_key, validate_endpoint


USER_SAMPLE_CONFIG = """[Interface]
PrivateKey = aAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=
Address = 10.0.0.2/32
DNS = 1.1.1.1, 8.8.8.8

[Peer]
PublicKey = bBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=
AllowedIPs = 0.0.0.0/0, ::/0
Endpoint = vpn.example.com:51820
PersistentKeepalive = 25
"""


class TestConfigManager(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.json_path = Path(self.tmp_dir.name) / "configs.json"
        self.mgr = ConfigManager(json_path=self.json_path)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_parse_user_sample_config(self):
        cfg = WireGuardConfig.from_conf_str(USER_SAMPLE_CONFIG, name="Sample Tunnel")
        self.assertEqual(cfg.name, "Sample Tunnel")
        self.assertEqual(cfg.interface.get("PrivateKey"), "aAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
        self.assertEqual(cfg.interface.get("Address"), "10.0.0.2/32")
        self.assertEqual(cfg.interface.get("DNS"), "1.1.1.1, 8.8.8.8")
        self.assertEqual(cfg.peer.get("PublicKey"), "bBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=")
        self.assertEqual(cfg.peer.get("AllowedIPs"), "0.0.0.0/0, ::/0")
        self.assertEqual(cfg.peer.get("Endpoint"), "vpn.example.com:51820")
        self.assertEqual(cfg.peer.get("PersistentKeepalive"), "25")

        host, port = cfg.get_endpoint_host_and_port()
        self.assertEqual(host, "vpn.example.com")
        self.assertEqual(port, 51820)

        # Validation
        valid, errors = validate_config_dict(cfg.to_dict())
        self.assertTrue(valid, f"Validation failed with errors: {errors}")

    def test_crud_and_json_persistence(self):
        cfg1 = WireGuardConfig.from_conf_str(USER_SAMPLE_CONFIG, name="Server 1")
        self.mgr.add(cfg1)
        self.assertEqual(len(self.mgr.get_all()), 1)

        # Verify JSON file exists on disk
        self.assertTrue(self.json_path.exists())

        # Reload manager from disk
        mgr2 = ConfigManager(json_path=self.json_path)
        loaded = mgr2.get_by_id(cfg1.id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.name, "Server 1")
        self.assertEqual(loaded.peer.get("Endpoint"), "vpn.example.com:51820")

        # Update
        loaded.name = "Renamed Server"
        loaded.is_favorite = True
        mgr2.update(loaded)

        mgr3 = ConfigManager(json_path=self.json_path)
        updated = mgr3.get_by_id(cfg1.id)
        self.assertEqual(updated.name, "Renamed Server")
        self.assertTrue(updated.is_favorite)

        # Delete
        self.assertTrue(mgr3.delete(cfg1.id))
        self.assertEqual(len(mgr3.get_all()), 0)

    def test_search_and_sort(self):
        c1 = WireGuardConfig(name="Alpha VPN", peer={"Endpoint": "alpha.com:51820"}, last_ping=120.0, last_ping_status="ok")
        c2 = WireGuardConfig(name="Beta VPN", peer={"Endpoint": "beta.net:51820"}, is_favorite=True, last_ping=45.0, last_ping_status="ok")
        c3 = WireGuardConfig(name="Gamma Gaming", peer={"Endpoint": "10.0.0.1:51820"}, last_ping=350.0, last_ping_status="high")

        self.mgr.add(c1)
        self.mgr.add(c2)
        self.mgr.add(c3)

        # Search by name
        res = self.mgr.search_and_sort(query="Gamma")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].name, "Gamma Gaming")

        # Search by endpoint
        res = self.mgr.search_and_sort(query="beta.net")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].name, "Beta VPN")

        # Sort by ping ascending (favorites still first by default)
        res_ping = self.mgr.search_and_sort(sort_by="ping_asc")
        self.assertEqual(res_ping[0].name, "Beta VPN")  # Favorite + lowest ping

    def test_export_import_roundtrip(self):
        cfg = WireGuardConfig.from_conf_str(USER_SAMPLE_CONFIG, name="Export Test")
        self.mgr.add(cfg)

        export_path = Path(self.tmp_dir.name) / "exported.conf"
        self.assertTrue(self.mgr.export_to_file(cfg.id, str(export_path)))
        self.assertTrue(export_path.exists())

        # Read back
        imported = self.mgr.import_from_file(str(export_path), custom_name="Reimported")
        self.assertEqual(imported.name, "Reimported")
        self.assertEqual(imported.peer.get("Endpoint"), "vpn.example.com:51820")


if __name__ == "__main__":
    unittest.main()
