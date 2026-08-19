import os
import unittest
from PyQt6.QtWidgets import QApplication
import sys

from wireg.core.qr_generator import PureQRCode, generate_qr_pixmap


class TestQRGenerator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_pure_qr_generation(self):
        sample_text = (
            "[Interface]\n"
            "PrivateKey = aAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=\n"
            "Address = 10.0.0.2/32\n"
            "DNS = 1.1.1.1\n\n"
            "[Peer]\n"
            "PublicKey = bBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=\n"
            "AllowedIPs = 0.0.0.0/0, ::/0\n"
            "Endpoint = vpn.example.com:51820\n"
            "PersistentKeepalive = 25\n"
        )
        qr = PureQRCode(sample_text)
        self.assertGreater(qr.version, 1)
        self.assertGreater(qr.size, 21)
        self.assertEqual(len(qr.matrix), qr.size)
        self.assertEqual(len(qr.matrix[0]), qr.size)

        # Generate QPixmap
        pix = generate_qr_pixmap(sample_text, pixel_size=300)
        self.assertFalse(pix.isNull())
        self.assertGreater(pix.width(), 200)
        self.assertGreater(pix.height(), 200)


if __name__ == "__main__":
    unittest.main()
