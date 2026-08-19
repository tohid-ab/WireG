"""
Pure Python & PyQt6 QR Code Generator for WireGuard configs.
Zero external pip dependency required. Works offline and renders directly to QPixmap or QImage.
"""

from typing import List, Optional
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor
from PyQt6.QtCore import Qt


class PureQRCode:
    """
    Standard QR Code generator (Byte Mode, ISO/IEC 18004).
    Generates module matrix for arbitrary text (including WireGuard configs).
    """

    # Galois Field GF(256) tables with primitive polynomial 0x11d (285)
    EXP_TABLE = [0] * 512
    LOG_TABLE = [0] * 256

    @classmethod
    def _init_gf(cls):
        if cls.EXP_TABLE[0] != 0:
            return
        x = 1
        for i in range(255):
            cls.EXP_TABLE[i] = x
            cls.LOG_TABLE[x] = i
            x <<= 1
            if x >= 256:
                x ^= 0x11D
        for i in range(255, 512):
            cls.EXP_TABLE[i] = cls.EXP_TABLE[i - 255]

    @classmethod
    def _gmult(cls, x: int, y: int) -> int:
        if x == 0 or y == 0:
            return 0
        return cls.EXP_TABLE[cls.LOG_TABLE[x] + cls.LOG_TABLE[y]]

    @classmethod
    def _rs_poly(cls, degree: int) -> List[int]:
        cls._init_gf()
        poly = [1]
        for i in range(degree):
            factor = [1, cls.EXP_TABLE[i]]
            new_poly = [0] * (len(poly) + 1)
            for j, p in enumerate(poly):
                new_poly[j] ^= p
                new_poly[j + 1] ^= cls._gmult(p, factor[1])
            poly = new_poly
        return poly

    @classmethod
    def _rs_encode(cls, data: List[int], num_ec: int) -> List[int]:
        poly = cls._rs_poly(num_ec)
        msg = data + [0] * num_ec
        for i in range(len(data)):
            coef = msg[i]
            if coef != 0:
                for j in range(len(poly)):
                    msg[i + j] ^= cls._gmult(poly[j], coef)
        return msg[len(data):]

    # QR Version Specs: (Version, TotalCodewords, ECCodewordsPerBlock, NumBlocksGroup1, DataWordsBlock1, NumBlocksGroup2, DataWordsBlock2)
    # Using Error Correction Level L (approx 7% recovery, best capacity for dense config data)
    VERSION_SPECS = {
        1: (26, 7, 1, 19, 0, 0),
        2: (44, 10, 1, 34, 0, 0),
        3: (70, 15, 1, 55, 0, 0),
        4: (100, 20, 1, 80, 0, 0),
        5: (134, 26, 1, 108, 0, 0),
        6: (172, 18, 2, 68, 0, 0),
        7: (196, 20, 2, 78, 0, 0),
        8: (242, 24, 2, 97, 0, 0),
        9: (292, 30, 2, 116, 0, 0),
        10: (346, 18, 2, 68, 2, 69),
        11: (404, 20, 4, 81, 0, 0),
        12: (466, 24, 2, 92, 2, 93),
        13: (532, 26, 4, 107, 0, 0),
        14: (581, 30, 3, 115, 1, 116),
        15: (655, 22, 5, 87, 1, 88),
        16: (733, 24, 5, 98, 1, 99),
        17: (815, 28, 1, 107, 5, 108),
        18: (901, 30, 5, 120, 1, 121),
        19: (991, 28, 3, 113, 4, 114),
        20: (1085, 28, 3, 107, 5, 108),
    }

    # Alignment pattern center locations for versions 2-20
    ALIGNMENT_LOCATIONS = {
        2: [6, 18],
        3: [6, 22],
        4: [6, 26],
        5: [6, 30],
        6: [6, 34],
        7: [6, 22, 38],
        8: [6, 24, 42],
        9: [6, 26, 46],
        10: [6, 28, 50],
        11: [6, 30, 54],
        12: [6, 32, 58],
        13: [6, 34, 62],
        14: [6, 26, 46, 66],
        15: [6, 26, 48, 70],
        16: [6, 26, 50, 74],
        17: [6, 30, 54, 78],
        18: [6, 30, 56, 82],
        19: [6, 30, 58, 86],
        20: [6, 34, 62, 90],
    }

    def __init__(self, text: str):
        self.text = text
        self.bytes = text.encode("utf-8")
        self.version = self._determine_version()
        self.size = 17 + 4 * self.version
        self.matrix = [[0] * self.size for _ in range(self.size)]
        self.reserved = [[False] * self.size for _ in range(self.size)]
        self._generate()

    def _determine_version(self) -> int:
        data_len = len(self.bytes)
        for ver, spec in self.VERSION_SPECS.items():
            tot_codew, ec_per_blk, b1, d1, b2, d2 = spec
            total_data_capacity = b1 * d1 + b2 * d2
            # Byte mode header: 4 bits mode + (8 or 16 bits count)
            count_bits = 8 if ver <= 9 else 16
            required_bits = 4 + count_bits + data_len * 8
            required_bytes = (required_bits + 7) // 8
            if required_bytes <= total_data_capacity:
                return ver
        raise ValueError(f"Content too large for QR generator: {data_len} bytes")

    def _generate(self):
        self._add_finders()
        self._add_alignments()
        self._add_timing()
        self._add_dark_module()
        self._reserve_format_info()
        data_bits = self._prepare_data_bits()
        codewords = self._bits_to_codewords(data_bits)
        final_stream = self._build_interleaved_data(codewords)
        self._place_data_bits(final_stream)
        mask = self._choose_best_mask()
        self._apply_mask(mask)
        self._write_format_info(mask)

    def _add_finders(self):
        # 3 Finder patterns at top-left, top-right, bottom-left
        corners = [(0, 0), (0, self.size - 7), (self.size - 7, 0)]
        for r, c in corners:
            for y in range(7):
                for x in range(7):
                    is_black = (y == 0 or y == 6 or x == 0 or x == 6 or (2 <= y <= 4 and 2 <= x <= 4))
                    self.matrix[r + y][c + x] = 1 if is_black else 0
                    self.reserved[r + y][c + x] = True

            # Separator ring
            for y in range(-1, 8):
                for x in range(-1, 8):
                    nr, nc = r + y, c + x
                    if 0 <= nr < self.size and 0 <= nc < self.size:
                        self.reserved[nr][nc] = True

    def _add_alignments(self):
        if self.version < 2:
            return
        coords = self.ALIGNMENT_LOCATIONS.get(self.version, [])
        for r in coords:
            for c in coords:
                # Skip if overlapping with finders
                if (r < 9 and c < 9) or (r < 9 and c >= self.size - 8) or (r >= self.size - 8 and c < 9):
                    continue
                for y in range(-2, 3):
                    for x in range(-2, 3):
                        nr, nc = r + y, c + x
                        is_black = (abs(y) == 2 or abs(x) == 2 or (y == 0 and x == 0))
                        self.matrix[nr][nc] = 1 if is_black else 0
                        self.reserved[nr][nc] = True

    def _add_timing(self):
        for i in range(8, self.size - 8):
            bit = 1 if (i % 2 == 0) else 0
            if not self.reserved[6][i]:
                self.matrix[6][i] = bit
                self.reserved[6][i] = True
            if not self.reserved[i][6]:
                self.matrix[i][6] = bit
                self.reserved[i][6] = True

    def _add_dark_module(self):
        self.matrix[4 * self.version + 9][8] = 1
        self.reserved[4 * self.version + 9][8] = True

    def _reserve_format_info(self):
        for i in range(9):
            self.reserved[8][i] = True
            self.reserved[i][8] = True
        for i in range(self.size - 8, self.size):
            self.reserved[8][i] = True
            self.reserved[i][8] = True

    def _prepare_data_bits(self) -> List[int]:
        bits = [0, 1, 0, 0]  # Byte mode indicator
        count = len(self.bytes)
        count_bits = 8 if self.version <= 9 else 16
        for i in range(count_bits - 1, -1, -1):
            bits.append((count >> i) & 1)
        for byte in self.bytes:
            for i in range(7, -1, -1):
                bits.append((byte >> i) & 1)

        spec = self.VERSION_SPECS[self.version]
        tot_data_bytes = spec[2] * spec[3] + spec[4] * spec[5]
        max_bits = tot_data_bytes * 8

        # Terminator
        for _ in range(min(4, max_bits - len(bits))):
            bits.append(0)
        # Pad to byte boundary
        while len(bits) % 8 != 0 and len(bits) < max_bits:
            bits.append(0)
        # Pad bytes 0xEC, 0x11
        pads = [0xEC, 0x11]
        pad_idx = 0
        while len(bits) < max_bits:
            p = pads[pad_idx % 2]
            for i in range(7, -1, -1):
                bits.append((p >> i) & 1)
            pad_idx += 1
        return bits[:max_bits]

    def _bits_to_codewords(self, bits: List[int]) -> List[int]:
        cw = []
        for i in range(0, len(bits), 8):
            v = 0
            for b in bits[i : i + 8]:
                v = (v << 1) | b
            cw.append(v)
        return cw

    def _build_interleaved_data(self, data_cw: List[int]) -> List[int]:
        spec = self.VERSION_SPECS[self.version]
        tot_cw, num_ec, b1, d1, b2, d2 = spec
        blocks = []
        ec_blocks = []
        idx = 0
        for _ in range(b1):
            blk = data_cw[idx : idx + d1]
            idx += d1
            blocks.append(blk)
            ec_blocks.append(self._rs_encode(blk, num_ec))
        for _ in range(b2):
            blk = data_cw[idx : idx + d2]
            idx += d2
            blocks.append(blk)
            ec_blocks.append(self._rs_encode(blk, num_ec))

        interleaved = []
        max_d = max(d1, d2)
        for i in range(max_d):
            for blk in blocks:
                if i < len(blk):
                    interleaved.append(blk[i])
        for i in range(num_ec):
            for ec in ec_blocks:
                interleaved.append(ec[i])
        return interleaved

    def _place_data_bits(self, codewords: List[int]):
        bits = []
        for cw in codewords:
            for i in range(7, -1, -1):
                bits.append((cw >> i) & 1)

        bit_idx = 0
        right = self.size - 1
        upward = True

        while right > 0:
            if right == 6:  # Skip vertical timing column
                right -= 1
            rows = range(self.size - 1, -1, -1) if upward else range(self.size)
            for r in rows:
                for col in [right, right - 1]:
                    if not self.reserved[r][col]:
                        if bit_idx < len(bits):
                            self.matrix[r][col] = bits[bit_idx]
                            bit_idx += 1
                        else:
                            self.matrix[r][col] = 0
            upward = not upward
            right -= 2

    def _mask_cond(self, mask: int, r: int, c: int) -> bool:
        if mask == 0:
            return (r + c) % 2 == 0
        elif mask == 1:
            return r % 2 == 0
        elif mask == 2:
            return c % 3 == 0
        elif mask == 3:
            return (r + c) % 3 == 0
        elif mask == 4:
            return (r // 2 + c // 3) % 2 == 0
        elif mask == 5:
            return ((r * c) % 2 + (r * c) % 3) == 0
        elif mask == 6:
            return (((r * c) % 2 + (r * c) % 3) % 2) == 0
        elif mask == 7:
            return (((r + c) % 2 + (r * c) % 3) % 2) == 0
        return False

    def _apply_mask(self, mask: int):
        for r in range(self.size):
            for c in range(self.size):
                if not self.reserved[r][c] and self._mask_cond(mask, r, c):
                    self.matrix[r][c] ^= 1

    def _choose_best_mask(self) -> int:
        # Default mask pattern 0 (reliable and standard)
        return 0

    def _write_format_info(self, mask: int):
        # Error correction L = 01 (binary 1)
        # Format string for Level L + mask (BCH code + mask 0x5412)
        # Precomputed format info table for L:
        FORMAT_L = [
            0x77C4, 0x72F3, 0x7DAA, 0x789D,
            0x662F, 0x6318, 0x6C41, 0x6976
        ]
        info = FORMAT_L[mask % 8]
        bits = [(info >> i) & 1 for i in range(14, -1, -1)]

        # Top-left format placement
        seq1 = [(8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 7), (8, 8),
                (7, 8), (5, 8), (4, 8), (3, 8), (2, 8), (1, 8), (0, 8)]
        for (r, c), b in zip(seq1, bits):
            self.matrix[r][c] = b

        # Split format placement on edges
        seq2 = [(self.size - 1, 8), (self.size - 2, 8), (self.size - 3, 8), (self.size - 4, 8),
                (self.size - 5, 8), (self.size - 6, 8), (self.size - 7, 8),
                (8, self.size - 8), (8, self.size - 7), (8, self.size - 6), (8, self.size - 5),
                (8, self.size - 4), (8, self.size - 3), (8, self.size - 2), (8, self.size - 1)]
        for (r, c), b in zip(seq2, bits):
            self.matrix[r][c] = b


def generate_qr_pixmap(text: str, pixel_size: int = 300, quiet_zone: int = 4) -> QPixmap:
    """Generates a high quality QPixmap QR code from text."""
    qr = PureQRCode(text)
    matrix = qr.matrix
    mod_count = qr.size + 2 * quiet_zone
    cell_size = max(1, pixel_size // mod_count)
    img_dim = mod_count * cell_size

    img = QImage(img_dim, img_dim, QImage.Format.Format_RGB32)
    img.fill(QColor("#FFFFFF"))

    painter = QPainter(img)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#000000"))

    for r in range(qr.size):
        for c in range(qr.size):
            if matrix[r][c] == 1:
                painter.drawRect(
                    (c + quiet_zone) * cell_size,
                    (r + quiet_zone) * cell_size,
                    cell_size,
                    cell_size
                )
    painter.end()

    return QPixmap.fromImage(img)
