"""Self-check for the density patch. Run: python tools/test_build.py"""
import struct

from build import DENSITY_COLS, LEVELS_RECORD, density_bin, density_txt

header = b'Name\t' + b'\t'.join(c.encode() for c in DENSITY_COLS) + b'\tOther'
row = b'Lvl\t100\t200\t300\t1\t2\t3\t4\t5\t60\t7'
blank = b'Town\t\t\t\t\t\t\t\t\t\t7'
txt = density_txt(b'\r\n'.join([header, row, blank, b'']), 5)
assert txt == b'\r\n'.join([header, b'Lvl\t500\t1000\t1500\t5\t10\t15\t20\t25\t255\t7', blank, b'']), txt

rec = bytearray(LEVELS_RECORD)
struct.pack_into('<3i', rec, 28, 100, 200, 300)
rec[40:46] = bytes([1, 2, 3, 4, 5, 60])
out = density_bin(struct.pack('<I', 1) + bytes(rec), 5)
assert struct.unpack_from('<3i', out, 4 + 28) == (500, 1000, 1500)
assert list(out[4 + 40:4 + 46]) == [5, 10, 15, 20, 25, 255]
assert out[4 + 46:] == bytes(LEVELS_RECORD - 46)
print('ok')
